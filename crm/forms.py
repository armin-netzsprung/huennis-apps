from django import forms
from .models import LegalEntity, Person, PostalAddress

from django import forms
from django.forms import inlineformset_factory
from .models import LegalEntity, Person, PostalAddress, ContactPerson

class LegalEntityForm(forms.ModelForm):
    class Meta:
        model = LegalEntity
        fields = ['entity_type', 'internal_id', 'company_name', 'parent', 
                  'vat_id', 'tax_id_local', 'tax_regime', 'is_zec_approved', 'webseite']

        widgets = {
            'entity_type': forms.Select(attrs={'class': 'form-input-styled'}),
            'internal_id': forms.TextInput(attrs={'class': 'form-input-styled', 'readonly': 'readonly'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input-styled', 'placeholder': 'z.B. Muster GmbH'}),
            'parent': forms.Select(attrs={'class': 'form-input-styled'}),
            'vat_id': forms.TextInput(attrs={'class': 'form-input-styled'}),
            'tax_id_local': forms.TextInput(attrs={'class': 'form-input-styled'}),
            'tax_regime': forms.Select(attrs={'class': 'form-input-styled'}),
            'webseite': forms.URLInput(attrs={'class': 'form-input-styled', 'placeholder': 'https://...'}),
        }


# Formsets erstellen
AddressFormSet = inlineformset_factory(
    LegalEntity, PostalAddress,
    fields=['address_type', 'street', 'zip_code', 'city', 'country'],
    extra=1, can_delete=True
)

ContactFormSet = inlineformset_factory(
    LegalEntity, ContactPerson,
    fields=['person', 'department', 'is_re_contact', 'is_vertrag'],
    extra=1, can_delete=True
)