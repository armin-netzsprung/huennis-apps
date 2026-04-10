from django.shortcuts import render, get_object_or_404
from .models import WikiNode

def wiki_index(request, slug=None):
    # Wir laden alle Knoten für die Sidebar (MPTT sortiert diese automatisch korrekt)
    nodes = WikiNode.objects.all()
    
    current_node = None
    if slug:
        # Falls ein Slug übergeben wurde, suchen wir den passenden Eintrag
        current_node = get_object_or_404(WikiNode, slug=slug)
    
    return render(request, 'wiki/wiki_index.html', {
        'nodes': nodes,
        'current_node': current_node,
    })
