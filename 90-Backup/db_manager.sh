#!/bin/bash
# BACKUP_DIR="./db_backups"
BACKUP_DIR="/home/armin-huenniger/dev/90-Backup/huennis-apps"
mkdir -p "$BACKUP_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================"
echo -e "   DATENBANK MANAGEMENT (BLICK/NETZ/OFFICE)"
echo -e "========================================${NC}"

select_file() {
    local pattern=$1
    local files=($(find "$BACKUP_DIR" -maxdepth 1 -name "${pattern}*.sql"))
    if [ ${#files[@]} -eq 0 ]; then return 1; fi
    echo -e "${YELLOW}Verfügbare Backups für $pattern:${NC}"
    for i in "${!files[@]}"; do echo "$((i+1))) ${files[$i]}"; done
    read -p "Wahl (1-${#files[@]}): " file_idx
    [[ "$file_idx" =~ ^[0-9]+$ ]] && SELECTED_FILE="${files[$((file_idx-1))]}" || return 1
}

do_backup() {
    local db=$1
    local file="$BACKUP_DIR/${db}_$(date +%Y-%m-%d_%H-%M).sql"
    echo -e "${BLUE}Sichere $db...${NC}"
    sudo -u postgres pg_dump "$db" > "$file"
    echo -e "${GREEN}Gespeichert in: $file${NC}"
}

do_restore() {
    local db=$1
    local user=$2
    local pattern=$3
    if ! select_file "$pattern"; then echo "Kein Backup gefunden."; return; fi
    read -p "Sicher? Alle Daten in $db werden überschrieben! (y/n): " confirm
    if [ "$confirm" == "y" ]; then
        sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$db' AND pid <> pg_backend_pid();"
        sudo -u postgres dropdb "$db"
        sudo -u postgres createdb -O "$user" "$db"
        sudo -u postgres psql "$db" < "$SELECTED_FILE"
        echo -e "${GREEN}Restore erfolgreich abgeschlossen!${NC}"
    fi
}

while true; do
    echo -e "\n1) Backup: Blick-Dahinter\n2) Backup: Netzsprung\n3) Backup: OfficeCentral365\n4) Backup: ALLE\n---"
    echo -e "5) Restore: Blick\n6) Restore: Netz\n7) Restore: Office\nq) Zurück"
    read -p "Auswahl: " c
    case $c in
        1) do_backup "blick_dahinter_db" ;;
        2) do_backup "netzsprung_db" ;;
        3) do_backup "db_officecentral365" ;;
        4) do_backup "blick_dahinter_db"; do_backup "netzsprung_db"; do_backup "db_officecentral365" ;;
        5) do_restore "blick_dahinter_db" "db_blickdahinter" "blick_dahinter_db" ;;
        6) do_restore "netzsprung_db" "db_netzsprung" "netzsprung_db" ;;
        7) do_restore "db_officecentral365" "db_office_admin" "db_officecentral365" ;;
        q) break ;;
    esac
done