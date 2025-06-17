from hairbnb.models import TblPaiementStatut, TblMethodePaiement

# 🟢 Statuts de paiement
STATUTS = [
    {"code": "en_attente", "libelle": "En attente"},
    {"code": "payé", "libelle": "Payé"},
    {"code": "échoué", "libelle": "Échoué"},
    {"code": "remboursé", "libelle": "Remboursé"},
]

# 💳 Méthodes de paiement
METHODES = [
    {"code": "card", "libelle": "Carte Bancaire"},
]

def populate_paiement_data():
    for statut in STATUTS:
        obj, created = TblPaiementStatut.objects.get_or_create(code=statut["code"], defaults={"libelle": statut["libelle"]})
        if created:
            print(f"✅ Statut ajouté : {obj.code}")
        else:
            print(f"⚠️ Statut existant : {obj.code}")

    for methode in METHODES:
        obj, created = TblMethodePaiement.objects.get_or_create(code=methode["code"], defaults={"libelle": methode["libelle"]})
        if created:
            print(f"✅ Méthode ajoutée : {obj.code}")
        else:
            print(f"⚠️ Méthode existante : {obj.code}")

# ➕ Exécution
populate_paiement_data()
