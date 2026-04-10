import email
from email import policy
import hashlib
import re
import os
from pathlib import Path
from django.utils.timezone import now
from django.conf import settings
from .paths import get_email_file_path
from .crypto import encrypt_bytes
from ..models import FetchedEmail, MailAuditLog

def strip_html_tags(html_content):
    """Entfernt HTML-Tags für den Such-Index."""
    if not html_content:
        return ""
    clean = re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<.*?>', ' ', clean)
    return ' '.join(clean.split())

def process_incoming_email(account, raw_eml_bytes, meta_data):
    """
    Verarbeitet E-Mails: Erkennt Verschiebungen bei Dubletten oder legt neue Einträge an.
    """
    msg_id = meta_data.get('message_id', '')
    mid_hash = hashlib.sha256(msg_id.encode('utf-8')).hexdigest()
    new_folder = meta_data.get('folder_original', 'INBOX')

    # 1. Dubletten- & Verschiebe-Check
    existing_email = FetchedEmail.objects.filter(account=account, message_id_hash=mid_hash).first()
    
    if existing_email:
        # Falls die Mail bereits existiert, prüfen wir auf einen Ordnerwechsel
        if existing_email.folder_name != new_folder:
            old_folder = existing_email.folder_name
            existing_email.folder_name = new_folder
            existing_email.save(update_fields=['folder_name'])
            
            # Revisions-Eintrag für die Verschiebung
            MailAuditLog.objects.create(
                email=existing_email,
                action='MOVE',
                details=f"Verschoben von '{old_folder}' nach '{new_folder}'"
            )
            print(f"    [MOVE] {existing_email.subject[:30]} -> {new_folder}")
        return existing_email

    # --- AB HIER: LOGIK FÜR NEUE MAILS ---

    # 2. Text-Extraktion für den Such-Index
    search_text = meta_data.get('plain_body', '')
    if not search_text and raw_eml_bytes:
        try:
            msg = email.message_from_bytes(raw_eml_bytes, policy=policy.default)
            plain_part = msg.get_body(preferencelist=('plain', 'html'))
            if plain_part:
                content = plain_part.get_content()
                search_text = strip_html_tags(content) if plain_part.get_content_type() == 'text/html' else content
        except Exception as e:
            search_text = f"Extraktionsfehler: {e}"

    # 3. Pfad-Logik & Dateisystem
    timestamp = now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{mid_hash[:8]}.eml.enc"
    
    rel_path = get_email_file_path(account, new_folder, filename)
    abs_path = Path(settings.MEDIA_ROOT) / rel_path
    
    # Sicherstellen, dass das Verzeichnis existiert
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    # 4. Datei verschlüsselt speichern
    try:
        encrypted_data = encrypt_bytes(raw_eml_bytes)
        with open(abs_path, 'wb') as f:
            f.write(encrypted_data)
    except Exception as e:
        print(f"CRITICAL: Fehler beim Schreiben der Datei: {e}")
        return None

    # 5. DB-Eintrag erstellen
    email_obj = FetchedEmail.objects.create(
        account=account,
        message_id_hash=mid_hash,
        subject=meta_data.get('subject', '(Kein Betreff)'),
        from_addr=meta_data.get('from', ''),
        to_addr=meta_data.get('to', ''),
        date_sent=meta_data.get('date', now()),
        folder_name=new_folder,  # WICHTIG: Neues Feld nutzen
        search_index_text=search_text[:10000],
        file_path=rel_path
    )

    # 6. Audit Log für den Erst-Abruf
    MailAuditLog.objects.create(
        email=email_obj,
        action='FETCH',
        details=f"Initialer Abruf in Ordner: {new_folder}"
    )

    return email_obj
