################################################################################
#                                                                              #
#         VUES API POUR LA GESTION DES SALONS (CÔTÉ COIFFEUSE)                  #
#                                                                              #
#  Ce fichier contient les points d'accès (vues) de l'API permettant à une     #
#  coiffeuse de gérer son salon.                                               #
#                                                                              #
#  Fonctionnalités incluses :                                                  #
#    - `get_salon_by_coiffeuse`: Récupère le salon dont une coiffeuse est        #
#      actuellement la propriétaire.                                           #
#    - `ajout_salon`: Permet à une coiffeuse authentifiée de créer un nouveau  #
#      salon, en gérant la validation des données et la création des objets    #
#      liés en base de données.                                                #
#                                                                              #
################################################################################


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from decorators.decorators import firebase_authenticated
from hairbnb.models import TblCoiffeuse, TblCoiffeuseSalon
import logging
from hairbnb.salon.salon_serializers import TblSalonSerializer, SalonCreateSerializer
from hairbnb_backend import settings_test_secure

# Configuration du logger pour ce fichier.
logger = logging.getLogger(__name__)


################################################################################
#           VUE POUR RÉCUPÉRER LE SALON APPARTENANT À UNE COIFFEUSE            #
################################################################################

@firebase_authenticated
def get_salon_by_coiffeuse(request, coiffeuse_id):
    """
    Récupère le salon dont une coiffeuse spécifique est la propriétaire.
    Cette vue est une vue Django standard retournant une JsonResponse.
    """
    try:
        # Étape 1 : Vérifier que la coiffeuse demandée existe.
        coiffeuse = TblCoiffeuse.objects.get(idTblUser_id=coiffeuse_id)

        # Étape 2 : Chercher la relation dans la table de liaison `TblCoiffeuseSalon`
        # où la coiffeuse est marquée comme propriétaire. `.first()` est utilisé car
        # on suppose qu'une coiffeuse ne peut être propriétaire que d'un seul salon.
        relation = TblCoiffeuseSalon.objects.filter(
            coiffeuse=coiffeuse,
            est_proprietaire=True
        ).first()

        # Étape 3 : Si aucune relation de propriété n'est trouvée.
        if not relation:
            return JsonResponse({
                'exists': False,
                'message': "Cette coiffeuse n'est propriétaire d'aucun salon"
            }, status=404)

        # Étape 4 : Si une relation est trouvée, extraire l'objet salon.
        salon = relation.salon

        # Étape 5 : Utiliser le serializer pour formater les données du salon en JSON.
        serializer = TblSalonSerializer(salon, context={'request': request})

        # Étape 6 : Retourner une réponse positive avec les données du salon.
        return JsonResponse({
            'exists': True,
            'salon': serializer.data
        })

    # Gestion de l'erreur si la coiffeuse n'est pas trouvée en base de données.
    except TblCoiffeuse.DoesNotExist:
        logger.warning(f"Coiffeuse avec ID {coiffeuse_id} introuvable")
        return JsonResponse({
            'exists': False,
            'message': "Coiffeuse introuvable"
        }, status=404)

    # Gestion de toute autre erreur serveur inattendue.
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du salon pour la coiffeuse {coiffeuse_id}: {str(e)}",
                     exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


################################################################################
#                   VUE API POUR LA CRÉATION D'UN SALON                        #
################################################################################

# @api_view(['POST']) : Définit cette fonction comme une vue DRF qui n'accepte que les requêtes POST.
# @firebase_authenticated : Décorateur personnalisé pour vérifier l'authentification Firebase de l'utilisateur.
@api_view(['POST'])
@firebase_authenticated
def ajout_salon(request):
    """
    Crée un nouveau salon pour la coiffeuse authentifiée.
    Cette vue s'appuie sur `SalonCreateSerializer` pour valider les données et
    créer les objets en base de données de manière transactionnelle et sécurisée.
    """
    try:
        # Étape 1 : Récupération de l'ID utilisateur depuis le corps de la requête.
        # Bien que le serializer le valide aussi, une vérification précoce renvoie une erreur claire.
        user_id = request.data.get('idTblUser')
        if not user_id:
            return Response({
                "status": "error",
                "message": "Le champ idTblUser est obligatoire"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Étape 2 : Préparation du dictionnaire de données pour le serializer.
        # `coiffeuse_id` est le champ attendu par `SalonCreateSerializer`.
        data = {
            "coiffeuse_id": user_id,
            "nom_salon": request.data.get('nom_salon'),
            "slogan": request.data.get('slogan'),
            "a_propos": request.data.get('a_propos'),
            "position": request.data.get('position'),
            "numero_tva": request.data.get('numero_tva'),
            "adresse": request.data.get('adresse')
        }

        # Étape 3 : Ajout du fichier image (logo) s'il est présent dans la requête.
        if 'logo_salon' in request.FILES:
            data['logo_salon'] = request.FILES['logo_salon']

        # Étape 4 : Instanciation du serializer avec les données reçues.
        serializer = SalonCreateSerializer(data=data, context={'request': request})

        # Étape 5 : Validation des données par le serializer.
        if serializer.is_valid():
            # `.save()` appelle la méthode `create` personnalisée du serializer,
            # qui gère la création du salon ET de la relation propriétaire.
            salon = serializer.save()

            # Étape 6 : Retourner une réponse de succès avec les données complètes du salon créé.
            return Response({
                "status": "success",
                "message": "Salon créé avec succès",
                "salon_id": salon.idTblSalon,
                "salon_data": serializer.to_representation(salon)
            }, status=status.HTTP_201_CREATED)

        # Si la validation échoue, retourner les erreurs détaillées fournies par le serializer.
        return Response({
            "status": "error",
            "message": "Données invalides",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # Gestion de toute autre erreur serveur inattendue lors du processus.
    except Exception as e:
        logger.error(f"Erreur serveur lors de la création du salon : {str(e)}", exc_info=True)
        return Response({
            "status": "error",
            "message": "Erreur serveur lors de la création du salon",
            # Affiche les détails de l'erreur uniquement en mode DEBUG.
            "details": str(e) if settings_test_secure.DEBUG else "Contactez l'administrateur"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
#
# from decorators.decorators import firebase_authenticated
# from hairbnb.models import TblCoiffeuse,TblCoiffeuseSalon
# import logging
# from hairbnb.salon.salon_serializers import TblSalonSerializer, SalonCreateSerializer
# from hairbnb_backend import settings_test_old, settings_test
#
# # Configurer le logger
# logger = logging.getLogger(__name__)
#
#
# @csrf_exempt
# def get_salon_by_coiffeuse(request, coiffeuse_id):
#     """
#     Récupère le salon d'une coiffeuse (salon où elle est propriétaire)
#     """
#     try:
#         # Vérifier que la coiffeuse existe
#         coiffeuse = TblCoiffeuse.objects.get(idTblUser_id=coiffeuse_id)
#
#         # Récupérer le(s) salon(s) dont cette coiffeuse est propriétaire via la table de jonction
#         relation = TblCoiffeuseSalon.objects.filter(
#             coiffeuse=coiffeuse,
#             est_proprietaire=True
#         ).first()
#
#         if not relation:
#             return JsonResponse({
#                 'exists': False,
#                 'message': "Cette coiffeuse n'est propriétaire d'aucun salon"
#             }, status=404)
#
#         # Récupérer le salon depuis la relation
#         salon = relation.salon
#
#         # Utiliser le sérialiseur pour formater les données
#         serializer = TblSalonSerializer(salon, context={'request': request})
#
#         return JsonResponse({
#             'exists': True,
#             'salon': serializer.data
#         })
#
#     except TblCoiffeuse.DoesNotExist:
#         logger.warning(f"Coiffeuse avec ID {coiffeuse_id} introuvable")
#         return JsonResponse({
#             'exists': False,
#             'message': "Coiffeuse introuvable"
#         }, status=404)
#
#     except Exception as e:
#         logger.error(f"Erreur lors de la récupération du salon pour la coiffeuse {coiffeuse_id}: {str(e)}",
#                      exc_info=True)
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         }, status=500)
#
#
# @api_view(['POST'])
# @firebase_authenticated
# def ajout_salon(request):
#     """
#     Crée un salon pour une coiffeuse.
#     Utilise SalonCreateSerializer pour une gestion complète et sécurisée.
#
#     TOUS LES CHAMPS SONT OBLIGATOIRES :
#     - idTblUser, nom_salon, slogan, logo_salon, a_propos, position, numero_tva, adresse
#
#     Renvoie : salon_id et données complètes du salon créé
#     """
#     try:
#         # 🔥 Récupération de l'ID utilisateur (obligatoire)
#         user_id = request.data.get('idTblUser')
#         if not user_id:
#             return Response({
#                 "status": "error",
#                 "message": "Le champ idTblUser est obligatoire"
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#         # 📦 Préparation des données pour le serializer
#         # Le serializer gère toutes les validations (champs requis, existance coiffeuse, etc.)
#         data = {
#             "coiffeuse_id": user_id,  # ✅ Mapping vers le champ attendu par le serializer
#             "nom_salon": request.data.get('nom_salon'),
#             "slogan": request.data.get('slogan'),
#             "a_propos": request.data.get('a_propos'),
#             "position": request.data.get('position'),
#             "numero_tva": request.data.get('numero_tva'),
#             "adresse": request.data.get('adresse')  # ID de l'adresse si fournie
#         }
#
#         # 🖼️ Gestion du fichier logo (si présent)
#         if 'logo_salon' in request.FILES:
#             data['logo_salon'] = request.FILES['logo_salon']
#
#         # 🚀 Utilisation du serializer spécialisé pour la création
#         serializer = SalonCreateSerializer(data=data, context={'request': request})
#
#         if serializer.is_valid():
#             # ✅ Le serializer gère automatiquement :
#             # - La création du salon
#             # - La création de la relation propriétaire dans TblCoiffeuseSalon
#             # - Toutes les validations nécessaires
#             salon = serializer.save()
#
#             return Response({
#                 "status": "success",
#                 "message": "Salon créé avec succès",
#                 "salon_id": salon.idTblSalon,
#                 "salon_data": serializer.to_representation(salon)  # ✅ Données complètes du salon
#             }, status=status.HTTP_201_CREATED)
#
#         # ❌ Erreurs de validation détaillées
#         return Response({
#             "status": "error",
#             "message": "Données invalides",
#             "errors": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)
#
#     except Exception as e:
#         print(f"🔥 Erreur lors de la création du salon : {str(e)}")
#         return Response({
#             "status": "error",
#             "message": "Erreur serveur lors de la création du salon",
#             "details": str(e) if settings_test.DEBUG else "Contactez l'administrateur"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
