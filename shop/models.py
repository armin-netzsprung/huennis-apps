from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    PRODUCT_TYPES = (
        ('download', 'Digitales Material (PDF)'),
        ('skill', 'Skill / Dienstleistung'),
    )

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Für Downloads (optional, falls es ein PDF ist)
    # file = models.FileField(upload_to='shop/downloads/', blank=True, null=True)
    file = models.FileField(upload_to='protected_downloads/', blank=True, null=True)
    preview_image = models.ImageField(upload_to='shop/previews/', blank=True, null=True)
    
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='download')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    paypal_order_id = models.CharField(max_length=100, blank=True) # Für die PayPal-Referenz

    def __str__(self):
        return f"{self.user.email} kaufte {self.product.name}"
        