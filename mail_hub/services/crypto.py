import json
from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings

def _get_fernet():
    keys = getattr(settings, "MAILHUB_ENCRYPTION_KEYS", [])
    if not keys:
        # Fallback auf SECRET_KEY, falls nichts definiert ist (nicht empfohlen für Prod)
        raise RuntimeError("MAILHUB_ENCRYPTION_KEYS ist nicht in den Settings definiert!")
    return MultiFernet([Fernet(k) for k in keys])

def encrypt_string(plain_text: str) -> str:
    """Verschlüsselt einen String (z.B. Passwort oder Token) und gibt einen String zurück."""
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode("utf-8")).decode("ascii")

def decrypt_string(cipher_text: str) -> str:
    """Entschlüsselt einen String."""
    if not cipher_text:
        return ""
    f = _get_fernet()
    return f.decrypt(cipher_text.encode("ascii")).decode("utf-8")

def encrypt_bytes(data: bytes) -> bytes:
    """Verschlüsselt Rohdaten (z.B. EML-Inhalt)."""
    return _get_fernet().encrypt(data)

def decrypt_bytes(data: bytes) -> bytes:
    """Entschlüsselt Rohdaten."""
    return _get_fernet().decrypt(data)

