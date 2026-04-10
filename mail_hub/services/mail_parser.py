import os
from email import message_from_string
from django.conf import settings
from mail_hub.services.crypto import decrypt_bytes 

def get_mail_content(file_path):
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if not os.path.exists(full_path):
        return {'text': 'Datei nicht gefunden', 'html': None, 'raw_eml': 'Datei nicht gefunden.', 'attachments': []}

    try:
        with open(full_path, 'rb') as f:
            encrypted_data = f.read()

        # 1. Entschlüsseln
        decrypted_bin = decrypt_bytes(encrypted_data)
        
        # 2. Raw-Text dekodieren (latin-1 fängt fast alles ab ohne abzustürzen)
        raw_text = decrypted_bin.decode('latin-1', errors='replace')

        # Sicherheits-Check: Falls raw_text aus irgendeinem Grund leer ist
        if not raw_text:
            raw_text = "Fehler: EML-Inhalt ist leer nach Entschlüsselung."

        # 3. Parsen mit Standard-Lib
        msg = message_from_string(raw_text)
        
        res = {
            'html': [], 
            'text': [], 
            'subject': msg.get('subject', '(Kein Betreff)'), 
            'from': msg.get('from', '(Unbekannt)'),
            'attachments': []
        }

        # --- DEBUG LOG ---
        print("\n" + "="*60)
        print(f"PARSING: {file_path}")

        # 4. Rekursives Durchlaufen
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        res['attachments'].append({
                            'filename': filename,
                            'content_type': content_type,
                            'size': len(part.get_payload(decode=False) or "")
                        })
                    continue

                if content_type in ["text/html", "text/plain"]:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'iso-8859-1'
                        try:
                            decoded = payload.decode(charset, errors='replace')
                        except:
                            decoded = payload.decode('latin-1', errors='replace')
                        
                        if content_type == "text/html":
                            res['html'].append(decoded)
                        else:
                            res['text'].append(decoded)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'iso-8859-1'
                decoded = payload.decode(charset, errors='replace')
                if msg.get_content_type() == "text/html":
                    res['html'].append(decoded)
                else:
                    res['text'].append(decoded)

        final_html = "".join(res['html'])
        final_text = "".join(res['text'])

        print(f"STATUS -> HTML: {len(final_html)>0} | Text: {len(final_text)>0} | Anhänge: {len(res['attachments'])}")
        print("="*60 + "\n")

        return {
            'html': final_html if final_html.strip() else None,
            'text': final_text if final_text.strip() else "Kein Textinhalt verfügbar.",
            'subject': res['subject'],
            'from': res['from'],
            'attachments': res['attachments'],
            'raw_eml': raw_text  # Wird garantiert zurückgegeben
        }

    except Exception as e:
        print(f"!!! FEHLER: {e}")
        return {
            'text': f"Fehler: {str(e)}", 
            'html': None, 
            'attachments': [], 
            'raw_eml': f"Kritischer Fehler beim Parsen: {str(e)}"
        }
    
    