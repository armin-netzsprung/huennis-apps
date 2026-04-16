from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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
        'items': [
            {'pos': 1, 'title': 'Webdesign Konzept', 'qty': 1, 'price': 850.00, 'discount_pct': 0, 'tax_rate': 19, 'total': 850.00},
            {'pos': 2, 'title': 'Entwicklung (Stunden)', 'qty': 10, 'price': 95.00, 'discount_pct': 10, 'tax_rate': 19, 'total': 855.00}, 
            {'pos': 3, 'title': 'Hosting (Kanaren-Server)', 'qty': 1, 'price': 120.00, 'discount_pct': 0, 'tax_rate': 7, 'total': 120.00}, 
            {'pos': 4, 'title': 'Kostenloses Erstgespräch', 'qty': 1, 'price': 0.00, 'discount_pct': 0, 'tax_rate': 0, 'total': 0.00}, 
        ],
        'subtotal': 1825.00,               
        'global_discount_pct': 5,          
        'global_discount_amount': 91.25,   
        'net_total': 1733.75,              
        'taxes': [
            {'label': '19% MwSt.', 'amount': 307.75},
            {'label': '7% IGIC (Teneriffa)', 'amount': 8.40},
        ],
        'gross_total': 2049.90,            
        'skonto_pct': 2,
        'skonto_days': 8,
        'skonto_amount': 41.00,            
    }
    return render(request, 'erp/mock_editor.html', context)
