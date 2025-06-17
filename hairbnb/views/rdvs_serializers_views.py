from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from decimal import Decimal
from hairbnb.models import (
    TblCoiffeuse, TblSalon, TblService, TblRendezVous, TblRendezVousService, TblUser,
    TblServicePrix, TblServiceTemps, TblPromotion, TblIndisponibilite, TblHoraireCoiffeuse,
)
from hairbnb.serializers.horaire_coiffeuse_serializers import HoraireCoiffeuseSerializer
from hairbnb.serializers.rdvs_serializers import IndisponibiliteSerializer


# 📅 **Créer un rendez-vous avec gestion automatique du prix et de la durée**
@api_view(['POST'])
def create_rendez_vous(request):
    """
    Créer un rendez-vous pour un client avec une coiffeuse et un salon,
    en prenant en compte les promotions et en calculant le prix final et la durée totale.
    """
    try:
        #print("📌 Requête reçue:", request.data)  # ✅ Log pour voir les données reçues

        user_id = request.data.get('user_id')  # ID du client
        coiffeuse_id = request.data.get('coiffeuse_id')  # ID de la coiffeuse
        date_heure = request.data.get('date_heure')  # Date du RDV
        services_ids = request.data.get('services', [])  # Liste des services sélectionnés

        if not all([user_id, coiffeuse_id, date_heure, services_ids]):
            return Response({"error": "Tous les champs sont requis."}, status=400)

        # ✅ Vérifie l'utilisateur et que c'est bien un client
        user = get_object_or_404(TblUser, idTblUser=user_id)
        client = get_object_or_404(user.clients)

        # ✅ Vérifie la coiffeuse
        coiffeuse = get_object_or_404(TblCoiffeuse, idTblUser=coiffeuse_id)

        # ✅ Récupère automatiquement l'ID du salon à partir de la coiffeuse
        #salon = get_object_or_404(TblSalon, coiffeuse=coiffeuse)

        # ✅LOGIQUE COMPLÈTE ET SÉCURISÉE ✅
        salon = coiffeuse.salons.first()
        if not salon:
            return Response({"error": "La coiffeuse n'est associée à aucun salon."}, status=404)

        #print(f"✅ Client trouvé: {client}")
        #print(f"✅ Coiffeuse trouvée: {coiffeuse}")
        #print(f"✅ Salon trouvé: {salon}")

        # Initialisation des totaux
        total_prix = Decimal("0.00")
        total_duree = 0

        # Création du rendez-vous
        rdv = TblRendezVous.objects.create(
            client=client,
            coiffeuse=coiffeuse,
            salon=salon,  # ✅ Plus besoin de l'envoyer depuis le frontend !
            date_heure=date_heure,
            statut="en attente",
            total_prix=0,  # Sera mis à jour après
            duree_totale=0  # Idem
        )

        # Ajouter les services au rendez-vous et calculer les totaux
        for service_id in services_ids:
            service = get_object_or_404(TblService, idTblService=service_id)
            #print(f"🔍 Service trouvé: {service.intitule_service}")

            # 🔥 Récupère le prix standard
            prix_service_obj = TblServicePrix.objects.filter(service=service).first()
            prix_service = prix_service_obj.prix.prix if prix_service_obj else Decimal("0.00")
            #print(f"💰 Prix du service: {prix_service}")

            # 🔥 Récupère la durée estimée
            temps_service_obj = TblServiceTemps.objects.filter(service=service).first()
            duree_service = temps_service_obj.temps.minutes if temps_service_obj else 0
            #print(f"⏳ Durée du service: {duree_service} min")

            # 🔥 Vérifier s'il y a une promotion active
            promo = TblPromotion.objects.filter(
                service=service,
                start_date__lte=now(),  # La promo est active au moment de la réservation
                end_date__gte=now()
            ).first()

            # ✅ Appliquer la réduction si une promotion existe
            if promo:
                reduction = (promo.discount_percentage / Decimal("100")) * prix_service
                prix_applique = prix_service - reduction  # Prix final avec réduction
                #print(f"🔥 Promo appliquée: {promo.discount_percentage}% -> {prix_applique} €")
            else:
                prix_applique = prix_service  # Prix normal sans réduction
                #print("⚠️ Pas de promotion active.")

            # 🔹 Ajouter le service au rendez-vous
            TblRendezVousService.objects.create(
                rendez_vous=rdv,
                service=service,
                prix_applique=prix_applique,
                duree_estimee=duree_service
            )

            # 🔹 Mise à jour des totaux
            total_prix += prix_applique
            total_duree += duree_service

        # ✅ Mise à jour des totaux dans le RDV
        rdv.total_prix = total_prix
        rdv.duree_totale = total_duree
        rdv.save()  # Sauvegarde du rendez-vous avec les valeurs mises à jour

        #print(f"✅ Rendez-vous créé: {rdv}")

        return Response({
            "message": "Rendez-vous créé ✅ avec prise en compte des promotions",
            "rendez_vous": {
                "id": rdv.idRendezVous,
                "date_heure": rdv.date_heure,
                "total_prix": float(total_prix),
                "duree_totale": total_duree,
            }
        }, status=201)

    except Exception as e:
        #print(f"❌ Erreur serveur: {e}")  # ✅ Capture et affiche l'erreur dans la console
        return Response({"error": f"Erreur serveur: {str(e)}"}, status=500)

@api_view(['GET'])
def get_coiffeuse_disponibilites(request, coiffeuse_id):
    """
    Retourne :
    - les rendez-vous existants (créneaux réservés)
    - les indisponibilités manuelles
    - les horaires d'ouverture du salon
    """
    try:
        # ✅ 1. Récupérer les RDV de la coiffeuse
        rdvs = TblRendezVous.objects.filter(coiffeuse__idTblUser=coiffeuse_id)
        rdv_creneaux = [{
            "date": rdv.date_heure.date(),
            "heure_debut": rdv.date_heure.time(),
            "duree_minutes": rdv.duree_totale
        } for rdv in rdvs]

        # ✅ 2. Récupérer les indisponibilités
        indispo = TblIndisponibilite.objects.filter(coiffeuse__idTblUser=coiffeuse_id)
        indispo_serialized = IndisponibiliteSerializer(indispo, many=True).data

        # ✅ 3. Récupérer les horaires hebdomadaires du salon
        horaires = TblHoraireCoiffeuse.objects.filter(salon__coiffeuse__idTblUser=coiffeuse_id)
        horaires_serialized = HoraireCoiffeuseSerializer(horaires, many=True).data

        return Response({
            "rendez_vous": rdv_creneaux,
            "indisponibilites": indispo_serialized,
            "horaires_salon": horaires_serialized
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def add_indisponibilite(request):
    """
    Ajouter une indisponibilité (pause, congé, etc.)
    """
    serializer = IndisponibiliteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Indisponibilité ajoutée avec succès ✅"})
    return Response(serializer.errors, status=400)


@api_view(['GET'])
def get_horaires_salon(request, coiffeuse_id):
    try:
        horaires = TblHoraireCoiffeuse.objects.filter(salon__coiffeuse__idTblUser=coiffeuse_id)
        serializer = HoraireCoiffeuseSerializer(horaires, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def set_horaire_jour(request):
    """
    Crée ou met à jour l'horaire pour un jour donné.
    Format attendu :
    {
        "salon": 1,
        "jour": 0,  // 0 = Lundi, 6 = Dimanche
        "heure_debut": "08:00",
        "heure_fin": "18:00"
    }
    """
    try:
        data = request.data
        salon_id = data.get("salon")
        jour = data.get("jour")

        if not all([salon_id is not None, jour is not None]):
            return Response({"error": "Champs requis : salon, jour, heure_debut, heure_fin"}, status=400)

        horaire, created = TblHoraireCoiffeuse.objects.update_or_create(
            salon_id=salon_id,
            jour=jour,
            defaults={
                "heure_debut": data["heure_debut"],
                "heure_fin": data["heure_fin"]
            }
        )

        serializer = HoraireCoiffeuseSerializer(horaire)
        return Response({
            "message": "Horaire ajouté ✅" if created else "Horaire mis à jour 🔁",
            "horaire": serializer.data
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['DELETE'])
def delete_horaire_jour(request, salon_id, jour):
    """
    Supprime l’horaire du salon pour un jour donné.
    """
    try:
        horaire = TblHoraireCoiffeuse.objects.filter(salon_id=salon_id, jour=jour).first()
        if not horaire:
            return Response({"error": "Horaire introuvable"}, status=404)

        horaire.delete()
        return Response({"message": f"Horaire supprimé pour le jour {jour}"})

    except Exception as e:
        return Response({"error": str(e)}, status=500)

