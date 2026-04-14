#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime

class HuennisMaster:
    def __init__(self):
        # Pfade basierend auf deiner neuen Struktur
        self.envs = {
            "1": ("DEV", "/home/coder/10-dev-huennis-apps"),
            "2": ("TEST", "/home/coder/20-test-huennis-apps"),
            "3": ("PROD", "/home/coder/30-prod-huennis-apps")
        }
        self.identities = {"1": "office", "2": "blick", "3": "netzsprung"}
        self.backup_dir = "/home/coder/90-Backup"
        
        self.cur_env = "DEV"
        self.cur_path = self.envs["1"][1]
        self.cur_id = "office"
        self.cur_py = "3.14" # Fixiert auf deine portable Version

    def cls(self): os.system('clear')

    def header(self):
        self.cls()
        print("="*75)
        print(f" 🚀 MASTER-ADMIN | ENV: {self.cur_env} | ID: {self.cur_id.upper()} | PY: {self.cur_py}")
        print(f" PATH: {self.cur_path}")
        print("="*75)

    def select_setup(self):
        self.header()
        print(" WÄHLE UMGEBUNG:")
        print(" [1] DEV (10-...)  [2] TEST (20-...)  [3] PROD (30-...)")
        ev = input("\nWahl [1]: ") or "1"
        self.cur_env, self.cur_path = self.envs.get(ev, self.envs["1"])
        
        print("\nWÄHLE IDENTITY:")
        print(" [1] office  [2] blick  [3] netzsprung")
        self.cur_id = self.identities.get(input("\nWahl [1]: "), "office")
        
        # Python 3.12 Option entfernt, da wir nur 3.14 portabel nutzen
        self.cur_py = "3.14"

    def run_django(self, args):
        venv_py = f"{self.cur_path}/venv-{self.cur_py}/bin/python"
        
        if not os.path.exists(venv_py):
            print(f"\n❌ venv nicht gefunden unter: {venv_py}")
            return

        env_vars = os.environ.copy()
        env_vars["SITE_IDENTITY"] = self.cur_id
        
        print(f"\nDEBUG: Starte {args} in {self.cur_path}...")
        try:
            # shell=False ist sicherer, wir geben die env_vars explizit mit
            subprocess.run([venv_py, "manage.py"] + args, cwd=self.cur_path, env=env_vars, check=True)
        except subprocess.CalledProcessError as e:
            print(f"\n❌ FEHLER beim Ausführen von Django:")
            print(f"Rückgabecode: {e.returncode}")
        except Exception as e:
            print(f"\n❌ Unerwarteter Fehler: {e}")
    def do_deploy(self):
        if self.cur_env == "PROD": 
            print("\n❌ Aus PROD heraus kann nicht gepusht werden.")
            return
            
        target_env = "TEST" if self.cur_env == "DEV" else "PROD"
        target_path = self.envs["2"][1] if target_env == "TEST" else self.envs["3"][1]
        
        print(f"\n⚠️  DEPLOY: {self.cur_env} (Pfad: {self.cur_path}) -> {target_env}")
        if input("Sicher? (y/n): ").lower() != 'y': return
        
        # Rsync wie im alten deploy_manager_v2
        subprocess.run(["rsync", "-av", "--delete", "--exclude", "venv*", "--exclude", "media/", "--exclude", ".git/", f"{self.cur_path}/", f"{target_path}/"])
        
        # Berechtigungen auf dem Host fixen (via dein Host-Script)
        subprocess.run(["sudo", "bash", f"{self.envs['1'][1]}/10-Manage-Scripte/server2-berechtigungen.sh"])
        print(f"✅ Deploy nach {target_env} abgeschlossen.")

    def do_backup(self, full=False):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        fname = f"{self.cur_env}_{self.cur_id}_py{self.cur_py}_{ts}{'_FULL' if full else ''}.tar.gz"
        target = f"{self.backup_dir}/{fname}"
        
        # Excludes für Light-Backup
        exclude = ["--exclude=media", "--exclude=venv*", "--exclude=staticfiles", "--exclude=.git"] if not full else []
        
        print(f"\n📦 Erstelle {'FULL' if full else 'LIGHT'} Backup...")
        # Nutzt tar -C um Pfade im Archiv sauber zu halten
        subprocess.run(["tar"] + exclude + ["-czf", target, "-C", "/home/coder", os.path.basename(self.cur_path)])
        print(f"✅ Backup gespeichert: {target}")

    def manage_services(self):
        print("\n [1] Nginx Reload  [2] Restart Gunicorn (Current ID)  [3] Restart ALL")
        c = input("\nWahl: ")
        if c == "1":
            subprocess.run(["sudo", "nginx", "-t"])
            subprocess.run(["sudo", "systemctl", "reload", "nginx"])
        elif c == "2":
            svc = f"gunicorn_{self.cur_id}_{self.cur_env.lower()}"
            subprocess.run(["sudo", "systemctl", "restart", svc])
        elif c == "3":
            subprocess.run(["sudo", "systemctl", "restart", "gunicorn_*"])

    def main_menu(self):
        self.select_setup()
        while True:
            self.header()
            if self.cur_env == "DEV": 
                print(f" [1] ⚡ START ENTWICKLUNG (runserver 8010)")
            
            print("\n --- WARTUNG / SYSTEM ---")
            print(" [2] Migrations & Migrate       [3] Collectstatic")
            print(" [4] Berechtigungen (www-data)  [5] Service neustarten (Nginx/Gunicorn)")
            
            if self.cur_env != "PROD": 
                print(f" [d] 🚚 DEPLOY: {self.cur_env} -> {'TEST' if self.cur_env=='DEV' else 'PROD'}")

            print("\n --- BACKUP ---")
            print(" [6] DB Backup (db_manager)     [7] File Backup (Light)")
            print(" [8] Full Backup (inkl. Media)  [9] System-Config Backup")
            
            print("\n [s] Setup / Umgebung ändern    [q] Beenden")

            choice = input("\nAktion: ").lower()
            if choice == 'q': break
            elif choice == 's': self.select_setup()
            elif choice == '1' and self.cur_env == "DEV": 
                self.run_django(["runserver", "0.0.0.0:8010"])
            elif choice == '2': 
                self.run_django(["makemigrations"])
                self.run_django(["migrate"])
            elif choice == '3': 
                self.run_django(["collectstatic", "--noinput"])
            elif choice == '4': 
                subprocess.run(["sudo", "bash", f"{self.envs['1'][1]}/10-Manage-Scripte/server2-berechtigungen.sh"])
            elif choice == '5': 
                self.manage_services()
            elif choice == 'd': 
                self.do_deploy()
            elif choice == '6': 
                subprocess.run(["bash", f"{self.envs['1'][1]}/10-Manage-Scripte/db_manager.sh"])
            elif choice == '7': 
                self.do_backup(full=False)
            elif choice == '8': 
                self.do_backup(full=True)
            elif choice == '9':
                # Backup der gemounteten Config-Ordner
                ts = datetime.now().strftime("%Y%m%d")
                subprocess.run(["tar", "-czf", f"{self.backup_dir}/SYS_CONFIGS_{ts}.tar.gz", "/home/coder/95-nginx-config", "/home/coder/96-systemd-configs"])
                print("✅ System-Configs gesichert.")
            
            input("\nFertig. Weiter mit Enter...")

if __name__ == "__main__":
    try:
        HuennisMaster().main_menu()
    except KeyboardInterrupt:
        print("\n\nCiao!")
        sys.exit()