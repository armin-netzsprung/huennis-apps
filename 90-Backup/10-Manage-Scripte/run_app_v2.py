import os, sys, subprocess

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
    
    # Log-Verzeichnis sicherstellen
    log_dir = os.path.join(root, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_path = os.path.join(log_dir, "django_dev.log")
    
    # --- VENV AUSWAHL ---
    venv_dirs = sorted([d for d in os.listdir('.') if d.startswith('venv-')], reverse=True)
    if not venv_dirs:
        print(f"❌ Kein venv- Ordner in {root} gefunden!")
        return
    
    # Automatische Wahl oder Abfrage
    if len(venv_dirs) > 1:
        print("\nMehrere VENVs gefunden. Welches soll genutzt werden?")
        for i, d in enumerate(venv_dirs):
            print(f" [{i}] {d}")
        v_choice = input("\nWahl [Standard 0]: ")
        v_idx = int(v_choice) if v_choice.isdigit() and int(v_choice) < len(venv_dirs) else 0
        selected_venv = venv_dirs[v_idx]
    else:
        selected_venv = venv_dirs[0]

    python_bin = f"{root}/{selected_venv}/bin/python"
    os.environ['SITE_IDENTITY'] = identity

    print(f"✅ Nutze: {selected_venv} ({identity.upper()})")

    if env == "DEV":
        # Port-Zuweisung pro Identität
        ports = {
            "office": "8000",
            "netzsprung": "8001",
            "blick": "8002"
        }
        port = ports.get(identity, "8000")
        
        print(f"🛠️  Migrationen für {identity.upper()}...")
        subprocess.run([python_bin, "manage.py", "makemigrations"])
        subprocess.run([python_bin, "manage.py", "migrate"])
        
        print(f"🚀 Starte Runserver für {identity.upper()} auf Port {port}...")
        
        # WICHTIG: Hier muss f"0.0.0.0:{port}" stehen!
        cmd = [python_bin, "manage.py", "runserver", f"0.0.0.0:{port}"]
        
        with open(log_file_path, "a") as f:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            # ... Rest deiner Logging-Logik (Zeilen lesen und ausgeben)

            proc = subprocess.Popen(
                [python_bin, "manage.py", "runserver", f"0.0.0.0:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            try:
                # Wir lesen die Ausgabe Zeile für Zeile
                for line in proc.stdout:
                    sys.stdout.write(line) # Ausgabe auf Terminal
                    f.write(line)          # Ausgabe in Datei
                    f.flush()              # Sofort speichern
            except KeyboardInterrupt:
                print("\n🛑 Server wird gestoppt...")
                proc.terminate()
    else:
        service_name = f"gunicorn_{identity}_{env.lower()}"
        subprocess.run(["sudo", "journalctl", "-u", f"{service_name}", "-f"])

if __name__ == "__main__":
    run()
