################################################################################
#                                                                              #
#        VUE DE L'API POUR LA RÉCUPÉRATION D'INFORMATIONS COIFFEUSES             #
#                                                                              #
#  Ce fichier définit un point d'accès (endpoint) utilitaire de l'API dont le  #
#  rôle est de récupérer des informations essentielles sur plusieurs coiffeuses #
#  en une seule requête.                                                       #
#                                                                              #
#  Il prend en entrée une liste d'identifiants uniques (UUIDs) et retourne     #
#  un ensemble de données minimales pour chaque coiffeuse correspondante,      #
#  en utilisant la classe de logique métier `MinimalCoiffeuseData` pour        #
#  formater la réponse.                                                        #
#                                                                              #
################################################################################

# --- Importations ---
import json
import logging
# Outils de Django et Django REST Framework pour créer la vue et la réponse
from django.http import JsonResponse
from rest_framework.decorators import api_view

from decorators.decorators import firebase_authenticated
# Importations des modules personnalisés de l'application
from hairbnb.coiffeuse.coiffeuse_business_logic import MinimalCoiffeuseData
from hairbnb.models import TblCoiffeuse

# Initialisation du logger pour enregistrer les informations et erreurs
logger = logging.getLogger(__name__)


@api_view(['POST'])
@firebase_authenticated
def get_coiffeuses_info(request):
    """
    Récupère un ensemble de données minimales pour une liste de coiffeuses,
    identifiées par leurs UUIDs d'utilisateur.
    Accepte une requête POST avec un corps JSON contenant une liste d'UUIDs.
    """
    try:
        # --- Étape 1 : Récupérer et valider les données de la requête ---
        # Tente de parser le corps de la requête en tant que JSON.
        data = json.loads(request.body)
        # Extrait la liste des UUIDs. Retourne une liste vide si la clé n'existe pas.
        uuids = data.get("uuids", [])

        # Vérifie si la liste d'UUIDs fournie n'est pas vide.
        if not uuids:
            return JsonResponse({
                "status": "error",
                "message": "Aucun UUID fourni"
            }, status=400)

        # Log des UUIDs reçus pour le débogage.
        logger.info(f"📩 UUIDs reçus : {uuids}")

        # --- Étape 2 : Interroger la base de données ---
        # Effectue une seule requête à la base de données pour récupérer toutes les coiffeuses
        # dont l'UUID de l'utilisateur lié est dans la liste fournie.
        # L'utilisation de `__in` est très efficace pour ce type de requête.
        coiffeuses = TblCoiffeuse.objects.filter(idTblUser__uuid__in=uuids)

        # --- Étape 3 : Formater les données pour la réponse ---
        # Utilise la classe de logique métier `MinimalCoiffeuseData` pour transformer
        # chaque objet modèle Django en un dictionnaire propre et structuré.
        coiffeuses_data = [MinimalCoiffeuseData(c).to_dict() for c in coiffeuses]

        # Log un résumé des résultats pour le suivi.
        logger.info(f"🔍 {len(coiffeuses_data)} coiffeuses trouvées sur {len(uuids)} UUIDs demandés")

        # --- Étape 4 : Renvoyer la réponse en cas de succès ---
        return JsonResponse({
            "status": "success",
            "coiffeuses": coiffeuses_data
        })

    # --- Gestion des erreurs ---
    except json.JSONDecodeError:
        # Capture l'erreur si le corps de la requête n'est pas un JSON valide.
        logger.error("❌ Format JSON invalide dans la requête")
        return JsonResponse({
            "status": "error",
            "message": "Format de requête invalide"
        }, status=400)

    except Exception as e:
        # Capture toutes les autres erreurs internes qui pourraient survenir.
        # `exc_info=True` inclut la trace complète de l'erreur dans les logs,
        # ce qui est crucial pour le débogage.
        logger.error(f"❌ Erreur interne : {str(e)}", exc_info=True)

        # Retourne une réponse d'erreur générique au client pour ne pas exposer
        # les détails internes de l'erreur.
        return JsonResponse({
            "status": "error",
            "message": "Erreur interne du serveur"
        }, status=500)









# import json
# import logging
# from django.http import JsonResponse
# from rest_framework.decorators import api_view
# from hairbnb.coiffeuse.coiffeuse_business_logic import MinimalCoiffeuseData
# from hairbnb.models import TblCoiffeuse
#
# logger = logging.getLogger(__name__)
# @api_view(['POST'])
# def get_coiffeuses_info(request):
#     """
#     Récupère les informations des coiffeuses à partir d'une liste d'UUIDs.
#
#     Requête attendue:
#     {
#         "uuids": ["uuid1", "uuid2", ...]
#     }
#     """
#     try:
#         # Récupérer et valider les données de la requête
#         data = json.loads(request.body)
#         uuids = data.get("uuids", [])
#
#         if not uuids:
#             return JsonResponse({
#                 "status": "error",
#                 "message": "Aucun UUID fourni"
#             }, status=400)
#
#         logger.info(f"📩 UUIDs reçus : {uuids}")
#
#         # Récupérer les coiffeuses qui correspondent aux UUIDs
#         coiffeuses = TblCoiffeuse.objects.filter(idTblUser__uuid__in=uuids)
#
#         # Transformer les objets en JSON minimaliste
#         coiffeuses_data = [MinimalCoiffeuseData(c).to_dict() for c in coiffeuses]
#
#         # Log un résumé des résultats (nombre de coiffeuses trouvées)
#         logger.info(f"🔍 {len(coiffeuses_data)} coiffeuses trouvées sur {len(uuids)} UUIDs demandés")
#
#         return JsonResponse({
#             "status": "success",
#             "coiffeuses": coiffeuses_data
#         })
#
#     except json.JSONDecodeError:
#         logger.error("❌ Format JSON invalide dans la requête")
#         return JsonResponse({
#             "status": "error",
#             "message": "Format de requête invalide"
#         }, status=400)
#
#     except Exception as e:
#         # Log l'erreur complète avec la stack trace
#         logger.error(f"❌ Erreur interne : {str(e)}", exc_info=True)
#
#         return JsonResponse({
#             "status": "error",
#             "message": "Erreur interne du serveur"
#         }, status=500)