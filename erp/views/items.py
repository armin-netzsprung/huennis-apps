from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from erp.models import Document, DocumentItem, Article
from .utils import get_document_summary_context

@login_required
@require_POST
def save_item_field(request, pk, field):
    item = get_object_or_404(DocumentItem, pk=pk)
    value = request.POST.get(f'item_{pk}_{field}')
    
    if not value: return HttpResponse(status=400)

    if field == 'price': item.unit_price = Decimal(value.replace(',', '.'))
    elif field == 'qty': item.quantity = Decimal(value.replace(',', '.'))
    elif field == 'discount': item.discount_percentage = Decimal(value.replace(',', '.'))
    elif field == 'title': item.title = value
    
    item.save()
    
    if field in ['price', 'qty', 'discount', 'tax']:
        doc = item.document
        tax_list = [{'label': f"{r}% MwSt.", 'amount': a} for r, a in doc.taxes.items()]
        context = {
            'item': item, 'doc': doc, 'subtotal': doc.subtotal,
            'global_discount_pct': doc.global_discount_percentage,
            'global_discount_amount': doc.global_discount_amount,
            'net_total': doc.net_total, 'taxes': tax_list,
            'gross_total': doc.gross_total, 'skonto_pct': doc.skonto_percentage,
            'skonto_amount': doc.skonto_amount, 'skonto_days': doc.skonto_days,
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
    
    remaining_items = doc.items.all().order_by('position')
    for i, remaining_item in enumerate(remaining_items, start=1):
        if remaining_item.position != i:
            remaining_item.position = i
            remaining_item.save()

    context = get_document_summary_context(doc)
    context['items'] = remaining_items
    return render(request, 'erp/partials/item_list_only.html', context)

@login_required
def add_item_row(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    new_pos = doc.items.count() + 1
    item = DocumentItem.objects.create(
        document=doc, position=new_pos, title="Neue Position",
        unit_price=Decimal('0.00'), tax_rate=Decimal('19.00')
    )
    context = get_document_summary_context(doc)
    context['item'] = item
    return render(request, 'erp/partials/item_added_with_summary.html', context)

@login_required
def apply_article(request, pk):
    item = get_object_or_404(DocumentItem, pk=pk)
    article_id = request.POST.get('article_select')
    
    if article_id:
        article = get_object_or_404(Article, pk=article_id)
        item.article = article
        item.title = article.name
        item.unit_price = article.net_price
        item.unit = article.unit
        item.tax_rate = article.default_tax_rate
        item.save()
        item.refresh_from_db() 
        
    doc = item.document
    context = get_document_summary_context(doc)
    context['item'] = item 
    return render(request, 'erp/partials/item_added_with_summary.html', context)

@login_required
@require_POST
def reorder_items(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    item_ids = request.POST.getlist('item_id_order')
    
    for index, item_id in enumerate(item_ids, start=1):
        DocumentItem.objects.filter(id=item_id, document=doc).update(position=index)
    
    context = get_document_summary_context(doc)
    context['items'] = doc.items.all().order_by('position')
    return render(request, 'erp/partials/item_list_only.html', context)
    