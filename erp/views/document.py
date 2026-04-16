from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from erp.models import Document, Article
from crm.models import LegalEntity

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
        'skonto_payable_amount': doc.gross_total - doc.skonto_amount,
    }
    
    return render(request, 'erp/mock_editor.html', context)

@login_required
def document_save_basics(request, pk):
    if request.method == 'POST':
        doc = get_object_or_404(Document, pk=pk)
        try:
            doc.intro_text = request.POST.get('intro_text', '')
            doc.outro_text = request.POST.get('outro_text', '')
            doc.global_discount_percentage = request.POST.get('global_discount_pct', '0').replace(',', '.')
            doc.skonto_percentage = request.POST.get('skonto_pct', '0').replace(',', '.')
            doc.skonto_days = request.POST.get('skonto_days', 0)
            doc.is_small_business = request.POST.get('is_small_business') == 'on'
            doc.save()
            messages.success(request, f"{doc.get_document_type_display()} {doc.document_number} erfolgreich gespeichert.")
        except Exception as e:
            messages.error(request, f"Fehler beim Speichern: {str(e)}")
        return render(request, 'includes/messages.html')
    return HttpResponse(status=405)

def clear_messages(request):
    return HttpResponse("")

@login_required
def document_recalculate(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        discount_pct = request.POST.get('global_discount_pct', '0').replace(',', '.')
        doc.global_discount_percentage = Decimal(discount_pct or '0')
        doc.is_small_business = request.POST.get('is_small_business') == 'on'
        
        for item in doc.items.all():
            qty = request.POST.get(f'item_{item.id}_qty')
            disc = request.POST.get(f'item_{item.id}_discount')
            if qty: item.quantity = Decimal(qty.replace(',', '.'))
            if disc: item.discount_percentage = Decimal(disc.replace(',', '.'))
            item.save()
        doc.save()

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

@login_required
def convert_document(request, pk, target_type):
    source_doc = get_object_or_404(Document, pk=pk)
    valid_types = [t[0] for t in Document.DOC_TYPES]
    if target_type not in valid_types:
        messages.error(request, "Ungültiger Dokumententyp.")
        return redirect('erp:dashboard')

    new_doc = source_doc.create_follow_up(target_type)
    messages.success(request, f"{source_doc.get_document_type_display()} wurde erfolgreich in {new_doc.get_document_type_display()} umgewandelt.")
    return redirect('erp:document_edit', pk=new_doc.pk)

@login_required
def change_customer(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    new_customer_id = request.POST.get('customer_change')
    if new_customer_id:
        doc.customer = get_object_or_404(LegalEntity, pk=new_customer_id)
        doc.save()
    return render(request, 'erp/partials/customer_address.html', {'customer': doc.customer})