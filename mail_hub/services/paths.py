import os
import re
from pathlib import Path
from django.conf import settings

# mail_hub/services/paths.py

def get_clean_folder_name(name: str) -> str:
    """
    Bereinigt den Ordnernamen für das Dateisystem.
    Erlaubt Schrägstriche (/), um echte Unterordner-Strukturen zu bilden.
    """
    if not name:
        return "unnamed_folder"
    
    # 1. Wir entfernen / NICHT mehr aus der Liste der verbotenen Zeichen,
    #    damit 'Posteingang/Bewerbungen' als Pfad erhalten bleibt.
    #    Verbotene Zeichen (riskant für Linux/Shell): \ * ? : " < > |
    clean_name = re.sub(r'[\\*?:"<>|]', '_', name)
    
    # 2. Doppelte Schrägstriche verhindern (falls mal einer leer ist)
    clean_name = re.sub(r'/+', '/', clean_name)
    
    # 3. Führende/folgende Leerzeichen und Punkte entfernen
    #    Wir splitten nach / um jeden Teil einzeln zu säubern
    parts = [p.strip().strip('.') for p in clean_name.split('/')]
    clean_name = '/'.join([p for p in parts if p])
    
    return clean_name or "folder"

def get_account_root(account) -> Path:
    """
    Basis-Pfad: media/mail_storage/{user_id}/{account_id}/
    """
    storage_root = Path(getattr(settings, "MAILHUB_BASE_PATH", os.path.join(settings.MEDIA_ROOT, "mail_storage")))
    # Wir nutzen IDs für die Stammordner, da E-Mail-Adressen sich ändern könnten
    path = storage_root / str(account.user.id) / str(account.id)
    return path

def get_email_file_path(account, folder_name: str, filename: str) -> str:
    """
    Generiert den Pfad für eine EML-Datei.
    Gibt den relativen Pfad ab MEDIA_ROOT zurück.
    """
    account_path = get_account_root(account)
    
    # Hier nutzen wir die neue Logik: Umlaute bleiben erhalten!
    safe_folder = get_clean_folder_name(folder_name)
    
    target_dir = account_path / safe_folder
    
    # Erstellt das Verzeichnis physisch auf dem Server
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    
    full_path = target_dir / filename
    
    # Rückgabe relativ zu MEDIA_ROOT für das CharField in FetchedEmail
    try:
        return str(full_path.relative_to(settings.MEDIA_ROOT))
    except ValueError:
        return str(full_path)

def get_absolute_path(relative_path: str) -> Path:
    """Wandelt den DB-Pfad wieder in einen absoluten Systempfad um."""
    return Path(settings.MEDIA_ROOT) / relative_path
