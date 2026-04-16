#!/bin/bash

# --- KONFIGURATION ---
BACKUP_DIR="$HOME/dev/90-Backup"
DB_NAME="test_db_officecentral365"
VENV_PATH="/var/www/test-huennis-apps/venv-3.14"
MANAGE_PY="/var/www/test-huennis-apps/manage.py"

echo "==============================================="
echo "   DB Import Tool: Dev -> Test"
echo "==============================================="

# 1. SQL Dateien auflisten
cd "$BACKUP_DIR" || { echo "Backup Ordner nicht gefunden!"; exit 1; }
files=(*.sql)

if [ ${#files[@]} -eq 0 ]; then
    echo "Keine .sql Dateien in $BACKUP_DIR gefunden."
    exit 1
fi

echo "Verfügbare Backups:"
for i in "${!files[@]}"; do
    echo "  [$i] ${files[$i]}"
done

# 2. Auswahl treffen
read -p "Welches Backup soll importiert werden? (Nummer): " selection
selected_file="${files[$selection]}"

if [ -z "$selected_file" ]; then
    echo "Ungültige Auswahl."
    exit 1
fi

echo "-----------------------------------------------"
echo "Starte Import von: $selected_file"
echo "Ziel-Datenbank: $DB_NAME"
echo "-----------------------------------------------"

# 3. Schema Reset (Wichtig für sauberen Import)
echo "[1/3] Setze Schema 'public' zurück..."
sudo -u postgres psql -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public;"

# 4. Import durchführen
echo "[2/3] Importiere Daten..."
sudo -u postgres psql "$DB_NAME" < "$BACKUP_DIR/$selected_file"

# 5. Django Nacharbeiten
echo "[3/3] Django Nacharbeiten (Domain-Fix)..."
SITE_IDENTITY=office $VENV_PATH/bin/python $MANAGE_PY shell <<EOF
from django.contrib.sites.models import Site
try:
    s = Site.objects.first()
    s.domain = 'test.officecentral365.netzsprung.de'
    s.name = 'Test System'
    s.save()
    print("Domain wurde auf TEST angepasst.")
except:
    print("Sites Framework nicht aktiv oder Fehler.")
EOF

echo "-----------------------------------------------"
echo "FERTIG! Du kannst dich jetzt mit deinen Dev-Daten einloggen."

SITE_IDENTITY=office /var/www/test-huennis-apps/venv-3.14/bin/python manage.py makemigrations
SITE_IDENTITY=office /var/www/test-huennis-apps/venv-3.14/bin/python manage.py migrate
SITE_IDENTITY=office /var/www/test-huennis-apps/venv-3.14/bin/python manage.py collectstatic --noinput

sudo systemctl restart gunicorn_office_test.service
sudo systemctl status gunicorn_office_test.service
