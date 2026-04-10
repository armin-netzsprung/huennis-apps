# ### NICHT LÖSCHEN ### #
# SITE_IDENTITY=office python 10-Manage-Scripte/clean_account.py armin.huenniger@outlook.de
# SITE_IDENTITY=office python manage.py mail_runner --account armin.huenniger@outlook.de
# ### #

import os
import shutil
import sys
from pathlib import Path

# 1. Pfad-Korrektur: Füge das Hauptverzeichnis (eins drüber) zum Python-Pfad hinzu
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# 2. Django-Umgebung laden
# WICHTIG: Ersetze 'huennis_blog' durch den NAMEN DEINES PROJEKT-ORDNERS (wo die settings.py drin liegt)
# Wenn dein Hauptordner 'huennis_blog' heißt, ist das meist korrekt. 
# Falls die settings.py in 'core/settings.py' liegt, wäre es 'core.settings'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huennis_config.settings')

import django
django.setup()

from django.conf import settings
from mail_hub.models import MailAccount, FetchedEmail

def wipe_account(email_address):
    try:
        # 1. Account suchen
        account = MailAccount.objects.get(email_address=email_address)
        acc_id = account.id
        user_id = account.user.id
        
        print(f"--- Starte Reinigung für: {email_address} (ID: {acc_id}) ---")

        # 2. DB-Einträge löschen
        emails_count, _ = FetchedEmail.objects.filter(account=account).delete()
        print(f"-> {emails_count} E-Mails aus der Datenbank gelöscht.")

        # 3. Dateien auf dem Filesystem löschen
        storage_path = os.path.join(settings.MEDIA_ROOT, 'mail_storage', str(user_id), str(acc_id))
        
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
            print(f"-> Verzeichnis gelöscht: {storage_path}")
        else:
            print(f"-> Info: Verzeichnis existierte nicht: {storage_path}")

        # 4. Last Sync zurücksetzen
        account.last_sync_at = None
        account.save()
        
        print(f"--- Erfolg: Konto {email_address} ist jetzt leer. ---")

    except MailAccount.DoesNotExist:
        print(f"FEHLER: Konto '{email_address}' nicht gefunden.")
    except Exception as e:
        print(f"FEHLER: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Benutzung: SITE_IDENTITY=office python clean_account.py email@beispiel.de")
        sys.exit(1)
        
    target_email = sys.argv[1]
    
    confirm = input(f"ALLE Daten für {target_email} löschen? (j/n): ")
    if confirm.lower() == 'j':
        wipe_account(target_email)
    else:
        print("Abgebrochen.")

