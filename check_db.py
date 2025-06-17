#!/usr/bin/env python3
"""
Script pour vérifier les données dans la base
"""

import os
import sys
import django

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hairbnb_backend.settings')
django.setup()

from hairbnb.models import TblSalon, TblCoiffeuse, TblUser, TblCoiffeuseSalon

def check_database():
    """Vérifie le contenu de la base de données"""
    print("=== VÉRIFICATION DE LA BASE DE DONNÉES ===\n")
    
    # Vérifier les utilisateurs
    user_count = TblUser.objects.count()
    print(f"👥 Utilisateurs en base : {user_count}")
    
    # Vérifier les coiffeuses
    coiffeuse_count = TblCoiffeuse.objects.count()
    print(f"✂️  Coiffeuses en base : {coiffeuse_count}")
    
    # Vérifier les salons
    salon_count = TblSalon.objects.count()
    print(f"🏪 Salons en base : {salon_count}")
    
    # Vérifier les relations coiffeuse-salon
    relation_count = TblCoiffeuseSalon.objects.count()
    print(f"🔗 Relations coiffeuse-salon : {relation_count}")
    
    if salon_count > 0:
        print(f"\n📋 DÉTAILS DES SALONS :")
        for salon in TblSalon.objects.all()[:5]:  # Limiter à 5 pour éviter le spam
            print(f"  - Salon #{salon.idTblSalon}: {salon.nom_salon}")
            print(f"    Slogan: {salon.slogan}")
            print(f"    Position: {salon.position}")
            
            # Vérifier les coiffeuses liées
            relations = TblCoiffeuseSalon.objects.filter(salon=salon)
            print(f"    Coiffeuses ({relations.count()}):")
            for relation in relations:
                coiffeuse = relation.coiffeuse
                print(f"      → {coiffeuse.idTblUser.nom} {coiffeuse.idTblUser.prenom} (Propriétaire: {relation.est_proprietaire})")
            print()
    else:
        print("\n⚠️  Aucun salon trouvé en base !")
        print("   Vous devez créer au moins un salon pour tester l'endpoint.")

if __name__ == "__main__":
    check_database()
