# Huennis Blog & Office Central 365

Ein leistungsstarkes **Multi-Site-Projekt** auf Basis von Django, das verschiedene Plattformen unter einem gemeinsamen Kern vereint. 

## 🚀 Übersicht der Identitäten

Das Projekt steuert über die Umgebungsvariable `SITE_IDENTITY` dynamisch drei verschiedene Plattformen:

* **Blick Dahinter (`blick`):** Der persönliche Hauptblog.
* **Netzsprung (`netzsprung`):** IT-Blog inklusive Wiki und Shop-Funktionalitäten.
* **Office Central 365 (`office`):** Das Business-HQ für CRM, Billing und das **Mail Hub** (zentrale E-Mail-Verwaltung).

---

## 🛠 Tech-Stack

* **Sprache:** Python 3.14
* **Framework:** Django (mit Django-HTMX für dynamische Frontends)
* **Datenbank:** PostgreSQL
* **Betriebssystem:** Ubuntu 24.04 (Noble Numbat)
* **Webserver:** Nginx & Gunicorn
* **Frontend:** Tailwind CSS & TinyMCE Editor

---

## 📁 Projektstruktur & Features

### Core-Apps (Global)
- **accounts:** Erweitertes User-Modell (`CustomUser`).
- **core:** Basis-Logik und Multi-Site-Kontextprozessoren.
- **blog:** Beitragsverwaltung für blick-dahinter.de.
- **wiki:** Dokumentationsplattform (MPTT-basiert für Hierarchien).

### Office-Spezifisch (`SITE_IDENTITY=office`)
- **mail_hub:** E-Mail-Client mit OAuth2 (Microsoft Graph) und IMAP-Unterstützung.
- **crm / seafile_drive:** Kundenverwaltung und Cloud-Integration.

---

## ⚙️ Installation & Setup

### 1. Voraussetzungen
Stelle sicher, dass Python 3.14 und die PostgreSQL-Datenbank auf Ubuntu 24.04 installiert sind.

### 2. Repository klonen & Venv einrichten
```bash
git clone <dein-repo-url>
cd huennis-blog
python3.14 -m venv venv
source venv/bin/activate
pip install -r requirements.txt