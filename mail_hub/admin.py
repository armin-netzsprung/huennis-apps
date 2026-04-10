import json
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.safestring import mark_safe
from django.core.management import call_command
from .services.crypto import encrypt_string # statt encrypt_data

from .models import MailAccount, FetchedEmail, MailAuditLog
from .services.oauth_outlook_device import connect_outlook_account_db, complete_device_flow_for_account

@admin.register(MailAccount)
class MailAccountAdmin(admin.ModelAdmin):
    # 1. Anzeige in der Liste
    list_display = ('id', 'email_address', 'user', 'auth_type', 'is_active', 'last_sync_at')
    list_display_links = ('id', 'email_address')
    list_filter = ('auth_type', 'is_active')
    actions = ['sync_selected_accounts']

    # 2. Felder in der Bearbeitungsmaske
    readonly_fields = ('microsoft_login_link', 'oauth_token_expires')
    
    fields = (
        'email_address', 'user', 'auth_type', 'is_active', 
        'imap_host', 'encrypted_credentials', 
        'microsoft_login_link', 
        'oauth_token_expires'
    )

    # 3. Der Button-Generator
    def microsoft_login_link(self, obj):
        if obj.pk and obj.auth_type == 'ms_graph':
            url = f"/admin/mail_hub/mailaccount/{obj.pk}/connect-microsoft/"
            return mark_safe(f'<a class="button" href="{url}" style="background: #007bff; color: white; padding: 5px 10px; border-radius: 4px;">🚀 Mit Microsoft verbinden</a>')
        return "Nur für Microsoft-Konten (OAuth2) verfügbar"
    
    microsoft_login_link.short_description = "Microsoft Aktion"

    # 4. Custom URLs für den OAuth-Flow
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/connect-microsoft/', self.connect_microsoft, name='connect-microsoft'),
        ]
        return custom_urls + urls

    # 5. Die View für den Device-Flow in admin.py
    def connect_microsoft(self, request, pk):
        account = self.get_object(request, pk)
        
        if request.method == 'POST' and 'flow_data' in request.POST:
            try:
                flow = json.loads(request.POST.get('flow_data'))
                
                # Wir rufen die Funktion auf und fangen das Ergebnis sicher ab
                outcome = complete_device_flow_for_account(account, flow)
                
                # outcome ist ein Tuple: (Session, Result-Dict) oder None
                if outcome and outcome[0] is not None: 
                    session, result = outcome
                    messages.success(request, f"Konto {account.email_address} erfolgreich verbunden!")
                    return redirect(f'/admin/mail_hub/mailaccount/{pk}/change/')
                else:
                    # Wenn outcome[0] None ist, gab es einen Fehler von Microsoft
                    result = outcome[1] if outcome else {}
                    error_msg = result.get('error_description', 'Timeout oder Konfigurationsfehler')
                    messages.error(request, f"Fehler bei der Verbindung: {error_msg}")
                    return redirect(f'/admin/mail_hub/mailaccount/{pk}/change/')
            except Exception as e:
                messages.error(request, f"Technischer Fehler beim Abschluss: {str(e)}")
                return redirect(f'/admin/mail_hub/mailaccount/{pk}/change/')

        # Initialer Flow-Start (GET Request)
        session, device_info = connect_outlook_account_db(account, web_interactive=True)
        
        if not device_info:
            messages.error(request, "Konnte keine Verbindung zu Microsoft aufbauen. Prüfen Sie die Client-ID in den Settings.")
            return redirect(f'/admin/mail_hub/mailaccount/{pk}/change/')

        return render(request, 'admin/mail_hub/microsoft_auth.html', {
            'account': account,
            'device_info': device_info,
            'flow_json': json.dumps(device_info['flow'])
        })
    
    # 6. Aktion: Manueller Sync aus der Liste
    def sync_selected_accounts(self, request, queryset):
        for account in queryset:
            call_command('mail_runner', account=account.email_address)
        self.message_user(request, f"Sync für {queryset.count()} Konten wurde angestoßen.")
    def save_model(self, request, obj, form, change):
        """
        Prüft beim Speichern, ob das Passwort im Klartext vorliegt 
        und verschlüsselt es ggf. automatisch.
        """
        if obj.encrypted_credentials:
            # Wir prüfen, ob es bereits verschlüsselt ist. 
            # Fernet-Tokens (Standard in cryptography) starten meist mit 'gAAAA'
            if not obj.encrypted_credentials.startswith('gAAAA'):
                # Es ist Klartext -> Verschlüsseln!
                raw_password = obj.encrypted_credentials
                obj.encrypted_credentials = encrypt_string(raw_password)
        
        super().save_model(request, obj, form, change)

    sync_selected_accounts.short_description = "Ausgewählte Konten jetzt synchronisieren"

from django.contrib import admin
from .models import FetchedEmail, MailAuditLog

class MailAuditLogInline(admin.TabularInline):
    model = MailAuditLog
    extra = 0
    readonly_fields = ('timestamp', 'action', 'details')
    can_delete = False

@admin.register(FetchedEmail)
class FetchedEmailAdmin(admin.ModelAdmin):
    # 'file_path' in die Liste aufnehmen
    list_display = ('subject', 'account', 'folder_name', 'date_sent', 'get_file_info')
    list_filter = ('account', 'folder_name')
    search_fields = ('subject', 'from_addr', 'to_addr', 'search_index_text')
    readonly_fields = ('message_id_hash', 'file_path', 'date_sent')
    inlines = [MailAuditLogInline]

    def get_file_info(self, obj):
        """
        Zeigt nur den Dateinamen an, damit die Spalte nicht zu breit wird, 
        und gibt einen Hinweis, wenn der physische Pfad vom logischen Ordner abweicht.
        """
        if not obj.file_path:
            return "-"
        
        filename = obj.file_path.split('/')[-1]
        
        # Kleiner visueller Check: Liegt die Datei im aktuellen Ordner?
        # Wir prüfen, ob der folder_name im file_path vorkommt
        if obj.folder_name and obj.folder_name not in obj.file_path:
            return f"📂 {filename} (Moved)"
        
        return filename

    get_file_info.short_description = "Dateiname / Status"

@admin.register(MailAuditLog)
class MailAuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'get_account', 'action', 'get_email_subject', 'details')
    list_filter = ('action', 'timestamp', 'email__account')
    search_fields = ('email__subject', 'details')
    readonly_fields = ('timestamp', 'email', 'action', 'details')

    def get_email_subject(self, obj):
        return obj.email.subject
    get_email_subject.short_description = "Betreff"

    def get_account(self, obj):
        return obj.email.account
    get_account.short_description = "Konto"
