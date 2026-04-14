#!/bin/bash
TARGET=$1
echo "🔐 Setze Berechtigungen für $TARGET..."

chown -R netzsprung-admin:www-data "$TARGET"
chmod -R 775 "$TARGET"
find "$TARGET" -type d -exec chmod g+s {} +

cd "$TARGET"
VENV=$(ls -d venv-* | sort -V | tail -n 1)

# Build-Schritte für alle Identitäten
for ID in office netzsprung blick; do
    echo "⚙️  Build für $ID..."
    export SITE_IDENTITY=$ID
    ./$VENV/bin/python manage.py migrate --noinput
    ./$VENV/bin/python manage.py collectstatic --noinput
done

echo "🔄 Neustart Gunicorn..."
systemctl restart "gunicorn_*"