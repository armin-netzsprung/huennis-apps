import os
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .client import SeafileClient
import requests 

from django.urls import reverse
import requests
import os
from urllib.parse import quote

import subprocess
import os
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
import subprocess

@login_required
def create_file_view(request):
    path = request.GET.get('p')
    token = request.user.seafile_auth_token
    client = SeafileClient(token)
    repo_id = client.get_repo_id_by_name("OfficeCentral365")

    # Seafile 11 Hybrid-Modell: 
    # 'p' muss in die URL, 'op' in den Body
    url = f"{client.server_url.rstrip('/')}/api2/repos/{repo_id}/file/"
    
    # Pfad für die URL vorbereiten
    params = {'p': path}
    
    # Operation für den Body vorbereiten
    # data = {
    #     'op': 'create',
    #     'reltxt': '1'
    # }
    
    data = {
        'operation': 'create',
        'op': 'create', # Manche APIs wollen 'op', manche 'operation' - wir senden beides!
        'p': '/Neues Dokument.docx'
    }
    # Header OHNE Content-Type (requests setzt das bei data= automatisch richtig)
    headers = {'Authorization': f'Token {token}'}

    try:
        response = requests.post(url, headers=headers, params=params, data=data)
        
        if response.status_code in [200, 201]:
            parent_dir = os.path.dirname(path) or '/'
            return redirect(f"{reverse('seafile_drive:index')}?p={parent_dir}")
        else:
            # Auf dem Server wollen wir im Fehlerfall das JSON sehen
            return render(request, 'seafile_drive/error.html', {
                'message': f'Server-Fehler ({response.status_code}): {response.text}'
            })
    except Exception as e:
        return render(request, 'seafile_drive/error.html', {'message': str(e)})
    
    

@login_required
def rename_item_view(request):
    repo_id = request.GET.get('repo_id')
    old_path = request.GET.get('p')
    new_name = request.GET.get('new_name')
    token = request.user.seafile_auth_token
    
    client = SeafileClient(token)
    headers = {'Authorization': f'Token {token}'}
    
    # Wir probieren erst 'file', dann 'dir'
    for endpoint in ['file', 'dir']:
        url = f"{client.server_url.rstrip('/')}/api2/repos/{repo_id}/{endpoint}/"
        
        # Das Hybrid-Modell wieder:
        # 'p' in die Query-Parameter
        params = {'p': old_path}
        
        # 'operation' und 'newname' in den Body
        data = {
            'operation': 'rename',
            'op': 'rename',
            'newname': new_name
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, data=data)
            if response.status_code == 200:
                break # Erfolg!
        except Exception:
            continue

    parent_dir = os.path.dirname(old_path) or '/'
    return redirect(f"{reverse('seafile_drive:index')}?p={parent_dir}")




@login_required
def explorer_view(request):
    token = request.user.seafile_auth_token
    
    # Sicherheit: Prüfen ob Token vorhanden
    if not token:
        return render(request, 'seafile_drive/no_token.html')

    client = SeafileClient(token)
    
    # 1. Die ID der gewünschten Bibliothek finden
    repo_name = "OfficeCentral365"
    repo_id = client.get_repo_id_by_name(repo_name)
    
    if not repo_id:
        return render(request, 'seafile_drive/error.html', {
            'message': f'Bibliothek "{repo_name}" wurde auf dem Seafile-Server nicht gefunden.'
        })

    # 2. Aktuellen Pfad aus der URL holen (Default ist Root '/')
    path = request.GET.get('p', '/')
    
    # 3. Inhalt des Verzeichnisses über den Client abrufen
    items = client.get_directory_tree(repo_id, path)

    # 4. Übergeordneten Pfad berechnen (für den "Zurück"-Button)
    # os.path.dirname('/Test/Ordner') -> '/Test'
    parent_path = os.path.dirname(path.rstrip('/'))
    if not parent_path.startswith('/'):
        parent_path = '/'

    context = {
        'items': items,
        'current_path': path,
        'parent_path': parent_path,
        'repo_id': repo_id,
        'repo_name': repo_name
    }
    return render(request, 'seafile_drive/explorer.html', context)

@login_required
def download_file_view(request):
    repo_id = request.GET.get('repo_id')
    path = request.GET.get('p')
    
    if not repo_id or not path:
        return HttpResponseForbidden("Ungültige Anfrage: Parameter fehlen.")

    token = request.user.seafile_auth_token
    client = SeafileClient(token)
    
    # Temporären Download-Link von der Seafile API anfordern
    download_url = client.get_download_link(repo_id, path)
    
    if download_url:
        return redirect(download_url)
    
    return render(request, 'seafile_drive/error.html', {
        'message': 'Der Download-Link konnte nicht generiert werden.'
    })

@login_required
def delete_item_view(request):
    repo_id = request.GET.get('repo_id')
    path = request.GET.get('p')
    token = request.user.seafile_auth_token

    if not repo_id or not path:
        return redirect('seafile_drive:index')

    client = SeafileClient(token)
    base_url = client.server_url.rstrip('/')
    
    # ÄNDERUNG: Kein Slash nach 'dir'
    url = f"{base_url}/api2/repos/{repo_id}/dir" 
    
    headers = {'Authorization': f'Token {token}'}
    
    # p: Pfad des Elements
    # recursively: '1' erlaubt das Löschen von Ordnern mit Inhalt
    params = {
        'p': path,
        'recursively': '1' 
    }

    try:
        response = requests.delete(url, headers=headers, params=params)
        
        # Debugging: Falls es immer noch nicht geht, siehst du hier warum
        if response.status_code != 200:
            print(f"--- Seafile Delete Debug ---")
            print(f"URL: {url}")
            print(f"Path: {path}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Delete Exception: {e}")
    
    # Ermittle den Parent-Ordner für den Redirect
    parent_dir = os.path.dirname(path)
    if not parent_dir or parent_dir == "":
        parent_dir = "/"
        
    return redirect(f"{reverse('seafile_drive:index')}?p={parent_dir}")
