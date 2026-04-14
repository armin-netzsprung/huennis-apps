# Deinen User zur Gruppe www-data hinzufügen (falls noch nicht geschehen)
sudo usermod -a -G www-data netzsprung-admin

# Den Besitz wieder auf deinen User setzen, die Gruppe auf www-data
sudo chown -R netzsprung-admin:www-data /var/www/huennis-apps

# Rechte so setzen, dass User UND Gruppe schreiben dürfen
sudo find /var/www/huennis-apps -type d -exec chmod 775 {} +
sudo find /var/www/huennis-apps -type f -exec chmod 664 {} +

# Das "Sticky Bit" für Verzeichnisse setzen (neue Dateien erben die Gruppe)
sudo find /var/www/huennis-apps -type d -exec chmod g+s {} +

sudo chown -R netzsprung-admin:www-data /var/www/huennis-apps
sudo chmod -R 775 /var/www/huennis-apps
# Wichtig: Die Binaries im VENV müssen ausführbar sein
sudo chmod -R +x /var/www/huennis-apps/venv-3.14/bin/
