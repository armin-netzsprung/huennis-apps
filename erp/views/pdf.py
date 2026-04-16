from io import BytesIO
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.text import slugify
from erp.models import Document
from seafile_drive.client import SeafileClient
from django.utils.text import slugify

@login_required
def document_finalize_and_upload(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    user = request.user
    
    # 1. Sicherheits-Checks
    if not user.seafile_auth_token:
        messages.error(request, "Kein Seafile Token gefunden.")
        return redirect('erp:document_edit', pk=doc.pk)
    
    # 2. Status fixieren
    if doc.status == 'draft':
        doc.status = 'sent'
        doc.save()

    # 3. Adressdaten für das Template vorbereiten
    # Wir suchen die Billing-Adresse des Kunden
    address = doc.customer.addresses.filter(address_type='BILLING').first()

    # 4. HTML rendern
    html_string = render_to_string('erp/pdf/invoice_template.html', {
        'doc': doc,
        'address': address,
    })

    # 5. PDF generieren
    try:
        from xhtml2pdf import pisa
        result = BytesIO()
        pisa.CreatePDF(BytesIO(html_string.encode("utf-8")), dest=result, encoding='utf-8')
        pdf_file = result.getvalue()
    except Exception as e:
        messages.error(request, f"Fehler beim PDF-Rendering: {str(e)}")
        return redirect('erp:document_edit', pk=doc.pk)

    # 6. Strukturierter Seafile Pfad
    # Nutze internal_id statt customer_number
    customer_folder = f"{doc.customer.internal_id}_{slugify(doc.customer.company_name or str(doc.customer))}"
    type_folder = doc.get_document_type_display() 
    target_path = f"/{customer_folder}/{type_folder}"

    # ... nach der PDF-Generierung ...
    client = SeafileClient(token=user.seafile_auth_token)
    repo_name = "OfficeCentral365"
    repo_id = client.get_repo_id_by_name(repo_name)
    
    if not repo_id:
        # HIER: Prüfen ob der Name vielleicht doch anders ist
        messages.error(request, f"Bibliothek '{repo_name}' nicht gefunden. Prüfe den Namen in Seafile!")
        return redirect('erp:document_edit', pk=doc.pk)

    filename = f"{slugify(doc.document_number)}.pdf"
    
    # Debug-Print in die Konsole
    print(f"DEBUG: Starte Upload nach {target_path}/{filename} in Repo {repo_id}")
    
    success = client.upload_file(
        repo_id=repo_id, 
        filename=filename, 
        file_content=pdf_file,
        parent_dir=target_path
    )
    
    if success:
        messages.success(request, f"Dokument in {target_path} archiviert.")
    else:
        # Wenn success False ist, liegt es meist an der ensure_dir_exists Logik
        messages.error(request, "Seafile Upload fehlgeschlagen. Siehe Terminal-Log.")
        
    return redirect('erp:dashboard')