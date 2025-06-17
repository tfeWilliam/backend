#!/bin/bash

echo "🧹 Nettoyage des secrets dans le dépôt Git..."

# 1. Arrêter et supprimer tous les fichiers secrets du staging
git reset HEAD .env 2>/dev/null || true
git reset HEAD firebase_auth_services/firebase_credentials.json 2>/dev/null || true

# 2. Supprimer les fichiers secrets de l'index Git (mais les garder localement)
git rm --cached .env 2>/dev/null || true
git rm --cached firebase_auth_services/firebase_credentials.json 2>/dev/null || true

# 3. Supprimer ces fichiers de l'historique Git
echo "🔄 Suppression de .env de l'historique..."
git filter-branch --force --index-filter \
"git rm --cached --ignore-unmatch .env" \
--prune-empty --tag-name-filter cat -- --all

echo "🔄 Suppression de firebase_credentials.json de l'historique..."
git filter-branch --force --index-filter \
"git rm --cached --ignore-unmatch firebase_auth_services/firebase_credentials.json" \
--prune-empty --tag-name-filter cat -- --all

# 4. Forcer le garbage collection
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now

echo "✅ Nettoyage terminé !"
echo "⚠️  IMPORTANT: Il faut maintenant :"
echo "   1. Modifier settings_test.py pour utiliser os.getenv()"
echo "   2. Créer un nouveau .env avec tes vraies clés (en local seulement)"
echo "   3. Vérifier que .env est dans .gitignore"
echo "   4. Commit et push"
