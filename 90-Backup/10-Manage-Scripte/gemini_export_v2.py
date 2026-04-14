import os, subprocess, datetime

def export_for_gemini():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    backup_dir = "/home/netzsprung-admin/dev/90-Backup/gemini_exports"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 1. DB Export als Text (für Code-Server)
    print("Backup der DBs für KI...")
    for db in ["dev_blick_dahinter_db", "dev_netzsprung_db", "dev_db_officecentral365"]:
        txt_file = f"{backup_dir}/{db}_{timestamp}.sql"
        subprocess.run(f"sudo -u postgres pg_dump {db} > {txt_file}", shell=True)
    
    # 2. Code exportieren (ohne Müll)
    target_zip = f"{backup_dir}/code_export_{timestamp}.zip"
    subprocess.run([
        "zip", "-r", target_zip, ".", 
        "-x", "*venv*", "*staticfiles*", "*media*", "*.git*", "*.pyc"
    ])
    print(f"✅ Export fertig in: {backup_dir}")

if __name__ == "__main__": export_for_gemini()
