# crm/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import LegalEntity

from .forms import LegalEntityForm, AddressFormSet, ContactFormSet
from django.http import JsonResponse
from .models import Person, CommChannel

def quick_create_person(request):
    # DATEN LADEN (GET)
    if request.method == "GET":
        p_id = request.GET.get('person_id')
        if not p_id:
            return JsonResponse({'error': 'No ID provided'}, status=400)
            
        person = get_object_or_404(Person, id=p_id)
        return JsonResponse({
            'salutation': person.salutation,
            'title': person.title,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'pref_lang': person.pref_lang,
            'email': person.channels.filter(channel_type='MAIL').first().value if person.channels.filter(channel_type='MAIL').exists() else '',
            'phone': person.channels.filter(channel_type='PHONE').first().value if person.channels.filter(channel_type='PHONE').exists() else '',
            'mobile': person.channels.filter(channel_type='MOBILE').first().value if person.channels.filter(channel_type='MOBILE').exists() else '',
        })

    # SPEICHERN / UPDATEN (POST)
    if request.method == "POST":
        p_id = request.POST.get('person_id')
        
        data = {
            'salutation': request.POST.get('salutation', 'NEUTRAL'),
            'title': request.POST.get('title', ''),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'pref_lang': request.POST.get('pref_lang', 'DE'),
        }
        
        if p_id and p_id.isdigit():
            person = get_object_or_404(Person, id=p_id)
            for key, value in data.items():
                setattr(person, key, value)
            person.save()
        else:
            person = Person.objects.create(**data)

        # Kanäle aktualisieren
        channels = [
            ('MAIL', request.POST.get('email')),
            ('PHONE', request.POST.get('phone')),
            ('MOBILE', request.POST.get('mobile')),
        ]
        
        for c_type, val in channels:
            if val:
                CommChannel.objects.update_or_create(
                    person=person, channel_type=c_type, 
                    defaults={'value': val}
                )
            else:
                # Falls Feld geleert wurde, Kanal löschen
                CommChannel.objects.filter(person=person, channel_type=c_type).delete()
        
        return JsonResponse({'status': 'ok', 'id': person.id, 'name': str(person)})

    return JsonResponse({'error': 'Invalid method'}, status=405)    
    


@login_required # CRM sollte immer geschützt sein
def index(request):
    return render(request, 'crm/index.html')

def customer_list(request):
    query = request.GET.get('q', '')
    entities = LegalEntity.objects.all()
    
    if query:
        entities = entities.filter(
            Q(internal_id__icontains=query) |
            Q(company_name__icontains=query) |
            Q(is_private_person__last_name__icontains=query)
        )
    
    return render(request, 'crm/legalentity_list.html', {
        'entities': entities,
        'query': query
    })

# crm/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import LegalEntity, PostalAddress, ContactPerson, Person, CommChannel
from .forms import LegalEntityForm

def entity_edit(request, pk=None):
    entity = get_object_or_404(LegalEntity, pk=pk) if pk else LegalEntity()
    
    # Formsets für Adressen und Ansprechpartner
    AddressFormSet = inlineformset_factory(LegalEntity, PostalAddress, fields='__all__', extra=1, can_delete=True)
    ContactFormSet = inlineformset_factory(LegalEntity, ContactPerson, fields='__all__', extra=1, can_delete=True)

    if request.method == "POST":
        form = LegalEntityForm(request.POST, instance=entity)
        address_fs = AddressFormSet(request.POST, instance=entity)
        contact_fs = ContactFormSet(request.POST, instance=entity)

        if form.is_valid() and address_fs.is_valid() and contact_fs.is_valid():
            form.save()
            address_fs.save()
            contact_fs.save()
            return redirect('crm:customer_list')
    else:
        form = LegalEntityForm(instance=entity)
        address_fs = AddressFormSet(instance=entity)
        contact_fs = ContactFormSet(instance=entity)

    return render(request, 'crm/entity_form.html', {
        'form': form,
        'address_fs': address_fs,
        'contact_fs': contact_fs,
        'entity': entity,
        'title': "Kunden bearbeiten" if pk else "Neuanlage"
    })

def entity_edit(request, pk=None):
    if pk:
        entity = get_object_or_404(LegalEntity, pk=pk)
        title = "Kunde bearbeiten"
    else:
        entity = LegalEntity()
        title = "Neuen Kunden anlegen"

    if request.method == "POST":
        form = LegalEntityForm(request.POST, instance=entity)
        address_fs = AddressFormSet(request.POST, instance=entity)
        contact_fs = ContactFormSet(request.POST, instance=entity)

        if form.is_valid() and address_fs.is_valid() and contact_fs.is_valid():
            # Erst das Hauptobjekt speichern
            entity = form.save()
            # Dann die Inlines (Adressen & Kontakte)
            address_fs.instance = entity
            address_fs.save()
            contact_fs.instance = entity
            contact_fs.save()
            return redirect('crm:customer_list')
    else:
        form = LegalEntityForm(instance=entity)
        address_fs = AddressFormSet(instance=entity)
        contact_fs = ContactFormSet(instance=entity)

    return render(request, 'crm/entity_form.html', {
        'form': form,
        'address_fs': address_fs,
        'contact_fs': contact_fs,
        'entity': entity,
        'title': title
    })