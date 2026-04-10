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
    
    scopes = scopes or GRAPH_SCOPES
    client_id = getattr(settings, 'AZURE_CLIENT_ID', None)
    authority = getattr(settings, 'AZURE_AUTHORITY', 'https://login.microsoftonline.com/common')

    if not client_id:
        log_event("FEHLER: AZURE_CLIENT_ID fehlt in settings.py")
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
    if web_interactive:
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            log_event(f"Device-Flow Start fehlgeschlagen: {flow}")
            return None, None
        
        return None, flow # Wir geben den ganzen Flow zurück

    return None, None

def complete_device_flow_for_account(account: MailAccount, flow: dict) -> Tuple[Optional[requests.Session], dict]:
    client_id = getattr(settings, 'AZURE_CLIENT_ID', None)
    authority = getattr(settings, 'AZURE_AUTHORITY', 'https://login.microsoftonline.com/common')
    
    app = msal.PublicClientApplication(client_id=client_id, authority=authority)
    
    # Dies blockiert NICHT ewig, wenn der Flow abgelaufen ist
    res = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in res:
        _save_token_result_to_db(account, res)
        sess = requests.Session()
        sess.headers.update({"Authorization": f"Bearer {res['access_token']}"})
        return sess, res
    
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
