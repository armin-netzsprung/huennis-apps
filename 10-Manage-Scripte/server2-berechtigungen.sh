#!/bin/bash

# Definition der Pfade
APPS_ROOT="/home/coder"
ENVIRONMENTS=("10-dev-huennis-apps" "20-test-huennis-apps" "30-prod-huennis-apps")
OWNER="coder"
GROUP="www-data"

echo "-------------------------------------------------------"
echo " 🛡️  Setze Berechtigungen für Hünnis-Apps (Dev, Test, Prod)"
echo "-------------------------------------------------------"

for ENV in "${ENVIRONMENTS[@]}"; do
    TARGET="$APPS_ROOT/$ENV"
    
    if [ -d "$TARGET" ]; then
        echo "Processing: $TARGET"
        
        # 1. Besitzer und Gruppe setzen
        sudo chown -R $OWNER:$GROUP "$TARGET"
        
        # 2. Verzeichnisse: 775 (User & Gruppe dürfen rein und schreiben)
        sudo find "$TARGET" -type d -exec chmod 775 {} +
        
        # 3. Dateien: 664 (Lesen/Schreiben für User & Gruppe)
        sudo find "$TARGET" -type f -exec chmod 664 {} +
        
        # 4. Sticky Bit für Gruppe (Neue Dateien erben www-data)
        sudo find "$TARGET" -type d -exec chmod g+s {} +
        
        # 5. WICHTIG: Ausführbare Dateien (Venvs und Scripte)
        # Wir suchen alle venv-Ordner und machen deren bin-Inhalt ausführbar
        if [ -d "$TARGET/venv-3.14" ]; then
            sudo chmod -R +x "$TARGET/venv-3.14/bin/"
        fi
        
        # Auch deine Management-Scripte ausführbar machen
        if [ -d "$TARGET/10-Manage-Scripte" ]; then
            sudo chmod +x "$TARGET/10-Manage-Scripte/"*.sh
            sudo chmod +x "$TARGET/10-Manage-Scripte/"*.py
        fi
        
        echo "✅ $ENV fertig."
    else
        echo "⚠️  $TARGET nicht gefunden, überspringe."
    fi
done

echo "-------------------------------------------------------"
echo " 🎉 Alle Berechtigungen wurden glattgezogen!"
