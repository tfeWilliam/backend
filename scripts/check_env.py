#!/usr/bin/env python3
"""
Script pour vérifier la configuration des variables d'environnement
Usage: python scripts/check_env.py
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.append(str(Path(__file__).parent.parent))

def check_environment():
    """Vérifie que toutes les variables nécessaires sont définies"""
    
    required_vars = [
        'SECRET_KEY',
        'DB_NAME', 'DB_USER', 'DB_PASSWORD',
        'STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY', 'STRIPE_WEBHOOK_SECRET',
        'ANTHROPIC_API_KEY',
        'MAPBOX_API_KEY',
        'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD'
    ]
    
    optional_vars = [
        'DEBUG', 'ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS',
        'CSRF_TRUSTED_ORIGINS', 'FIREBASE_CREDENTIALS_PATH',
        'ENVIRONMENT'
    ]
    
    missing_vars = []
    present_vars = []
    
    print("🔍 Vérification des variables d'environnement...\n")
    
    # Vérifier les variables requises
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            present_vars.append(var)
            # Masquer les valeurs sensibles
            if 'KEY' in var or 'PASSWORD' in var or 'SECRET' in var:
                masked_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
    
    print()
    
    # Vérifier les variables optionnelles
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"ℹ️  {var}: {value}")
    
    print()
    
    if missing_vars:
        print("❌ Variables requises manquantes:")
        for var in missing_vars:
            print(f"  • {var}")
        return False
    else:
        print(f"✅ Toutes les {len(required_vars)} variables requises sont présentes")
        return True

def check_secret_files():
    """Vérifie que les fichiers secrets existent"""
    base_dir = Path(__file__).parent.parent
    
    # Fichiers qui devraient exister
    required_files = [
        base_dir / '.env'
    ]
    
    # Fichiers optionnels mais recommandés
    optional_files = [
        base_dir / 'secrets' / 'firebase_credentials.json',
        base_dir / 'firebase_auth_services' / 'firebase_credentials.json'
    ]
    
    print("📁 Vérification des fichiers secrets...\n")
    
    missing_required = []
    missing_optional = []
    
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ {file_path.relative_to(base_dir)}")
        else:
            missing_required.append(file_path)
            print(f"❌ {file_path.relative_to(base_dir)} (REQUIS)")
    
    for file_path in optional_files:
        if file_path.exists():
            print(f"✅ {file_path.relative_to(base_dir)}")
        else:
            missing_optional.append(file_path)
            print(f"⚠️  {file_path.relative_to(base_dir)} (optionnel)")
    
    print()
    
    if missing_required:
        print("❌ Fichiers requis manquants:")
        for file_path in missing_required:
            print(f"  • {file_path}")
        return False
    else:
        print("✅ Tous les fichiers requis sont présents")
        
    if missing_optional:
        print("ℹ️  Fichiers optionnels manquants (non critiques):")
        for file_path in missing_optional:
            print(f"  • {file_path}")
    
    return True

def check_gitignore():
    """Vérifie que le .gitignore protège les fichiers sensibles"""
    base_dir = Path(__file__).parent.parent
    gitignore_path = base_dir / '.gitignore'
    
    print("🔒 Vérification de la sécurité .gitignore...\n")
    
    if not gitignore_path.exists():
        print("❌ Fichier .gitignore manquant!")
        return False
    
    gitignore_content = gitignore_path.read_text()
    
    # Patterns qui doivent être présents pour la sécurité
    required_patterns = [
        '.env',
        '*.env',
        'secrets/',
        '*.log',
        '__pycache__/',
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
        else:
            print(f"✅ {pattern} est ignoré")
    
    if missing_patterns:
        print("\n❌ Patterns manquants dans .gitignore:")
        for pattern in missing_patterns:
            print(f"  • {pattern}")
        return False
    else:
        print("\n✅ .gitignore sécurisé correctement")
        return True

def check_django_settings():
    """Vérifie que Django peut charger les settings"""
    print("⚙️  Vérification du chargement Django...\n")
    
    try:
        # Essayer d'importer Django et charger les settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hairbnb_backend.settings')
        
        import django
        from django.conf import settings
        django.setup()
        
        print(f"✅ Django chargé avec succès")
        print(f"✅ DEBUG = {settings.DEBUG}")
        print(f"✅ Base de données: {settings.DATABASES['default']['NAME']}")
        
        # Vérifier quelques settings critiques
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
            print("✅ SECRET_KEY configurée")
        else:
            print("❌ SECRET_KEY manquante")
            return False
            
        if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
            print("✅ STRIPE_SECRET_KEY configurée")
        else:
            print("❌ STRIPE_SECRET_KEY manquante")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement Django: {str(e)}")
        return False

def main():
    """Fonction principale de vérification"""
    print("🔧 VÉRIFICATION DE LA CONFIGURATION SÉCURISÉE HAIRBNB\n")
    print("=" * 60)
    
    # Charger le .env si présent
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"📥 Fichier .env chargé: {env_file}\n")
    else:
        print("⚠️  Aucun fichier .env trouvé\n")
    
    # Tests de vérification
    tests = [
        ("Variables d'environnement", check_environment),
        ("Fichiers secrets", check_secret_files),
        ("Sécurité .gitignore", check_gitignore),
        ("Configuration Django", check_django_settings),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Résumé final
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ FINAL:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ RÉUSSI" if passed else "❌ ÉCHEC"
        print(f"{status:<12} {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 FÉLICITATIONS! Configuration sécurisée correctement mise en place!")
        print("🚀 Votre application HairBnB est prête pour la production!")
        return 0
    else:
        print("💥 Des problèmes de configuration ont été détectés!")
        print("🔧 Veuillez corriger les erreurs avant de continuer.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
