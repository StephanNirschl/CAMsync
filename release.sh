#!/bin/bash

# ==========
# CAMsync Release-Skript (sicher)
# ==========

set -e

# 🏷 Versionsnummer abfragen
read -p "Welche Versionsnummer möchtest du releasen? (z.B. v0.X.X): " VERSION

# Eingabe prüfen
if [[ -z "$VERSION" ]]; then
  echo "❌ Keine Versionsnummer eingegeben. Abbruch."
  exit 1
fi

# Doppelte Tags vermeiden
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "❌ Tag '$VERSION' existiert bereits – bitte neue Version wählen."
  exit 1
fi

# Committet Änderungen
echo "📥 Änderungen werden committet..."
git add .
git commit -m "🔖 Release $VERSION"

# Push to main
echo "⬆️  Push nach origin..."
git push origin main

# Tag setzen und pushen
echo "🏷 Tag $VERSION wird erstellt..."
git tag "$VERSION"
git push origin "$VERSION"

echo "✅ Release $VERSION wurde erstellt und gepusht."
echo "📦 GitHub Actions sollte jetzt automatisch die .exe bauen."