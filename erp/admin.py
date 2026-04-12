from django.contrib import admin
from .models import Article, TextModule, Document, DocumentItem, Unit

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('article_number', 'name', 'unit', 'net_price', 'default_tax_rate')
    search_fields = ('article_number', 'name', 'description')
    list_filter = ('default_tax_rate', 'unit')
    ordering = ('article_number', 'name')


@admin.register(TextModule)
class TextModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'module_type', 'is_default_for_an', 'is_default_for_re')
    list_filter = ('module_type', 'is_default_for_an', 'is_default_for_re')
    search_fields = ('name', 'content')


class DocumentItemInline(admin.TabularInline):
    model = DocumentItem
    extra = 1  # Zeigt standardmäßig eine leere Extra-Zeile für neue Positionen an
    fields = ('position', 'article', 'title', 'quantity', 'unit', 'unit_price', 'tax_rate', 'discount_percentage')
    autocomplete_fields = ['article'] # Macht die Artikelauswahl bei vielen Artikeln durchsuchbar


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'document_type', 'customer', 'document_date', 'status', 'net_total', 'gross_total')
    list_filter = ('document_type', 'status', 'document_date', 'is_small_business')
    search_fields = ('document_number', 'customer__company_name', 'customer__is_private_person__last_name')
    autocomplete_fields = ['customer', 'parent_document']
    
    # Gruppierung der Felder im Admin-Bereich für bessere Übersicht
    fieldsets = (
        ('Kopfdaten', {
            'fields': ('document_type', 'document_number', 'status', 'customer', 'parent_document')
        }),
        ('Datum & Fristen', {
            'fields': ('document_date', 'due_date')
        }),
        ('Konditionen & Steuern', {
            'fields': ('global_discount_percentage', 'skonto_percentage', 'skonto_days', 'is_small_business', 'tax_note')
        }),
        ('Texte', {
            'fields': ('intro_text', 'outro_text'),
            'classes': ('collapse',) # Versteckt diesen Block standardmäßig (aufklappbar)
        }),
        ('System-Referenzen', {
            'fields': ('seafile_reference',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DocumentItemInline]
    
    # Damit 'document_number' leer bleiben darf und beim Speichern generiert wird
    readonly_fields = ('document_number',)

    def save_model(self, request, obj, form, change):
        """
        Optional: Hier könnten wir beim allerersten Speichern prüfen, 
        ob wir Standardtexte aus TextModule ziehen sollen, falls die Felder leer sind.
        Fürs Erste lassen wir die normale save()-Methode die Nummerngenerierung machen.
        """
        super().save_model(request, obj, form, change)
