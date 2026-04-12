# erp/views.py
from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Document
from django.http import HttpResponse
from django.contrib import messages



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