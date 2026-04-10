from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Count  # WICHTIG: Hier Q und Count importieren
from .models import FetchedEmail, MailAccount, MailSignature
from mail_hub.services.mail_parser import get_mail_content

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
    """AJAX: Liefert den Editor zum Verfassen einer Mail."""
    sig = MailSignature.objects.filter(user=request.user, is_default=True).first()
    return render(request, 'mail_hub/partials/compose_email.html', {'signature': sig})

@login_required
@require_POST
def mail_send_view(request):
    """Verarbeitet den SMTP-Versand."""
    # Logik für den Versand folgt hier
    return render(request, 'mail_hub/partials/send_success_toast.html')
