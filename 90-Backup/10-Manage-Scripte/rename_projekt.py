import os

def rename_content_and_paths():
    old_name = "huennis-apps"
    new_name = "huennis-apps"
    
    # Verzeichnisse/Dateien, die wir ignorieren
    ignored_dirs = {'.git', 'venv', 'venv-3.14', '__pycache__', 'node_modules', 'staticfiles', 'media'}

    print(f"🚀 Starte Umbenennung von '{old_name}' zu '{new_name}'...")

    for root, dirs, files in os.walk(".", topdown=True):
        # Ignorierte Ordner überspringen
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            # Nur Textdateien bearbeiten
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old_name in content:
                    # HIER war der Fehler: new_name statt new_content_name
                    new_content = content.replace(old_name, new_name)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ Inhalt angepasst: {file_path}")
            except (UnicodeDecodeError, PermissionError):
                # Binärdateien oder geschützte Dateien überspringen
                continue

    print("\n✨ Fertig! Alle Textvorkommen wurden ersetzt.")

if __name__ == "__main__":
    rename_content_and_paths()