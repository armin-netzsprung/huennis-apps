from io import BytesIO
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.text import slugify
from erp.models import Document
from seafile_drive.client import SeafileClient

@login_required
def document_finalize_and_upload(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    user = request.user
    
    if not user.seafile_auth_token:
        messages.error(request, "Kein Seafile Token gefunden.")
        return redirect('erp:document_edit', pk=doc.pk)
    
    # Status ändern (falls noch Entwurf)
    if doc.status == 'draft':
        doc.status = 'sent'
        doc.save()

    # 1. HTML rendern (Pfad korrigiert)
    context = {
        'doc': doc,
        # Wir stellen sicher, dass die Summen da sind, falls das Model sie nicht hat
        'net_total': getattr(doc, 'net_total', 0),
        'gross_total': getattr(doc, 'gross_total', 0),
    }
    html_string = render_to_string('erp/pdf/invoice_template.html', context)

    # 2. PDF generieren - LOKALER IMPORT um den Crash beim Booten zu verhindern
    try:
        from xhtml2pdf import pisa
        import logging
        
        # Wir schalten das Logging für pisa ein, um Fehler zu sehen
        logging.getLogger("xhtml2pdf").setLevel(logging.ERROR)
        
        result = BytesIO()
        # Erzeuge PDF direkt aus dem HTML String
        pisa_status = pisa.CreatePDF(
            html_string, 
            dest=result,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            messages.error(request, "Das PDF konnte nicht korrekt formatiert werden.")
            return redirect('erp:document_edit', pk=doc.pk)
            
        pdf_file = result.getvalue()
        
    except Exception as e:
        # Falls es hier einen Segfault gibt, wird die 502 ausgelöst
        messages.error(request, f"Kritischer Systemfehler bei PDF: {str(e)}")
        return redirect('erp:document_edit', pk=doc.pk)

    # 3. Seafile Upload
    try:
        client = SeafileClient(token=user.seafile_auth_token)
        repo_name = "OfficeCentral365"
        repo_id = client.get_repo_id_by_name(repo_name)
        
        if not repo_id:
            messages.error(request, f"Seafile-Bibliothek '{repo_name}' nicht gefunden.")
            return redirect('erp:document_edit', pk=doc.pk)

        filename = f"{slugify(doc.document_number)}.pdf"
        success = client.upload_file(repo_id=repo_id, filename=filename, file_content=pdf_file)
        
        if success:
            messages.success(request, f"Rechnung {doc.document_number} erfolgreich archiviert.")
        else:
            messages.error(request, "Fehler beim Upload zu Seafile.")
    except Exception as e:
        messages.error(request, f"Cloud-Fehler: {str(e)}")

    return redirect('erp:dashboard')