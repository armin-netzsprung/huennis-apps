import os, sys, subprocess

def deploy():
    source_env = sys.argv[1]
    paths = {"DEV": "/home/netzsprung-admin/dev/dev-huennis-apps", "TEST": "/var/www/test-huennis-apps", "PROD": "/var/www/huennis-apps"}
    
    print(f"\nQUELLE: {source_env}")
    if source_env == "DEV":
        print("1) DEV -> TEST\n2) DEV -> PROD")
    else:
        print("1) TEST -> PROD")
    
    ziel_wahl = input("Ziel: ")
    if source_env == "DEV":
        target = paths["TEST"] if ziel_wahl == "1" else paths["PROD"]
    else:
        target = paths["PROD"]

    source = paths[source_env]

    # 1. RSYNC LOKAL
    print(f"🚚 Kopiere Daten nach {target}...")
    subprocess.run([
        "rsync", "-av", "--delete",
        "--exclude", "venv*", "--exclude", "*.sql", "--exclude", "media/", "--exclude", ".git/",
        f"{source}/", f"{target}/"
    ])

    # 2. BERECHTIGUNGEN & DJANGO BUILDS
    # Hier rufen wir ein Shell-Skript auf, das sudo-Rechte nutzt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(["sudo", "bash", f"{script_dir}/finalize_deploy.sh", target])

if __name__ == "__main__": deploy()
