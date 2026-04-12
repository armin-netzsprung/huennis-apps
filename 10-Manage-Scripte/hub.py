#!/usr/bin/env python3
import os
import socket
import sys
import subprocess
import datetime

def get_env_info():
    hostname = socket.gethostname()
    if "devlap" in hostname.lower():
        return f"\033[92m💻 ENTWICKLUNGS-CLIENT ({hostname})\033[0m", True
    else:
        return f"\033[41m\033[37m 🔥 PRAXISSERVER ({hostname}) \033[0m", False

def run_full_backup(script_dir):
    """Erstellt ein Backup vom gesamten Projekt und speichert es EINE EBENE HÖHER."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"FULL-BACKUP_{timestamp}.tar.gz"
    
    # 1. Pfade definieren
    # script_dir ist ~/dev/huennis-blog/10-Manage-Scripte
    # project_root ist ~/dev/huennis-blog
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    # dev_dir ist ~/dev/
    dev_dir = os.path.abspath(os.path.join(project_root, ".."))
    
    # Ziel: ~/dev/90-Backup/huennis-blog
    target_base = os.path.join(dev_dir, "90-Backup", "huennis-blog")
    
    if not os.path.exists(target_base):
        os.makedirs(target_base, exist_ok=True)

    full_output_path = os.path.join(target_base, backup_filename)

    print(f"\n" + "="*60)
    print(f"📦 STARTE VOLL-SICHERUNG (GESAMTER SOURCECODE)")
    print(f"🕒 ZEITPUNKT: {timestamp}")
    print(f"📂 QUELLE:    {project_root}")
    print(f"📂 ZIEL:      {full_output_path}")
    print("="*60)
    
    # DB-Dumps via db_manager.sh erzeugen
    db_manager = os.path.join(script_dir, "db_manager.sh")
    if os.path.exists(db_manager):
        print("\n[1/2] Erstelle frische Datenbank-Dumps...")
        subprocess.run(["bash", db_manager, "dump_all"])

    # 2. Packen
    print(f"\n[2/2] Komprimiere Verzeichnis...")
    
    exclude_args = [
        "--exclude=venv", 
        "--exclude=.git", 
        "--exclude=__pycache__", 
        "--exclude=node_modules",
        "--exclude=*.pyc",
        # Da das Backup jetzt außerhalb liegt, brauchen wir 90-Backup hier nicht exkludieren,
        # es schadet aber auch nicht zur Sicherheit.
        "--exclude=90-Backup" 
    ]
    
    try:
        # Wir stehen in ~/dev/ und packen den Ordner "huennis-blog"
        parent_dir = dev_dir
        target_folder = os.path.basename(project_root) # "huennis-blog"
        
        cmd = ["tar", "-czf", full_output_path] + exclude_args + ["-C", parent_dir, target_folder]
        
        subprocess.run(cmd, check=True)
        
        print("\n" + "-"*60)
        print(f"✅ VOLL-BACKUP ERFOLGREICH")
        print(f"📄 DATEI: {backup_filename}")
        print("-" * 60)
    except Exception as e:
        print(f"\n❌ Fehler beim Backup: {e}")
    
    input("\nDrücke Enter zum Fortfahren...")

def run_gemini_backup(script_dir):
    """Erstellt ein schlankes Backup ohne venv, media, staticfiles für den KI-Upload."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"GEMINI-UPLOAD_{timestamp}.tar.gz"
    
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    dev_dir = os.path.abspath(os.path.join(project_root, ".."))
    target_base = os.path.join(dev_dir, "90-Backup", "huennis-blog")
    
    if not os.path.exists(target_base):
        os.makedirs(target_base, exist_ok=True)
        
    target_path = os.path.join(target_base, backup_filename)
    project_folder_name = os.path.basename(project_root)
    
    # Diese Ordner/Dateien werden für die KI ignoriert
    # Diese Ordner/Dateien werden für die KI ignoriert
    excludes = [
        "--exclude=venv*",
        "--exclude=.venv*",        # Falls die Umgebung mit Punkt anfängt
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "--exclude=.git",
        "--exclude=.idea",         # PyCharm Cache
        "--exclude=.vscode",       # VS Code Cache
        "--exclude=media",
        "--exclude=staticfiles",
        "--exclude=db.sqlite3",
        "--exclude=node_modules",  # Der häufigste Übeltäter!
        "--exclude=*.log",
        "--exclude=*.sql",
        "--exclude=tailwindcss",
        "--exclude=static/tinymce" # Kann ignoriert werden, da es Standard-Code ist
    ]
    
    # tar Befehl zusammensetzen (-C sorgt dafür, dass die Ordnerstruktur relativ bleibt)
    cmd = ["tar", "-czf", target_path] + excludes + ["-C", dev_dir, project_folder_name]
    
    print(f"\n🤖 Erstelle Gemini-optimiertes Backup...")
    try:
        subprocess.run(cmd, check=True)
        print(f"\033[92m✔ Gemini-Backup erfolgreich erstellt!\033[0m")
        print(f"📁 Datei: {target_path}")
        print("💡 Diese Datei kannst du jetzt direkt ins Chat-Fenster ziehen.")
    except subprocess.CalledProcessError as e:
        print(f"\033[91m✖ Fehler beim Erstellen des Backups: {e}\033[0m")

def main():
    env_label, is_dev = get_env_info()
    # Das Verzeichnis, in dem dieses Script liegt (~/dev/huennis-blog)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        # os.system('clear')
        print("="*60)
        print(f"      🚀 HÜNNIS-BLOG & OFFICECENTRAL MANAGEMENT HUB")
        print("="*60)
        print(f" STANDORT: {env_label}")
        print("="*60)

        print("\n Verfügbare Werkzeuge:")
        print(f" [1] Dev-Starter      -> Django-Server starten")
        print(f" [2] Deployment       -> Code auf Server übertragen")
        print(f" [3] Python-Admin     -> Versionen & Umgebungen")
        print(f" [4] DB-Manager       -> Backups & Restore (SQL)")
        print(f" [5] 📦 FULL BACKUP   -> DEV! Gesamten Sourcecode sichern (nach ../90-Backup)")
        print(f" [6] 🤖 GEMINI BACKUP -> Code für KI-Upload (ohne venv, db, media...)")

        print("\n [q] Beenden")
        print("-" * 60)

        choice = input("Wähle eine Aktion: ").strip().lower()
        if choice == 'q': break
        
        mapping = {
            "1": ["python3", "run_dev.py"],
            "2": ["python3", "deploy-master-server2.py"],
            "3": ["python3", "manage_python_version.py"],
            "4": ["bash", "db_manager.sh"]
        }

        if choice == "5":
            run_full_backup(script_dir)
        elif choice == "6":
            run_gemini_backup(script_dir)
        elif choice in mapping:
            cmd = mapping[choice]
            script_path = os.path.join(script_dir, cmd[1])
            if os.path.exists(script_path):
                try:
                    subprocess.run([cmd[0], script_path])
                except KeyboardInterrupt: pass
            else:
                print(f"\n❌ Fehler: {cmd[1]} nicht gefunden!")
                input("Enter zum Fortfahren...")

if __name__ == "__main__":
    main()
