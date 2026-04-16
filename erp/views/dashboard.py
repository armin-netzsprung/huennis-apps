from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from erp.models import Document

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
    