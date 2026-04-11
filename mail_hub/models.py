from django.db import models
from django.conf import settings
from django.utils.timezone import now

class MailAccount(models.Model):
    """
    Zentrale Verwaltung der E-Mail-Konten pro User.
    Speichert Zugangsdaten verschlüsselt.
    """
    AUTH_TYPES = [
        ('imap_pwd', 'IMAP / SMTP (Passwort)'),
        ('ms_graph', 'Microsoft 365 / Outlook (OAuth2)'),
        ('google', 'Google Mail (OAuth2)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='mail_accounts'
    )
    email_address = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True, help_text="z.B. Privat oder Geschäftlich")
    
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPES)
    
    # Neues Feld für den Server
    imap_host = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="z.B. imap.ionos.de oder imap.gmx.net"
    )

    smtp_host = models.CharField(max_length=255, blank=True, help_text="z.B. smtp.ionos.de")
    smtp_port = models.PositiveIntegerField(default=587)

    # OAuth Felder
    client_id = models.CharField(max_length=255, blank=True, help_text="Azure App Client ID")
    authority = models.CharField(max_length=255, default="https://login.microsoftonline.com/common")
    
    oauth_access_token = models.TextField(blank=True, null=True)
    oauth_refresh_token = models.TextField(blank=True, null=True)
    oauth_token_expires = models.DateTimeField(blank=True, null=True)

    

    # Hier speichern wir das Passwort (IMAP) oder das Token-JSON (OAuth) 
    # als verschlüsselten String via services/crypto.py
    # encrypted_credentials = models.TextField() 
    encrypted_credentials = models.TextField(
        blank=True,  # Erlaubt leeres Feld im Admin-Formular
        null=True,   # Erlaubt NULL in der Datenbank
        verbose_name="Verschlüsselte Zugangsdaten (nur für IMAP)"
    )
    
    # Konfiguration
    is_priority = models.BooleanField(default=False, help_text="Wird als Standard-Konto im UI geladen")
    is_active = models.BooleanField(default=True)
    
    # Statistiken
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mail Konto"
        verbose_name_plural = "Mail Konten"

    # def __str__(self):
    #     return f"{self.email_address} ({self.get_auth_type_display()})"

    def __str__(self):
        # Zeigt im Admin: "armin.huenniger (armin.h@netzsprung.de)"
        return f"{self.user.email} ({self.email_address})"



class FetchedEmail(models.Model):
    """
    Metadaten und Such-Index der abgerufenen E-Mails.
    Die echte EML liegt verschlüsselt im Dateisystem.
    """
    account = models.ForeignKey(
        MailAccount, 
        on_delete=models.CASCADE, 
        related_name='emails'
    )
    
    # SHA-256 Hash der Message-ID zur Vermeidung von Dubletten
    message_id_hash = models.CharField(max_length=64, db_index=True)
    
    # Header-Daten
    subject = models.CharField(max_length=500, blank=True)
    from_addr = models.CharField(max_length=255)
    to_addr = models.TextField(blank=True)
    cc_addr = models.TextField(blank=True)
    date_sent = models.DateTimeField(db_index=True)
    
    # Der "Search-Index": Reintext ohne HTML und Anhänge
    search_index_text = models.TextField(blank=True)
    
    # Pfad zur Datei: media/mail_storage/{user_id}/{account_id}/{safe_folder}/...
    file_path = models.CharField(max_length=1024)
    
    # Neues Feld für den Ordnernamen/Pfad
    folder_name = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Optional: Die interne Microsoft-Ordner-ID (sehr sicher für Vergleiche)
    remote_folder_id = models.CharField(max_length=255, blank=True, null=True)

    # Status-Flags
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False) # Soft-Delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Eine Mail darf pro Konto physikalisch nur einmal existieren
        unique_together = ('account', 'message_id_hash')
        ordering = ['-date_sent']
        verbose_name = "Abgerufene E-Mail"
        verbose_name_plural = "Abgerufene E-Mails"

    # def __str__(self):
    #     return f"{self.subject[:50]} (von {self.from_addr})"

    def __str__(self):
        # Zeigt im Admin den Betreff und das zugehörige Konto
        return f"{self.subject[:40]}... [{self.account.email_address}]"


class MailAuditLog(models.Model):
    """
    Revisions-Log: Wer hat wann was mit einer Mail gemacht?
    """
    email = models.ForeignKey(
        FetchedEmail, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, help_text="z.B. FETCH, READ, DELETE, RESTORE")
    timestamp = models.DateTimeField(default=now)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)

    def __str__(self):
        # Zeigt im Admin z.B.: "2026-04-08 17:00 | MOVE | INBOX -> TESTER"
        local_time = self.timestamp.strftime('%Y-%m-%d %H:%M')
        return f"{local_time} | {self.action} | {self.email.subject[:30]}"

    class Meta:
        verbose_name = "Mail Revisions-Eintrag"
        verbose_name_plural = "Mail Revisions-Einträge"
        ordering = ['-timestamp'] # Neueste Logs immer oben

# mail_hub/models.py

class MailUserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mail_settings")
    layout_mode = models.CharField(max_length=20, default='vertical', choices=[
        ('vertical', 'Vorschau rechts'),
        ('horizontal', 'Vorschau unten'),
        ('none', 'Keine Vorschau')
    ])
    show_unified_inbox = models.BooleanField(default=True)
    favorites = models.JSONField(default=list, blank=True) # Speichert Pfade wie ["INBOX", "Sent"]
    
    def __str__(self):
        return f"Settings für {self.user.username}"

class MailSignature(models.Model):
    account = models.ForeignKey('MailAccount', on_delete=models.CASCADE, related_name="signatures", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="Standard")
    content_html = models.TextField()
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"Signatur: {self.name} ({self.user.username})"

class UserFolderPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey('MailAccount', on_delete=models.CASCADE, null=True, blank=True)
    folder_path = models.CharField(max_length=255) # z.B. "INBOX/Bewerbungen"
    is_favorite = models.BooleanField(default=False)
    display_name = models.CharField(max_length=100, blank=True) # Eigener Name für Favorit
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'account', 'folder_path')
        ordering = ['sort_order']
