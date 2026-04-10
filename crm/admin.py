from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Person, LegalEntity, PostalAddress, 
    ContactPerson, CommChannel, Interaction
)

# --- INLINES ---

class PostalAddressInline(admin.TabularInline):
    model = PostalAddress
    extra = 1

class CommChannelInline(admin.TabularInline):
    model = CommChannel
    extra = 1
    fields = ('channel_type', 'value', 'label', 'is_primary')

class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0
    autocomplete_fields = ['person']

# --- ADMIN CLASSES ---

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'salutation', 'pref_lang')
    search_fields = ('last_name', 'first_name')
    inlines = [CommChannelInline]

class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0
    autocomplete_fields = ['person']
    # NEU: Zeige die wichtigsten Checkboxen direkt in der Zeile an
    fields = ('person', 'department', 'employment_type', 'is_re_contact', 'is_vertrag', 'is_allgemein')
    verbose_name = _("Ansprechpartner")
    verbose_name_plural = _("Ansprechpartner")

@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'display_name', 'parent', 'entity_type', 'tax_regime')
    list_filter = ('entity_type', 'tax_regime', 'is_zec_approved')
    search_fields = ('company_name', 'internal_id', 'is_private_person__last_name')
    
    # Gruppierung der Felder im Formular
    fieldsets = (
        (_('Basis Info'), {
            'fields': ('internal_id', 'entity_type', 'parent')
        }),
        (_('Name / Person'), {
            'fields': ('company_name', 'is_private_person'),
            'description': _('Fill Company Name for businesses or select Person for private clients.')
        }),
        (_('Tax & Legal'), {
            'fields': ('vat_id', 'tax_id_local', 'tax_regime', 'is_zec_approved')
        }),
        (_('Web'), {
            'fields': ('webseite',)
        }),
    )
    
    inlines = [PostalAddressInline, ContactPersonInline, CommChannelInline]

    def display_name(self, obj):
        return str(obj)
    display_name.short_description = _("Name")

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'entity', 'interaction_type', 'subject', 'created_by')
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('subject', 'content', 'entity__company_name')
    readonly_fields = ('created_at', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Nur beim Erstellen
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Einfache Registrierung für den Rest
admin.site.register(PostalAddress)
admin.site.register(ContactPerson)
admin.site.register(CommChannel)
