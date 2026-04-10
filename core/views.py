from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def cloud_explorer_view(request):
    # Hier könntest du später Logik einbauen, die je nach User die richtige ID holt
    # Für Max Mustermann zum Testen:
    seafile_lib_id = "ebb93acc-1599-49f8-83bf-312d385da6e2" 
    # seafile_lib_id = "a0abfeea-2ea6-4a67-8266-98dfb5ea6921"
    # https://cloud.netzsprung.de/library/a0abfeea-2ea6-4a67-8266-98dfb5ea6921/Max%20Mustermann/

    context = {
        'SEAFILE_LIB_ID': seafile_lib_id,
    }
    return render(request, 'core/cloud_explorer.html', context)

def home(request):
    return render(request, 'core/home.html')

def impressum(request):
    return render(request, 'core/impressum.html')

def datenschutz(request):
    return render(request, 'core/datenschutz.html')
    