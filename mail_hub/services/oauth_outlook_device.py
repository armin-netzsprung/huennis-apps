import msal
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict

from django.conf import settings  # Nutze IMMER diesen Import für die settings!
from django.utils.timezone import is_naive, make_aware
from mail_hub.models import MailAccount

def log_event(msg):
    print(f"DEBUG [OAUTH]: {msg}")

GRAPH_SCOPES = [
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
]

def _token_valid(account: MailAccount) -> bool:
    exp = getattr(account, "oauth_token_expires", None)
    if not account.oauth_access_token or not exp:
        return False
    
    now = datetime.utcnow()
    if is_naive(exp):
        exp = make_aware(exp)
    
    # Sicherheitsmarge von 60 Sekunden
    return exp > make_aware(now + timedelta(seconds=60))

def _save_token_result_to_db(account: MailAccount, result: dict) -> None:
    try:
        if result.get("access_token"):
            account.oauth_access_token = result["access_token"]
        if result.get("refresh_token"):
            account.oauth_refresh_token = result["refresh_token"]
        
        ttl = int(result.get("expires_in", 3600))
        exp = datetime.utcnow() + timedelta(seconds=ttl)
        
        account.oauth_token_expires = make_aware(exp)
        
        account.save(update_fields=[
            "oauth_access_token", 
            "oauth_refresh_token", 
            "oauth_token_expires"
        ])
        log_event(f"Token gespeichert für {account.email_address}")
    except Exception as e:
        log_event(f"Token-Speicherung fehlgeschlagen: {e}")

def connect_outlook_account_db(
    account: MailAccount,
    scopes: Optional[list] = None,
    web_interactive: bool = False,
) -> Tuple[Optional[requests.Session], Optional[Dict]]:
    
    from django.conf import settings # Lokal importieren für frische Daten
    import os

    scopes = scopes or GRAPH_SCOPES
    
    # Wir suchen die ID in dieser Reihenfolge: 
    # 1. DB-Feld, 2. Settings-Variable, 3. Direkt aus der System-Umgebung
    client_id = (
        account.client_id or 
        getattr(settings, 'AZURE_CLIENT_ID', None) or 
        os.getenv('OFFICE_AZURE_CLIENT_ID')
    )

    authority = getattr(settings, 'AZURE_AUTHORITY', 'https://login.microsoftonline.com/common')

    if not client_id:
        log_event("FEHLER: Keine Client ID gefunden (Settings & ENV geprüft)")
        return None, None

    # 1. Bestehendes Token prüfen
    if _token_valid(account):
        sess = requests.Session()
        sess.headers.update({"Authorization": f"Bearer {account.oauth_access_token}"})
        return sess, None

    app = msal.PublicClientApplication(client_id=client_id, authority=authority)

    # 2. Versuche Refresh-Token (für Hintergrund-Versand wie Billing!)
    if account.oauth_refresh_token:
        log_event("Versuche Token-Refresh via Refresh-Token...")
        res = app.acquire_token_by_refresh_token(account.oauth_refresh_token, scopes=scopes)
        if "access_token" in res:
            _save_token_result_to_db(account, res)
            sess = requests.Session()
            sess.headers.update({"Authorization": f"Bearer {res['access_token']}"})
            return sess, None

    # 3. Wenn Interaktiv (für das User-Frontend)
# 3. Wenn Interaktiv (für das User-Frontend)
    if web_interactive:
        print(f"DEBUG: MSAL Request startet...")
        print(f"DEBUG: Scopes: {scopes}")
        
        try:
            flow = app.initiate_device_flow(scopes=scopes)
            
            if flow and "user_code" in flow:
                print(f"✅ SUCCESS: Flow erhalten! Code ist: {flow['user_code']}")
                return None, flow
            else:
                # DAS HIER IST DIE ENTSCHEIDENDE STELLE
                print("\n" + "!"*30)
                print(f"❌ MSAL FEHLER ANTWORT: {flow}")
                print("!"*30 + "\n")
                log_event(f"Device-Flow Start fehlgeschlagen: {flow}")
                return None, None
                
        except Exception as e:
            print(f"❌ KRITISCHER FEHLER BEIM MSAL AUFRUF: {str(e)}")
            return None, None

    return None, None


    return None, None

def complete_device_flow_for_account(account: MailAccount, flow: dict) -> Tuple[Optional[requests.Session], dict]:
    from django.conf import settings
    import os
    
    # Identische Logik wie beim Starten des Flows
    client_id = (
        account.client_id or 
        getattr(settings, 'AZURE_CLIENT_ID', None) or 
        os.getenv('OFFICE_AZURE_CLIENT_ID')
    )

    authority = getattr(settings, 'AZURE_AUTHORITY', 'https://login.microsoftonline.com/common')
    
    # DEBUG-Print hinzufügen, um sicherzugehen
    print(f"DEBUG COMPLETE: Nutze Client ID {client_id}")
    
    if not client_id:
        return None, {"error": "no_client_id", "error_description": "Client ID in complete_flow nicht gefunden"}

    # WICHTIG: Die App braucht die Client ID!
    app = msal.PublicClientApplication(client_id=client_id, authority=authority)
    
    # Den Code bei Microsoft einlösen
    res = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in res:
        _save_token_result_to_db(account, res)
        sess = requests.Session()
        sess.headers.update({"Authorization": f"Bearer {res['access_token']}"})
        return sess, res
    
    # Wenn es schiefgeht, sehen wir hier das Resultat (den AADSTS Fehler)
    print(f"❌ MSAL ERROR BEIM ABSCHLUSS: {res}")
    return None, res

def run_oauth_step_by_step(account):
    """ Zentrale Einstiegsfunktion für deine Views """
    session, device_info = connect_outlook_account_db(account, web_interactive=True)
    
    if device_info:
        return {
            "status": "pending",
            "url": device_info.get("verification_uri"),
            "user_code": device_info.get("user_code"),
            "message": device_info.get("message"),
            "flow": device_info
        }
    return {"status": "error", "message": "Konnte Flow nicht starten."}
