# ####
# Aufruf:
# SITE_IDENTITY=office python ./10-Manage-Scripte/create_new_user_sealive.py
# ####

import os
import sys
import django
import requests
import getpass

# 1. Pfad-Korrektur
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 2. Django Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huennis_config.settings')
django.setup()

from django.contrib.auth import get_user_model

def setup_new_seafile_user():
    User = get_user_model()
    
    # Konfiguration
    SERVER_URL = "https://cloud.netzsprung.de"
    ADMIN_EMAIL = "admin.officecentral365@netzsprung.de"
    ADMIN_PW = "Sa7,ar9N"
    REPO_NAME = "OfficeCentral365"

    print(f"\n--- Seafile User & Library Setup (via Admin) ---")
    
    new_user_email = input("E-Mail für den User: ")
    new_user_password = getpass.getpass(f"Passwort für {new_user_email}: ")

    # --- SCHRITT 1: Admin-Token holen ---
    auth_url = f"{SERVER_URL}/api2/auth-token/"
    try:
        admin_res = requests.post(auth_url, data={'username': ADMIN_EMAIL, 'password': ADMIN_PW})
        if admin_res.status_code != 200:
            print(f"❌ Admin-Login bei Seafile fehlgeschlagen.")
            return
        admin_token = admin_res.json().get('token')
        admin_headers = {'Authorization': f'Token {admin_token}'}
    except Exception as e:
        print(f"❌ Verbindung zu Seafile fehlgeschlagen: {e}")
        return

    # --- SCHRITT 2: User in Seafile anlegen (POST statt PUT für neue Accounts) ---
    # Die Seafile API nutzt POST /api2/accounts/, um neue User zu erstellen
    create_user_url = f"{SERVER_URL}/api2/accounts/"
    user_data = {
        'email': new_user_email,
        'password': new_user_password,
        'is_active': 'true'
    }
    
    user_res = requests.post(create_user_url, headers=admin_headers, data=user_data)
    
    if user_res.status_code in [200, 201]:
        print(f"✅ Seafile-User {new_user_email} erfolgreich angelegt.")
    elif user_res.status_code == 400 and "Already exists" in user_res.text:
        print(f"ℹ️ User {new_user_email} existiert bereits in Seafile. Fahre mit Token-Ermittlung fort...")
    else:
        print(f"❌ Fehler beim Seafile-Account-Check: {user_res.text}")
        # Wir machen trotzdem weiter, falls der User existiert aber die API anders antwortet

    # --- SCHRITT 3: Token für den User holen ---
    user_auth_res = requests.post(auth_url, data={'username': new_user_email, 'password': new_user_password})
    if user_auth_res.status_code == 200:
        user_token = user_auth_res.json().get('token')
        user_headers = {'Authorization': f'Token {user_token}'}
        print(f"✅ Token für {new_user_email} erfolgreich ermittelt.")
    else:
        print(f"❌ Konnte Token für {new_user_email} nicht abrufen. Passwort falsch?")
        return

    # --- SCHRITT 4: Bibliothek anlegen (nur wenn neu) ---
    repos_url = f"{SERVER_URL}/api2/repos/"
    create_repo_res = requests.post(repos_url, headers=user_headers, data={'name': REPO_NAME})
    
    if create_repo_res.status_code == 200:
        print(f"✅ Bibliothek '{REPO_NAME}' wurde erstellt.")
    else:
        # Falls die Bibliothek schon existiert, kommt oft ein Fehler, den wir hier ignorieren
        print(f"ℹ️ Bibliothek-Check: {create_repo_res.text}")

    # --- SCHRITT 5: Daten in lokaler Django-DB speichern/aktualisieren ---
    try:
        django_user = User.objects.filter(email=new_user_email).first()
        
        if not django_user:
            print(f"User {new_user_email} existiert nicht in Django. Lege ihn neu an...")
            django_user = User.objects.create_user(
                email=new_user_email,
                password=new_user_password,
                first_name="Office",
                last_name="User"
            )
            created = True
        else:
            created = False

        # Token und Aktivierung aktualisieren
        django_user.seafile_auth_token = user_token
        django_user.is_active = True
        django_user.save()
        
        status = "NEU ANGELEGT" if created else "AKTUALISIERT"
        print(f"✅ Django-User wurde {status} und Token hinterlegt.")
        
    except Exception as e:
        print(f"❌ Kritischer Fehler beim Speichern in Django: {e}")

if __name__ == "__main__":
    setup_new_seafile_user()