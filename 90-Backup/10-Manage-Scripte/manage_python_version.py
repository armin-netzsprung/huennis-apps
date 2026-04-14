#!/usr/bin/env python3
import os, socket, subprocess, sys
from datetime import datetime

PROJECTS = {
    "1": {
        "name": "Hünnis Blog & Office Cluster",
        "path": "huennis-apps",
        "systemd_files": [
            "/etc/systemd/system/gunicorn_blick.service",
            "/etc/systemd/system/gunicorn_netzsprung.service",
            "/etc/systemd/system/gunicorn_office.service"
        ]
    }
}

# (Restliche Logik für Backup-Erstellung der Service-Files und VENV-Update bleibt gleich wie in deiner ursprünglichen Datei)


def get_env_info():
    hostname = socket.gethostname()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(script_dir, "gunicorn_backups")
    
    # Sicherstellen, dass das Backup-Verzeichnis existiert
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    if "devlap" in hostname.lower():
        return True, f"\033[92mDu arbeitest auf dem Entwicklungs-Client ({hostname})\033[0m", os.path.expanduser("~/dev/"), backup_dir
    else:
        label = f"\033[41m\033[37m ACHTUNG: PRAXISSERVER ({hostname}) \033[0m"
        return False, label, "/var/www/", backup_dir

def get_current_venv(project_full_path):
    if not os.path.exists(project_full_path): return "Pfad nicht gefunden"
    v_dirs = sorted([d for d in os.listdir(project_full_path) if d.startswith("venv-")], reverse=True)
    return v_dirs[0] if v_dirs else "Kein venv vorhanden"

def update_systemd_files(files, old_v, new_v, backup_dir):
    print(f"\n\033[94m--- Systemd-Check & Backup ---\033[0m")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    to_update = []
    
    for f_path in files:
        if os.path.exists(f_path):
            with open(f_path, 'r') as f:
                if old_v in f.read():
                    to_update.append(f_path)
    
    if not to_update:
        print("✅ Alle verknüpften Systemd-Dateien sind bereits aktuell.")
        return

    print(f"Folgende Dateien werden von {old_v} auf {new_v} umgestellt:")
    for f in to_update: print(f" -> {f}")
    
    if input("\nÄnderungen jetzt durchführen und Backups erstellen? (j/n): ").lower() == 'j':
        for f_path in to_update:
            filename = os.path.basename(f_path)
            backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")
            
            # 1. Backup erstellen (in den gunicorn_backups Ordner)
            subprocess.run(["sudo", "cp", f_path, backup_path])
            subprocess.run(["sudo", "chown", os.getlogin(), backup_path]) # Damit du die Datei lesen kannst
            
            # 2. Inhalt ersetzen
            with open(f_path, 'r') as f: content = f.read()
            new_content = content.replace(old_v, new_v)
            
            # 3. Zurückschreiben
            with open("temp_fix", "w") as t: t.write(new_content)
            subprocess.run(["sudo", "mv", "temp_fix", f_path])
            subprocess.run(["sudo", "chown", "root:root", f_path])
            print(f"   💾 Backup erstellt: {os.path.basename(backup_path)}")
        
        subprocess.run(["sudo", "systemctl", "daemon-reload"])
        print("\n✅ Dateien aktualisiert, Backups gesichert und Systemd neu geladen.")
        # Nginx Test zur Sicherheit
        subprocess.run(["sudo", "nginx", "-t"])

def main():
    is_dev, env_label, base_path, backup_dir = get_env_info()
    
    while True:
        os.system('clear')
        print(f"{'='*60}\n{env_label}\n{'='*60}")
        print(f"Backup-Pfad: {backup_dir}")
        print("\nPROJEKT-AUSWAHL:")
        for k, v in PROJECTS.items():
            p_full = os.path.join(base_path, v['path'])
            v_curr = get_current_venv(p_full)
            print(f"   {k}) {v['name']}  (Aktiv: {v_curr})")
        print("   x) Programm beenden")
        
        choice = input("\nWähle ein Projekt: ").strip()
        if choice.lower() == 'x': break
        if choice not in PROJECTS: continue
        
        proj = PROJECTS[choice]
        proj_path = os.path.join(base_path, proj['path'])
        old_venv = get_current_venv(proj_path)
        
        print(f"\n\033[93m--- AKTIONEN FÜR {proj['name'].upper()} ---\033[0m")
        print("1) Backup erstellen (Datenbank & Media via db_manager)")
        print("2) Upgrade auf neue Python-Version (Installation & VENV)")
        print("3) Nur Systemd-Pfade (Gunicorn) korrigieren")
        
        task = input("\nWahl: ").strip()

        if task == "1":
            subprocess.run(["bash", os.path.join(proj_path, "10-Manage-Scripte/db_manager.sh"), "backup"])
            input("\nEnter...")

        elif task == "2":
            print("\nZiel: 1) 3.12  2) 3.13  3) 3.14")
            v_map = {"1": "3.12", "2": "3.13", "3": "3.14"}
            v_choice = input("Wahl: ")
            if v_choice in v_map:
                new_v = v_map[v_choice]
                new_venv_name = f"venv-{new_v}"
                
                if input(f"\nUpgrade auf Python {new_v} starten? (j/n): ").lower() == 'j':
                    subprocess.run(["sudo", "add-apt-repository", "ppa:deadsnakes/ppa", "-y"])
                    subprocess.run(["sudo", "apt", "update"])
                    subprocess.run(["sudo", "apt", "install", f"python{new_v}", f"python{new_v}-venv", "-y"])
                    
                    new_path = os.path.join(proj_path, new_venv_name)
                    subprocess.run([f"python{new_v}", "-m", "venv", new_path])
                    
                    # Hier wird die neue Backup-Logik aufgerufen
                    update_systemd_files(proj['systemd_files'], old_venv, new_venv_name, backup_dir)
                    input("\nEnter...")

        elif task == "3":
            new_v_man = input("Neuer VENV Name (z.B. venv-3.14): ")
            update_systemd_files(proj['systemd_files'], old_venv, new_v_man, backup_dir)
            input("\nEnter...")

if __name__ == "__main__":
    main()
    