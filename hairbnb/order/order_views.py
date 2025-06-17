################################################################################
#                                                                              #
#               VUES DE L'API POUR LE SYSTÈME DE COMMANDES (HAIRBNB)            #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour la gestion  #
#  des "Commandes", qui sont basées sur le modèle de Rendez-vous.              #
#                                                                              #
#  Il fournit des vues distinctes pour les clients et les coiffeuses,          #
#  utilisant des sérialiseurs différents pour présenter les données            #
#  pertinentes à chaque rôle. Il gère également la mise à jour sécurisée       #
#  des commandes par les coiffeuses.                                           #
#                                                                              #
################################################################################

# --- Importations ---
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Importations des modules personnalisés de l'application
from decorators.decorators import firebase_authenticated
from hairbnb.models import TblUser, TblClient, TblRendezVous, TblCoiffeuse
from hairbnb.order.order_serializes import CommandeSerializer, UpdateRendezVousSerializer, CommandeCoiffeuseSerializer

@firebase_authenticated
@api_view(['GET'])
def mes_commandes(request, idUser):
    """
    Récupère l'historique de toutes les commandes payées pour un utilisateur (client).
    """
    try:
        # Récupère l'objet utilisateur de base.
        user = TblUser.objects.get(idTblUser=idUser)
        # Récupère tous les profils "Client" liés à cet utilisateur.
        clients = TblClient.objects.filter(idTblUser=user)

        if not clients.exists():
            return Response([])

        all_commandes = []
        # Boucle sur chaque profil client pour rassembler toutes les commandes.
        for client in clients:
            # Filtre les rendez-vous pour ne garder que ceux avec un paiement réussi ('payé').
            commandes = TblRendezVous.objects.filter(
                client=client,
                tblpaiement__isnull=False,
                tblpaiement__statut__code="payé"
            ).select_related(
                # Optimisation : pré-charge les données des tables liées en une seule requête JOIN.
                'salon', 'coiffeuse', 'coiffeuse__idTblUser'
            ).prefetch_related(
                # Optimisation : pré-charge les données des relations "many" en une requête séparée.
                'rendez_vous_services', 'rendez_vous_services__service',
                'tblpaiement_set'
            )
            all_commandes.extend(commandes)

        # Trie la liste complète des commandes par date de paiement, de la plus récente à la plus ancienne.
        all_commandes.sort(key=lambda x: x.tblpaiement_set.first().date_paiement if x.tblpaiement_set.exists() else timezone.now(), reverse=True)

        # Utilise le sérialiseur conçu pour la vue client.
        serializer = CommandeSerializer(all_commandes, many=True)
        return Response(serializer.data)

    except TblUser.DoesNotExist:
        return Response({"detail": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Instructions de débogage en cas d'erreur.
        import traceback
        traceback.print_exc()
        print("ERREUR :", e)
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@firebase_authenticated
@api_view(['GET'])
def commandes_coiffeuse(request, idUser):
    """
    Récupère les commandes (rendez-vous) d'une coiffeuse, avec un filtre
    optionnel sur le statut (par défaut 'en attente').
    """
    try:
        # Récupère l'utilisateur et le profil coiffeuse associé.
        user = TblUser.objects.get(idTblUser=idUser)
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)

        # Récupère le paramètre de statut depuis l'URL, avec 'en attente' comme valeur par défaut.
        statut = request.query_params.get('statut', 'en attente')

        # Filtre les rendez-vous par coiffeuse et par statut.
        commandes = TblRendezVous.objects.filter(
            coiffeuse=coiffeuse,
            statut=statut
        ).select_related(
            # Optimisations pour réduire le nombre de requêtes à la base de données.
            'client', 'client__idTblUser', 'salon'
        ).prefetch_related(
            'rendez_vous_services', 'rendez_vous_services__service',
            'tblpaiement_set'
        ).order_by('date_heure') # Tri par date de rendez-vous.

        # Utilise le sérialiseur conçu pour la vue coiffeuse.
        serializer = CommandeCoiffeuseSerializer(commandes, many=True)
        return Response(serializer.data)

    except TblUser.DoesNotExist:
        return Response({"detail": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    except TblCoiffeuse.DoesNotExist:
        return Response({"detail": "Coiffeuse non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERREUR :", e)
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@firebase_authenticated
@api_view(['PATCH'])
def update_statut_commande(request, idRendezVous):
    """
    Permet à une coiffeuse authentifiée de mettre à jour le statut d'une commande (rendez-vous).
    """
    try:
        # Récupère le rendez-vous à modifier.
        rendez_vous = TblRendezVous.objects.get(idRendezVous=idRendezVous)

        # --- Vérification de sécurité ---
        # S'assure que l'utilisateur connecté est bien la coiffeuse assignée à ce rendez-vous.
        user = request.user
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        if rendez_vous.coiffeuse.idTblUser.idTblUser != user.idTblUser:
            return Response({"detail": "Vous n'êtes pas autorisé à modifier ce rendez-vous."}, status=status.HTTP_403_FORBIDDEN)

        # Utilise un sérialiseur de mise à jour. `partial=True` permet une mise à jour
        # partielle (seuls les champs fournis dans la requête seront mis à jour).
        serializer = UpdateRendezVousSerializer(rendez_vous, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Retourne l'objet complet et mis à jour.
            return Response(CommandeCoiffeuseSerializer(rendez_vous).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except TblRendezVous.DoesNotExist:
        return Response({"detail": "Rendez-vous non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    except TblCoiffeuse.DoesNotExist:
        return Response({"detail": "Coiffeuse non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@firebase_authenticated
@api_view(['PATCH'])
def update_date_heure_commande(request, idRendezVous):
    """
    Permet à une coiffeuse authentifiée de modifier la date et l'heure d'une commande.
    """
    try:
        rendez_vous = TblRendezVous.objects.get(idRendezVous=idRendezVous)

        # --- Vérification de sécurité (propriété du rendez-vous) ---
        user = request.user
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        if rendez_vous.coiffeuse.idTblUser.idTblUser != user.idTblUser:
            return Response({"detail": "Vous n'êtes pas autorisé à modifier ce rendez-vous."}, status=status.HTTP_403_FORBIDDEN)

        # --- Règle métier ---
        # Empêche la modification d'un rendez-vous déjà finalisé ou annulé.
        if rendez_vous.statut in ['annulé', 'terminé']:
            return Response({"detail": f"Impossible de modifier un rendez-vous avec le statut '{rendez_vous.statut}'."}, status=status.HTTP_400_BAD_REQUEST)

        # Utilise le même sérialiseur pour la mise à jour partielle.
        serializer = UpdateRendezVousSerializer(rendez_vous, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(CommandeCoiffeuseSerializer(rendez_vous).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except TblRendezVous.DoesNotExist:
        return Response({"detail": "Rendez-vous non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    except TblCoiffeuse.DoesNotExist:
        return Response({"detail": "Coiffeuse non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








# from django.utils import timezone
# from rest_framework import status
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
#
# from decorators.decorators import firebase_authenticated
# from hairbnb.models import TblUser, TblClient, TblRendezVous, TblCoiffeuse
# from hairbnb.order.order_serializes import CommandeSerializer, UpdateRendezVousSerializer, CommandeCoiffeuseSerializer
#
#
# @api_view(['GET'])
# def mes_commandes(request, idUser):
#     """
#     Récupère toutes les commandes (rendez-vous payés) d'un utilisateur,
#     quel que soit son type (client, coiffeuse, ou les deux).
#     """
#     try:
#         # Récupérer l'utilisateur
#         user = TblUser.objects.get(idTblUser=idUser)
#
#         # Vérifier les clients liés à cet utilisateur
#         clients = TblClient.objects.filter(idTblUser=user)
#
#         if not clients.exists():
#             # Aucun profil client - retourner une liste vide
#             return Response([])
#
#         # Récupérer les commandes pour tous les profils clients de cet utilisateur
#         all_commandes = []
#
#         for client in clients:
#             commandes = TblRendezVous.objects.filter(
#                 client=client,
#                 tblpaiement__isnull=False,
#                 tblpaiement__statut__code="payé"
#             ).select_related(
#                 'salon', 'coiffeuse', 'coiffeuse__idTblUser'
#             ).prefetch_related(
#                 'rendez_vous_services', 'rendez_vous_services__service',
#                 'tblpaiement_set'
#             )
#             all_commandes.extend(commandes)
#
#         # Trier toutes les commandes par date de paiement
#         all_commandes.sort(
#             key=lambda x: x.tblpaiement_set.first().date_paiement if x.tblpaiement_set.exists() else timezone.now(),
#             reverse=True)
#
#         # Serializer les données
#         serializer = CommandeSerializer(all_commandes, many=True)
#         return Response(serializer.data)
#     except TblUser.DoesNotExist:
#         return Response({"detail": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         print("ERREUR :", e)
#         return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# #@firebase_authenticated
# @api_view(['GET'])
# def commandes_coiffeuse(request, idUser):
#     """
#     Récupère toutes les commandes (rendez-vous) reçues par une coiffeuse,
#     par défaut filtrées sur statut 'en attente'
#     """
#     try:
#         # Récupérer l'utilisateur et la coiffeuse associée
#         user = TblUser.objects.get(idTblUser=idUser)
#         coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
#
#         # Récupérer le filtre de statut (par défaut 'en attente')
#         statut = request.query_params.get('statut', 'en attente')
#
#         # Filtrer les rendez-vous par statut
#         commandes = TblRendezVous.objects.filter(
#             coiffeuse=coiffeuse,
#             statut=statut
#         ).select_related(
#             'client', 'client__idTblUser', 'salon'
#         ).prefetch_related(
#             'rendez_vous_services', 'rendez_vous_services__service',
#             'tblpaiement_set'
#         ).order_by('date_heure')  # Tri par date/heure
#
#         # Serializer les données
#         serializer = CommandeCoiffeuseSerializer(commandes, many=True)
#         return Response(serializer.data)
#
#     except TblUser.DoesNotExist:
#         return Response({"detail": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
#     except TblCoiffeuse.DoesNotExist:
#         return Response({"detail": "Coiffeuse non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         print("ERREUR :", e)
#         return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @firebase_authenticated
# @api_view(['PATCH'])
# def update_statut_commande(request, idRendezVous):
#     """
#     Permet à une coiffeuse de modifier le statut d'une commande
#     """
#     try:
#         # Récupérer le rendez-vous
#         rendez_vous = TblRendezVous.objects.get(idRendezVous=idRendezVous)
#
#         # Vérifier que l'utilisateur connecté est bien la coiffeuse de ce rendez-vous
#         user = request.user
#         coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
#
#         if rendez_vous.coiffeuse.idTblUser.idTblUser != user.idTblUser:
#             return Response({"detail": "Vous n'êtes pas autorisé à modifier ce rendez-vous."},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         # Mise à jour du statut uniquement
#         serializer = UpdateRendezVousSerializer(rendez_vous, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(CommandeCoiffeuseSerializer(rendez_vous).data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     except TblRendezVous.DoesNotExist:
#         return Response({"detail": "Rendez-vous non trouvé."}, status=status.HTTP_404_NOT_FOUND)
#     except TblCoiffeuse.DoesNotExist:
#         return Response({"detail": "Coiffeuse non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @firebase_authenticated
# @api_view(['PATCH'])
# def update_date_heure_commande(request, idRendezVous):
#     """
#     Permet à une coiffeuse de modifier la date et l'heure d'une commande
#     """
#     try:
#         # Récupérer le rendez-vous
#         rendez_vous = TblRendezVous.objects.get(idRendezVous=idRendezVous)
#
#         # Vérifier que l'utilisateur connecté est bien la coiffeuse de ce rendez-vous
#         user = request.user
#         coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
#
#         if rendez_vous.coiffeuse.idTblUser.idTblUser != user.idTblUser:
#             return Response({"detail": "Vous n'êtes pas autorisé à modifier ce rendez-vous."},
#                             status=status.HTTP_403_FORBIDDEN)
#
#         # Vérifier que le rendez-vous n'est pas déjà annulé ou terminé
#         if rendez_vous.statut in ['annulé', 'terminé']:
#             return Response(
#                 {"detail": f"Impossible de modifier un rendez-vous avec le statut '{rendez_vous.statut}'."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Mise à jour de la date et l'heure uniquement
#         serializer = UpdateRendezVousSerializer(rendez_vous, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(CommandeCoiffeuseSerializer(rendez_vous).data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     except TblRendezVous.DoesNotExist:
#         return Response({"detail": "Rendez-vous non trouvé."}, status=status.HTTP_404_NOT_FOUND)
#     except TblCoiffeuse.DoesNotExist:
#         return Response({"detail": "Coiffeuse non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)