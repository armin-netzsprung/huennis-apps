#!/usr/bin/env python3
import os
import sys
import subprocess
import signal

# --- PFAD-LOGIK ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def get_available_venvs():
    try:
        return sorted([d for d in os.listdir(PROJECT_ROOT) 
                       if os.path.isdir(os.path.join(PROJECT_ROOT, d)) 
                       and d.startswith("venv-")], reverse=True)
    except Exception as e:
        print(f"Fehler beim Suchen der VENVs: {e}")
        return []

def run_app():
    # os.system('clear')
    print("="*45)
    print(" 🚀 OFFICE & BLOG - LOKALER STARTER ")
    print("="*45)

    venvs = get_available_venvs()
    if not venvs:
        print(f"❌ Kein venv in {PROJECT_ROOT} gefunden!")
        return

    print("Verfügbare Umgebungen:")
    for i, v in enumerate(venvs, 1):
        print(f"  {i}) {v}")
    
    v_choice = input(f"Wahl (1-{len(venvs)}) [Standard: 1]: ").strip()
    selected_venv = venvs[int(v_choice)-1] if v_choice.isdigit() and int(v_choice) <= len(venvs) else venvs[0]
    
    python_bin = os.path.join(PROJECT_ROOT, selected_venv, "bin", "python")
    manage_py = os.path.join(PROJECT_ROOT, "manage.py")
    req_file = os.path.join(PROJECT_ROOT, "requirements.txt")
    tailwind_bin = os.path.join(PROJECT_ROOT, "tailwindcss")

    print("\nWelche Instanz starten?")
    print("  1) Blick-Dahinter (Port 8000)")
    print("  2) Netzsprung (Port 8001)")
    print("  3) Office Central 365 (Port 8002)")
    print("  q) Abbrechen")
    
    choice = input("\nAuswahl (1/2/3/q): ").strip().lower()

    if choice == '1':
        os.environ['SITE_IDENTITY'] = 'blick'
        port = "8000"
    elif choice == '2':
        os.environ['SITE_IDENTITY'] = 'netzsprung'
        port = "8001"
    elif choice == '3':
        os.environ['SITE_IDENTITY'] = 'office'
        port = "8002"
    else:
        return

    # 1. Check & Auto-Install Abhängigkeiten
    print(f"\n--- 🔍 Prüfe Abhängigkeiten in {selected_venv} ---")
    try:
        subprocess.run([python_bin, "-c", "import django"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"⚠️  Django fehlt. Installiere aus requirements.txt...")
        subprocess.run([python_bin, "-m", "pip", "install", "-r", req_file])

    # 2. AUTOMATISCHE MIGRATIONEN
    print(f"\n--- 🛠️  Synchronisiere Datenbank: {os.environ['SITE_IDENTITY'].upper()} ---")
    subprocess.run([python_bin, manage_py, "makemigrations"], cwd=PROJECT_ROOT)
    subprocess.run([python_bin, manage_py, "migrate"], cwd=PROJECT_ROOT)

    # 3. TAILWIND WATCH STARTEN (Hintergrundprozess)
    tailwind_proc = None
    if os.path.exists(tailwind_bin):
        print(f"\n--- 🎨 Starte Tailwind Watcher ---")
        # Wir starten Tailwind als Hintergrundprozess
        tailwind_proc = subprocess.Popen(
            [tailwind_bin, "-i", "./static/css/input.css", "-o", "./static/css/output.css", "--watch"],
            cwd=PROJECT_ROOT
        )
    else:
        print(f"\n⚠️  Tailwind-Binary nicht in {PROJECT_ROOT} gefunden. Watcher startet nicht.")

    # 4. Server starten
    print(f"\n--> Starte {os.environ['SITE_IDENTITY'].upper()} auf Port {port}...")
    
    try:
        subprocess.run([python_bin, manage_py, "runserver", port], cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print("\n🛑 Server wird beendet...")
    finally:
        # Falls Tailwind läuft, beenden wir es sauber mit dem Server zusammen
        if tailwind_proc:
            print("🎨 Beende Tailwind Watcher...")
            tailwind_proc.terminate()
            # Kurz warten, falls es nicht sofort schließt
            try:
                tailwind_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                tailwind_proc.kill()

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print("\n👋 Beendet durch Nutzer.")
    except Exception as e:
        print("\n" + "!"*60)
        print(" 🔥 KRITISCHER FEHLER BEIM STARTEN DER APP")
        print("!"*60)
        import traceback
        traceback.print_exc() # Das zeigt dir die Zeilennummer im Django-Code!
        print("!"*60)
        input("\nDrücke ENTER, um dieses Fenster zu schließen...")    