import os
import django
import sys


sys.path.insert(0, 'C:/Users/Admin/PycharmProjects/hairbnb_backend')

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hairbnb_backend.settings')  # Remplace par ton chemin correct
django.setup()

# Import des modèles
from hairbnb.models import TblLocalite, TblRue, TblAdresse, TblClient, TblCoiffeuse

# Ajouter des données
localite = TblLocalite.objects.create(commune="Lyon", code_postal="69001")
rue = TblRue.objects.create(nom_rue="Rue Victor Hugo", localite=localite)
adresse = TblAdresse.objects.create(numero="25", rue=rue)
TblClient.objects.create(
    uuid="client_uuid_789",
    nom="Lemoine",
    prenom="Paul",
    email="paul.lemoine@example.com",
    type="client",
    sexe="homme",
    numero_telephone="0145896325",
    adresse=adresse
)
TblCoiffeuse.objects.create(
    uuid="coiffeuse_uuid_890",
    nom="Durand",
    prenom="Marie",
    email="marie.durand@example.com",
    type="coiffeuse",
    sexe="femme",
    numero_telephone="0678451236",
    adresse=adresse,
    specialite="Coupe",
    experience=3,
    disponible=True
)

print("Données insérées avec succès.")
