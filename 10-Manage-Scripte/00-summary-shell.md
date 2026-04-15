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

cd /opt/vscode
docker compose up -d --force-recreate
pip freeze > requirements.txt

cd /opt/vscode
docker compose pull   # Lädt das aktuellste Image vom Hub herunter
docker compose up -d  # Startet den Container mit dem neuen Image neu

ldconfig -p | grep libpq


Mein Rat für jetzt:

su coder
source venv-3.14/bin/activate


# In den Test-Ordner wechseln
cd /var/www/test-huennis-apps/

# Falls das alte venv existiert, weg damit (da es evtl. kaputte Links enthält)
rm -rf venv-3.14

# Neues Venv mit dem System-Python erstellen
# (Stelle sicher, dass python3-venv auf dem Host installiert ist: sudo apt install python3-venv)
python3 -m venv venv-3.14

# Wichtig: Requirements mit dem NEUEN pip installieren
./venv-3.14/bin/pip install --upgrade pip
./venv-3.14/bin/pip install -r requirements.txt

cd /opt/vscode
docker compose up -d --force-recreate
sudo docker logs vscode -f

armin-huenniger ALL=(ALL) NOPASSWD:ALL
sudo usermod -aG sudo armin-huenniger


# Zum richtigen Verzeichnis wechseln
cd /etc/nginx/sites-enabled/

# Bestehende (alte) Verknüpfung entfernen, falls vorhanden
sudo rm -f cloud.netzsprung.de.conf

# Neue Verknüpfung von 'available' nach 'enabled' erstellen
sudo ln -s /etc/nginx/sites-available/cloud.netzsprung.de.conf /etc/nginx/sites-enabled/

sudo docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' seafile-onlyoffice




Dienst / Container,Port (Host),Ziel (Intern),Status / Info
Nginx (Host),80 / 443,-,Aktiv (Entry Point)
Seafile (Cloud),8082,80,Hier liegt der Fehler! (Nginx sucht 8081)
Mailcow (UI),8080 / 8443,8080 / 8443,Aktiv
Postgres (DB),5432,-,Aktiv (System-Dienst)
VS Code Server,8070,8080,Aktiv
VS Code Apps,8010 - 8012,8010 - 8012,Reserviert für deine Dev-Apps




Das ist eine sehr hilfreiche Übersicht. Ich habe dir daraus eine strukturierte Dokumentation erstellt, die nicht nur die nackten Daten enthält, sondern auch direkt die **Zusammenhänge** (wer spricht mit wem) und eine **Checkliste für Fehler** bietet.

Diese Datei kannst du als `SERVER_PORTS.md` in deinem `~/tools/` Ordner speichern.

***

# 🖥️ System Port Dashboard: Server-Zustand
**Stand:** 15. April 2026, 09:01 UTC
**Server:** `server2.netzsprung.de`

---

## 🌍 1. Web-Entry Points (Öffentliche Ports)
Diese Ports sind die "Eingangstüren" deines Servers. Nginx nimmt die Anfragen hier an und verteilt sie intern weiter.

| Port | Dienst | Funktion | Status |
|:--- |:--- |:--- |:---|
| **80** | Nginx | HTTP (wird autom. auf HTTPS umgeleitet) | ✅ Aktiv |
| **443** | Nginx | HTTPS (Haupt-Verschlüsselung) | ✅ Aktiv |
| **22** | SSH | Fernwartung (sshd) | ✅ Aktiv |

---

## 🐳 2. Docker & Container Services
Hier sind die internen Brücken zwischen dem Host-System und den isolierten Containern.

### 🌊 Seafile & Office (Cloud-Infrastruktur)
| Host-Port | Ziel (Container) | Dienst | Nginx-Backend Ziel |
|:--- |:--- |:--- |:---|
| **8081** | 80/tcp | Seafile-Server | `http://127.0.0.1:8081` |
| **8444** | 443/tcp | Seafile-Server (SSL) | - |
| **8082** | 80/tcp | OnlyOffice | `http://127.0.0.1:8082` |

### 📧 Mailcow (E-Mail System)
| Host-Port | Dienst | Funktion |
|:--- |:--- |:--- |
| **8080** | Mailcow UI | Admin-Oberfläche & Webmail (SOGo) |
| **8443** | Mailcow UI | Verschlüsseltes Admin-Interface |
| **25, 465, 587** | Postfix | SMTP (E-Mail Versand) |
| **110, 143, 993, 995**| Dovecot | IMAP/POP3 (E-Mail Empfang) |

### 💻 Development (VS-Code & Tools)
| Host-Port | Dienst | Funktion |
|:--- |:--- |:--- |
| **8070** | VS-Code Server | Web-IDE Browserzugriff |
| **8010 - 8012** | Dev-Apps | Reservierte Ports für Python/Django Testläufe |

---

## 🐍 3. Python & Gunicorn (Interne Apps)
Gunicorn nutzt **Unix-Sockets** anstelle von Ports, was schneller und sicherer ist.

> [!CAUTION]
> **Aktueller Status:** Keine aktiven Sockets gefunden.
> Wenn du deine Django-Apps (test.netzsprung.de) erreichen willst, müssen die `.service`-Units gestartet sein.

**Befehl zum Fixen:**
```bash
sudo systemctl start gunicorn_netzsprung.socket
sudo systemctl start gunicorn_netzsprung_test.service
```

---

## 🐘 4. Datenbanken & Systemdienste
| Port | Dienst | Nutzer | Zugriff |
|:--- |:--- |:--- |:---|
| **5432** | PostgreSQL | `postgres` | Lokal & Intern (0.0.0.0) |
| **13306** | MariaDB (Mailcow) | `root` | Nur Localhost (127.0.0.1) |
| **53** | systemd-resolve | `systemd` | DNS-Auflösung |

---

## 🛠️ Schnell-Diagnose bei Fehlern

### "502 Bad Gateway" (Cloud/Seafile)
1. Prüfen ob Container läuft: `docker ps | grep seafile`
2. Prüfen ob Port 8081 offen ist: `sudo ss -tulpn | grep 8081`
3. Nginx-Config checken: `cat /etc/nginx/sites-enabled/cloud.netzsprung.de.conf`

### "500 Internal Server Error" (Django Test-App)
1. Identity prüfen: `echo $SITE_IDENTITY`
2. Gunicorn Status: `sudo systemctl status gunicorn_netzsprung_test.service`
3. Logs einsehen: `sudo journalctl -u gunicorn_netzsprung_test -f`

### "SSL-Fehler"
1. Zertifikatsliste: `sudo certbot certificates`
2. Nginx-Test: `sudo nginx -t`

---

**Hinweis:** Dieses Dokument wurde automatisch basierend auf dem `show-ports.sh` Output generiert. Alle Passwörter und Identitäten (z.B. `netzsprung`) müssen in den jeweiligen `.env` oder Service-Dateien hinterlegt sein.

***

### Wie du diese Datei nutzt:
Du kannst diesen Block einfach kopieren und in eine Datei namens `ZUSTAND.md` auf deinem Server einfügen. Wenn du das nächste Mal eine Port-Übersicht brauchst, hast du diese Legende als Vergleichswert.



Kategorie,Dienst / Container,Port / Pfad,Ziel / Info,Status
Web,Nginx (Main),80 / 443,External Entry Point,✅ AKTIV
System,SSH Daemon,22,Fernwartung,✅ AKTIV
Datenbank,PostgreSQL,5432,System DB (Postgres),✅ AKTIV
Cloud,Seafile Server,8081,-> Container Port 80,✅ AKTIV
Cloud,Seafile Server,8444,-> Container Port 443,✅ AKTIV
Office,OnlyOffice,8082,-> Container Port 80,✅ AKTIV
Dev,VS-Code UI,8070,-> Container Port 8080,✅ AKTIV
Dev,VS-Code Apps,8010 - 8012,Manuelle Dev-Ports,✅ BEREIT
Mail,Mailcow Nginx,8080 / 8443,Admin & Webmail UI,✅ AKTIV
Mail,Postfix,25 / 465 / 587,SMTP Versand,✅ AKTIV
Mail,Dovecot,110 / 143 / 993 / 995,IMAP/POP3 Empfang,✅ AKTIV
Mail,Mailcow MySQL,13306,Nur 127.0.0.1 (Docker),✅ AKTIV
Python,Gunicorn Netzsprung,/run/gunicorn_netzsprung.sock,Prod Identity: netzsprung,✅ AKTIV
Python,Gunicorn Netzsprung Test,/run/gunicorn_netzsprung_test.sock,Test Identity: netzsprung,✅ AKTIV
Python,Gunicorn Blick,/run/gunicorn_blick.sock,Prod Identity: blick,✅ AKTIV
Python,Gunicorn Blick Test,/run/gunicorn_blick_test.sock,Test Identity: blick,✅ AKTIV
Python,Gunicorn Office,/run/gunicorn_office.sock,Prod Identity: office,✅ AKTIV
Python,Gunicorn Office Test,/run/gunicorn_office_test.sock,Test Identity: office,✅ AKTIV
System,DNS Resolver,53,systemd-resolve,✅ AKTIV
Docker,Seafile-Redis,6379 (intern),Cache,✅ AKTIV
Docker,Seafile-DB,3306 (intern),MariaDB 10.11,✅ AKTIV