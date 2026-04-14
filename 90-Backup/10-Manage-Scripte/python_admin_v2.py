import os, sys, subprocess

def clear(): os.system('clear')

def run():
    if len(sys.argv) < 3:
        print("❌ Fehler: Identity oder Env fehlt!")
        return

    identity = sys.argv[1].lower()
    env = sys.argv[2].upper()

    paths = {
        "DEV": "/home/netzsprung-admin/dev/dev-huennis-apps",
        "TEST": "/var/www/test-huennis-apps",
        "PROD": "/var/www/huennis-apps"
    }

    root = paths.get(env)
    if not root: return
    os.chdir(root)

    # VENV finden
    venv_dirs = [d for d in os.listdir('.') if d.startswith('venv-')]
    venv = sorted(venv_dirs, reverse=True)[0] if venv_dirs else "venv"
    pip_bin = f"{root}/{venv}/bin/pip"
    python_bin = f"{root}/{venv}/bin/python"

    while True:
        clear()
        print(f"=== 🐍 PYTHON ADMIN | {identity.upper()} | {env} ===")
        print(f"Aktiv: {venv}")
        print("-" * 45)
        print(" [1] pip install -r requirements.txt")
        print(" [2] pip install --upgrade pip")
        print(" [3] Paket installieren (manuell)")
        print(" [4] Installierte Pakete listen (pip freeze)")
        print(" [5] Django Check (inspectdb/check)")
        print("-" * 45)
        print(" [b] Zurück")

        choice = input("\nAktion wählen: ").lower()

        if choice == 'b': break
        
        print("\n--- Ausführung ---")
        if choice == '1':
            subprocess.run([pip_bin, "install", "-r", "requirements.txt"])
        elif choice == '2':
            subprocess.run([pip_bin, "install", "--upgrade", "pip"])
        elif choice == '3':
            pkg = input("Paketname: ")
            subprocess.run([pip_bin, "install", pkg])
        elif choice == '4':
            subprocess.run([pip_bin, "freeze"])
        elif choice == '5':
            subprocess.run([python_bin, "manage.py", "check"])
        
        input("\nDrücke Enter zum Fortfahren...")

if __name__ == "__main__":
    run()