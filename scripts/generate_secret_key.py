#!/usr/bin/env python3
"""
Générateur de clé secrète Django sécurisée
Usage: python scripts/generate_secret_key.py
"""
import secrets
import string

def generate_secret_key(length=50):
    """Génère une clé secrète Django sécurisée"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_multiple_keys():
    """Génère plusieurs clés pour différents environnements"""
    print("🔐 Générateur de clés secrètes sécurisées\n")
    
    keys = {
        "DÉVELOPPEMENT": generate_secret_key(),
        "TEST": generate_secret_key(),
        "PRODUCTION": generate_secret_key(64)  # Plus longue pour la prod
    }
    
    for env, key in keys.items():
        print(f"=== {env} ===")
        print(f"SECRET_KEY={key}")
        print()
    
    print("⚠️  IMPORTANT:")
    print("• Copiez ces clés dans vos fichiers .env appropriés")
    print("• Utilisez des clés différentes pour chaque environnement")
    print("• Ne partagez jamais ces clés publiquement!")
    print("• Changez-les régulièrement (tous les 6 mois)")

if __name__ == "__main__":
    generate_multiple_keys()
