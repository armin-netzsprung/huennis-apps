#!/bin/bash
set -e

# --- KONFIGURATION ---
REMOTE_USER="netzsprung-admin"
REMOTE_HOST="server2.netzsprung.de" 
REMOTE_TARGET="/var/www/huennis-blog"

# 1. VENV-ERKENNUNG (LOKAL)
if [ -n "$VIRTUAL_ENV" ]; then
    VENV_NAME=$(basename "$VIRTUAL_ENV")
else
    VENV_NAME=$(ls -d venv-* 2>/dev/null | sort -V | tail -n 1)
fi

echo "🚀 Starte Deployment..."
echo "📍 Ziel-VENV auf Server: $VENV_NAME"

# Pfad-Logik
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 2. SAUBERE REQUIREMENTS
echo "--- 📦 Erstelle saubere requirements.txt ---"
pip freeze | grep -vE "(cloud-init|ufw|ubuntu|systemd|command-not-found|language-selector|launchpad|distro|apt|dbus|Brlapi|bcc|cupshelpers|python-apt|defer|netifaces|httplib2|pycups|libvirt|virt-manager|reportlab|pexpect|ptyprocess|gnome|snack|gpg|cryptography|pycparser|louis|brlapi|macaroonbakery|pymacaroons|secretstorage|jeepney|keyring)" > requirements.txt

# 3. TRANSFER
# Hinweis: Wir lassen die 'tailwindcss' binary und 'output.css' im Ausschluss, 
# da der Server diese durch das Script selbst baut (sauberer Workflow).
rsync -avz --delete \
    --exclude="venv-*" \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='*.sqlite3' \
    --exclude='.env' \
    --exclude='tailwindcss' \
    --exclude='static/css/output.css' \
    --exclude='media/mail_storage' \
    ./ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_TARGET"

# 4. REMOTE-SETUP
ssh -t "$REMOTE_USER@$REMOTE_HOST" << EOF
    cd "$REMOTE_TARGET"

    # VENV Check/Erstellung
    if [ ! -d "$VENV_NAME" ]; then
        PYTHON_VER=\$(echo "$VENV_NAME" | cut -d'-' -f2)
        python\$PYTHON_VER -m venv "$VENV_NAME"
    fi

    echo "--- 🛠️ Erzwungene Installation im VENV ---"
    ./$VENV_NAME/bin/pip install --upgrade pip
    ./$VENV_NAME/bin/pip install -r requirements.txt || echo "Einige Pakete übersprungen..."

    echo "--- 🔧 Installiere fehlende Core-Apps manuell ---"
    ./$VENV_NAME/bin/pip install django gunicorn pillow whitenoise django-tinymce django-resized django-cleanup

    # --- 🎨 TAILWIND BUILD SCHRITT ---
    echo "--- 🖌️ Tailwind CSS Build ---"
    if [ -f "./10-Manage-Scripte/setup_tailwind.sh" ]; then
        bash ./10-Manage-Scripte/setup_tailwind.sh
    else
        echo "⚠️ Warnung: setup_tailwind.sh nicht gefunden!"
    fi

    echo "--- 🗄️ Migrationen & Statics ---"
    
    # Jetzt collectstatic ausführen (nimmt die neue output.css mit auf)
    ./$VENV_NAME/bin/python manage.py collectstatic --noinput

    # Migrationen für jede Identität
    echo "Updating Database: OfficeCentral365..."
    SITE_IDENTITY=office ./$VENV_NAME/bin/python manage.py migrate --noinput
    
    echo "Updating Database: Netzsprung..."
    SITE_IDENTITY=netzsprung ./$VENV_NAME/bin/python manage.py migrate --noinput
    
    echo "Updating Database: Blick..."
    SITE_IDENTITY=blick ./$VENV_NAME/bin/python manage.py migrate --noinput

    echo "--- 🔧 Service-Restart ---"
    sudo systemctl restart gunicorn_blick.service gunicorn_netzsprung.service gunicorn_office
    sudo nginx -t && sudo systemctl restart nginx
EOF

echo "✨ Fertig!"
