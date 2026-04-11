import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .oauth_outlook_device import connect_outlook_account_db
from .crypto import decrypt_string

def send_mail_auto(account, subject, recipient, body_content):
    """Entscheidet anhand des auth_type, wie gesendet wird."""
    if account.auth_type == 'ms_graph':
        return _send_via_graph(account, subject, recipient, body_content)
    else:
        # Alles andere (imap_pwd) läuft über SMTP
        return _send_via_smtp(account, subject, recipient, body_content)

def _send_via_graph(account, subject, recipient, body_content):
    session, _ = connect_outlook_account_db(account)
    if not session:
        return False, "Microsoft-Verbindung fehlgeschlagen."
    
    endpoint = "https://graph.microsoft.com/v1.0/me/sendMail"
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body_content},
            "toRecipients": [{"emailAddress": {"address": recipient}}]
        }
    }
    res = session.post(endpoint, json=payload)
    return (True, "OK") if res.status_code == 202 else (False, res.text)

def _send_via_smtp(account, subject, recipient, body_content):
    try:
        # Hier holen wir das Passwort aus deinem verschlüsselten Feld
        password = decrypt_string(account.encrypted_credentials)
        
        msg = MIMEMultipart()
        msg['From'] = f"{account.display_name} <{account.email_address}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body_content, 'html'))

        # Fallback-Logik für Host/Port
        host = account.smtp_host or account.imap_host.replace('imap', 'smtp')
        port = account.smtp_port or 587

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(account.email_address, password)
            server.send_message(msg)
        return True, "Gesendet"
    except Exception as e:
        return False, str(e)
    