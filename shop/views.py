from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Purchase
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests # Du musst 'requests' installieren
from django.conf import settings

@login_required
def payment_success(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order_id = request.GET.get('order_id')

    if not order_id:
        messages.error(request, "Ungültige Bestelldaten.")
        return redirect('product_list')

    # OPTIONAL (aber empfohlen): PayPal API Check
    # Hier würdest du normalerweise ein Access Token holen und 
    # https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id} abrufen,
    # um den Status und den Betrag zu prüfen.

    purchase, created = Purchase.objects.get_or_create(
        user=request.user,
        product=product,
        # Wir nutzen die order_id hier als eindeutigen Schlüssel
        paypal_order_id=order_id 
    )

    if created:
        messages.success(request, f"Vielen Dank! Zugriff auf '{product.name}' freigeschaltet.")
    else:
        messages.info(request, "Du hast dieses Produkt bereits erworben.")
    
    return render(request, 'shop/payment_success.html', {
        'product': product,
        'purchase': purchase
    })


def product_list(request):
    # Wir holen alle aktiven Produkte, sortiert nach dem neuesten
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'shop/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    # Später prüfen wir hier, ob der User das Produkt bereits gekauft hat
    user_has_purchased = False
    if request.user.is_authenticated:
        user_has_purchased = product.purchase_set.filter(user=request.user).exists()
    
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'user_has_purchased': user_has_purchased
    })

import os
from django.http import FileResponse, Http404, HttpResponseForbidden

@login_required
def download_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # 1. Prüfen, ob das Produkt überhaupt eine Datei hat
    if not product.file:
        raise Http404("Keine Datei für dieses Produkt gefunden.")

    # 2. Prüfen, ob der User das Produkt gekauft hat ODER der Preis 0 ist
    has_purchased = Purchase.objects.filter(user=request.user, product=product).exists()
    
    if product.price > 0 and not has_purchased:
        return HttpResponseForbidden("Du musst dieses Produkt erst kaufen, um es herunterzuladen.")

    # 3. Datei sicher ausliefern
    # Wir nutzen FileResponse, das ist speicherschonend
    response = FileResponse(product.file.open('rb'), as_attachment=True)
    
    # Optional: Den Dateinamen beim Download schön setzen
    filename = f"Blick-Dahinter-{product.slug}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
    