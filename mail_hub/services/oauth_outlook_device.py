# mail_hub/services/oauth_outlook_device.py
from django.conf import settings # Sicherstellen, dass das oben steht!
import msal
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict

from django.utils.timezone import is_naive, make_aware
# Hier die korrekten Pfade zu DEINER App:
from huennis_config import settings
from mail_hub.models import MailAccount

# Hilfsfunktion für Logausgaben (da du wahrscheinlich kein eigenes Logging-Modul hast, 
# nutzen wir hier einfaches print für die Konsole)
def log_event(msg):
    print(f"DEBUG: {msg}")

GRAPH_SCOPES = [
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
]

def _token_valid(account: MailAccount) -> bool:
    exp = getattr(account, "oauth_token_expires", None)
    if not account.oauth_access_token or not exp:
        return False
    if is_naive(exp):
        exp = make_aware(exp)
    # kleine Sicherheitsmarge (30 Sek)
    return exp > make_aware(datetime.utcnow() + timedelta(seconds=30))

def _save_token_result_to_db(account: MailAccount, result: dict) -> None:
    try:
        if result.get("access_token"):
            account.oauth_access_token = result["access_token"]
        if result.get("refresh_token"):
            account.oauth_refresh_token = result["refresh_token"]
        
        ttl = int(result.get("expires_in", 3600))
        exp = datetime.utcnow() + timedelta(seconds=ttl)
        if is_naive(exp):
            exp = make_aware(exp)
        
        account.oauth_token_expires = exp
        # Wir speichern die Token-Felder
        account.save(update_fields=[
            "oauth_access_token", 
            "oauth_refresh_token", 
            "oauth_token_expires"
        ])
        log_event(f"[GRAPH] Token gespeichert für {account.email_address} (Ablauf={account.oauth_token_expires})")
    except Exception as e:
        log_event(f"[GRAPH] Token-Speicherung fehlgeschlagen: {e}")



def connect_outlook_account_db(
    account: MailAccount,
    scopes: Optional[list] = None,
    web_interactive: bool = False,
) -> Tuple[Optional[requests.Session], Optional[Dict]]:
    
    scopes = scopes or GRAPH_SCOPES

    # --- KORREKTUR START ---
    # Wir nehmen die ID aus deinen globalen settings.py, nicht vom Account!
    client_id = getattr(settings, 'AZURE_CLIENT_ID', None)
    authority = getattr(settings, 'AZURE_AUTHORITY', 'https://login.microsoftonline.com/common')

    if not client_id:
        log_event("[GRAPH] FEHLER: AZURE_CLIENT_ID fehlt in settings.py")
        return None, None
    # --- KORREKTUR ENDE ---

    if _token_valid(account):
        sess = requests.Session()
        sess.headers.update({"Authorization": f"Bearer {account.oauth_access_token}"})
        return sess, None

    app = msal.PublicClientApplication(
        client_id=client_id, # Hier die Variable von oben nutzen
        authority=authority,
    )

    # ... (Refresh-Token Teil bleibt gleich)

    if web_interactive:
        try:
            flow = app.initiate_device_flow(scopes=scopes)
            if "user_code" not in flow:
                # Hier loggen wir jetzt den echten Grund, falls es scheitert
                log_event(f"[GRAPH] Device-Flow Start fehlgeschlagen: {flow}")
                return None, None
            
            return None, {
                "verification_uri": flow.get("verification_uri"),
                "user_code": flow.get("user_code"),
                "message": flow.get("message"),
                "flow": flow,
            }
        except Exception as e:
            log_event(f"[GRAPH] Device-Flow Exception: {e}")
            return None, None

    return None, None


def complete_device_flow_for_account(account: MailAccount, flow: dict) -> Tuple[Optional[requests.Session], dict]:
    """Wartet auf die Eingabe des Nutzers bei Microsoft."""
    
    # KORREKTUR: Hier auch die Settings nutzen!
    client_id = getattr(settings, 'AZURE_CLIENT_ID', None)
    authority = getattr(settings, 'AZURE_AUTHORITY', 'https://login.microsoftonline.com/common')
    
    try:
        app = msal.PublicClientApplication(
            client_id=client_id, # Variable nutzen
            authority=authority, # Variable nutzen
        )
        # Dies blockiert, bis der User den Code eingegeben hat
        res = app.acquire_token_by_device_flow(flow)
    except Exception as e:
        log_event(f"[GRAPH] Fehler beim Abschluss: {e}")
        return None, {"error": str(e)}

    if not res or "access_token" in res == False: # Sicherere Prüfung
        return None, res if res else {"error": "No response from Microsoft"}

    _save_token_result_to_db(account, res)
    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {res['access_token']}"})
    return sess, res
    

def run_oauth_step_by_step(account):
    """
    Diese Funktion steuert den Prozess.
    1. Sie prüft, ob wir einen Flow starten müssen.
    2. Sie gibt dem User die Anweisungen.
    """
    # Schritt 1: Flow initialisieren
    session, device_info = connect_outlook_account_db(account, web_interactive=True)
    
    if device_info:
        # Hier geben wir die Daten für das Frontend zurück
        return {
            "status": "pending",
            "url": device_info["verification_uri"],
            "user_code": device_info["user_code"],
            "message": device_info["message"],
            "flow": device_info["flow"]
        }
    return {"status": "error", "message": "Konnte Flow nicht starten."}