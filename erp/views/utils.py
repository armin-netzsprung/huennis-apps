from erp.models import Article

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
