import imaplib
import email
from django.conf import settings
from mail_hub.services.crypto import decrypt_string
from mail_hub.services.processor import process_incoming_email
from mail_hub.services.mime_utils import decode_imap_utf7, decode_mime_header

def sync_account(account):
    """Verbindet sich per IMAP und ruft neue Mails ab."""
    # 1. Passwort entschlüsseln
    password = decrypt_string(account.encrypted_credentials)
    
    # 2. Host dynamisch aus dem Datenbank-Feld laden (Anpassung hier!)
    host = account.imap_host
    if not host:
        raise ValueError(f"Fehler: Kein IMAP-Host für {account.email_address} im Admin hinterlegt!")

    print(f"Versuche Login bei {host} für {account.email_address}...")

    with imaplib.IMAP4_SSL(host) as mail:
        mail.login(account.email_address, password)
        print("Login erfolgreich. Starte Ordner-Scan...")
        
        # Alle Ordner abrufen
        typ, folder_list = mail.list()
        for folder_raw in folder_list:
            # Beispiel-Parsing von folder_raw: '(\HasNoChildren) "/" "INBOX"'
            try:
                folder_name_encoded = folder_raw.decode().split(' "/" ')[-1].strip('"')
                folder_name = decode_imap_utf7(folder_name_encoded)
                
                print(f"Synchronisiere Ordner: {folder_name}")
                mail.select(f'"{folder_name_encoded}"', readonly=True)
                
                # Suche nach allen UIDs (ALL ist für den Anfang okay)
                typ, data = mail.uid('search', None, "ALL")
                uids = data[0].split()
                print(f"Gefunden: {len(uids)} Nachrichten.")

                for uid in uids:
                    # Mail abrufen
                    typ, msg_data = mail.uid('fetch', uid, '(RFC822)')
                    if not msg_data or not msg_data[0]:
                        continue
                        
                    raw_bytes = msg_data[0][1]
                    
                    # Metadaten extrahieren
                    msg = email.message_from_bytes(raw_bytes)
                    
                    meta = {
                        'subject': decode_mime_header(msg.get('Subject', '')),
                        'from': msg.get('From', ''),
                        'to': msg.get('To', ''),
                        'date': email.utils.parsedate_to_datetime(msg.get('Date')),
                        'folder_original': folder_name,
                        'message_id': msg.get('Message-ID', f"no-id-{uid.decode()}"),
                        'plain_body': "" # Wird im Processor extrahiert
                    }
                    
                    # Übergabe an den zentralen Processor (erledigt Dubletten-Check und Filesystem)
                    process_incoming_email(account, raw_bytes, meta)
            
            except Exception as folder_err:
                print(f"Fehler beim Verarbeiten von Ordner {folder_raw}: {str(folder_err)}")
                continue

    print(f"Sync für {account.email_address} abgeschlossen.")
