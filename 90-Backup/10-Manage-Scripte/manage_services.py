#!/usr/bin/env python3
import os
import subprocess
import sys

def clear():
    os.system('clear')

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Befehl erfolgreich: {cmd}")
    except subprocess.CalledProcessError:
        print(f"❌ Fehler bei: {cmd}")

def menu():
    while True:
        clear()
        print("="*50)
        print("   ⚙️  SERVER-SERVICE MANAGER (GUNICORN & NGINX)")
        print("="*50)
        print(" [1] ENTWICKLUNG (DEV)  - Neustart")
        print(" [2] TEST-UMGEBUNG      - Neustart")
        print(" [3] PRODUKTION (PROD)  - Neustart")
        print("-" * 50)
        print(" [4] NGINX              - Konfig prüfen & Reload")
        print(" [5] ALLE GUNICORNS     - Massen-Neustart")
        print("-" * 50)
        print(" [q] Beenden")
        
        choice = input("\nWahl: ").strip().lower()
        
        if choice == 'q':
            break
            
        if choice == '1': # DEV
            print("Restarting DEV Services...")
            run_cmd("sudo systemctl restart gunicorn_dev_*.socket gunicorn_dev_*.service")
        
        elif choice == '2': # TEST
            print("Restarting TEST Services...")
            run_cmd("sudo systemctl restart gunicorn_test_*.socket gunicorn_test_*.service")
            
        elif choice == '3': # PROD
            print("Restarting PROD Services...")
            run_cmd("sudo systemctl restart gunicorn_blick.service gunicorn_netzsprung.service gunicorn_office.service")
            
        elif choice == '4':
            print("Nginx Check...")
            run_cmd("sudo nginx -t && sudo systemctl reload nginx")
            
        elif choice == '5':
            print("Full Restart...")
            run_cmd("sudo systemctl restart 'gunicorn_*'")
            
        input("\nDrücke Enter zum Fortfahren...")

if __name__ == "__main__":
    menu()