#!/bin/bash

# Pfad zum neuen 3.14er Binary
PY_BASE="/home/coder/00-portable-py-3.14/bin/python3.14"
MASTER_SCRIPT="/home/coder/10-dev-huennis-apps/10-Manage-Scripte/master_admin.py"

# Optik & Info
echo -e "\033[0;34m======================================================"
echo -e "   🌐 HÜNNIS CLOUD ENVIRONMENT (SERVER 2)"
echo -e "   Active Python: 3.14 (Portable)"
echo -e "======================================================\033[0m"

# Ins Dev-Verzeichnis springen
cd /home/coder/10-dev-huennis-apps

# Master Admin starten
if [ -x "$PY_BASE" ]; then
    if [ -f "$MASTER_SCRIPT" ]; then
        # Wir starten das Master-Script direkt mit dem neuen Python
        $PY_BASE $MASTER_SCRIPT
    else
        echo -e "\033[0;31m[!] Master-Script nicht gefunden: $MASTER_SCRIPT\033[0m"
    fi
else
    echo -e "\033[0;31m[!] Python 3.14 nicht gefunden unter: $PY_BASE\033[0m"
    echo "Check: Ist der Mount in der docker-compose.yml aktiv?"
fi