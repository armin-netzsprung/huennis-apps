#!/bin/bash

# ==============================================================================
# 1. ZENTRALE KONFIGURATION
# ==============================================================================
TEMP_STAGE="/tmp/backup_stage"
REMOTE_TARGET="u466131@u466131.your-storagebox.de:backup-server2"
SSH_KEY="/home/netzsprung-admin/.ssh/hetzner-storage-box"

PYTHON_APPS_DIR="/home/netzsprung-admin/dev"
WEB_ASSETS_DIR="/var/www"
MAILCOW_DIR="/opt/mailcow-dockerized"
SEAFILE_DIR="/opt/seafile-server"
VSCODE_DIR="/opt/vscode"   # NEU: VS-Code IDE Daten

PSQL_USER="postgres"

MAIL_TO="armin.huenniger@outlook.de"
MAIL_FROM="armin.huenniger@netzsprung.de"

DATE=$(date +%Y-%m-%d_%H-%M-%S)
LOGFILE="/var/log/backup_server2_${DATE}.log"
TS_START=$(date +%s)

# ==============================================================================
# 2. INTERAKTIVE AUSWAHL
# ==============================================================================
CHOICES=$(whiptail --title "Backup-Master Server 2 -> HETZNER" --checklist \
"Leertaste zum Auswählen, Enter zum Bestätigen:" 22 75 12 \
"DB_PSQL" "Postgres Voll-Sicherung (Django, Seafile)" ON \
"PY_APPS" "Python Code (Ohne lokale Backups)" ON \
"WEB_DATA" "Web-Assets, Media (/var/www)" ON \
"VSCODE" "VS-Code Settings & Extensions" ON \
"MAILCOW" "Mailcow Config & Postfächer" ON \
"SEAFILE" "Seafile Daten & Config" ON \
"SYSTEM" "Nginx, Systemd, Cron, Apt-Sources" ON \
"SSL" "SSL Zertifikate (/etc/letsencrypt)" ON \
"HOME" "Gesamte User-Home-Verzeichnisse" OFF 3>&1 1>&2 2>&3)

if [ $? -ne 0 ]; then echo "Abbruch."; exit 1; fi

# ==============================================================================
# 3. FUNKTIONEN
# ==============================================================================
log_msg() { echo -e "$(date +'%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOGFILE"; }

backup_dbs() {
    if [[ $CHOICES == *"DB_PSQL"* ]]; then
        log_msg "🐘 Postgres: Voll-Dump aller Datenbanken (Vermeidet Einzel-Dumps)..."
        # Sichert alle DBs, Rollen und Rechte in eine Datei
        sudo -u postgres pg_dumpall -c | gzip > "$TEMP_STAGE/db_psql_FULL_CLUSTER_${DATE}.sql.gz" || log_msg "❌ FEHLER bei Postgres"
    fi
}

backup_files() {
    if [[ $CHOICES == *"PY_APPS"* ]]; then
        log_msg "🐍 Sichere Python-Apps (Schließe lokale Master-Backups & venv aus)..."
        # WICHTIG: --exclude="90-Backup" verhindert, dass wir Backups im Backup speichern
        tar -czf "$TEMP_STAGE/app_logic_${DATE}.tar.gz" \
            # --exclude="90-Backup" \
            --exclude="*/venv*" \
            --exclude="*/.venv*" \
            --exclude="*/__pycache__*" \
            "$PYTHON_APPS_DIR"
    fi

    if [[ $CHOICES == *"VSCODE"* ]]; then
        log_msg "💻 Sichere VS-Code Persistenz (Extensions & Config)..."
        tar -czf "$TEMP_STAGE/vscode_ide_data_${DATE}.tar.gz" "$VSCODE_DIR"
    fi

    if [[ $CHOICES == *"WEB_DATA"* ]]; then
        log_msg "🌐 Sichere Web-Daten..."
        tar -czf "$TEMP_STAGE/web_assets_${DATE}.tar.gz" --exclude="*/staticfiles/*" "$WEB_ASSETS_DIR"
    fi
}

backup_system() {
    if [[ $CHOICES == *"SYSTEM"* ]]; then
        log_msg "⚙️ Sichere System-Struktur (Nginx, Systemd, Cron)..."
        tar -czf "$TEMP_STAGE/sys_configs_${DATE}.tar.gz" \
            /etc/nginx \
            /etc/systemd/system \
            /etc/crontab \
            /etc/msmtprc \
            /home/netzsprung-admin/dev/server-config \
            2>/dev/null
        
        dpkg --get-selections > "$TEMP_STAGE/installed_packages_${DATE}.txt"
    fi
    
    [[ $CHOICES == *"SSL"* ]] && tar -czf "$TEMP_STAGE/sys_ssl_letsencrypt_${DATE}.tar.gz" /etc/letsencrypt 2>/dev/null
}

backup_docker_apps() {
    if [[ $CHOICES == *"MAILCOW"* ]]; then
        log_msg "📧 Mailcow: Nutze internes Backup-Script für Konsistenz..."
        export MAILCOW_BACKUP_LOCATION="$TEMP_STAGE/mailcow_tmp"
        mkdir -p "$MAILCOW_BACKUP_LOCATION"
        cd "$MAILCOW_DIR" && sudo ./helper-scripts/backup_and_restore.sh backup all > /dev/null
        tar -czf "$TEMP_STAGE/mailcow_full_backup_${DATE}.tar.gz" "$MAILCOW_BACKUP_LOCATION"
        rm -rf "$MAILCOW_BACKUP_LOCATION"
    fi

    if [[ $CHOICES == *"SEAFILE"* ]]; then
        log_msg "🌊 Seafile: Sichere Container-Verzeichnisse..."
        cd "$SEAFILE_DIR" && sudo docker compose pause
        tar -czf "$TEMP_STAGE/seafile_server_data_${DATE}.tar.gz" "$SEAFILE_DIR"
        sudo docker compose unpause
    fi
}

# ==============================================================================
# 4. AUSFÜHRUNG & TRANSFER
# ==============================================================================
mkdir -p "$TEMP_STAGE"

backup_dbs
backup_files
backup_system
backup_docker_apps

log_msg "🚀 Übertragung via rsync zur Hetzner Storage Box..."
rsync -avz -e "ssh -i $SSH_KEY -p 23" "$TEMP_STAGE/" "$REMOTE_TARGET/"

# Aufräumen
rm -rf "$TEMP_STAGE"

# ==============================================================================
# 5. BERICHT
# ==============================================================================
DURATION=$(( $(date +%s) - TS_START ))
log_msg "✅ Backup abgeschlossen. Dauer: $((DURATION/60)) Min."

{
    echo "Subject: Server2 Hetzner-Backup $DATE"
    echo -e "Hetzner-Backup erfolgreich.\nLog:\n"
    tail -n 20 "$LOGFILE"
} | msmtp -t

exit 0
