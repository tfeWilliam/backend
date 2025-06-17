################################################################################
#                                                                              #
#                 VUES DE L'API POUR LE SYSTÈME D'AVIS (HAIRBNB)                #
#                                                                              #
#  Ce fichier définit l'ensemble des points d'accès (endpoints) de l'API pour  #
#  la gestion complète des avis clients. Il gère le cycle de vie d'un avis :   #
#    - Vérification des rendez-vous éligibles à un avis.                       #
#    - Création, modification et suppression sécurisées des avis par leur      #
#      propriétaire.                                                           #
#    - Consultation de l'historique personnel des avis.                        #
#    - Affichage public des avis et des statistiques pour un salon.            #
#                                                                              #
#  La sécurité est assurée par l'authentification Firebase et des décorateurs  #
#  personnalisés comme `@is_owner` pour contrôler les permissions.             #
#                                                                              #
################################################################################

# --- Importations ---
import logging
from datetime import timedelta

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Importations des modules personnalisés de l'application
from decorators.decorators import firebase_authenticated, is_owner
from hairbnb.avis.avis_serializers import RdvEligibleAvisSerializer, AvisCreateSerializer, AvisDetailSerializer, \
    MesAvisSerializer, AvisListSerializer
from hairbnb.models import (
    TblAvis, TblRendezVous, TblClient,
    TblSalon
)

# Initialisation du logger pour enregistrer les erreurs et informations
logger = logging.getLogger(__name__)


# --- 1. VUE POUR RÉCUPÉRER LES RENDEZ-VOUS ÉLIGIBLES À UN AVIS ---
# Le décorateur @api_view définit le type de requête HTTP acceptée (GET).
# Le décorateur @firebase_authenticated s'assure que l'utilisateur est connecté.
@api_view(['GET'])
@firebase_authenticated
def mes_rdv_avis_en_attente(request):
    """
    Récupère la liste des rendez-vous terminés pour le client connecté
    qui sont désormais éligibles pour recevoir un avis.
    """
    try:
        # Récupère l'objet Client correspondant à l'utilisateur Firebase authentifié.
        client = get_object_or_404(TblClient, idTblUser__uuid=request.user.uuid)

        maintenant = timezone.now()

        # Requête pour trouver les RDV terminés du client, en excluant ceux
        # pour lesquels un avis a déjà été soumis.
        rdvs_termines = TblRendezVous.objects.filter(
            client=client,
            statut='terminé'
        ).exclude(
            idRendezVous__in=TblAvis.objects.values_list('rendez_vous__idRendezVous', flat=True)
        )

        # Filtre supplémentaire en Python pour appliquer la règle métier du délai.
        rdvs_eligibles = []
        for rdv in rdvs_termines:
            fin_theorique = rdv.date_heure + timedelta(minutes=rdv.duree_totale or 60)
            # Un RDV est éligible si au moins 2 heures se sont écoulées depuis sa fin.
            if maintenant >= fin_theorique + timedelta(hours=2):
                rdvs_eligibles.append(rdv)

        # Utilise un sérialiseur pour formater les données des RDV éligibles.
        serializer = RdvEligibleAvisSerializer(rdvs_eligibles, many=True)

        return Response({
            "success": True,
            "message": f"{len(rdvs_eligibles)} avis en attente",
            "count": len(rdvs_eligibles),
            "rdv_eligibles": serializer.data
        })

    except TblClient.DoesNotExist:
        return Response({
            "success": False,
            "message": "Client non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Erreur dans mes_rdv_avis_en_attente: {str(e)}")
        return Response({
            "success": False,
            "message": f"Erreur interne: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 2. VUE POUR CRÉER UN AVIS ---
@csrf_exempt
@api_view(['POST'])
@firebase_authenticated
@is_owner(param_name="client_uuid", use_uuid=True)
def creer_avis(request):
    """
    Permet à un client authentifié de poster un nouvel avis pour un
    de ses rendez-vous terminés. La validation est gérée par le sérialiseur.
    """
    try:
        # Ajoute l'UUID de l'utilisateur aux données pour que le décorateur @is_owner puisse le valider.
        request.data['client_uuid'] = request.user.uuid

        # Le 'contexte' est passé au sérialiseur pour lui donner accès à l'objet 'request',
        # ce qui est essentiel pour la validation de la propriété du rendez-vous.
        serializer = AvisCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # La méthode .save() du sérialiseur va appeler sa méthode .create() personnalisée.
            avis = serializer.save()

            # Après la création, on utilise un sérialiseur de détail pour renvoyer l'objet complet.
            response_serializer = AvisDetailSerializer(avis)

            return Response({
                "success": True,
                "message": "Avis créé avec succès !",
                "avis": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            # Si la validation échoue, renvoie les erreurs détaillées.
            return Response({
                "success": False,
                "message": "Erreurs de validation",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Erreur dans creer_avis: {str(e)}")
        return Response({
            "success": False,
            "message": f"Erreur lors de la création de l'avis: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 3. VUE POUR LISTER SES PROPRES AVIS ---
@csrf_exempt
@api_view(['GET'])
@firebase_authenticated
@is_owner(param_name="client_uuid", use_uuid=True)
def mes_avis(request):
    """
    Récupère l'historique de tous les avis postés par le client connecté.
    """
    try:
        # Le décorateur @is_owner vérifie que le client_uuid correspond à l'utilisateur connecté.
        client_uuid = request.query_params.get('client_uuid', request.user.uuid)
        client = get_object_or_404(TblClient, idTblUser__uuid=client_uuid)

        # Récupère tous les avis du client, triés du plus récent au plus ancien.
        avis = TblAvis.objects.filter(client=client).order_by('-date')

        # Logique de pagination simple basée sur les paramètres de la requête.
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size

        avis_paginated = avis[start:end]
        serializer = MesAvisSerializer(avis_paginated, many=True)

        return Response({
            "success": True,
            "message": f"{avis.count()} avis trouvés",
            "avis": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": avis.count(),
                "has_next": end < avis.count()
            }
        })

    except TblClient.DoesNotExist:
        return Response({"success": False, "message": "Client non trouvé"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur dans mes_avis: {str(e)}")
        return Response({"success": False, "message": f"Erreur interne: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 4. VUE POUR MODIFIER UN AVIS ---
@csrf_exempt
@api_view(['PATCH'])
@firebase_authenticated
@is_owner(param_name="avis_id", use_uuid=False)
def modifier_avis(request, avis_id):
    """
    Permet à un client de modifier la note ou le commentaire d'un avis
    qu'il a précédemment posté.
    """
    try:
        # Vérifie que l'utilisateur est bien un client enregistré.
        client = get_object_or_404(TblClient, idTblUser__uuid=request.user.uuid)

        # Récupère l'avis en s'assurant qu'il appartient bien au client connecté.
        avis = get_object_or_404(TblAvis, id=avis_id, client=client)

        # Prépare les données à mettre à jour, en gardant les anciennes valeurs si non fournies.
        data = {
            'note': request.data.get('note', avis.note),
            'commentaire': request.data.get('commentaire', avis.commentaire)
        }

        # Validation simple directement dans la vue.
        if 'note' in request.data:
            if not (1 <= int(data['note']) <= 5):
                return Response({"success": False, "message": "La note doit être entre 1 et 5"}, status=status.HTTP_400_BAD_REQUEST)
        if 'commentaire' in request.data:
            if len(data['commentaire'].strip()) < 10:
                return Response({"success": False, "message": "Le commentaire doit contenir au moins 10 caractères"}, status=status.HTTP_400_BAD_REQUEST)

        # Applique les modifications et sauvegarde l'objet.
        avis.note = data['note']
        avis.commentaire = data['commentaire'].strip()
        avis.save()

        # Retourne l'avis mis à jour et formaté.
        serializer = AvisDetailSerializer(avis)
        return Response({"success": True, "message": "Avis modifié avec succès", "avis": serializer.data})

    except TblAvis.DoesNotExist:
        return Response({"success": False, "message": "Avis non trouvé ou non autorisé"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur dans modifier_avis: {str(e)}")
        return Response({"success": False, "message": f"Erreur lors de la modification: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 5. VUE POUR SUPPRIMER UN AVIS ---
@csrf_exempt
@api_view(['DELETE'])
@firebase_authenticated
@is_owner(param_name="avis_id", use_uuid=False)
def supprimer_avis(request, avis_id):
    """
    Permet à un client de supprimer un de ses propres avis.
    """
    try:
        client = get_object_or_404(TblClient, idTblUser__uuid=request.user.uuid)
        avis = get_object_or_404(TblAvis, id=avis_id, client=client)

        # Sauvegarde quelques informations pour un message de confirmation plus clair.
        rdv_id = avis.rendez_vous.idRendezVous if avis.rendez_vous else None
        salon_nom = avis.salon.nom_salon

        # Suppression de l'objet avis de la base de données.
        avis.delete()

        return Response({"success": True, "message": f"Avis supprimé avec succès (RDV #{rdv_id} - {salon_nom})"})

    except TblAvis.DoesNotExist:
        return Response({"success": False, "message": "Avis non trouvé ou non autorisé"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur dans supprimer_avis: {str(e)}")
        return Response({"success": False, "message": f"Erreur lors de la suppression: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- 6. VUE PUBLIQUE POUR LES AVIS D'UN SALON ---
@api_view(['GET'])
def avis_salon_public(request, salon_id):
    """
    Endpoint public, accessible sans authentification, pour afficher
    les avis et les statistiques d'un salon donné.
    """
    try:
        salon = get_object_or_404(TblSalon, idTblSalon=salon_id)

        # Récupère uniquement les avis dont le statut est 'visible'.
        avis = TblAvis.objects.filter(
            salon=salon,
            statut__code='visible'
        ).order_by('-date')

        # Pagination des résultats.
        page_size = int(request.GET.get('page_size', 10))
        page = int(request.GET.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        avis_paginated = avis[start:end]
        serializer = AvisListSerializer(avis_paginated, many=True)

        # Calcul des statistiques globales sur les avis (moyenne et total).
        stats = avis.aggregate(
            moyenne_notes=Avg('note'),
            total_avis=Count('id')
        )

        # Calcul de la répartition des notes (nombre d'avis pour chaque étoile).
        repartition = {}
        for i in range(1, 6):
            repartition[f'note_{i}'] = avis.filter(note=i).count()

        # Construit la réponse JSON complète.
        return Response({
            "success": True,
            "salon": {
                "id": salon.idTblSalon,
                "nom": salon.nom_salon,
                "logo": salon.logo_salon.url if salon.logo_salon else None
            },
            "avis": serializer.data,
            "statistiques": {**stats, **repartition},
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": avis.count(),
                "has_next": end < avis.count()
            }
        })

    except TblSalon.DoesNotExist:
        return Response({"success": False, "message": "Salon non trouvé"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur dans avis_salon_public: {str(e)}")
        return Response({"success": False, "message": f"Erreur interne: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








# # views.py - Système d'avis avec décorateurs Firebase
#
# import logging
# from datetime import timedelta
#
# from django.db.models import Avg, Count
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
#
# from decorators.decorators import firebase_authenticated, is_owner
# from hairbnb.avis.avis_serializers import RdvEligibleAvisSerializer, AvisCreateSerializer, AvisDetailSerializer, \
#     MesAvisSerializer, AvisListSerializer
# from hairbnb.models import (
#     TblAvis, TblRendezVous, TblClient,
#     TblSalon
# )
#
# logger = logging.getLogger(__name__)
#
#
# # 1️⃣ VIEW POUR RÉCUPÉRER LES RDV ÉLIGIBLES AUX AVIS
# #@csrf_exempt
# @api_view(['GET'])
# @firebase_authenticated
# def mes_rdv_avis_en_attente(request):
#     """
#     Récupère les RDV éligibles aux avis pour le client connecté
#     Utilisé pour afficher la notification "X avis en attente" sur la home page
#     """
#     try:
#         # Récupérer le client depuis l'utilisateur Firebase connecté
#         client = get_object_or_404(TblClient, idTblUser__uuid=request.user.uuid)
#
#         # Calculer la limite de temps (2h après la fin théorique du RDV)
#         maintenant = timezone.now()
#
#         # RDV terminés du client
#         rdvs_termines = TblRendezVous.objects.filter(
#             client=client,
#             statut='terminé'
#         ).exclude(
#             # Exclure ceux qui ont déjà un avis
#             idRendezVous__in=TblAvis.objects.values_list('rendez_vous__idRendezVous', flat=True)
#         )
#
#         # Filtrer ceux éligibles (2h après la fin)
#         rdvs_eligibles = []
#         for rdv in rdvs_termines:
#             fin_theorique = rdv.date_heure + timedelta(minutes=rdv.duree_totale or 60)
#             if maintenant >= fin_theorique + timedelta(hours=2):
#                 rdvs_eligibles.append(rdv)
#
#         # Sérialiser les résultats
#         serializer = RdvEligibleAvisSerializer(rdvs_eligibles, many=True)
#
#         return Response({
#             "success": True,
#             "message": f"{len(rdvs_eligibles)} avis en attente",
#             "count": len(rdvs_eligibles),
#             "rdv_eligibles": serializer.data
#         })
#
#     except TblClient.DoesNotExist:
#         return Response({
#             "success": False,
#             "message": "Client non trouvé"
#         }, status=status.HTTP_404_NOT_FOUND)
#
#     except Exception as e:
#         logger.error(f"Erreur dans mes_rdv_avis_en_attente: {str(e)}")
#         return Response({
#             "success": False,
#             "message": f"Erreur interne: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # 2️⃣ VIEW POUR CRÉER UN AVIS
# @csrf_exempt
# @api_view(['POST'])
# @firebase_authenticated
# @is_owner(param_name="client_uuid", use_uuid=True)
# def creer_avis(request):
#     """
#     Crée un nouvel avis pour un RDV
#     Sécurisé : vérifie que le RDV appartient au client connecté
#     """
#     try:
#         # Le paramètre client_uuid sera vérifié par le décorateur is_owner
#         # On l'ajoute aux données pour que le décorateur puisse le vérifier
#         request.data['client_uuid'] = request.user.uuid
#
#         # Créer le serializer avec le contexte de la requête
#         serializer = AvisCreateSerializer(data=request.data, context={'request': request})
#
#         if serializer.is_valid():
#             avis = serializer.save()
#
#             # Retourner l'avis créé avec tous les détails
#             response_serializer = AvisDetailSerializer(avis)
#
#             return Response({
#                 "success": True,
#                 "message": "Avis créé avec succès !",
#                 "avis": response_serializer.data
#             }, status=status.HTTP_201_CREATED)
#         else:
#             return Response({
#                 "success": False,
#                 "message": "Erreurs de validation",
#                 "errors": serializer.errors
#             }, status=status.HTTP_400_BAD_REQUEST)
#
#     except Exception as e:
#         logger.error(f"Erreur dans creer_avis: {str(e)}")
#         return Response({
#             "success": False,
#             "message": f"Erreur lors de la création de l'avis: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # 3️⃣ VIEW POUR LISTER SES PROPRES AVIS
# @csrf_exempt
# @api_view(['GET'])
# @firebase_authenticated
# @is_owner(param_name="client_uuid", use_uuid=True)
# def mes_avis(request):
#     """
#     Liste tous les avis donnés par le client connecté
#     Historique personnel des avis
#     """
#     try:
#         # Le paramètre client_uuid sera vérifié par le décorateur
#         client_uuid = request.query_params.get('client_uuid', request.user.uuid)
#
#         # Récupérer le client
#         client = get_object_or_404(TblClient, idTblUser__uuid=client_uuid)
#
#         # Récupérer tous les avis du client
#         avis = TblAvis.objects.filter(client=client).order_by('-date')
#
#         # Pagination optionnelle
#         page_size = int(request.query_params.get('page_size', 10))
#         page = int(request.query_params.get('page', 1))
#         start = (page - 1) * page_size
#         end = start + page_size
#
#         avis_paginated = avis[start:end]
#         serializer = MesAvisSerializer(avis_paginated, many=True)
#
#         return Response({
#             "success": True,
#             "message": f"{avis.count()} avis trouvés",
#             "avis": serializer.data,
#             "pagination": {
#                 "page": page,
#                 "page_size": page_size,
#                 "total": avis.count(),
#                 "has_next": end < avis.count()
#             }
#         })
#
#     except TblClient.DoesNotExist:
#         return Response({
#             "success": False,
#             "message": "Client non trouvé"
#         }, status=status.HTTP_404_NOT_FOUND)
#
#     except Exception as e:
#         logger.error(f"Erreur dans mes_avis: {str(e)}")
#         return Response({
#             "success": False,
#             "message": f"Erreur interne: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # 4️⃣ VIEW POUR MODIFIER UN AVIS
# @csrf_exempt
# @api_view(['PATCH'])
# @firebase_authenticated
# @is_owner(param_name="avis_id", use_uuid=False)
# def modifier_avis(request, avis_id):
#     """
#     Modifie un avis existant
#     Seul le propriétaire de l'avis peut le modifier
#     """
#     try:
#         # Récupérer le client connecté
#         client = get_object_or_404(TblClient, idTblUser__uuid=request.user.uuid)
#
#         # Récupérer l'avis et vérifier qu'il appartient au client
#         avis = get_object_or_404(TblAvis, id=avis_id, client=client)
#
#         # Seuls la note et le commentaire peuvent être modifiés
#         data = {
#             'note': request.data.get('note', avis.note),
#             'commentaire': request.data.get('commentaire', avis.commentaire)
#         }
#
#         # Validation basique
#         if 'note' in request.data:
#             if not (1 <= int(data['note']) <= 5):
#                 return Response({
#                     "success": False,
#                     "message": "La note doit être entre 1 et 5"
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#         if 'commentaire' in request.data:
#             if len(data['commentaire'].strip()) < 10:
#                 return Response({
#                     "success": False,
#                     "message": "Le commentaire doit contenir au moins 10 caractères"
#                 }, status=status.HTTP_400_BAD_REQUEST)
#
#         # Mettre à jour l'avis
#         avis.note = data['note']
#         avis.commentaire = data['commentaire'].strip()
#         avis.save()
#
#         # Retourner l'avis modifié
#         serializer = AvisDetailSerializer(avis)
#
#         return Response({
#             "success": True,
#             "message": "Avis modifié avec succès",
#             "avis": serializer.data
#         })
#
#     except TblAvis.DoesNotExist:
#         return Response({
#             "success": False,
#             "message": "Avis non trouvé ou non autorisé"
#         }, status=status.HTTP_404_NOT_FOUND)
#
#     except Exception as e:
#         logger.error(f"Erreur dans modifier_avis: {str(e)}")
#         return Response({
#             "success": False,
#             "message": f"Erreur lors de la modification: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # 5️⃣ VIEW POUR SUPPRIMER UN AVIS
# @csrf_exempt
# @api_view(['DELETE'])
# @firebase_authenticated
# @is_owner(param_name="avis_id", use_uuid=False)
# def supprimer_avis(request, avis_id):
#     """
#     Supprime un avis existant
#     Seul le propriétaire de l'avis peut le supprimer
#     """
#     try:
#         # Récupérer le client connecté
#         client = get_object_or_404(TblClient, idTblUser__uuid=request.user.uuid)
#
#         # Récupérer l'avis et vérifier qu'il appartient au client
#         avis = get_object_or_404(TblAvis, id=avis_id, client=client)
#
#         # Sauvegarder les infos avant suppression
#         rdv_id = avis.rendez_vous.idRendezVous if avis.rendez_vous else None
#         salon_nom = avis.salon.nom_salon
#
#         # Supprimer l'avis
#         avis.delete()
#
#         return Response({
#             "success": True,
#             "message": f"Avis supprimé avec succès (RDV #{rdv_id} - {salon_nom})"
#         })
#
#     except TblAvis.DoesNotExist:
#         return Response({
#             "success": False,
#             "message": "Avis non trouvé ou non autorisé"
#         }, status=status.HTTP_404_NOT_FOUND)
#
#     except Exception as e:
#         logger.error(f"Erreur dans supprimer_avis: {str(e)}")
#         return Response({
#             "success": False,
#             "message": f"Erreur lors de la suppression: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # 6️⃣ VIEW PUBLIQUE POUR LES AVIS D'UN SALON
# @api_view(['GET'])
# def avis_salon_public(request, salon_id):
#     """
#     API publique pour afficher les avis d'un salon
#     Accessible sans authentification
#     """
#     try:
#         salon = get_object_or_404(TblSalon, idTblSalon=salon_id)
#
#         # Récupérer seulement les avis visibles
#         avis = TblAvis.objects.filter(
#             salon=salon,
#             statut__code='visible'
#         ).order_by('-date')
#
#         # Pagination
#         page_size = int(request.GET.get('page_size', 10))
#         page = int(request.GET.get('page', 1))
#         start = (page - 1) * page_size
#         end = start + page_size
#
#         avis_paginated = avis[start:end]
#         serializer = AvisListSerializer(avis_paginated, many=True)
#
#         # Statistiques
#         stats = avis.aggregate(
#             moyenne_notes=Avg('note'),
#             total_avis=Count('id')
#         )
#
#         # Répartition par note
#         repartition = {}
#         for i in range(1, 6):
#             repartition[f'note_{i}'] = avis.filter(note=i).count()
#
#         return Response({
#             "success": True,
#             "salon": {
#                 "id": salon.idTblSalon,
#                 "nom": salon.nom_salon,
#                 "logo": salon.logo_salon.url if salon.logo_salon else None
#             },
#             "avis": serializer.data,
#             "statistiques": {
#                 **stats,
#                 **repartition
#             },
#             "pagination": {
#                 "page": page,
#                 "page_size": page_size,
#                 "total": avis.count(),
#                 "has_next": end < avis.count()
#             }
#         })
#
#     except TblSalon.DoesNotExist:
#         return Response({
#             "success": False,
#             "message": "Salon non trouvé"
#         }, status=status.HTTP_404_NOT_FOUND)
#
#     except Exception as e:
#         logger.error(f"Erreur dans avis_salon_public: {str(e)}")
#         return Response({
#             "success": False,
#             "message": f"Erreur interne: {str(e)}"
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)