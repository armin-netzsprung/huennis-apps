import os

# Definition der Umgebungen (Pfade wie besprochen)
ENV_CONFIGS = {
    "PROD": {"root": "/var/www/huennis-apps", "suffix": "", "sub": ""},
    "TEST": {"root": "/var/www/test-huennis-apps", "suffix": "_test", "sub": "test."},
    "DEV":  {"root": "/home/netzsprung-admin/dev/dev-huennis-apps", "suffix": "_dev", "sub": "dev."}
}

# Deine Original-Dateinamen (aus dem Upload)
GUNICORN_BASE = ["gunicorn_blick", "gunicorn_netzsprung", "gunicorn_office"]
NGINX_BASE = ["netzsprung.de.conf", "officecentral365.netzsprung.de.conf", "blick-dahinter.de.conf"]

def generate():
    # Wir erstellen Unterordner, damit du die Dateien vor dem Kopieren sichten kannst
    for env, cfg in ENV_CONFIGS.items():
        out_dir = f"./output_{env.lower()}"
        os.makedirs(out_dir, exist_ok=True)
        
        # --- GUNICORN SERVICES & SOCKETS ---
        for base in GUNICORN_BASE:
            for ext in [".service", ".socket"]:
                src = f"{base}{ext}"
                if not os.path.exists(src): continue
                
                with open(src, 'r') as f: content = f.read()
                
                # 1. Pfad-Korrektur (Blog -> Apps)
                new = content.replace("/var/www/huennis-blog", cfg["root"])
                new = new.replace("huennis-blog", "huennis-apps")
                
                # 2. Umgebungs-Suffix nur wenn nicht PROD
                if env != "PROD":
                    # Ändert Service-Namen und Socket-Dateinamen im Inhalt
                    new = new.replace(f"{base}", f"{base}{cfg['suffix']}")
                    new = new.replace(f"/run/{base}.sock", f"/run/{base}{cfg['suffix']}.sock")
                
                # Speichern mit passendem Dateinamen (z.B. gunicorn_blick_test.service)
                out_file = f"{base}{cfg['suffix']}{ext}"
                with open(os.path.join(out_dir, out_file), 'w') as f: f.write(new)

        # --- NGINX CONFIGS ---
        for src in NGINX_BASE:
            if not os.path.exists(src): continue
            
            with open(src, 'r') as f: content = f.read()
            
            # 1. Pfad-Korrektur
            new = content.replace("/var/www/huennis-blog", cfg["root"])
            new = new.replace("huennis-blog", "huennis-apps")
            
            # 2. Subdomain & Socket Anpassung für TEST/DEV
            if env != "PROD":
                # Fügt test. oder dev. vor den Servernamen
                new = new.replace("server_name ", f"server_name {cfg['sub']}")
                for base in GUNICORN_BASE:
                    new = new.replace(f"/run/{base}.sock", f"/run/{base}{cfg['suffix']}.sock")
            
            # Dateiname bleibt gleich oder bekommt Suffix für TEST/DEV
            out_file = f"{env.lower()}_{src}" if env != "PROD" else src
            with open(os.path.join(out_dir, out_file), 'w') as f: f.write(new)
            
    print("✅ Generierung abgeschlossen. Ordner: output_prod, output_test, output_dev")

if __name__ == "__main__":
    generate()
