################################################################################
#                                                                              #
#             VUES DE L'API POUR LE SYSTÈME DE PROMOTIONS (HAIRBNB)             #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour la gestion  #
#  complète des promotions sur les services. Il permet d'effectuer les         #
#  opérations CRUD (Créer, Lire, Mettre à jour, Supprimer) sur les promotions. #
#                                                                              #
#  Fonctionnalités clés :                                                      #
#    - Création et modification de promotions avec une logique anti-           #
#      chevauchement pour garantir qu'une seule promotion est active à la      #
#      fois pour un service donné dans un salon.                               #
#    - Lister les promotions (actives, à venir, expirées) pour un service.     #
#    - Suppression d'une promotion.                                            #
#    - Vérifications de permissions pour s'assurer que seules les coiffeuses   #
#      autorisées peuvent gérer les promotions de leurs salons.                #
#                                                                              #
################################################################################

# --- Importations ---
from datetime import datetime

# Utilitaire Django pour créer des objets datetime conscients du fuseau horaire
from django.utils.timezone import make_aware

# Importations des modules personnalisés de l'application
from hairbnb.promotion.business_logique import PromotionManager
from hairbnb.promotion.promotion_serializers import PromotionUpdateSerializer
from hairbnb.salon_services.salon_services_business_logic import ServiceData
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decorators.decorators import firebase_authenticated
from hairbnb.models import TblService, TblSalon, TblPromotion, TblCoiffeuse, TblCoiffeuseSalon


@firebase_authenticated
@api_view(['DELETE'])
def delete_promotion(request, promotion_id):
    """
    Supprime une promotion existante par son ID.
    """
    try:
        # Tente de trouver la promotion par sa clé primaire.
        promotion = TblPromotion.objects.get(idPromotion=promotion_id)
        # Supprime l'objet de la base de données.
        promotion.delete()
        # Renvoie une réponse de succès vide avec le statut 204.
        return Response({'status': 'success', 'message': 'Promotion supprimée.'}, status=status.HTTP_204_NO_CONTENT)
    except TblPromotion.DoesNotExist:
        # Si la promotion n'est pas trouvée, renvoie une erreur 404.
        return Response({'status': 'error', 'message': 'Promotion introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'status': 'error', 'message': f'Erreur: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@firebase_authenticated
@api_view(['GET'])
def get_promotions_for_service(request, service_id):
    """
    Récupère et catégorise toutes les promotions pour un service donné.
    """
    try:
        # Récupère l'objet service.
        service = TblService.objects.get(idTblService=service_id)
        # Instancie le PromotionManager qui va gérer toute la logique de tri.
        promo_mgr = PromotionManager(service)

        # Gère la pagination pour les promotions expirées.
        try:
            page = int(request.GET.get("page") or 1)
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get("page_size") or 5)
        except ValueError:
            page_size = 5

        # Si le client demande spécifiquement les promotions expirées, on les calcule.
        expired_data = {}
        if request.GET.get("expired"):
            expired_data = promo_mgr.get_expired(page=page, page_size=page_size)

        # Construit la réponse en utilisant les méthodes du PromotionManager.
        return Response({
            "status": "success",
            "counts": promo_mgr.get_counts(),
            "active": promo_mgr.get_active(),
            "upcoming": promo_mgr.get_upcoming(),
            "expired": expired_data
        })
    except TblService.DoesNotExist:
        return Response({"status": "error", "message": "Service introuvable"}, status=404)

@firebase_authenticated
@api_view(['POST'])
def create_promotion(request, salon_id, service_id):
    """
    Crée une nouvelle promotion pour un service dans un salon donné.
    """
    try:
        # Instruction de débogage laissée intentionnellement.
        print("📥 Données reçues :", request.data)

        # Récupère et valide l'existence du salon et du service.
        try:
            salon = TblSalon.objects.get(idTblSalon=salon_id)
        except TblSalon.DoesNotExist:
            return Response({"error": "Salon introuvable."}, status=404)
        try:
            service = TblService.objects.get(idTblService=service_id)
        except TblService.DoesNotExist:
            return Response({"error": "Service introuvable."}, status=404)

        # Valide la présence des données nécessaires dans la requête.
        discount_percentage = request.data.get("discount_percentage")
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")
        if not discount_percentage or not end_date_str:
            return Response({"error": "Le pourcentage et la date de fin sont obligatoires."}, status=400)

        # Convertit les dates reçues en objets datetime conscients du fuseau horaire.
        start_date = make_aware(datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d"))
        end_date = make_aware(datetime.strptime(end_date_str.split("T")[0], "%Y-%m-%d"))

        # --- Vérification anti-chevauchement ---
        # Récupère les promotions existantes pour ce service et ce salon.
        existing_promotions = TblPromotion.objects.filter(service=service, salon=salon)
        # Filtre pour ne garder que celles dont les dates chevauchent la nouvelle promotion.
        overlapping_promotions = existing_promotions.filter(start_date__lte=end_date, end_date__gte=start_date)

        if overlapping_promotions.exists():
            return Response({
                                "error": f"Il existe déjà une promotion active pour ce service dans le salon {salon.nom_salon} durant cette période. Veuillez choisir des dates qui ne chevauchent pas d'autres promotions."},
                            status=400)

        print(
            f"📝 Promotion reçue: {discount_percentage}% | Début: {start_date} | Fin: {end_date} | Salon: {salon.nom_salon}")

        # Crée la nouvelle promotion en base de données.
        promotion = TblPromotion.objects.create(salon=salon, service=service,
                                                discount_percentage=float(discount_percentage), start_date=start_date,
                                                end_date=end_date)

        # Prépare une réponse détaillée.
        service_data = ServiceData(service).to_dict()
        return Response({
            "message": f"Promotion créée avec succès pour le salon {salon.nom_salon}.",
            "service": service_data,
            "promotion": {"id": promotion.idPromotion, "salon_id": salon.idTblSalon, "salon_nom": salon.nom_salon,
                          "discount_percentage": promotion.discount_percentage,
                          "start_date": promotion.start_date.isoformat(), "end_date": promotion.end_date.isoformat(),
                          "is_active": promotion.is_active()}
        }, status=201)
    except Exception as e:
        print("❌ Erreur interne:", str(e))
        return Response({"error": str(e)}, status=500)


@firebase_authenticated
@api_view(['PUT', 'PATCH'])
def update_promotion(request, salon_id, service_id, promotion_id):
    """
    Met à jour une promotion existante après avoir vérifié les permissions.
    """
    try:
        # --- Étape 1 : Vérification des permissions de l'utilisateur ---
        user = request.user
        try:
            coiffeuse = TblCoiffeuse.objects.get(idTblUser=user.idTblUser)
        except TblCoiffeuse.DoesNotExist:
            return Response({"detail": "Utilisateur non autorisé (pas une coiffeuse)."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            salon = TblSalon.objects.get(idTblSalon=salon_id)
        except TblSalon.DoesNotExist:
            return Response({"error": "Salon introuvable."}, status=404)

        # Vérifie que la coiffeuse connectée travaille bien dans ce salon.
        if not TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse, salon=salon).exists():
            return Response({"detail": "Accès interdit à ce salon."}, status=status.HTTP_403_FORBIDDEN)

        try:
            service = TblService.objects.get(idTblService=service_id)
        except TblService.DoesNotExist:
            return Response({"error": "Service introuvable."}, status=404)

        # Vérifie que la promotion à modifier appartient bien au bon service et salon.
        try:
            promotion = TblPromotion.objects.get(idPromotion=promotion_id, salon=salon, service=service)
        except TblPromotion.DoesNotExist:
            return Response({"error": "Promotion introuvable pour ce salon et ce service."}, status=404)

        print(
            f"📝 Modification promotion #{promotion_id}\n   Salon: {salon.nom_salon}\n   Service: {service.intitule_service}\n   Utilisateur: {user.nom} {user.prenom}\n   Données reçues: {request.data}")

        # --- Étape 2 : Validation des nouvelles données ---
        serializer = PromotionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "Données invalides", "details": serializer.errors}, status=400)

        validated_data = serializer.validated_data
        start_date, end_date = validated_data['start_date'], validated_data['end_date']

        # --- Étape 3 : Vérification anti-chevauchement ---
        # Recherche les promotions qui chevauchent les nouvelles dates,
        # en excluant la promotion actuelle de la recherche.
        overlapping_promotions = TblPromotion.objects.filter(service=service, salon=salon, start_date__lte=end_date,
                                                             end_date__gte=start_date).exclude(
            idPromotion=promotion.idPromotion)
        if overlapping_promotions.exists():
            existing_promo = overlapping_promotions.first()
            return Response({
                                "error": f"Cette période chevauche avec une promotion existante ({existing_promo.start_date.strftime('%d/%m/%Y')} - {existing_promo.end_date.strftime('%d/%m/%Y')}). Veuillez choisir des dates différentes."},
                            status=400)

        # --- Étape 4 : Mise à jour de la promotion ---
        promotion.discount_percentage, promotion.start_date, promotion.end_date = validated_data['discount_percentage'], \
        validated_data['start_date'], validated_data['end_date']
        promotion.save()

        print(
            f"✅ Promotion modifiée avec succès:\n   Nouveau pourcentage: {promotion.discount_percentage}%\n   Nouvelles dates: {promotion.start_date.strftime('%Y-%m-%d')} → {promotion.end_date.strftime('%Y-%m-%d')}")

        # --- Étape 5 : Retourner la réponse ---
        return Response({
            "message": f"Promotion modifiée avec succès pour le salon {salon.nom_salon}.",
            "promotion": {"idPromotion": promotion.idPromotion, "salon_id": salon.idTblSalon,
                          "salon_nom": salon.nom_salon, "service_id": service.idTblService,
                          "service_nom": service.intitule_service,
                          "discount_percentage": float(promotion.discount_percentage),
                          "start_date": promotion.start_date.strftime('%Y-%m-%d'),
                          "end_date": promotion.end_date.strftime('%Y-%m-%d'), "is_active": promotion.is_active()}
        }, status=200)
    except Exception as e:
        print(f"❌ Erreur interne lors de la modification: {str(e)}")
        return Response({"error": str(e)}, status=500)










# from datetime import datetime
#
# from django.utils.timezone import make_aware
# from hairbnb.promotion.business_logique import PromotionManager
# from hairbnb.promotion.promotion_serializers import PromotionUpdateSerializer
# from hairbnb.salon_services.salon_services_business_logic import ServiceData
#
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from decorators.decorators import firebase_authenticated
# from hairbnb.models import TblService, TblSalon, TblPromotion, TblCoiffeuse, TblCoiffeuseSalon
#
#
# @api_view(['DELETE'])
# def delete_promotion(request, promotion_id):
#     try:
#         promotion = TblPromotion.objects.get(idPromotion=promotion_id)
#         promotion.delete()
#         return Response({'status': 'success', 'message': 'Promotion supprimée.'}, status=status.HTTP_204_NO_CONTENT)
#     except TblPromotion.DoesNotExist:
#         return Response({'status': 'error', 'message': 'Promotion introuvable.'}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({'status': 'error', 'message': f'Erreur: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @api_view(['GET'])
# def get_promotions_for_service(request, service_id):
#     try:
#         service = TblService.objects.get(idTblService=service_id)
#         promo_mgr = PromotionManager(service)
#
#         # Récupérer pagination depuis la query string
#         try:
#             page = int(request.GET.get("page") or 1)
#         except ValueError:
#             page = 1
#
#         try:
#             page_size = int(request.GET.get("page_size") or 5)
#         except ValueError:
#             page_size = 5
#
#         # S'il demande les expirées
#         expired_data = {}
#         if request.GET.get("expired"):
#             expired_data = promo_mgr.get_expired(page=page, page_size=page_size)
#
#         return Response({
#             "status": "success",
#             "counts": promo_mgr.get_counts(),
#             "active": promo_mgr.get_active(),
#             "upcoming": promo_mgr.get_upcoming(),
#             "expired": expired_data
#         })
#
#     except TblService.DoesNotExist:
#         return Response({"status": "error", "message": "Service introuvable"}, status=404)
#
# #@firebase_authenticated
# @api_view(['POST'])
# def create_promotion(request, salon_id, service_id):
#     try:
#         print("📥 Données reçues :", request.data)
#
#         # Récupérer le salon et le service
#         try:
#             salon = TblSalon.objects.get(idTblSalon=salon_id)
#         except TblSalon.DoesNotExist:
#             return Response({"error": "Salon introuvable."}, status=404)
#
#         try:
#             service = TblService.objects.get(idTblService=service_id)
#         except TblService.DoesNotExist:
#             return Response({"error": "Service introuvable."}, status=404)
#
#         # Récupérer les données de la nouvelle promotion
#         discount_percentage = request.data.get("discount_percentage")
#         start_date_str = request.data.get("start_date")
#         end_date_str = request.data.get("end_date")
#
#         # Vérifier que les champs sont bien remplis
#         if not discount_percentage or not end_date_str:
#             return Response({
#                 "error": "Le pourcentage et la date de fin sont obligatoires."
#             }, status=400)
#
#         # Conversion des dates
#         start_date = make_aware(datetime.strptime(start_date_str.split("T")[0], "%Y-%m-%d"))
#         end_date = make_aware(datetime.strptime(end_date_str.split("T")[0], "%Y-%m-%d"))
#
#         # 🔥 MISE À JOUR : Vérifier s'il existe déjà une promotion qui chevauche cette période
#         # pour ce service ET ce salon spécifiquement
#         existing_promotions = TblPromotion.objects.filter(
#             service=service,
#             salon=salon  # 🔥 NOUVEAU : Filtrer aussi par salon
#         )
#
#         # Une promotion chevauche si:
#         # - Sa date de début est <= à la date de fin de la nouvelle promo ET
#         # - Sa date de fin est >= à la date de début de la nouvelle promo
#         overlapping_promotions = existing_promotions.filter(
#             start_date__lte=end_date,
#             end_date__gte=start_date
#         )
#
#         if overlapping_promotions.exists():
#             return Response({
#                 "error": f"Il existe déjà une promotion active pour ce service dans le salon {salon.nom_salon} durant cette période. Veuillez choisir des dates qui ne chevauchent pas d'autres promotions."
#             }, status=400)
#
#         print(
#             f"📝 Promotion reçue: {discount_percentage}% | Début: {start_date} | Fin: {end_date} | Salon: {salon.nom_salon}")
#
#         # 🔥 MISE À JOUR : Créer la promotion avec le salon
#         promotion = TblPromotion.objects.create(
#             salon=salon,  # 🔥 NOUVEAU : Ajouter le salon
#             service=service,
#             discount_percentage=float(discount_percentage),
#             start_date=start_date,
#             end_date=end_date
#         )
#
#         # Récupérer les données du service pour la réponse
#         service_data = ServiceData(service).to_dict()
#
#         return Response({
#             "message": f"Promotion créée avec succès pour le salon {salon.nom_salon}.",
#             "service": service_data,
#             "promotion": {
#                 "id": promotion.idPromotion,
#                 "salon_id": salon.idTblSalon,
#                 "salon_nom": salon.nom_salon,
#                 "discount_percentage": promotion.discount_percentage,
#                 "start_date": promotion.start_date.isoformat(),
#                 "end_date": promotion.end_date.isoformat(),
#                 "is_active": promotion.is_active()
#             }
#         }, status=201)
#
#     except Exception as e:
#         print("❌ Erreur interne:", str(e))
#         return Response({"error": str(e)}, status=500)
#
#
# @firebase_authenticated
# @api_view(['PUT', 'PATCH'])
# def update_promotion(request, salon_id, service_id, promotion_id):
#     """
#     Met à jour une promotion existante.
#
#     URL: PUT /api/salon/{salon_id}/service/{service_id}/promotion/{promotion_id}/
#
#     Body (JSON):
#         {
#             "discount_percentage": 25.0,
#             "start_date": "2025-06-15",
#             "end_date": "2025-06-25"
#         }
#     """
#     try:
#         # 🔐 Vérification manuelle de l'accès au salon (complément aux décorateurs)
#         user = request.user
#
#         # Vérifier que l'utilisateur est une coiffeuse
#         try:
#             coiffeuse = TblCoiffeuse.objects.get(idTblUser=user.idTblUser)
#         except TblCoiffeuse.DoesNotExist:
#             return Response({
#                 "detail": "Utilisateur non autorisé (pas une coiffeuse)."
#             }, status=status.HTTP_403_FORBIDDEN)
#
#         # Vérifier que le salon existe
#         try:
#             salon = TblSalon.objects.get(idTblSalon=salon_id)
#         except TblSalon.DoesNotExist:
#             return Response({"error": "Salon introuvable."}, status=404)
#
#         # Vérifier que la coiffeuse a accès à ce salon
#         salon_access = TblCoiffeuseSalon.objects.filter(
#             coiffeuse=coiffeuse,
#             salon=salon
#         ).exists()
#
#         if not salon_access:
#             return Response({
#                 "detail": "Accès interdit à ce salon."
#             }, status=status.HTTP_403_FORBIDDEN)
#
#         # Vérifier que le service existe
#         try:
#             service = TblService.objects.get(idTblService=service_id)
#         except TblService.DoesNotExist:
#             return Response({"error": "Service introuvable."}, status=404)
#
#         # Vérifier que la promotion existe et appartient à ce salon/service
#         try:
#             promotion = TblPromotion.objects.get(
#                 idPromotion=promotion_id,
#                 salon=salon,
#                 service=service
#             )
#         except TblPromotion.DoesNotExist:
#             return Response({
#                 "error": "Promotion introuvable pour ce salon et ce service."
#             }, status=404)
#
#         print(f"📝 Modification promotion #{promotion_id}")
#         print(f"   Salon: {salon.nom_salon}")
#         print(f"   Service: {service.intitule_service}")
#         print(f"   Utilisateur: {user.nom} {user.prenom}")
#         print(f"   Données reçues: {request.data}")
#
#         # Valider les données avec le serializer
#         serializer = PromotionUpdateSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({
#                 "error": "Données invalides",
#                 "details": serializer.errors
#             }, status=400)
#
#         validated_data = serializer.validated_data
#
#         # Vérifier les chevauchements avec d'autres promotions
#         start_date = validated_data['start_date']
#         end_date = validated_data['end_date']
#
#         overlapping_promotions = TblPromotion.objects.filter(
#             service=service,
#             salon=salon,
#             start_date__lte=end_date,
#             end_date__gte=start_date
#         ).exclude(idPromotion=promotion.idPromotion)
#
#         if overlapping_promotions.exists():
#             existing_promo = overlapping_promotions.first()
#             return Response({
#                 "error": f"Cette période chevauche avec une promotion existante "
#                          f"({existing_promo.start_date.strftime('%d/%m/%Y')} - "
#                          f"{existing_promo.end_date.strftime('%d/%m/%Y')}). "
#                          f"Veuillez choisir des dates différentes."
#             }, status=400)
#
#         # Mettre à jour la promotion
#         promotion.discount_percentage = validated_data['discount_percentage']
#         promotion.start_date = validated_data['start_date']
#         promotion.end_date = validated_data['end_date']
#         promotion.save()
#
#         print(f"✅ Promotion modifiée avec succès:")
#         print(f"   Nouveau pourcentage: {promotion.discount_percentage}%")
#         print(
#             f"   Nouvelles dates: {promotion.start_date.strftime('%Y-%m-%d')} → {promotion.end_date.strftime('%Y-%m-%d')}")
#
#         # Retourner la promotion mise à jour
#         return Response({
#             "message": f"Promotion modifiée avec succès pour le salon {salon.nom_salon}.",
#             "promotion": {
#                 "idPromotion": promotion.idPromotion,
#                 "salon_id": salon.idTblSalon,
#                 "salon_nom": salon.nom_salon,
#                 "service_id": service.idTblService,
#                 "service_nom": service.intitule_service,
#                 "discount_percentage": float(promotion.discount_percentage),
#                 "start_date": promotion.start_date.strftime('%Y-%m-%d'),
#                 "end_date": promotion.end_date.strftime('%Y-%m-%d'),
#                 "is_active": promotion.is_active()
#             }
#         }, status=200)
#
#     except Exception as e:
#         print(f"❌ Erreur interne lors de la modification: {str(e)}")
#         return Response({"error": str(e)}, status=500)