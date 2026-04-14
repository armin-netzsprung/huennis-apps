#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime

class HuennisMaster:
    def __init__(self):
        # Pfade INNERHALB des Containers
        self.envs = {
            "1": ("DEV", "/home/coder/10-dev-huennis-apps"),
            "2": ("TEST", "/home/coder/20-test-huennis-apps"),
            "3": ("PROD", "/home/coder/30-prod-huennis-apps")
        }
        
        # ECHTE PFADE auf Server 2 (Host-Sicht für SSH)
        self.host_paths = {
            "DEV": "/home/netzsprung-admin/dev/dev-huennis-apps",
            "TEST": "/var/www/test-huennis-apps",
            "PROD": "/var/www/huennis-apps"
        }

        self.identities = {"1": "office", "2": "blick", "3": "netzsprung"}
        self.backup_dir = "/home/coder/90-Backup"
        
        self.db_configs = {
            "office": {"db": "db_officecentral365", "user": "db_office_admin", "pw": "ArmLeicht48#"},
            "netzsprung": {"db": "netzsprung_db", "user": "db_netzsprung", "pw": "ArmLeicht48#"},
            "blick": {"db": "blick_dahinter_db", "user": "db_blickdahinter", "pw": "ArmLeicht48#"}
        }
        
        self.cur_env = "DEV"
        self.cur_path = self.envs["1"][1]
        self.cur_id = "office"
        self.cur_py = "3.14"

    def cls(self): os.system('clear')

    def header(self):
        self.cls()
        print("="*75)
        print(f" 🚀 MASTER-ADMIN | ENV: {self.cur_env} | ID: {self.cur_id.upper()}")
        print(f" CONTAINER: {self.cur_path}")
        print("="*75)

    def select_setup(self):
        while True:
            self.cls()
            print("="*75)
            print(" 🚀 HÜNNIS MASTER-CONTROL | START-MENÜ")
            print("="*75)
            print("\n WÄHLE UMGEBUNG:")
            print(" [1] DEV (10-...)  [2] TEST (20-...)  [3] PROD (30-...)")
            print("\n GLOBAL:")
            print(" [a] 🌀 TOTAL AUTO-BACKUP (Alle Umgebungen & Datenbanken)")
            print(" [q] Beenden")
            
            ev = input("\nWahl [1]: ").lower() or "1"
            if ev == 'q': sys.exit()
            if ev == 'a': 
                self.run_total_backup()
                continue
            
            if ev in self.envs:
                self.cur_env, self.cur_path = self.envs[ev]
                print("\nWÄHLE IDENTITY: [1] office  [2] blick  [3] netzsprung")
                id_choice = input("\nWahl [1]: ") or "1"
                self.cur_id = self.identities.get(id_choice, "office")
                break

    def run_ssh_host_cmd(self, cmd, use_sudo=False):
        ssh_key = "/home/coder/.ssh/server2_netzsprung-admin"
        host_user = "netzsprung-admin"
        host_ip = "172.17.0.1"
        full_cmd = f"sudo {cmd}" if use_sudo else cmd
        ssh_cmd = ["ssh", "-i", ssh_key, "-o", "StrictHostKeyChecking=no", f"{host_user}@{host_ip}", full_cmd]
        try:
            subprocess.run(ssh_cmd, check=True)
            return True
        except Exception as e:
            print(f"  ❌ SSH-Fehler: {e}")
            return False

    def run_django(self, args):
        if self.cur_env == "DEV":
            venv_py = f"{self.cur_path}/venv-{self.cur_py}/bin/python"
            env_vars = os.environ.copy()
            env_vars["SITE_IDENTITY"] = self.cur_id
            try:
                subprocess.run([venv_py, "manage.py"] + args, cwd=self.cur_path, env=env_vars, check=True)
            except Exception as e: print(f"\n❌ Django-Lokal-Fehler: {e}")
        else:
            h_path = self.host_paths.get(self.cur_env)
            h_venv_py = f"{h_path}/venv-3.14/bin/python"
            cmd_str = f"cd {h_path} && SITE_IDENTITY={self.cur_id} {h_venv_py} manage.py {' '.join(args)}"
            print(f"  🌐 Sende Django-Befehl an Host-Pfad: {h_path}...")
            self.run_ssh_host_cmd(cmd_str, use_sudo=False)

    def do_db_backup(self):
        conf = self.db_configs.get(self.cur_id)
        db_name = conf["db"]
        if self.cur_env == "DEV": db_name = f"dev_{db_name}"
        elif self.cur_env == "TEST": db_name = f"test_{db_name}"
        
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        target = f"{self.backup_dir}/DB_{db_name}_{ts}.sql"
        print(f"  ⤷ DB-Backup: {db_name}...")
        env_vars = os.environ.copy()
        env_vars["PGPASSWORD"] = conf["pw"]
        try:
            with open(target, "w") as f:
                subprocess.run(["pg_dump", "-h", "172.17.0.1", "-U", conf["user"], db_name], 
                               stdout=f, env=env_vars, check=True, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"  ❌ DB-Fehler ({db_name}): {e}")
            return False

    def do_file_backup(self, full=False):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        suffix = "FULL" if full else "LIGHT"
        target = f"{self.backup_dir}/FILES_{self.cur_env}_{self.cur_id}_{suffix}_{ts}.tar.gz"
        exclude = ["--exclude=media", "--exclude=venv*", "--exclude=staticfiles", "--exclude=.git"] if not full else []
        print(f"  ⤷ File-Backup ({suffix}): {self.cur_id}...")
        try:
            subprocess.run(["tar"] + exclude + ["-czf", target, "-C", "/home/coder", os.path.basename(self.cur_path)], 
                           check=True, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"  ❌ File-Fehler: {e}")
            return False

    def do_sys_config_backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        target = f"{self.backup_dir}/SYS_CONFIGS_{ts}.tar.gz"
        print(f"\n⚙️  Sichere System-Configs (Nginx, Systemd & VS-Code)...")
        try:
            # Hier haben wir jetzt 97-vscode-data mit in die Liste aufgenommen
            subprocess.run(["tar", "-czf", target, "-C", "/home/coder", 
                            "95-nginx-config", 
                            "96-systemd-configs", 
                            "97-vscode-data"], check=True)
            print(f"✅ System-Configs & VS-Code Einstellungen gesichert.")
        except Exception as e: 
            print(f"❌ System-Backup-Fehler: {e}")

    def run_total_backup(self):
        self.cls()
        print("="*75)
        print(" 🌀 START TOTAL AUTO-BACKUP (Alle Umgebungen & Identitäten)")
        print("="*75)
        start_time = datetime.now()
        for e_key, (e_name, e_path) in self.envs.items():
            for i_name in self.identities.values():
                self.cur_env, self.cur_path, self.cur_id = e_name, e_path, i_name
                print(f"\nProcessing: [{self.cur_env}] Identity: [{self.cur_id.upper()}]")
                self.do_db_backup()
                self.do_file_backup(full=False)
        self.do_sys_config_backup()
        print(f"\n✅ TOTAL BACKUP FERTIG! Dauer: {(datetime.now()-start_time).seconds}s")
        input("\nWeiter mit Enter...")

    def do_deploy(self):
        if self.cur_env == "PROD": return
        target_env = "TEST" if self.cur_env == "DEV" else "PROD"
        target_path = self.envs["2"][1] if target_env == "TEST" else self.envs["3"][1]
        
        if self.cur_env == "DEV":
            print(f"  📦 Aktualisiere requirements.txt in DEV...")
            venv_pip = f"{self.cur_path}/venv-{self.cur_py}/bin/pip"
            try:
                with open(f"{self.cur_path}/requirements.txt", "w") as f:
                    subprocess.run([venv_pip, "freeze"], stdout=f, check=True)
            except: pass

        print(f"\n⚠️  DEPLOY FILES: {self.cur_env} -> {target_env}")
        if input("Sicher? (y/n): ").lower() != 'y': return

        excludes = ["--exclude=venv*", "--exclude=__pycache__", "--exclude=staticfiles", 
                    "--exclude=media", "--exclude=.git", "--exclude=.idea", "--exclude=.vscode"]
        subprocess.run(["rsync", "-av", "--delete"] + excludes + [f"{self.cur_path}/", f"{target_path}/"], check=True)
        subprocess.run(["sudo", "bash", f"{self.envs['1'][1]}/10-Manage-Scripte/server2-berechtigungen.sh"], check=True)
        print(f"✅ Files kopiert.")

    def do_full_deploy_flow(self):
        self.header()
        print(f"🚀 STARTE FULL DEPLOY FLOW: {self.cur_env} -> TARGET")
        self.do_deploy()
        target_env_key = "2" if self.cur_env == "DEV" else "3"
        target_env_name = self.envs[target_env_key][0]
        h_path = self.host_paths.get(target_env_name)
        
        old_env, old_path = self.cur_env, self.cur_path
        self.cur_env, self.cur_path = target_env_name, self.envs[target_env_key][1]

        print(f"\n--- SCHRITT 2: INSTALL REQUIREMENTS (SSH) ---")
        h_pip = f"{h_path}/venv-3.14/bin/pip"
        self.run_ssh_host_cmd(f"{h_pip} install -r {h_path}/requirements.txt")
        
        print(f"\n--- SCHRITT 3: MIGRATIONS (SSH) ---")
        self.run_django(["makemigrations"])
        self.run_django(["migrate"])
        
        print(f"\n--- SCHRITT 4: COLLECTSTATIC (SSH) ---")
        self.run_django(["collectstatic", "--noinput"])
        
        print(f"\n--- SCHRITT 5: SERVICE NEUSTART (HOST) ---")
        svc_name = f"gunicorn_{self.cur_id}_{self.cur_env.lower()}"
        self.run_ssh_host_cmd(f"systemctl restart {svc_name}", use_sudo=True)

        self.cur_env, self.cur_path = old_env, old_path
        print(f"\n✅ FULL DEPLOY FLOW ERFOLGREICH!")

    def manage_services(self):
        print("\n [1] Nginx Reload (Host)  [2] Gunicorn Restart  [3] All Gunicorn Restart")
        c = input("\nWahl: ")
        if c == "1": self.run_ssh_host_cmd("nginx -t && systemctl reload nginx", use_sudo=True)
        elif c == "2": self.run_ssh_host_cmd(f"systemctl restart gunicorn_{self.cur_id}_{self.cur_env.lower()}", use_sudo=True)
        elif c == "3": self.run_ssh_host_cmd("systemctl restart gunicorn_*", use_sudo=True)

    def main_menu(self):
        while True:
            self.select_setup()
            while True:
                self.header()
                if self.cur_env == "DEV": print(f" [1] ⚡ START ENTWICKLUNG (runserver 8010)")
                print("\n --- WARTUNG / SYSTEM ---")
                print(" [2] Migrations & Migrate       [3] Collectstatic")
                print(" [4] Berechtigungen (www-data)  [5] Service neustarten (Nginx/Gunicorn)")
                if self.cur_env != "PROD": 
                    print(f" [d] 🚚 DEPLOY: {self.cur_env} -> NEXT (Files)")
                    print(f" [a] 🚀 FULL DEPLOY FLOW (All-in-One)")
                print("\n --- BACKUP ---")
                print(" [6] DB Backup (Aktuell)        [7] File Backup (Light)")
                print("\n [s] Setup ändern               [q] Beenden")

                choice = input("\nAktion: ").lower()
                if choice == 'q': sys.exit()
                elif choice == 's': break
                elif choice == '1' and self.cur_env == "DEV": self.run_django(["runserver", "0.0.0.0:8010"])
                elif choice == '2': self.run_django(["makemigrations"]); self.run_django(["migrate"])
                elif choice == '3': self.run_django(["collectstatic", "--noinput"])
                elif choice == '4': subprocess.run(["sudo", "bash", f"{self.envs['1'][1]}/10-Manage-Scripte/server2-berechtigungen.sh"])
                elif choice == '5': self.manage_services()
                elif choice == 'a' and self.cur_env != "PROD": self.do_full_deploy_flow()
                elif choice == 'd': self.do_deploy()
                elif choice == '6': self.do_db_backup()
                elif choice == '7': self.do_file_backup()
                input("\nWeiter mit Enter...")

if __name__ == "__main__":
    try: HuennisMaster().main_menu()
    except KeyboardInterrupt: sys.exit()
    