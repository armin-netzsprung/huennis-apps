# erp/views.py
from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Article, Document, DocumentItem, Unit # Sicherstellen, dass alles importiert ist
from django.http import HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from crm.models import LegalEntity
from django.template.loader import render_to_string
from django.http import HttpResponse
import requests
from django.conf import settings
from django.utils.text import slugify
from xhtml2pdf import pisa
from io import BytesIO


@login_required
def mock_document_editor(request):
    context = {
        'doc_type': 'Rechnung',
        'doc_number': 'RE-2026-0042',
        'doc_date': '11.04.2026',
        'due_date': '25.04.2026',
        'customer': {
            'name': 'Max Mustermann GmbH',
            'street': 'Musterstraße 12',
            'city': '12345 Musterstadt',
            'country': 'Deutschland'
        },
        
        'intro_text': 'Sehr geehrte Damen und Herren,<br><br>gemäß unserer Vereinbarung berechnen wir Ihnen folgende Leistungen:',
        'outro_text': 'Wir bedanken uns für die gute Zusammenarbeit.',
        
        # Positionen mit individuellen Steuersätzen
        'items': [
            {'pos': 1, 'title': 'Webdesign Konzept', 'qty': 1, 'price': 850.00, 'discount_pct': 0, 'tax_rate': 19, 'total': 850.00},
            {'pos': 2, 'title': 'Entwicklung (Stunden)', 'qty': 10, 'price': 95.00, 'discount_pct': 10, 'tax_rate': 19, 'total': 855.00}, 
            {'pos': 3, 'title': 'Hosting (Kanaren-Server)', 'qty': 1, 'price': 120.00, 'discount_pct': 0, 'tax_rate': 7, 'total': 120.00}, 
            {'pos': 4, 'title': 'Kostenloses Erstgespräch', 'qty': 1, 'price': 0.00, 'discount_pct': 0, 'tax_rate': 0, 'total': 0.00}, 
        ],
        
        # Summen
        'subtotal': 1825.00,               
        'global_discount_pct': 5,          
        'global_discount_amount': 91.25,   
        'net_total': 1733.75,              
        
        # Steuern aufgeschlüsselt (z.B. für DE und ES gemischt)
        'taxes': [
            {'label': '19% MwSt.', 'amount': 307.75},
            {'label': '7% IGIC (Teneriffa)', 'amount': 8.40},
        ],
        
        'gross_total': 2049.90,            
        
        # Skonto
        'skonto_pct': 2,
        'skonto_days': 8,
        'skonto_amount': 41.00,            
    }
    return render(request, 'erp/mock_editor.html', context)

#### hier ist die richtig VIEW oben nur der MOCK #####
@login_required
def erp_dashboard(request):
    # Wir filtern: Status darf nicht 'paid' oder 'cancelled' sein
    active_documents = Document.objects.exclude(
        status__in=['paid', 'cancelled']
    ).order_by('-document_date', '-document_number')
    
    context = {
        'documents': active_documents,
    }
    return render(request, 'erp/dashboard.html', context)


@login_required
def document_edit(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    
    tax_list = []
    for rate, amount in doc.taxes.items():
        tax_list.append({
            'label': f"{rate}% MwSt.",
            'amount': amount
        })

    context = {
        'doc': doc,
        'doc_type': doc.get_document_type_display(),
        'doc_number': doc.document_number,
        'doc_date': doc.document_date,
        'due_date': doc.due_date,
        'customer': doc.customer,
        'articles': Article.objects.all(),
        'intro_text': doc.intro_text or "",
        'outro_text': doc.outro_text or "",
        'items': doc.items.all().order_by('position'),
        
        'subtotal': doc.subtotal,
        'global_discount_pct': doc.global_discount_percentage,
        'global_discount_amount': doc.global_discount_amount,
        'net_total': doc.net_total,
        'taxes': tax_list,
        'gross_total': doc.gross_total,
        'skonto_pct': doc.skonto_percentage,
        'skonto_days': doc.skonto_days,
        'skonto_amount': doc.skonto_amount,
        'all_customers': LegalEntity.objects.all().order_by('company_name'),
        # 'all_customers': LegalEntity.objects.all().order_by('name'),
        # Neu: Fertig berechneter Zahlbetrag bei Skonto
        'skonto_payable_amount': doc.gross_total - doc.skonto_amount,
    }
    
    return render(request, 'erp/mock_editor.html', context)

@login_required
def document_save_basics(request, pk):
    if request.method == 'POST':
        doc = get_object_or_404(Document, pk=pk)
        
        try:
            # Daten speichern
            doc.intro_text = request.POST.get('intro_text', '')
            doc.outro_text = request.POST.get('outro_text', '')
            doc.global_discount_percentage = request.POST.get('global_discount_pct', '0').replace(',', '.')
            doc.skonto_percentage = request.POST.get('skonto_pct', '0').replace(',', '.')
            doc.skonto_days = request.POST.get('skonto_days', 0)
            
            # Kleinunternehmer-Checkbox (kommt als 'on' oder None)
            doc.is_small_business = request.POST.get('is_small_business') == 'on'
            
            doc.save()
            
            # Nachricht für das Framework hinzufügen
            messages.success(request, f"{doc.get_document_type_display()} {doc.document_number} erfolgreich gespeichert.")
            
        except Exception as e:
            messages.error(request, f"Fehler beim Speichern: {str(e)}")
        
        # Wir geben nur das kleine Stück HTML für die Messages zurück
        # Wir erstellen dafür ein mini-template oder nutzen render_to_string
        return render(request, 'includes/messages.html')
    
    return HttpResponse(status=405)

def clear_messages(request):
    """Gibt einen leeren Content zurück, um das Message-Container-Div zu löschen"""
    return HttpResponse("")


@login_required
def document_recalculate(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        # Wir ziehen die globalen Werte aus dem POST
        discount_pct = request.POST.get('global_discount_pct', '0').replace(',', '.')
        doc.global_discount_percentage = Decimal(discount_pct or '0')
        doc.is_small_business = request.POST.get('is_small_business') == 'on'
        
        # Wichtig: Damit .subtotal und .taxes stimmen, müssen wir die 
        # Mengen/Rabatte der Items im Speicher (oder DB) aktualisieren
        for item in doc.items.all():
            qty = request.POST.get(f'item_{item.id}_qty')
            disc = request.POST.get(f'item_{item.id}_discount')
            if qty: item.quantity = Decimal(qty.replace(',', '.'))
            if disc: item.discount_percentage = Decimal(disc.replace(',', '.'))
            # Wir speichern hier direkt, damit die Kalkulation konsistent bleibt
            item.save()
        
        doc.save()

    # Wir bereiten die Daten für das Partial-Template vor
    tax_list = [{'label': f"{r}% MwSt.", 'amount': a} for r, a in doc.taxes.items()]
    
    context = {
        'subtotal': doc.subtotal,
        'global_discount_pct': doc.global_discount_percentage,
        'global_discount_amount': doc.global_discount_amount,
        'net_total': doc.net_total,
        'taxes': tax_list,
        'gross_total': doc.gross_total,
        'skonto_pct': doc.skonto_percentage,
        'skonto_amount': doc.skonto_amount,
        'skonto_days': doc.skonto_days,
        'skonto_payable_amount': doc.gross_total - doc.skonto_amount,
    }
    return render(request, 'erp/partials/summary_box.html', context)

# In erp/views.py ergänzen:

@login_required
def convert_document(request, pk, target_type):
    source_doc = get_object_or_404(Document, pk=pk)
    
    # Validierung der Typen
    valid_types = [t[0] for t in Document.DOC_TYPES]
    if target_type not in valid_types:
        messages.error(request, "Ungültiger Dokumententyp.")
        return redirect('erp:dashboard')

    new_doc = source_doc.create_follow_up(target_type)
    messages.success(request, f"{source_doc.get_document_type_display()} wurde erfolgreich in {new_doc.get_document_type_display()} umgewandelt.")
    
    return redirect('erp:document_edit', pk=new_doc.pk)


@login_required
@require_POST
def save_item_field(request, pk, field):
    item = get_object_or_404(DocumentItem, pk=pk)
    # Wert aus dem POST ziehen (Format: item_123_price)
    value = request.POST.get(f'item_{pk}_{field}')
    
    if not value:
        return HttpResponse(status=400)

    if field == 'price':
        item.unit_price = Decimal(value.replace(',', '.'))
    elif field == 'qty':
        item.quantity = Decimal(value.replace(',', '.'))
    elif field == 'discount':
        item.discount_percentage = Decimal(value.replace(',', '.'))
    elif field == 'title':
        item.title = value
    
    item.save()
    
    # Wenn sich kaufmännische Werte ändern, schicken wir die Zeilensumme 
    # UND die globale Summary zurück
    if field in ['price', 'qty', 'discount', 'tax']:
        doc = item.document
        tax_list = [{'label': f"{r}% MwSt.", 'amount': a} for r, a in doc.taxes.items()]
        context = {
            'item': item,
            'doc': doc,
            'subtotal': doc.subtotal,
            'global_discount_pct': doc.global_discount_percentage,
            'global_discount_amount': doc.global_discount_amount,
            'net_total': doc.net_total,
            'taxes': tax_list,
            'gross_total': doc.gross_total,
            'skonto_pct': doc.skonto_percentage,
            'skonto_amount': doc.skonto_amount,
            'skonto_days': doc.skonto_days,
            'skonto_payable_amount': doc.gross_total - doc.skonto_amount,
        }
        return render(request, 'erp/partials/item_total_update.html', context)
    
    return HttpResponse(status=204)


@login_required
@require_http_methods(["DELETE"])
def delete_item(request, pk):
    item = get_object_or_404(DocumentItem, pk=pk)
    doc = item.document
    item.delete()
    
    # Positionen neu durchnummerieren
    remaining_items = doc.items.all().order_by('position')
    for i, remaining_item in enumerate(remaining_items, start=1):
        if remaining_item.position != i:
            remaining_item.position = i
            remaining_item.save()

    # Context vorbereiten
    context = get_document_summary_context(doc)
    context['items'] = remaining_items
    
    # Wir geben das Partial zurück, das den Inhalt von #item-list ersetzt
    return render(request, 'erp/partials/item_list_only.html', context)


def get_document_summary_context(doc):
    """Hilfsfunktion, um den kaufmännischen Context für OOB-Updates zentral zu verwalten."""
    tax_list = [{'label': f"{r}% MwSt.", 'amount': a} for r, a in doc.taxes.items()]
    return {
        'doc': doc,
        'subtotal': doc.subtotal,
        'global_discount_pct': doc.global_discount_percentage,
        'global_discount_amount': doc.global_discount_amount,
        'net_total': doc.net_total,
        'taxes': tax_list,
        'gross_total': doc.gross_total,
        'skonto_pct': doc.skonto_percentage,
        'skonto_amount': doc.skonto_amount,
        'skonto_days': doc.skonto_days,
        'skonto_payable_amount': doc.gross_total - doc.skonto_amount,
        'articles': Article.objects.all(), # Immer mitschicken für das Dropdown
    }

@login_required
def add_item_row(request, pk):
    """Legt eine neue Position an und aktualisiert Zeile + Summen."""
    doc = get_object_or_404(Document, pk=pk)
    
    # Neue Position am Ende anfügen
    new_pos = doc.items.count() + 1
    item = DocumentItem.objects.create(
        document=doc,
        position=new_pos,
        title="Neue Position",
        unit_price=Decimal('0.00'),
        tax_rate=Decimal('19.00')
    )
    
    context = get_document_summary_context(doc)
    context['item'] = item # Die neue Zeile muss zusätzlich in den Context
    
    # Nutzt das kombinierte Template für Zeile + Summary-Update
    return render(request, 'erp/partials/item_added_with_summary.html', context)

@login_required
def apply_article(request, pk):
    item = get_object_or_404(DocumentItem, pk=pk)
    article_id = request.POST.get('article_select')
    
    if article_id:
        article = get_object_or_404(Article, pk=article_id)
        # Daten übertragen
        item.article = article
        item.title = article.name
        item.unit_price = article.net_price
        item.unit = article.unit
        item.tax_rate = article.default_tax_rate
        item.save()
        
        # Erzwungener Refresh für die Anzeige
        item.refresh_from_db() 
        
    doc = item.document
    context = get_document_summary_context(doc)
    context['item'] = item # Hier ist jetzt das aktualisierte Item drin!
    
    return render(request, 'erp/partials/item_added_with_summary.html', context)

@login_required
@require_POST
@login_required
@require_POST
def reorder_items(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    item_ids = request.POST.getlist('item_id_order')
    
    # 1. Sortierung in DB speichern
    for index, item_id in enumerate(item_ids, start=1):
        DocumentItem.objects.filter(id=item_id, document=doc).update(position=index)
    
    # 2. Context für das Re-Rendering holen
    context = get_document_summary_context(doc)
    context['items'] = doc.items.all().order_by('position')
    
    # 3. Wir geben das Partial zurück, das die Zeilen UND den OOB-Swap für die Summary enthält
    return render(request, 'erp/partials/item_list_only.html', context)

@login_required
def change_customer(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    new_customer_id = request.POST.get('customer_change')
    if new_customer_id:
        from crm.models import LegalEntity # Pfad anpassen
        doc.customer = get_object_or_404(LegalEntity, pk=new_customer_id)
        doc.save()
    return render(request, 'erp/partials/customer_address.html', {'customer': doc.customer})

######



def upload_to_seafile(pdf_content, filename, repo_id):
    """
    Schickt das PDF direkt an die Seafile Web API.
    """
    base_url = "https://cloud.netzsprung.de" 
    token = "DEIN_SEAFILE_API_TOKEN"            # Anpassen!
    
    # 1. Upload-Link von Seafile holen
    header = {"Authorization": f"Token {token}"}
    upload_url_api = f"{base_url}/api2/repos/{repo_id}/upload-link/"
    
    response = requests.get(upload_url_api, headers=header)
    upload_url = response.json() # Das ist der temporäre Ziel-Link
    
    # 2. Datei tatsächlich hochladen
    files = {'file': (filename, pdf_content)}
    # 'parent_dir' ist der Ordner innerhalb der Library, z.B. "/"
    data = {'parent_dir': '/'} 
    
    upload_reponse = requests.post(upload_url, headers=header, files=files, data=data)
    return upload_reponse.status_code == 200


@login_required
def document_finalize_and_upload(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    
    # 1. Status auf "Gesendet" setzen (falls noch Entwurf)
    if doc.status == 'draft':
        doc.status = 'sent'
        doc.save()
    
    # 2. PDF Inhalt rendern (HTML -> PDF)
    # Wir nutzen ein spezielles Template für den Druck
    html_string = render_to_string('erp/pdf/invoice_template.html', {'doc': doc})
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    # 3. Dateiname generieren
    filename = f"{slugify(doc.document_number)}.pdf"
    
    # 4. Upload zu Seafile (Repo-ID deiner Bibliothek)
    repo_id = "DEINE-LIB-ID-HIER" 
    success = upload_to_seafile(pdf_file, filename, repo_id)
    
    if success:
        messages.success(request, f"Rechnung wurde erstellt und in Seafile gespeichert.")
    else:
        messages.error(request, "PDF erstellt, aber Seafile-Upload fehlgeschlagen.")
        
    return redirect('erp:document_edit', pk=doc.pk)

