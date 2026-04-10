import requests
import json
import hashlib
from django.utils.timezone import now
from mail_hub.services.processor import process_incoming_email
from mail_hub.services.oauth_outlook_device import connect_outlook_account_db

def sync_account(account):
    """Hauptfunktion für den Microsoft Graph Sync."""
    session, _ = connect_outlook_account_db(account)
    
    if not session:
        print(f"Fehler: Kein Zugriff für {account.email_address}.")
        return

    print(f"Starte rekursiven Sync für {account.email_address}...")

    # Start auf oberster Ebene (current_path ist leer)
    _sync_folder_level(session, account, "https://graph.microsoft.com/v1.0/me/mailFolders", current_path="")

    print(f"Sync für Microsoft-Konto {account.email_address} abgeschlossen.")


def _sync_folder_level(session, account, url, current_path=""):
    """Lädt Ordner und taucht rekursiv tiefer, während der Pfad-String mitwächst."""
    try:
        response = session.get(url)
        response.raise_for_status()
        folders = response.json().get('value', [])
    except Exception as e:
        print(f"Fehler beim Abrufen der Ordnerebene: {e}")
        return

    for folder in folders:
        display_name = folder['displayName']
        folder_id = folder['id']
        
        # Pfad-Hierarchie aufbauen (z.B. "Posteingang/Unterordner")
        if current_path:
            full_folder_path = f"{current_path}/{display_name}"
        else:
            full_folder_path = display_name
        
        print(f"  Check Ordner: {full_folder_path}")

        # 1. Nachrichten in diesem Ordner verarbeiten
        _fetch_messages_from_folder(session, account, folder_id, full_folder_path)

        # 2. Rekursion: Wenn Unterordner existieren, eine Ebene tiefer gehen
        if folder.get('childFolderCount', 0) > 0:
            child_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/childFolders"
            _sync_folder_level(session, account, child_url, current_path=full_folder_path)


def _fetch_messages_from_folder(session, account, folder_id, full_folder_path):
    """Holt Nachrichten und erkennt Verschiebungen via Processor."""
    messages_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages?$top=50"
    
    try:
        res = session.get(messages_url)
        res.raise_for_status()
        messages = res.json().get('value', [])
    except Exception as e:
        print(f"    Fehler beim Laden der Mails aus {full_folder_path}: {e}")
        return

    for msg in messages:
        try:
            # Schneller Check: Kennen wir die Mail schon?
            internet_id = msg.get('internetMessageId') or msg.get('id')
            m_hash = hashlib.sha256(internet_id.encode('utf-8')).hexdigest()
            
            # Wir rufen den Processor auf. Er wird:
            # - Bei Verschiebung: Nur den folder_name in der DB updaten.
            # - Bei Neu: Alles anlegen (EML downloaden).
            
            from mail_hub.models import FetchedEmail
            existing = FetchedEmail.objects.filter(account=account, message_id_hash=m_hash).first()
            
            if existing:
                # Logik für Verschiebungen
                if existing.folder_name != full_folder_path:
                    # Der Processor übernimmt das Update und das Audit-Log
                    meta_move = {'message_id': internet_id, 'folder_original': full_folder_path}
                    process_incoming_email(account, None, meta_move)
                continue

            # Nur wenn die Mail wirklich NEU ist: Rohdaten laden
            eml_url = f"https://graph.microsoft.com/v1.0/me/messages/{msg['id']}/$value"
            eml_res = session.get(eml_url)
            eml_res.raise_for_status()
            
            meta = {
                'subject': msg.get('subject', '(Kein Betreff)'),
                'from': msg.get('from', {}).get('emailAddress', {}).get('address', ''),
                'to': ", ".join([r.get('emailAddress', {}).get('address', '') for r in msg.get('toRecipients', [])]),
                'date': msg.get('receivedDateTime', now()),
                'folder_original': full_folder_path,
                'message_id': internet_id,
                'plain_body': msg.get('bodyPreview', '') 
            }
            
            process_incoming_email(account, eml_res.content, meta)
            
        except Exception as e:
            print(f"    Fehler bei Message {msg.get('id')[:10]}...: {e}")
            continue