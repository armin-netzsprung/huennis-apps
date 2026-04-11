# mail_hub/views.py
from django.http import HttpResponse

from .services.mail_sender import send_mail_auto
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Count  # WICHTIG: Hier Q und Count importieren
from .models import FetchedEmail, MailAccount, MailSignature
from mail_hub.services.mail_parser import get_mail_content
# mail_hub/views.py hinzufügen:
from .services.oauth_outlook_device import connect_outlook_account_db, complete_device_flow_for_account
# WICHTIG: Den Service als Ganzes importieren, damit wir den Pfad prüfen können
import mail_hub.services.oauth_outlook_device as oauth_service

print(f"DEBUG: Service Pfad: {oauth_service.__file__}")

# --- HELFER ---
def get_base_context(user):
    """Zentralisiert die Sidebar-Daten."""
    accounts = MailAccount.objects.filter(user=user)
    for acc in accounts:
        # dynamic_folders berechnen für die Sidebar-Anzeige
        acc.dynamic_folders = FetchedEmail.objects.filter(account=acc)\
            .values('folder_name')\
            .annotate(unread_count=Count('id', filter=Q(is_read=False)))\
            .order_by('folder_name')
    return {'accounts': accounts}

# --- VIEWS ---

@login_required
def mail_client_dashboard(request):
    """Lädt das Grundgerüst des Dashboards."""
    context = get_base_context(request.user)
    
    # Initialer Laden: Unified Inbox (Sammel-Eingang)
    context['emails'] = FetchedEmail.objects.filter(
        account__user=request.user
    ).filter(Q(folder_name__iexact="INBOX") | Q(folder_name__iexact="Posteingang"))
    
    context['current_label'] = "Sammel-Eingang"
    return render(request, 'mail_hub/client_dashboard.html', context)

@login_required
def mail_list_view(request):
    """AJAX: Liefert die Email-Liste für die mittlere Spalte."""
    folder_type = request.GET.get('type')
    account_id = request.GET.get('account_id')
    folder_name = request.GET.get('folder', 'INBOX')
    
    emails = FetchedEmail.objects.filter(account__user=request.user)
    
    if folder_type == 'unified_inbox':
        emails = emails.filter(Q(folder_name__iexact="INBOX") | Q(folder_name__iexact="Posteingang"))
        current_label = "Sammel-Eingang"
    elif account_id:
        emails = emails.filter(account_id=account_id, folder_name=folder_name)
        current_label = folder_name
    else:
        current_label = "Nachrichten"
    
    return render(request, 'mail_hub/partials/email_list_container.html', {
        'account_id': account_id,
        'emails': emails,
        'current_label': current_label
    })

@login_required
def mail_detail_view(request, pk):
    """AJAX: Liefert den Mail-Inhalt für die rechte Spalte."""
    email = get_object_or_404(FetchedEmail, id=pk, account__user=request.user)
    
    if not email.is_read:
        email.is_read = True
        email.save()

    mail_data = get_mail_content(email.file_path)
    # Daten an das Objekt binden für das Template
    email.body_html = mail_data.get('html')
    email.body_text = mail_data.get('text')
    email.attachments = mail_data.get('attachments')
    email.raw_eml = mail_data.get('raw_eml')
    
    return render(request, 'mail_hub/partials/email_detail.html', {'email': email})

@login_required
def mail_compose_view(request):
    account_id = request.GET.get('account_id')
    
    # 1. ALLE Konten des Users laden (für das Dropdown)
    all_accounts = MailAccount.objects.filter(user=request.user)
    
    # 2. Das aktuell vorausgewählte Konto ermitteln
    if not account_id:
        account = all_accounts.first()
    else:
        account = get_object_or_404(MailAccount, id=account_id, user=request.user)
    
    # Signatur laden (falls du eine hast)
    signature = MailSignature.objects.filter(account=account, is_default=True).first()
    
    context = {
        'current_account': account,   # Bestimmt, welches Konto im Dropdown auf "selected" steht
        'accounts': all_accounts,     # Die Liste aller Konten für das Dropdown
        'signature': signature,
    }
    return render(request, 'mail_hub/partials/compose_email.html', context)

# @login_required
# @require_POST
# def mail_send_view(request):
#     account_id = request.POST.get('account_id')
    
#     if not account_id or account_id == '':
#         # Fehlerbehandlung, falls die ID fehlt
#         return HttpResponse("Fehler: Keine Account-ID übergeben.", status=400)

#     # Jetzt ist sicher, dass account_id eine Zahl (als String) ist
#     account = get_object_or_404(MailAccount, id=account_id, user=request.user)
    
    
@login_required
def account_list(request):
    # Zeigt dem User seine Konten an
    accounts = MailAccount.objects.filter(user=request.user)
    return render(request, 'mail_hub/settings/account_list.html', {'accounts': accounts})

@login_required
def account_add_imap(request):
    # Formular für klassisches IMAP (Host, Email, Passwort)
    if request.method == 'POST':
        # Hier die Verschlüsselung anwenden!
        pass
    return render(request, 'mail_hub/settings/form_imap.html')


# In views.py innerhalb von account_setup_microsoft


@login_required
def account_setup_microsoft(request, account_id):
    # 1. Jetzt wird 'account' definiert!
    account = get_object_or_404(MailAccount, id=account_id, user=request.user)

    # 2. Jetzt funktionieren auch die Prints, weil wir innerhalb der Funktion sind
    print("\n" + "="*40)
    print(f"DEBUG: Service Pfad: {oauth_service.__file__}")
    print(f"DEBUG: Rufe jetzt connect_outlook_account_db auf für Account: {account.id}")
    
    # 3. Den Service aufrufen
    session, flow_data = oauth_service.connect_outlook_account_db(account, web_interactive=True)
    # Wir löschen das alte Token in der DB, um einen sauberen Neustart zu erzwingen
    account.oauth_access_token = None
    account.oauth_refresh_token = None
    account.save()

    # Jetzt den Service aufrufen
    session, flow_data = oauth_service.connect_outlook_account_db(account, web_interactive=True)
    
    print(f"DEBUG: Rückgabe erhalten: {bool(flow_data)}")
    print("="*40 + "\n")

    if flow_data and "user_code" in flow_data:
        request.session[f'ms_flow_{account.id}'] = flow_data
        return render(request, 'mail_hub/settings/microsoft_code.html', {
            'account': account,
            'url': flow_data.get("verification_uri"),
            'user_code': flow_data.get("user_code"),
            'message': flow_data.get("message"),
        })
    else:
        messages.error(request, "Konnte den Microsoft-Login nicht starten.")
        return redirect('mail_hub:dashboard')
    
@login_required
def complete_ms_flow(request, account_id):
    account = get_object_or_404(MailAccount, id=account_id, user=request.user)
    
    # Den Flow aus der Session holen (wurde oben gespeichert)
    # Er enthält das 'flow' Dictionary, das MSAL intern braucht
    flow_data = request.session.get(f'ms_flow_{account.id}')
    
    if not flow_data:
        messages.error(request, "Sitzung abgelaufen. Bitte erneut versuchen.")
        return redirect('mail_hub:setup_ms', account_id=account.id)

    # Hier nutzen wir DEINE zweite Funktion zum Abschließen:
    # Wir müssen das 'flow'-Dictionary extrahieren, das msal erwartet
    actual_msal_flow = flow_data.get('flow') 
    session, res = complete_device_flow_for_account(account, actual_msal_flow)
    
    if session and "access_token" in res:
        messages.success(request, f"Konto {account.email_address} erfolgreich verknüpft!")
        if f'ms_flow_{account.id}' in request.session:
            del request.session[f'ms_flow_{account.id}']
    else:
        messages.error(request, "Die Autorisierung schlug fehl oder wurde abgebrochen.")
        
    return redirect('mail_hub:dashboard')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import MailAccount
from .forms import MailAccountForm

@login_required
def account_list(request):
    accounts = MailAccount.objects.filter(user=request.user)
    return render(request, 'mail_hub/settings/account_list.html', {'accounts': accounts})

@login_required
def account_edit(request, pk=None):
    if pk:
        account = get_object_or_404(MailAccount, pk=pk, user=request.user)
    else:
        account = MailAccount(user=request.user)

    if request.method == 'POST':
        form = MailAccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('mail_hub:account_list')
    else:
        form = MailAccountForm(instance=account)
    
    return render(request, 'mail_hub/settings/account_form.html', {'form': form, 'account': account})

@login_required
def account_delete(request, pk):
    account = get_object_or_404(MailAccount, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
    return redirect('mail_hub:account_list')

@login_required
@require_POST
def account_setup_microsoft_complete(request, account_id):
    account = get_object_or_404(MailAccount, id=account_id, user=request.user)
    
    # Hol den gespeicherten Flow aus der Session
    flow = request.session.get(f'ms_flow_{account.id}')
    
    if not flow:
        messages.error(request, "Sitzung abgelaufen oder kein aktiver Login-Prozess gefunden.")
        return redirect('mail_hub:dashboard')
        
    # Jetzt den zweiten Teil des Device-Flows ausführen
    session, result = complete_device_flow_for_account(account, flow)
    
    if session:
        messages.success(request, f"Konto {account.email_address} wurde erfolgreich verknüpft!")
        # Den Flow aus der Session löschen, da er verbraucht ist
        del request.session[f'ms_flow_{account.id}']
    else:
        # Hier geben wir die Fehlermeldung von Microsoft aus, falls vorhanden
        error_msg = result.get('error_description', 'Unbekannter Fehler beim Abschluss des Logins.')
        messages.error(request, f"Login fehlgeschlagen: {error_msg}")
        
    return redirect('mail_hub:dashboard')


@login_required
@require_POST
def mail_send_view(request):
    account_id = request.POST.get('account_id')
    recipient = request.POST.get('to')
    subject = request.POST.get('subject')
    content = request.POST.get('content')

    account = get_object_or_404(MailAccount, id=account_id, user=request.user)

    # Die universelle Sende-Funktion aufrufen
    from .services.mail_sender import send_mail_auto
    success, message = send_mail_auto(account, subject, recipient, content)

    if success:
        return render(request, 'mail_hub/partials/send_success_toast.html', {'msg': message})
    else:
        return render(request, 'mail_hub/partials/send_error_toast.html', {'error': message})
    