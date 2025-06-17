from datetime import datetime

from django.utils.timezone import make_aware
from rest_framework.decorators import api_view
from rest_framework.response import Response

from hairbnb.business.business_logic import ServiceData
from hairbnb.models import TblService, TblSalonService, TblSalon, TblTemps, TblPrix, TblServicePrix, \
    TblServiceTemps, TblPromotion



# ✅ Ajouter un service à une coiffeuse

@api_view(['POST'])
def add_service_to_coiffeuse(request, coiffeuse_id):
    print(f"🔍 Requête reçue pour coiffeuse_id: {coiffeuse_id}")
    print(f"📩 Données reçues: {request.data}")

    try:
        # Vérifier si la coiffeuse a un salon
        salon = TblSalon.objects.get(coiffeuse__idTblUser=coiffeuse_id)
        print(f"✅ Salon trouvé: {salon}")

        # Extraire les données
        intitule_service = request.data.get('intitule_service')
        description = request.data.get('description', '')
        temps_minutes = request.data.get('temps')
        prix_montant = request.data.get('prix')

        # Vérifier si les champs sont bien remplis
        if not intitule_service or not prix_montant or not temps_minutes:
            return Response({"status": "error", "message": "Champs manquants"}, status=400)

        # Créer le service
        service = TblService.objects.create(intitule_service=intitule_service, description=description)
        print(f"✅ Service ajouté: {service}")

        # Associer Temps
        temps, _ = TblTemps.objects.get_or_create(minutes=temps_minutes)
        TblServiceTemps.objects.create(service=service, temps=temps)

        # 🔍 Vérifier si un prix existe déjà sans lever d'erreur
        prix = TblPrix.objects.filter(prix=prix_montant).first()

        # 🛠️ Si aucun prix trouvé, on le crée
        if not prix:
            prix = TblPrix.objects.create(prix=prix_montant)

        TblServicePrix.objects.create(service=service, prix=prix)

        # Lier au salon
        TblSalonService.objects.create(salon=salon, service=service)
        print("✅ Association Salon-Service créée.")

        return Response({"status": "success", "message": "Service ajouté avec succès."}, status=201)

    except TblSalon.DoesNotExist:
        print("❌ Erreur: Aucun salon trouvé pour cette coiffeuse.")
        return Response({"status": "error", "message": "Aucun salon trouvé pour cette coiffeuse."}, status=404)

    except Exception as e:
        print(f"❌ Erreur interne : {e}")
        return Response({"status": "error", "message": str(e)}, status=500)

# ✅ Supprimer un service
@api_view(['DELETE'])
def delete_service(request, service_id):
    try:
        service = TblService.objects.get(idTblService=service_id)
        service.delete()
        return Response({"status": "success", "message": "Service supprimé."}, status=200)

    except TblService.DoesNotExist:
        return Response({"status": "error", "message": "Service introuvable."}, status=404)