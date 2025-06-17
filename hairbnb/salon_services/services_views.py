################################################################################
#                                                                              #
#         VUES API POUR LA GESTION DU CATALOGUE GLOBAL DES SERVICES            #
#                                                                              #
#  Ce fichier contient les vues (endpoints) dédiées à la gestion du catalogue #
#  global des services de l'application. Ces vues permettent d'interagir avec #
#  la liste complète des services, indépendamment des salons individuels.     #
#                                                                              #
#  Fonctionnalités :                                                           #
#    - `get_all_services`: Récupère la liste de tous les services disponibles. #
#    - `create_new_global_service`: Crée un service qui n'existe pas encore    #
#      dans le catalogue et l'associe immédiatement au salon de l'utilisateur. #
#                                                                              #
################################################################################


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from decorators.decorators import firebase_authenticated, is_owner
from hairbnb.models import (
    TblUser, TblCoiffeuse, TblService, TblSalonService,
    TblPrix, TblTemps, TblServicePrix, TblServiceTemps, TblCoiffeuseSalon, TblCategorie
)
from hairbnb.salon_services.salon_services_serializers import (
    ServiceResponseSerializer, ServiceCreateSerializer
)


################################################################################
#                   VUE POUR LISTER TOUS LES SERVICES GLOBAUX                  #
################################################################################

@api_view(['GET'])
def get_all_services(request):
    """
    Récupère une liste complète de tous les services disponibles dans le
    catalogue global de l'application.
    """
    try:
        # Étape 1 : Récupérer tous les objets Service de la base de données.
        services = TblService.objects.all()

        # Étape 2 : Utiliser le serializer pour formater la liste d'objets en JSON.
        # `many=True` indique au serializer qu'il traite une liste d'objets.
        serializer = ServiceResponseSerializer(services, many=True)

        # Étape 3 : Retourner la réponse avec les données formatées.
        return Response({
            "status": "success",
            "message": "Services récupérés avec succès",
            "services": serializer.data,
            "count": services.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion des erreurs serveur inattendues.
        return Response({
            "status": "error",
            "message": f"Erreur lors de la récupération des services: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


################################################################################
#        VUE POUR CRÉER UN NOUVEAU SERVICE GLOBAL ET L'ASSOCIER À UN SALON     #
################################################################################

@api_view(['POST'])
@firebase_authenticated
@is_owner(param_name="userId")
def create_new_global_service(request):
    """
    Crée un service entièrement nouveau dans le catalogue global, et l'associe
    immédiatement au salon de la coiffeuse propriétaire qui effectue l'action.
    Cette vue doit être utilisée uniquement si le service n'existe pas déjà.
    """
    # Étape 1 : Validation des données d'entrée brutes via le serializer.
    serializer = ServiceCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            "status": "error",
            "message": "Données invalides",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    try:
        # Étape 2 : Extraction des données validées.
        validated_data = serializer.validated_data
        user_id = validated_data['userId']
        service_name = validated_data['intitule_service']
        service_description = validated_data['description']
        prix = validated_data['prix']
        temps_minutes = validated_data['temps_minutes']
        categorie_id = validated_data['categorie_id']

        # Étape 3 : Récupération des objets liés (Catégorie, Utilisateur, Salon).
        try:
            categorie = TblCategorie.objects.get(idTblCategorie=categorie_id)
        except TblCategorie.DoesNotExist:
            return Response({"status": "error", "message": "Catégorie non trouvée"}, status=status.HTTP_404_NOT_FOUND)

        user = TblUser.objects.get(idTblUser=user_id)
        if user.type_ref.libelle != 'Coiffeuse':
            return Response({"status": "error", "message": "L'utilisateur n'est pas une coiffeuse"},
                            status=status.HTTP_403_FORBIDDEN)

        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        coiffeuse_salon = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse, est_proprietaire=True).first()
        if not coiffeuse_salon:
            return Response({"status": "error", "message": "Vous n'êtes pas propriétaire d'un salon"},
                            status=status.HTTP_404_NOT_FOUND)
        salon = coiffeuse_salon.salon

        # Étape 4 : Vérification de l'unicité du nom du service pour éviter les doublons.
        if TblService.objects.filter(intitule_service__iexact=service_name).exists():
            return Response({
                "status": "error",
                "message": f"Un service nommé '{service_name}' existe déjà. Utilisez plutôt 'Ajouter un service existant'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Étape 5 : Création du nouvel objet Service dans la base de données.
        service = TblService.objects.create(
            intitule_service=service_name,
            description=service_description,
            categorie=categorie
        )

        # Étape 6 : Création des objets Prix et Temps.
        prix_obj, _ = TblPrix.objects.get_or_create(prix=prix)
        temps_obj, _ = TblTemps.objects.get_or_create(minutes=temps_minutes)

        # Étape 7 : Création des liaisons entre le service, le salon, le prix et le temps.
        # Associe le service au salon.
        TblSalonService.objects.create(salon=salon, service=service)
        # Crée le prix spécifique pour ce service dans ce salon.
        TblServicePrix.objects.create(service=service, prix=prix_obj, salon=salon)
        # Crée la durée spécifique pour ce service dans ce salon.
        TblServiceTemps.objects.create(service=service, temps=temps_obj, salon=salon)

        # Étape 8 : Construction de la réponse de succès.
        return Response({
            "status": "success",
            "message": "Nouveau service créé et ajouté au salon avec succès",
            "service": ServiceResponseSerializer(service).data,
            "salon_id": salon.idTblSalon,
            "is_new_service": True  # Un drapeau utile pour le client.
        }, status=status.HTTP_201_CREATED)

    # Gestion des erreurs spécifiques et génériques.
    except TblUser.DoesNotExist:
        return Response({"status": "error", "message": "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"status": "error", "message": f"Erreur inattendue: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# # services_views.py - Nouvelles vues pour gérer la logique correcte des services
#
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
#
# from decorators.decorators import firebase_authenticated, is_owner
# from hairbnb.models import (
#     TblUser, TblCoiffeuse, TblService, TblSalonService,
#     TblPrix, TblTemps, TblServicePrix, TblServiceTemps, TblCoiffeuseSalon, TblCategorie
# )
# from hairbnb.salon_services.salon_services_serializers import (
#     ServiceResponseSerializer, ServiceCreateSerializer
# )
#
#
# @api_view(['GET'])
# def get_all_services(request):
#     """
#     Récupère tous les services globaux existants avec leurs prix/durées moyens.
#     """
#     try:
#         services = TblService.objects.all()
#         serializer = ServiceResponseSerializer(services, many=True)
#
#         return Response({
#             "status": "success",
#             "message": "Services récupérés avec succès",
#             "services": serializer.data,
#             "count": services.count()
#         }, status=status.HTTP_200_OK)
#
#     except Exception as e:
#         return Response({
#             "status": "error",
#             "message": f"Erreur lors de la récupération des services: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @api_view(['POST'])
# @firebase_authenticated
# @is_owner(param_name="userId")
# def create_new_global_service(request):
#     """
#     Crée un nouveau service global ET l'associe au salon de la coiffeuse.
#     Body attendu:
#     {
#         "userId": int,
#         "intitule_service": str,
#         "description": str,
#         "prix": float,
#         "temps_minutes": int,
#         "categorie_id": int (obligatoire)
#     }
#     """
#     serializer = ServiceCreateSerializer(data=request.data)
#     if not serializer.is_valid():
#         return Response({
#             "status": "error",
#             "message": "Données invalides",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         # Extraire les données validées
#         user_id = serializer.validated_data['userId']
#         service_name = serializer.validated_data['intitule_service']
#         service_description = serializer.validated_data['description']
#         prix = serializer.validated_data['prix']
#         temps_minutes = serializer.validated_data['temps_minutes']
#         categorie_id = serializer.validated_data['categorie_id']  # ✅ AJOUTÉ
#
#         # ✅ Récupérer la catégorie
#         try:
#             categorie = TblCategorie.objects.get(idTblCategorie=categorie_id)
#         except TblCategorie.DoesNotExist:
#             return Response({
#                 "status": "error",
#                 "message": "Catégorie non trouvée"
#             }, status=status.HTTP_404_NOT_FOUND)
#
#         # Récupérer l'utilisateur et vérifier qu'il est une coiffeuse
#         user = TblUser.objects.get(idTblUser=user_id)
#         if user.type_ref.libelle != 'Coiffeuse':
#             return Response({
#                 "status": "error",
#                 "message": "L'utilisateur n'est pas une coiffeuse"
#             }, status=status.HTTP_403_FORBIDDEN)
#         # Récupérer la coiffeuse et son salon
#         coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
#         coiffeuse_salon = TblCoiffeuseSalon.objects.filter(
#             coiffeuse=coiffeuse,
#             est_proprietaire=True
#         ).first()
#         if not coiffeuse_salon:
#             return Response({
#                 "status": "error",
#                 "message": "Vous n'êtes pas propriétaire d'un salon"
#             }, status=status.HTTP_404_NOT_FOUND)
#         salon = coiffeuse_salon.salon
#
#         # Vérifier si un service avec ce nom existe déjà
#         if TblService.objects.filter(intitule_service__iexact=service_name).exists():
#             return Response({
#                 "status": "error",
#                 "message": f"Un service nommé '{service_name}' existe déjà. Utilisez plutôt 'Ajouter un service existant'."
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         # ✅ Créer le nouveau service global AVEC catégorie
#         service = TblService.objects.create(
#             intitule_service=service_name,
#             description=service_description,
#             categorie=categorie
#         )
#
#         # Créer ou récupérer le prix et le temps
#         prix_obj, _ = TblPrix.objects.get_or_create(prix=prix)
#         temps_obj, _ = TblTemps.objects.get_or_create(minutes=temps_minutes)
#
#         # Associer le service au salon
#         salon_service = TblSalonService.objects.create(
#             salon=salon,
#             service=service
#         )
#
#         # Créer les relations prix et temps
#         TblServicePrix.objects.create(
#             service=service,
#             prix=prix_obj,
#             salon=salon
#         )
#         TblServiceTemps.objects.create(
#             service=service,
#             temps=temps_obj,
#             salon=salon
#         )
#
#         return Response({
#             "status": "success",
#             "message": "Nouveau service créé et ajouté au salon avec succès",
#             "service": ServiceResponseSerializer(service).data,
#             "salon_id": salon.idTblSalon,
#             "is_new_service": True
#         }, status=status.HTTP_201_CREATED)
#
#     except TblUser.DoesNotExist:
#         return Response({
#             "status": "error",
#             "message": "Utilisateur non trouvé"
#         }, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({
#             "status": "error",
#             "message": f"Erreur inattendue: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)