import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from huennis_config import settings

def generate_customer_number():
    """Generiert KD-260001, KD-260002 etc."""
    year = datetime.datetime.now().strftime('%y')
    prefix = "KD-"
    last_entity = LegalEntity.objects.filter(internal_id__startswith=f"{prefix}{year}").order_by('internal_id').last()
    if not last_entity:
        return f"{prefix}{year}0001"
    
    last_id = int(last_entity.internal_id.split(year)[-1])
    new_id = last_id + 1
    return f"{prefix}{year}{new_id:04d}"

class Person(models.Model):
    CHOICES_ANREDE = (
        ('HERR', _('Mr.')),
        ('FRAU', _('Ms.')),
        ('DIVERS', _('Diverse')),
        ('NEUTRAL', _('Neutral')),
    )
    CHOICES_LANG = (
        ('DE', _('German')),
        ('ES', _('Spanish')),
        ('EN', _('English')),
    )

    salutation = models.CharField(_("Salutation"), max_length=10, choices=CHOICES_ANREDE, default='NEUTRAL')
    title = models.CharField(_("Title"), max_length=100, blank=True, help_text="e.g. Dr., Prof. Dr.")
    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    pref_lang = models.CharField(_("Preferred Language"), max_length=2, choices=CHOICES_LANG, default='DE')

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}".strip()


class LegalEntity(models.Model):
    CHOICES_TYPE = (
        ('COMPANY', _('Company / Organization')),
        ('PRIVATE', _('Private Person')),
    )
    CHOICES_TAX = (
        ('REGULAR', _('Regular (VAT/IVA)')),
        ('IGIC', _('Tenerife/Canaries (IGIC)')),
        ('REVERSE', _('Reverse Charge / Export')),
    )

    entity_type = models.CharField(_("Entity Type"), max_length=10, choices=CHOICES_TYPE, default='COMPANY')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='branches', verbose_name=_("Parent Company"))
    
    internal_id = models.CharField(_("Customer Number"), max_length=50, unique=True, default=generate_customer_number)
    company_name = models.CharField(_("Company Name"), max_length=255, blank=True)
    is_private_person = models.OneToOneField(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='as_legal_entity')
    
    vat_id = models.CharField(_("VAT/NIF/CIF ID"), max_length=50, blank=True)
    tax_id_local = models.CharField(_("Local Tax ID"), max_length=50, blank=True)
    tax_regime = models.CharField(_("Tax Regime"), max_length=10, choices=CHOICES_TAX, default='REGULAR')
    is_zec_approved = models.BooleanField(_("ZEC Approved"), default=False)
    
    webseite = models.URLField(_("Website"), blank=True)

    class Meta:
        verbose_name = _("Legal Entity")
        verbose_name_plural = _("Legal Entities")

    def __str__(self):
        if self.entity_type == 'COMPANY':
            return self.company_name
        return str(self.is_private_person)


class PostalAddress(models.Model):
    CHOICES_ADDR_TYPE = (
        ('BILLING', _('Billing Address')),
        ('SHIPPING', _('Shipping Address')),
        ('PRIVATE', _('Private Address')),
        ('BRANCH', _('Branch Office')),
    )
    legal_entity = models.ForeignKey(LegalEntity, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(_("Address Type"), max_length=10, choices=CHOICES_ADDR_TYPE, default='BILLING')
    street = models.CharField(_("Street"), max_length=255)
    street_extra = models.CharField(_("Street Extra"), max_length=255, blank=True, help_text="Apt, Building, Local")
    zip_code = models.CharField(_("ZIP Code"), max_length=20)
    city = models.CharField(_("City"), max_length=255)
    province = models.CharField(_("Province/State"), max_length=255, blank=True)
    country = models.CharField(_("Country"), max_length=100, default="Germany")

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")


class ContactPerson(models.Model):
    CHOICES_EMP = (
        ('INTERNAL', _('Internal / Permanent')),
        ('FREELANCE', _('Freelancer')),
        ('SUB', _('Sub-Contractor')),
    )
    legal_entity = models.ForeignKey(LegalEntity, on_delete=models.CASCADE, related_name='contacts')
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    
    employment_type = models.CharField(_("Employment Type"), max_length=10, choices=CHOICES_EMP, default='INTERNAL')
    department = models.CharField(_("Department"), max_length=255, blank=True)
    
    is_allgemein = models.BooleanField(_("General Contact"), default=True)
    is_re_contact = models.BooleanField(_("Invoice Recipient"), default=False)
    is_ls_contact = models.BooleanField(_("Shipping Contact"), default=False)
    is_as_contact = models.BooleanField(_("Order Contact"), default=False)
    is_vertrag = models.BooleanField(_("Contract Contact"), default=False)

    class Meta:
        verbose_name = _("Contact Person")
        verbose_name_plural = _("Contact Persons")


class CommChannel(models.Model):
    CHOICES_CHAN = (
        ('MAIL', _('E-Mail')),
        ('PHONE', _('Phone')),
        ('MOBILE', _('Mobile')),
        ('WHATSAPP', _('WhatsApp')),
        ('SIGNAL', _('Signal')),
        ('FAX', _('Fax')),
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name='channels')
    entity = models.ForeignKey(LegalEntity, on_delete=models.CASCADE, null=True, blank=True, related_name='channels')
    
    channel_type = models.CharField(_("Type"), max_length=10, choices=CHOICES_CHAN)
    value = models.CharField(_("Value"), max_length=255)
    label = models.CharField(_("Label"), max_length=100, blank=True, help_text="e.g. Office, Private")
    is_primary = models.BooleanField(_("Primary"), default=False)


class Interaction(models.Model):
    CHOICES_INT = (
        ('CALL', _('Phone Call')),
        ('MEETING', _('Meeting')),
        ('NOTE', _('Note')),
        ('EMAIL', _('E-Mail')),
    )
    entity = models.ForeignKey(LegalEntity, on_delete=models.CASCADE, related_name='interactions')
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    
    interaction_type = models.CharField(_("Type"), max_length=10, choices=CHOICES_INT, default='NOTE')
    subject = models.CharField(_("Subject"), max_length=255)
    content = models.TextField(_("Content"))
    attachment = models.FileField(_("Attachment"), upload_to='crm/interactions/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # KORREKTUR HIER: Nutzt das Modell aus deinen Settings
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )

    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")
        