from pyexpat.errors import messages

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Count  # WICHTIG: Hier Q und Count importieren
from .models import FetchedEmail, MailAccount, MailSignature
from mail_hub.services.mail_parser import get_mail_content
# mail_hub/views.py hinzufügen:
from .services.oauth_outlook_device import connect_outlook_account_db, complete_device_flow_for_account

# --- HELFER ---
def get_base_context(user):
    """Zentralisiert die Sidebar-Daten."""
    accounts = MailAccount.objects.filter(user=user)
    for acc in accounts:
        # dynamic_folders berechnen für die Sidebar-Anzeige
        acc.dynamic_folders = FetchedEmail.objects.filter(account=acc)\
            .values('folder_name')\
            .annotate(unread_count=Count('id', filter=Q(is_read=False)))\
            .order_by('folder_name')
    return {'accounts': accounts}

# --- VIEWS ---

@login_required
def mail_client_dashboard(request):
    """Lädt das Grundgerüst des Dashboards."""
    context = get_base_context(request.user)
    
    # Initialer Laden: Unified Inbox (Sammel-Eingang)
    context['emails'] = FetchedEmail.objects.filter(
        account__user=request.user
    ).filter(Q(folder_name__iexact="INBOX") | Q(folder_name__iexact="Posteingang"))
    
    context['current_label'] = "Sammel-Eingang"
    return render(request, 'mail_hub/client_dashboard.html', context)

@login_required
def mail_list_view(request):
    """AJAX: Liefert die Email-Liste für die mittlere Spalte."""
    folder_type = request.GET.get('type')
    account_id = request.GET.get('account_id')
    folder_name = request.GET.get('folder', 'INBOX')
    
    emails = FetchedEmail.objects.filter(account__user=request.user)
    
    if folder_type == 'unified_inbox':
        emails = emails.filter(Q(folder_name__iexact="INBOX") | Q(folder_name__iexact="Posteingang"))
        current_label = "Sammel-Eingang"
    elif account_id:
        emails = emails.filter(account_id=account_id, folder_name=folder_name)
        current_label = folder_name
    else:
        current_label = "Nachrichten"
    
    return render(request, 'mail_hub/partials/email_list_container.html', {
        'emails': emails,
        'current_label': current_label
    })

@login_required
def mail_detail_view(request, pk):
    """AJAX: Liefert den Mail-Inhalt für die rechte Spalte."""
    email = get_object_or_404(FetchedEmail, id=pk, account__user=request.user)
    
    if not email.is_read:
        email.is_read = True
        email.save()

    mail_data = get_mail_content(email.file_path)
    # Daten an das Objekt binden für das Template
    email.body_html = mail_data.get('html')
    email.body_text = mail_data.get('text')
    email.attachments = mail_data.get('attachments')
    email.raw_eml = mail_data.get('raw_eml')
    
    return render(request, 'mail_hub/partials/email_detail.html', {'email': email})

@login_required
def mail_compose_view(request):
    """AJAX: Liefert den Editor zum Verfassen einer Mail."""
    sig = MailSignature.objects.filter(user=request.user, is_default=True).first()
    return render(request, 'mail_hub/partials/compose_email.html', {'signature': sig})

@login_required
@require_POST
def mail_send_view(request):
    """Verarbeitet den SMTP-Versand."""
    # Logik für den Versand folgt hier
    return render(request, 'mail_hub/partials/send_success_toast.html')

# mail_hub/views.py (Theoretische Struktur)

@login_required
def account_list(request):
    # Zeigt dem User seine Konten an
    accounts = MailAccount.objects.filter(user=request.user)
    return render(request, 'mail_hub/settings/account_list.html', {'accounts': accounts})

@login_required
def account_add_imap(request):
    # Formular für klassisches IMAP (Host, Email, Passwort)
    if request.method == 'POST':
        # Hier die Verschlüsselung anwenden!
        pass
    return render(request, 'mail_hub/settings/form_imap.html')

@login_required
def account_setup_microsoft(request, account_id):
    account = get_object_or_404(MailAccount, id=account_id, user=request.user)
    
    # Hier nutzen wir DEINE Funktion:
    # web_interactive=True sorgt dafür, dass wir den Device-Flow-Code zurückbekommen
    session, flow_data = connect_outlook_account_db(account, web_interactive=True)
    
    # Wenn session None ist, aber flow_data gefüllt, läuft der Device Flow
    if flow_data and "user_code" in flow_data:
        # Den Flow für den zweiten Schritt in der Session speichern
        request.session[f'ms_flow_{account.id}'] = flow_data
        
        return render(request, 'mail_hub/settings/microsoft_code.html', {
            'account': account,
            'url': flow_data.get("verification_uri"),
            'user_code': flow_data.get("user_code"),
            'message': flow_data.get("message"),
        })
    else:
        messages.error(request, "Konnte den Microsoft-Login nicht starten.")
        return redirect('mail_hub:dashboard')

@login_required
def complete_ms_flow(request, account_id):
    account = get_object_or_404(MailAccount, id=account_id, user=request.user)
    
    # Den Flow aus der Session holen (wurde oben gespeichert)
    # Er enthält das 'flow' Dictionary, das MSAL intern braucht
    flow_data = request.session.get(f'ms_flow_{account.id}')
    
    if not flow_data:
        messages.error(request, "Sitzung abgelaufen. Bitte erneut versuchen.")
        return redirect('mail_hub:setup_ms', account_id=account.id)

    # Hier nutzen wir DEINE zweite Funktion zum Abschließen:
    # Wir müssen das 'flow'-Dictionary extrahieren, das msal erwartet
    actual_msal_flow = flow_data.get('flow') 
    session, res = complete_device_flow_for_account(account, actual_msal_flow)
    
    if session and "access_token" in res:
        messages.success(request, f"Konto {account.email_address} erfolgreich verknüpft!")
        if f'ms_flow_{account.id}' in request.session:
            del request.session[f'ms_flow_{account.id}']
    else:
        messages.error(request, "Die Autorisierung schlug fehl oder wurde abgebrochen.")
        
    return redirect('mail_hub:dashboard')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import MailAccount
from .forms import MailAccountForm

@login_required
def account_list(request):
    accounts = MailAccount.objects.filter(user=request.user)
    return render(request, 'mail_hub/settings/account_list.html', {'accounts': accounts})

@login_required
def account_edit(request, pk=None):
    if pk:
        account = get_object_or_404(MailAccount, pk=pk, user=request.user)
    else:
        account = MailAccount(user=request.user)

    if request.method == 'POST':
        form = MailAccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('mail_hub:account_list')
    else:
        form = MailAccountForm(instance=account)
    
    return render(request, 'mail_hub/settings/account_form.html', {'form': form, 'account': account})

@login_required
def account_delete(request, pk):
    account = get_object_or_404(MailAccount, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
    return redirect('mail_hub:account_list')