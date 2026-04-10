import requests

# KONFIGURATION
SEAFILE_URL = "https://cloud.netzsprung.de"
TOKEN = "aeda2f162aeae79ef4ce321b6f157d59eda8ea41"
REPO_ID = "ebb93acc-1599-49f8-83bf-312d385da6e2" # OfficeCentral365

headers = {
    "Authorization": f"Token {TOKEN}",
    "Accept": "application/json; indent=4"
}

def get_tree(path="/"):
    """Liest Verzeichnisse rekursiv aus."""
    url = f"{SEAFILE_URL}/api2/repos/{REPO_ID}/dir/"
    params = {"p": path}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Fehler bei Pfad {path}: {response.status_code}")
        return []
    
    items = response.json()
    for item in items:
        # Einrückung für Baumstruktur simulieren
        depth = path.count("/")
        indent = "  " * depth
        
        if item["type"] == "dir":
            print(f"{indent}📁 {item['name']}/")
            # Rekursiver Aufruf für Unterordner
            get_tree(f"{path}{item['name']}/")
        else:
            # Link-Generierung für CRM
            file_path = f"{path}{item['name']}"
            
            # 1. Editor-Link (OnlyOffice / PDF-Viewer von Seafile)
            # Seafile nutzt für Office & PDF denselben Viewer-Link
            view_url = f"{SEAFILE_URL}/lib/{REPO_ID}/file{file_path}"
            
            print(f"{indent}📄 {item['name']}")
            print(f"{indent}   🔗 CRM-Link: {view_url}")

if __name__ == "__main__":
    print(f"Baumstruktur für Bibliothek: OfficeCentral365\n" + "="*45)
    get_tree()
    