#!/bin/bash

# Pfad-Logik: Wechselt in das Hauptverzeichnis des Projekts (eine Ebene höher als das Script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🚀 Starte Projekt-Setup (Tailwind & JS) in: $PROJECT_ROOT"

# --- 1. TAILWIND CLI ---
BINARY_NAME="tailwindcss"
if [ ! -f "./$BINARY_NAME" ]; then
    echo "📥 Lade Tailwind CLI (Linux x64) herunter..."
    curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
    mv tailwindcss-linux-x64 "$BINARY_NAME"
    chmod +x "$BINARY_NAME"
    echo "✅ CLI installiert."
else
    echo "ℹ️ Tailwind CLI ist bereits vorhanden."
fi

# --- 2. ORDNERSTRUKTUR ---
echo "📁 Prüfe Ordnerstruktur..."
mkdir -p static/css
mkdir -p static/js

# --- 3. JAVASCRIPT LIBRARIES (Lokal) ---
echo "📦 Prüfe JavaScript Libraries..."

# HTMX
if [ ! -f "static/js/htmx.min.js" ]; then
    echo "📥 Lade HTMX herunter..."
    curl -L https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js -o static/js/htmx.min.js
    echo "✅ HTMX lokal gespeichert."
fi

# Alpine.js
if [ ! -f "static/js/alpine.min.js" ]; then
    echo "📥 Lade Alpine.js herunter..."
    curl -L https://cdn.jsdelivr.net/npm/alpinejs@3.13.5/dist/cdn.min.js -o static/js/alpine.min.js
    echo "✅ Alpine.js lokal gespeichert."
fi

# --- 4. TAILWIND INPUT CSS ---
if [ ! -f "static/css/input.css" ]; then
    echo "📝 Erstelle static/css/input.css..."
    echo '@import "tailwindcss";' > static/css/input.css
fi

# --- 5. BUILD PROZESS ---
echo "🔨 Generiere optimierte CSS-Datei (Production Build)..."
./$BINARY_NAME -i ./static/css/input.css -o ./static/css/output.css --minify

# --- 6. FONTS ---
echo "🔤 Prüfe Schriftarten..."
mkdir -p static/fonts
# Hinweis: Schriften (Inter, Playfair) sollten manuell in static/fonts liegen.
# Ein automatischer Download von Google Fonts via curl ist komplex, 
# da Google den User-Agent prüft.

# Ergänzung für dein setup_tailwind.sh
if [ ! -f "static/js/lucide.min.js" ]; then
    echo "📥 Lade Lucide Icons herunter..."
    curl -L https://cdn.jsdelivr.net/npm/lucide@0.479.0/dist/umd/lucide.min.js -o static/js/lucide.min.js
fi

echo "✨ Fertig! Das Projekt ist bereit."
echo "   - CSS: static/css/output.css"
echo "   - JS:  static/js/htmx.min.js, static/js/alpine.min.js"
