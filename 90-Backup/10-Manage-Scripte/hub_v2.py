import os, sys, subprocess

def clear(): os.system('clear')

def main_menu():
    while True:
        clear()
        print("="*60)
        print("   🚀 HÜNNIS-APPS MULTI-PROJECT MANAGEMENT (SERVER2)")
        print("="*60)
        print(" WÄHLE DAS PROJEKT:")
        print(" [1] Blick dahinter (blick)")
        print(" [2] Netzsprung (netzsprung)")
        print(" [3] Office (office)")
        print("-" * 60)
        print(" [q] Beenden")
        
        choice = input("\nProjekt wählen: ").lower()
        if choice == 'q': break
        
        identities = {"1": "blick", "2": "netzsprung", "3": "office"}
        if choice in identities:
            env_menu(identities[choice])

def env_menu(identity):
    while True:
        clear()
        print("="*60)
        print(f"   PROJEKT: {identity.upper()}")
        print("="*60)
        print(" [1] Entwicklung (DEV)  -> ~/dev/dev-huennis-apps")
        print(" [2] Test (TEST)         -> /var/www/test-huennis-apps")
        print(" [3] Produktion (PROD)   -> /var/www/huennis-apps")
        print("-" * 60)
        print(" [b] Zurück")
        
        choice = input("\nWähle die Umgebung: ").lower()
        if choice == 'b': break
        
        envs = {"1": "DEV", "2": "TEST", "3": "PROD"}
        if choice in envs:
            action_menu(identity, envs[choice])

def action_menu(identity, env):
    while True:
        clear()
        print(f"=== PROJEKT: {identity.upper()} | MODUS: {env} ===")
        print(f" [1] {env} starten (runserver/logs)")
        
        if env == "DEV":
            print(" [2] Deployment (DEV -> TEST oder DEV -> PROD)")
        elif env == "TEST":
            print(" [2] Deployment (TEST -> PROD)")
            
        print(" [3] Python-Admin (VENV/Versions-Management)")
        print(" [4] DB-Manager (Backup/Restore)")
        print(" [5] 📦 FULL BACKUP (Source + DB)")
        
        if env == "DEV":
            print(" [6] 🤖 GEMINI BACKUP (KI-Export inkl. SQL-Text)")
            print(" [7] 📜 LIVE-LOGS EINSEHEN (tail -f)")

        print("\n [b] Zurück | [q] Beenden")
        choice = input("\nAktion wählen: ").lower()
        
        if choice == 'b': break
        if choice == 'q': sys.exit()
        execute_task(choice, identity, env)

def execute_task(task, identity, env):
    script_path = os.path.dirname(os.path.abspath(__file__))
    # Pfade für Log-Abfrage definieren
    paths = {
        "DEV": "/home/netzsprung-admin/dev/dev-huennis-apps",
        "TEST": "/var/www/test-huennis-apps",
        "PROD": "/var/www/huennis-apps"
    }
    
    if task == "1":
        subprocess.run(["python3", f"{script_path}/run_app_v2.py", identity, env])
    elif task == "2":
        subprocess.run(["python3", f"{script_path}/deploy_manager_v2.py", identity, env])
    elif task == "3":
        subprocess.run(["python3", f"{script_path}/python_admin_v2.py", identity, env])
    elif task == "4":
        subprocess.run(["bash", f"{script_path}/db_manager_v2.sh", identity, env])
    elif task == "5":
        subprocess.run(["bash", f"{script_path}/full_backup.sh", identity])
    elif task == "6" and env == "DEV":
        subprocess.run(["python3", f"{script_path}/gemini_export_v2.py", identity])
    elif task == "7" and env == "DEV":
        log_file = f"{paths[env]}/logs/django_dev.log"
        if os.path.exists(log_file):
            subprocess.run(["tail", "-n", "100", "-f", log_file])
        else:
            print(f"❌ Log-Datei noch nicht erstellt: {log_file}")
    
    input("\nDrücke Enter...")

if __name__ == "__main__":
    main_menu()
    