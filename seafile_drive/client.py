import requests

class SeafileClient:
    def __init__(self, token, server_url="https://cloud.netzsprung.de"):
        self.token = token
        self.server_url = server_url.rstrip('/')
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Accept": "application/json"
        }

    def get_repo_id_by_name(self, repo_name):
        """Findet die ID einer Bibliothek anhand ihres Namens."""
        url = f"{self.server_url}/api2/repos/"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                if repo['name'] == repo_name:
                    return repo['id']
        return None

    def get_directory_tree(self, repo_id, path="/"):
        """
        Holt den Inhalt eines Verzeichnisses.
        Gibt eine Liste von Dictionaries zurück.
        """
        url = f"{self.server_url}/api2/repos/{repo_id}/dir/"
        params = {"p": path}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            items = response.json()
            # Wir bereichern die Daten um den vollständigen Pfad für die Links
            for item in items:
                item['full_path'] = f"{path.rstrip('/')}/{item['name']}"
                # Erzeuge den Viewer-Link direkt
                item['view_url'] = f"{self.server_url}/lib/{repo_id}/file{item['full_path']}"
            return items
        return []

    def get_download_link(self, repo_id, file_path):
        """Holt einen temporären Download-Link für eine Datei."""
        url = f"{self.server_url}/api2/repos/{repo_id}/file/"
        params = {"p": file_path, "reuse": 1}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json() # Das ist die reine URL als String
        return None

    def upload_file(self, repo_id, filename, file_content, parent_dir="/"):
        """
        Lädt eine Datei (als Byte-Stream) in ein Seafile-Verzeichnis hoch.
        """
        url = f"{self.server_url}/api2/repos/{repo_id}/upload-link/"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return False
            
        upload_url = response.json()
        files = {'file': (filename, file_content)}
        data = {'parent_dir': parent_dir}
        
        upload_response = requests.post(upload_url, headers=self.headers, files=files, data=data)
        return upload_response.status_code == 200