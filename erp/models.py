from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

class Unit(models.Model):
    """
    Pflegbare Einheiten für Artikel (Dropdown)
    """
    name = models.CharField('Bezeichnung', max_length=50, unique=True, help_text="z.B. Stück, Stunde, Pauschale")
    abbreviation = models.CharField('Abkürzung', max_length=10, blank=True, help_text="z.B. Stk., Std., mtl.")

    class Meta:
        verbose_name = 'Einheit'
        verbose_name_plural = 'Einheiten'
        ordering = ['name']

    def __str__(self):
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name
    
class Article(models.Model):
    """
    Der Artikel- und Dienstleistungsstamm.
    Dient als Vorlage. Beim Einfügen in ein Dokument werden die Werte kopiert!
    """
    article_number = models.CharField('Artikelnummer', max_length=50, unique=True, blank=True, null=True)
    name = models.CharField('Bezeichnung', max_length=255)
    description = models.TextField('Beschreibung', blank=True)
    
    # unit = models.CharField('Einheit', max_length=50, default='Stück', help_text="z.B. Stück, Std., Pauschale")
    # Alter Code: unit = models.CharField(...)
    # Neuer Code:
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Einheit')
    net_price = models.DecimalField('Einzelpreis (Netto)', max_digits=10, decimal_places=2, default=0.00)
    default_tax_rate = models.DecimalField('Standard-MwSt (%)', max_digits=5, decimal_places=2, default=19.00) 

    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['name']

    def __str__(self):
        return f"{self.article_number or ''} {self.name}".strip()


class TextModule(models.Model):
    """
    Vorlagen für Einleitungs- und Schlusstexte.
    """
    MODULE_TYPES = [
        ('INTRO', 'Einleitungstext'),
        ('OUTRO', 'Schlusstext')
    ]
    
    name = models.CharField('Name', max_length=100, help_text="Interner Name, z.B. 'Standard Angebot Intro'")
    module_type = models.CharField('Typ', max_length=10, choices=MODULE_TYPES)
    content = models.TextField('Inhalt (HTML)', help_text="Wird in TinyMCE geladen")
    
    is_default_for_an = models.BooleanField('Standard für Angebote', default=False)
    is_default_for_re = models.BooleanField('Standard für Rechnungen', default=False)

    class Meta:
        verbose_name = 'Textbaustein'
        verbose_name_plural = 'Textbausteine'

    def __str__(self):
        return f"{self.get_module_type_display()} - {self.name}"


class Document(models.Model):
    """
    Der Belegkopf (Haupttabelle für alle Dokumentenarten)
    """
    DOC_TYPES = [
        ('AN', 'Angebot'),
        ('AB', 'Auftragsbestätigung'),
        ('LI', 'Lieferschein'),
        ('RE', 'Rechnung'),
    ]
    
    # 1. Metadaten
    document_type = models.CharField('Dokumententyp', max_length=2, choices=DOC_TYPES, default='RE')
    document_number = models.CharField('Belegnummer', max_length=30, unique=True, blank=True)
    status = models.CharField('Status', max_length=20, default='draft', choices=[
        ('draft', 'Entwurf'), ('sent', 'Gesendet'), ('paid', 'Bezahlt'), ('cancelled', 'Storniert')
    ])
    
    # 2. Verknüpfungen
    customer = models.ForeignKey('crm.LegalEntity', verbose_name='Kunde', on_delete=models.RESTRICT, related_name='erp_documents')
    parent_document = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='child_documents')
    seafile_reference = models.CharField('Seafile ID', max_length=255, blank=True, null=True)
    
    # 3. Daten & Fristen
    created_at = models.DateTimeField('Erstellt am', auto_now_add=True)
    document_date = models.DateField('Belegdatum', default=timezone.now)
    due_date = models.DateField('Fälligkeitsdatum', null=True, blank=True)
    
    # 4. Inhalte (Texte)
    intro_text = models.TextField('Einleitungstext', blank=True, null=True)
    outro_text = models.TextField('Schlusstext', blank=True, null=True)
    
    # 5. Kaufmännische Bedingungen
    global_discount_percentage = models.DecimalField('Gesamtrabatt (%)', max_digits=5, decimal_places=2, default=0.00)
    skonto_percentage = models.DecimalField('Skonto (%)', max_digits=5, decimal_places=2, default=0.00)
    skonto_days = models.PositiveIntegerField('Skonto (Tage)', default=0)
    
    is_small_business = models.BooleanField('Kleinunternehmerregelung', default=False)
    tax_note = models.CharField('Steuer-Hinweis', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumente'
        ordering = ['-document_date', '-document_number']

    def __str__(self):
        return f"{self.document_number} - {self.customer}"

    def save(self, *args, **kwargs):
        # Automatische Nummernvergabe (z.B. RE-2026-0001)
        if not self.document_number:
            year = self.document_date.year
            prefix = self.document_type
            last_doc = Document.objects.filter(
                document_type=prefix, 
                document_date__year=year
            ).order_by('id').last()
            
            if last_doc and last_doc.document_number:
                try:
                    last_num = int(last_doc.document_number.split('-')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            self.document_number = f"{prefix}-{year}-{new_num:04d}"
            
        super().save(*args, **kwargs)

    # --- KAUFMÄNNISCHE BERECHNUNGEN FÜR DEN BELEGKOPF ---
    
    @property
    def subtotal(self):
        """Summe aller Positionen (bereits abzüglich Positionsrabatte)"""
        return sum(item.net_total for item in self.items.all())

    @property
    def global_discount_amount(self):
        """Der Wert des globalen Rabatts in Euro"""
        return self.subtotal * (self.global_discount_percentage / Decimal('100.00'))

    @property
    def net_total(self):
        """Netto-Gesamtsumme nach globalem Rabatt"""
        return self.subtotal - self.global_discount_amount

    @property
    def taxes(self):
        """
        Gruppiert die Steuern nach Sätzen. 
        Gibt z.B. zurück: {Decimal('19.00'): 150.00, Decimal('7.00'): 14.00}
        """
        if self.is_small_business:
            return {Decimal('0.00'): Decimal('0.00')}
            
        tax_groups = {}
        # Den globalen Rabatt müssen wir anteilig auf die Steuersätze verteilen!
        discount_factor = Decimal('1') - (self.global_discount_percentage / Decimal('100.00'))
        
        for item in self.items.all():
            rate = item.tax_rate
            if rate not in tax_groups:
                tax_groups[rate] = Decimal('0.00')
            # Steuer = (Positions-Netto * Globalrabatt-Faktor) * (Steuersatz / 100)
            discounted_item_net = item.net_total * discount_factor
            tax_groups[rate] += discounted_item_net * (rate / Decimal('100.00'))
            
        return tax_groups

    @property
    def total_tax_amount(self):
        """Die Summe aller Steuern"""
        return sum(self.taxes.values())

    @property
    def gross_total(self):
        """Brutto-Gesamtsumme"""
        return self.net_total + self.total_tax_amount

    @property
    def skonto_amount(self):
        """Der Skonto-Wert (wird vom Brutto berechnet)"""
        return self.gross_total * (self.skonto_percentage / Decimal('100.00'))


class DocumentItem(models.Model):
    """
    Die einzelnen Positionen auf einem Dokument.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='items')
    
    # SET_NULL: Wenn der Artikel gelöscht wird, bleibt die Rechnungshistorie bestehen!
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    
    position = models.PositiveIntegerField('Position', default=1)
    title = models.CharField('Bezeichnung', max_length=255)
    description = models.TextField('Beschreibung', blank=True)
    
    quantity = models.DecimalField('Menge', max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Einheit')
    unit_price = models.DecimalField('Einzelpreis', max_digits=10, decimal_places=2)
    
    tax_rate = models.DecimalField('MwSt (%)', max_digits=5, decimal_places=2, default=Decimal('19.00'))
    discount_percentage = models.DecimalField('Positionsrabatt (%)', max_digits=5, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Position'
        verbose_name_plural = 'Positionen'
        ordering = ['position']

    def __str__(self):
        return f"Pos {self.position} - {self.title}"

    # --- BERECHNUNGEN PRO POSITION ---
    
    @property
    def base_total(self):
        """Menge * Einzelpreis (Ohne Rabatt)"""
        return self.quantity * self.unit_price

    @property
    def discount_amount(self):
        """Wert des Positionsrabatts in Euro"""
        return self.base_total * (self.discount_percentage / Decimal('100.00'))

    @property
    def net_total(self):
        """Endgültiger Netto-Wert dieser Zeile"""
        return self.base_total - self.discount_amount

