import base64
import re
from email.header import decode_header

def decode_mime_header(raw_value):
    """Dekodiert E-Mail-Header wie Subject oder From."""
    if not raw_value:
        return ""
    try:
        decoded_parts = decode_header(raw_value)
        result = ''.join([
            part.decode(charset or 'utf-8') if isinstance(part, bytes) else part
            for part, charset in decoded_parts
        ])
        return result
    except Exception:
        return str(raw_value)

def decode_imap_utf7(s: str) -> str:
    """
    Dekodiert IMAP-spezifisches UTF-7 (für Ordnernamen).
    Beispiel: '&AMw-ller' -> 'Müller'
    """
    if not s:
        return ""

    def b64_utf7_decode(m):
        s = m.group(1).replace(',', '/')
        # Padding hinzufügen
        padding = '=' * ((4 - len(s) % 4) % 4)
        try:
            return base64.b64decode(s + padding).decode('utf-16-be')
        except Exception:
            return '_'

    # Ersetzt &...- durch die dekodierten UTF-16 Zeichen
    # Sonderfall: '&&' wird zu '&'
    res = s.replace('&&', '&')
    res = re.sub(r'&([^-]+)-', b64_utf7_decode, res)
    return res
