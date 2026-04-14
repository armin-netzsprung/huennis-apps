Großartig, dass die **DEV-Umgebungen** jetzt alle laufen! Das ist die halbe Miete.

Zu deiner Frage bezüglich der Ports: **Nein, TEST und DEV kommen sich nicht in die Quere.**
Das liegt daran, dass deine **TEST-Umgebung** über **Unix-Sockets** (`.sock`-Dateien) läuft, während deine **DEV-Umgebung** über **TCP-Ports** (`8000`, `8001`, `8002`) kommuniziert. Das ist eine sehr saubere Trennung.

Hier ist die gewünschte Zusammenfassung aller Befehle, um dein System für **DEV**, **TEST** und **PROD** (Praxis) perfekt abzusichern.

---

### 1. Nginx: Test und Neustart
Wann immer du eine Datei in `sites-available` änderst:
```bash
# Syntax prüfen (MUSS 'successful' melden)
sudo nginx -t

# Konfiguration neu laden (ohne Verbindungsabbruch)
sudo systemctl reload nginx

# Kompletter Neustart (falls reload nicht reicht)
sudo systemctl restart nginx
```

---

### 2. Certbot: Alle Domains absichern
Damit die SSL-Warnungen verschwinden, fassen wir die Domains pro Identität zusammen. Da `test.` im DNS scheinbar noch fehlt, konzentrieren wir uns auf das, was da ist:

```bash
# Für Office
sudo certbot --nginx -d officecentral365.netzsprung.de -d dev.officecentral365.netzsprung.de

# Für Netzsprung
sudo certbot --nginx -d netzsprung.de -d www.netzsprung.de -d dev.netzsprung.de

# Für Blick
sudo certbot --nginx -d blick-dahinter.de -d www.blick-dahinter.de -d dev.blick-dahinter.de
```
*Tipp: Sobald du die `test.` Subdomains im DNS deines Providers angelegt hast, wiederhole die Befehle einfach und füge `-d test.deinedomain.de` hinzu.*

---

### 3. Gunicorn: TEST & PROD verwalten
Wir löschen die alten `_dev` Services, da wir DEV jetzt manuell über den Hub starten.

#### Alte DEV-Services entfernen:
```bash
# 1. Stoppen und deaktivieren
sudo systemctl disable --now gunicorn_office_dev.socket gunicorn_office_dev.service
sudo systemctl disable --now gunicorn_netzsprung_dev.socket gunicorn_netzsprung_dev.service
sudo systemctl disable --now gunicorn_blick_dev.socket gunicorn_blick_dev.service

# 2. Dateien physisch löschen
sudo rm /etc/systemd/system/gunicorn_*_dev.service
sudo rm /etc/systemd/system/gunicorn_*_dev.socket

# 3. Systemd mitteilen, dass Dateien weg sind
sudo systemctl daemon-reload
```

#### TEST & PROD steuern:
```bash
# Status prüfen
sudo systemctl status gunicorn_netzsprung_test

# Neustart nach Code-Änderungen in TEST oder PROD
sudo systemctl restart gunicorn_netzsprung_test
sudo systemctl restart gunicorn_office

sudo systemctl daemon-reload
sudo systemctl restart gunicorn_netzsprung_test.socket
sudo systemctl restart gunicorn_netzsprung_test.service
```

---

### 4. Logging: Alles im Blick behalten
Hier sind die wichtigsten Befehle, um Fehler in Echtzeit zu sehen:

```bash
# Nginx: Wer greift gerade zu? (Access & Error kombiniert)
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log

# Gunicorn (TEST/PROD): Was macht Django im Hintergrund?
sudo journalctl -u gunicorn_netzsprung_test -f
sudo journalctl -u gunicorn_office -f

# Deine neuen DEV-Logs (aus dem Python-Skript)
tail -f ~/dev/dev-huennis-apps/logs/django_dev.log
```

---

### 5. Berechtigungen (chmod / chown)
Damit Nginx (User `www-data`) und du (`netzsprung-admin`) friedlich koexistieren:

#### Verzeichnisse öffnen (Wichtig für Nginx-Durchgang):
```bash
sudo chmod +x /home/netzsprung-admin
sudo chmod +x /home/netzsprung-admin/dev
sudo chmod -R 755 /home/netzsprung-admin/dev/dev-huennis-apps
sudo chmod -R 755 /var/www/test-huennis-apps
sudo chmod -R 755 /var/www/huennis-apps

# Nginx (www-data) Lese- und Ausführungsrechte für den Test-Ordner geben
sudo chown -R netzsprung-admin:www-data /var/www/test-huennis-apps/staticfiles
sudo chmod -R 755 /var/www/test-huennis-apps/staticfiles


```

#### Besitzer setzen:
```bash
# Dev gehört dir
sudo chown -R netzsprung-admin:www-data /home/netzsprung-admin/dev/dev-huennis-apps

# Test & Prod gehören ebenfalls dir, damit du deployen kannst
sudo chown -R netzsprung-admin:www-data /var/www/test-huennis-apps
sudo chown -R netzsprung-admin:www-data /var/www/huennis-apps
```

---

### Ein kleiner Tipp zu deiner `settings.py`:
Du hast in der `settings.py` eine sehr gute Logik für die Identitäten. Da du jetzt aber mehrere Umgebungen (DEV auf Port 8000-8002) hast, stelle sicher, dass in der `action_menu` deines Hub-Skripts die `SITE_IDENTITY` korrekt als Umgebungsvariable übergeben wird, damit Django weiß, ob es gerade "Blick" oder "Office" sein soll.

**Bist du bereit, den ersten TEST-Service (`test.netzsprung.de`) scharf zu schalten?** Dann müssten wir nur sicherstellen, dass das Verzeichnis `/var/www/test-huennis-apps` existiert und die Datenbank `test_dev_netzsprung` (oder wie sie in deiner Logik heißt) angelegt ist.






#####################################
Das ist die letzte Meile! Wenn der DNS jetzt auflöst und du ein Zertifikat hast, aber einen **502** siehst, bedeutet das: Nginx versucht die Anfrage an den Office-Test-Socket weiterzureichen, findet dort aber niemanden vor.

Da wir vorhin die "Geisterdateien" mit den Kommentaren gelöscht haben, müssen wir sicherstellen, dass der Office-Test-Service jetzt wirklich sauber unter dem neuen Namen läuft.

### 1. Der Socket-Check
Prüfe zuerst, ob der Socket physisch existiert und die richtigen Rechte hat:
```bash
ls -l /run/gunicorn_office_test.sock
```
* **Falls die Datei fehlt:** Der Socket-Dienst läuft nicht.
* **Falls sie `root` gehört:** Die `.socket`-Datei hat noch keine `SocketUser`-Einträge.

### 2. Service-Status prüfen
Schau nach, warum der Office-Test-Service eventuell nicht gestartet ist:
```bash
sudo systemctl status gunicorn_office_test.service
```
Wenn dort steht `Active: active (running)`, aber du trotzdem einen 502 bekommst, dann schau in das Log:
```bash
sudo journalctl -u gunicorn_office_test -f
```

### 3. Mögliche Ursachen für den 502 bei Office
Da die anderen (Blick & Netzsprung) laufen, tippe ich auf einen dieser drei Punkte:

**A. Migrationen vergessen:**
Hast du für Office in der Test-Umgebung schon die Tabellen erstellt?
```bash
cd /var/www/test-huennis-apps
sudo -u netzsprung-admin SITE_IDENTITY=office ./venv-3.14/bin/python manage.py migrate
```

**B. Pfad-Fehler in der Nginx-Config:**
Schau in `/etc/nginx/sites-available/test_officecentral365.netzsprung.de.conf`.
Zeigt der `proxy_pass` wirklich auf `http://unix:/run/gunicorn_office_test.sock;`? (Ohne Tippfehler).

**C. Gunicorn "Hängt":**
Manchmal blockiert ein alter Prozess den Start.
```bash
sudo systemctl stop gunicorn_office_test.service
sudo systemctl stop gunicorn_office_test.socket
sudo rm /run/gunicorn_office_test.sock
sudo systemctl daemon-reload
sudo systemctl start gunicorn_office_test.socket
sudo systemctl start gunicorn_office_test.service
```

### 4. Der interne Test
Wenn der Browser 502 sagt, teste es direkt auf dem Server:
```bash
sudo -u www-data curl --unix-socket /run/gunicorn_office_test.sock -H "Host: test.officecentral365.netzsprung.de" http://localhost/
```
* Kommt hier HTML? Dann liegt das Problem bei Nginx (Config prüfen).
* Kommt hier ein Fehler? Dann liegt das Problem bei Gunicorn/Django.

**Was sagt das Log (`journalctl -u gunicorn_office_test -f`), wenn du die Seite im Browser aufrufst?** Wir finden den Fehler jetzt!



##############################



cd /opt/vscode
sudo docker compose up -d

sudo apt update && sudo apt install -y libpq-dev clang build-essential
SITE_IDENTITY=office python manage.py check

# Zeigt an, ob Port 8010 wirklich auf 127.0.0.1 lauscht
netstat -tulpen | grep 8010
curl -I http://127.0.0.1:8010

docker compose up -d --force-recreate
pip freeze > requirements.txt

cd /opt/vscode
docker compose pull   # Lädt das aktuellste Image vom Hub herunter
docker compose up -d  # Startet den Container mit dem neuen Image neu

ldconfig -p | grep libpq


Mein Rat für jetzt:

su coder
source venv-3.14/bin/activate
