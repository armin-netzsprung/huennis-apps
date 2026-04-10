#!/usr/bin/env python3
import os
import subprocess
import sys

# Konfiguration der Projekte
# Name der Anzeige -> Pfad zum Shell-Skript
PROJECTS = {
    "1": ("Huennis Blog (Blick & Netzsprung & OfficeCentral365)", "deploy-huennis-blog.sh"),
    # "2": ("Anderes Projekt", "deploy-other.sh"), # Platzhalter für später
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear_screen()
        print("\033[94m========================================\033[0m")
        print("      🚀 MASTER DEPLOYMENT CENTER")
        print("\033[94m========================================\033[0m")
        
        for key, (name, _) in PROJECTS.items():
            print(f"{key}) {name}")
        
        print("q) Beenden")
        print("----------------------------------------")
        
        choice = input("Wähle ein Projekt zum Deployen: ").strip().lower()

        if choice == 'q':
            print("Abgebrochen.")
            sys.exit(0)

        if choice in PROJECTS:
            name, script_name = PROJECTS[choice]
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            
            if os.path.exists(script_path):
                print(f"\n\033[92mStarte Deployment für: {name}...\033[0m\n")
                try:
                    # Führt das Shell-Skript aus und leitet alle Ausgaben weiter
                    subprocess.run(["bash", script_path], check=True)
                    input("\n\033[92m✅ Fertig! Drücke Enter für das Menü...\033[0m")
                except subprocess.CalledProcessError:
                    input("\n\033[91m❌ Fehler beim Deployment. Drücke Enter...\033[0m")
            else:
                print(f"\n\033[91mFehler: Skript {script_name} nicht gefunden!\033[0m")
                input()
        else:
            print("\n\033[91mUngültige Auswahl.\033[0m")
            input()

if __name__ == "__main__":
    main()

