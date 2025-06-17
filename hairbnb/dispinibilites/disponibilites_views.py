################################################################################
#                                                                              #
#        VUES DE L'API POUR LES DISPONIBILITÉS DES COIFFEUSES (HAIRBNB)          #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour calculer    #
#  et récupérer les créneaux de disponibilité d'une coiffeuse. Il est          #
#  essentiel pour le système de prise de rendez-vous.                          #
#                                                                              #
#  Il contient deux vues principales :                                         #
#    - `get_disponibilites_client`: Une vue détaillée qui retourne les          #
#      créneaux disponibles avec des informations enrichies.                   #
#    - `get_creneaux_jour`: Une vue simplifiée, optimisée pour un client       #
#      spécifique (ex: une application mobile Flutter).                        #
#                                                                              #
#  La logique complexe de validation et de calcul est déléguée à la classe     #
#  `DisponibilitesClientSerializer` pour garder les vues claires et organisées.#
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

# Importations des modules personnalisés de l'application
from decorators.decorators import firebase_authenticated
from hairbnb.dispinibilites.disponibilities_serializers import DisponibilitesClientSerializer
from hairbnb.models import TblCoiffeuse


@api_view(['GET'])
@firebase_authenticated
def get_disponibilites_client(request, coiffeuse_id):
    """
    Calcule et récupère les créneaux de disponibilité pour une coiffeuse,
    une date et une durée de service spécifiques.
    """
    # Instructions de débogage pour tracer l'exécution de la vue.
    print(f"🔄 === DÉBUT GET_DISPONIBILITES_CLIENT ===")
    print(f"🔄 CoiffeuseId: {coiffeuse_id}")
    print(f"🔄 Utilisateur connecté: {request.user}")
    print(f"🔄 Paramètres GET: {dict(request.GET)}")

    try:
        # --- Étape 1 : Récupérer et valider la présence des paramètres ---
        date_param = request.GET.get('date')
        duree_param = request.GET.get('duree')

        # Vérifie que le paramètre 'date' est fourni dans la requête.
        if not date_param:
            print("❌ Paramètre 'date' manquant")
            return Response({"error": "Le paramètre 'date' est obligatoire (format: YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifie que le paramètre 'duree' est fourni.
        if not duree_param:
            print("❌ Paramètre 'duree' manquant")
            return Response({"error": "Le paramètre 'duree' est obligatoire (en minutes)"}, status=status.HTTP_400_BAD_REQUEST)

        # --- Étape 2 : Conversion et validation des types de données ---
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            duree_minutes = int(duree_param)
        except ValueError as e:
            # Gère les erreurs si le format de la date ou de la durée est incorrect.
            print(f"❌ Erreur de format: {e}")
            return Response({"error": f"Format invalide - date: YYYY-MM-DD, durée: nombre entier. Erreur: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        print(f"✅ Date parsée: {target_date}")
        print(f"✅ Durée parsée: {duree_minutes} minutes")

        # --- Étape 3 : Validation de la logique métier via le sérialiseur ---
        # Prépare un dictionnaire avec les données à valider.
        data_to_validate = {
            'coiffeuse_id': coiffeuse_id,
            'date': target_date,
            'duree': duree_minutes
        }
        # Le sérialiseur va vérifier si la coiffeuse existe, si la date n'est pas passée, etc.
        serializer = DisponibilitesClientSerializer(data=data_to_validate)
        if not serializer.is_valid():
            print(f"❌ Erreurs de validation: {serializer.errors}")
            return Response({"error": "Données invalides", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        print("✅ Validation réussie")

        # --- Étape 4 : Calculer les disponibilités ---
        # La logique complexe de calcul est déléguée à une méthode du sérialiseur.
        print(f"🔄 Calcul des disponibilités...")
        disponibilites = serializer.calculate_disponibilites(coiffeuse_id=int(coiffeuse_id), target_date=target_date, duree_minutes=duree_minutes)
        print(f"✅ {len(disponibilites)} créneaux calculés")

        # --- Étape 5 : Enrichir les données de la réponse ---
        # Récupère le nom de la coiffeuse pour un affichage plus convivial.
        try:
            coiffeuse = TblCoiffeuse.objects.select_related('idTblUser').get(idTblUser__idTblUser=coiffeuse_id)
            coiffeuse_nom = f"{coiffeuse.idTblUser.prenom} {coiffeuse.idTblUser.nom}"
        except TblCoiffeuse.DoesNotExist:
            coiffeuse_nom = f"Coiffeuse #{coiffeuse_id}"

        # --- Étape 6 : Construire la réponse finale ---
        # Assemble toutes les informations dans un dictionnaire structuré.
        response_data = {
            "success": True,
            "coiffeuse_id": int(coiffeuse_id),
            "coiffeuse_nom": coiffeuse_nom,
            "date": date_param,
            "duree_demandee": duree_minutes,
            "disponibilites": disponibilites,
            "nb_creneaux": len(disponibilites),
            "timestamp": datetime.now().isoformat()
        }

        print(f"✅ Réponse construite: {len(disponibilites)} créneaux")
        print(f"✅ === FIN GET_DISPONIBILITES_CLIENT ===")

        return Response(response_data, status=status.HTTP_200_OK)

    # --- Gestion des erreurs inattendues ---
    except Exception as e:
        # Capture toute autre erreur qui pourrait survenir et la logue avec détails.
        print(f"💥 ERREUR INATTENDUE: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"💥 Stack trace: {traceback.format_exc()}")

        # Renvoie une réponse d'erreur générique au client.
        return Response({"error": "Erreur interne du serveur", "details": str(e), "timestamp": datetime.now().isoformat()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@firebase_authenticated
def get_creneaux_jour(request, coiffeuse_id):
    """
    Récupère les créneaux disponibles pour un jour donné dans un format simplifié,
    potentiellement pour une application mobile.
    """
    print(f"🔄 === GET_CRENEAUX_JOUR ===")
    print(f"🔄 CoiffeuseId: {coiffeuse_id}")

    try:
        # La récupération et la validation des paramètres sont similaires à la vue précédente.
        date_param = request.GET.get('date')
        duree_param = request.GET.get('duree')

        if not date_param or not duree_param:
            return Response({"error": "Paramètres 'date' et 'duree' obligatoires"}, status=status.HTTP_400_BAD_REQUEST)

        # Réutilise la même logique de conversion et de validation.
        target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        duree_minutes = int(duree_param)

        # La validation est également déléguée au même sérialiseur.
        serializer = DisponibilitesClientSerializer(data={'coiffeuse_id': coiffeuse_id, 'date': target_date, 'duree': duree_minutes})
        if not serializer.is_valid():
            return Response({"error": "Données invalides", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Le calcul des créneaux réutilise la même méthode.
        creneaux = serializer.calculate_disponibilites(coiffeuse_id=int(coiffeuse_id), target_date=target_date, duree_minutes=duree_minutes)

        # Construit une réponse avec un format plus simple et direct.
        response_data = {
            "success": True,
            "creneaux": creneaux,
            "date": date_param
        }

        print(f"✅ {len(creneaux)} créneaux retournés pour le {date_param}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion d'erreur simplifiée pour cette vue.
        print(f"❌ Erreur get_creneaux_jour: {e}")
        return Response({"error": f"Erreur serveur: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from datetime import datetime
#
# from decorators.decorators import firebase_authenticated
# from hairbnb.dispinibilites.disponibilities_serializers import DisponibilitesClientSerializer
# from hairbnb.models import TblCoiffeuse
#
#
# @api_view(['GET'])
# @firebase_authenticated
# def get_disponibilites_client(request, coiffeuse_id):
#     """
#     Récupère les disponibilités d'une coiffeuse pour une date donnée.
#
#     URL: /api/get_disponibilites_client/{coiffeuse_id}/
#     Paramètres GET:
#     - date: Date au format YYYY-MM-DD
#     - duree: Durée du service en minutes
#
#     Exemple d'appel:
#     GET /api/get_disponibilites_client/124/?date=2025-06-10&duree=158
#     """
#     print(f"🔄 === DÉBUT GET_DISPONIBILITES_CLIENT ===")
#     print(f"🔄 CoiffeuseId: {coiffeuse_id}")
#     print(f"🔄 Utilisateur connecté: {request.user}")
#     print(f"🔄 Paramètres GET: {dict(request.GET)}")
#
#     try:
#         # 1️⃣ Récupérer et valider les paramètres
#         date_param = request.GET.get('date')
#         duree_param = request.GET.get('duree')
#
#         # Validation des paramètres obligatoires
#         if not date_param:
#             print("❌ Paramètre 'date' manquant")
#             return Response(
#                 {"error": "Le paramètre 'date' est obligatoire (format: YYYY-MM-DD)"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         if not duree_param:
#             print("❌ Paramètre 'duree' manquant")
#             return Response(
#                 {"error": "Le paramètre 'duree' est obligatoire (en minutes)"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # 2️⃣ Conversion et validation des types
#         try:
#             target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
#             duree_minutes = int(duree_param)
#         except ValueError as e:
#             print(f"❌ Erreur de format: {e}")
#             return Response(
#                 {"error": f"Format invalide - date: YYYY-MM-DD, durée: nombre entier. Erreur: {str(e)}"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         print(f"✅ Date parsée: {target_date}")
#         print(f"✅ Durée parsée: {duree_minutes} minutes")
#
#         # 3️⃣ Validation avec le serializer
#         data_to_validate = {
#             'coiffeuse_id': coiffeuse_id,
#             'date': target_date,
#             'duree': duree_minutes
#         }
#
#         serializer = DisponibilitesClientSerializer(data=data_to_validate)
#
#         if not serializer.is_valid():
#             print(f"❌ Erreurs de validation: {serializer.errors}")
#             return Response(
#                 {"error": "Données invalides", "details": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         print("✅ Validation réussie")
#
#         # 4️⃣ Calculer les disponibilités
#         print(f"🔄 Calcul des disponibilités...")
#         disponibilites = serializer.calculate_disponibilites(
#             coiffeuse_id=int(coiffeuse_id),
#             target_date=target_date,
#             duree_minutes=duree_minutes
#         )
#
#         print(f"✅ {len(disponibilites)} créneaux calculés")
#
#         # 5️⃣ Enrichir les données de réponse
#         try:
#             coiffeuse = TblCoiffeuse.objects.select_related('idTblUser').get(
#                 idTblUser__idTblUser=coiffeuse_id
#             )
#             coiffeuse_nom = f"{coiffeuse.idTblUser.prenom} {coiffeuse.idTblUser.nom}"
#         except TblCoiffeuse.DoesNotExist:
#             coiffeuse_nom = f"Coiffeuse #{coiffeuse_id}"
#
#         # 6️⃣ Construire la réponse finale
#         response_data = {
#             "success": True,
#             "coiffeuse_id": int(coiffeuse_id),
#             "coiffeuse_nom": coiffeuse_nom,
#             "date": date_param,
#             "duree_demandee": duree_minutes,
#             "disponibilites": disponibilites,
#             "nb_creneaux": len(disponibilites),
#             "timestamp": datetime.now().isoformat()
#         }
#
#         print(f"✅ Réponse construite: {len(disponibilites)} créneaux")
#         print(f"✅ === FIN GET_DISPONIBILITES_CLIENT ===")
#
#         return Response(response_data, status=status.HTTP_200_OK)
#
#     except Exception as e:
#         print(f"💥 ERREUR INATTENDUE: {type(e).__name__}: {str(e)}")
#         import traceback
#         print(f"💥 Stack trace: {traceback.format_exc()}")
#
#         return Response(
#             {
#                 "error": "Erreur interne du serveur",
#                 "details": str(e),
#                 "timestamp": datetime.now().isoformat()
#             },
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
#
#
# @api_view(['GET'])
# @firebase_authenticated
# def get_creneaux_jour(request, coiffeuse_id):
#     """
#     Récupère les créneaux d'un jour spécifique.
#     Utilisée par Flutter pour la sélection d'horaire.
#
#     URL: /api/get_creneaux_jour/{coiffeuse_id}/
#     """
#     print(f"🔄 === GET_CRENEAUX_JOUR ===")
#     print(f"🔄 CoiffeuseId: {coiffeuse_id}")
#
#     try:
#         # Mêmes paramètres que get_disponibilites_client
#         date_param = request.GET.get('date')
#         duree_param = request.GET.get('duree')
#
#         if not date_param or not duree_param:
#             return Response(
#                 {"error": "Paramètres 'date' et 'duree' obligatoires"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Réutiliser la même logique
#         target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
#         duree_minutes = int(duree_param)
#
#         # Validation
#         serializer = DisponibilitesClientSerializer(data={
#             'coiffeuse_id': coiffeuse_id,
#             'date': target_date,
#             'duree': duree_minutes
#         })
#
#         if not serializer.is_valid():
#             return Response(
#                 {"error": "Données invalides", "details": serializer.errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         # Calculer
#         creneaux = serializer.calculate_disponibilites(
#             coiffeuse_id=int(coiffeuse_id),
#             target_date=target_date,
#             duree_minutes=duree_minutes
#         )
#
#         # Format simplifié pour Flutter
#         response_data = {
#             "success": True,
#             "creneaux": creneaux,
#             "date": date_param
#         }
#
#         print(f"✅ {len(creneaux)} créneaux retournés pour le {date_param}")
#         return Response(response_data, status=status.HTTP_200_OK)
#
#     except Exception as e:
#         print(f"❌ Erreur get_creneaux_jour: {e}")
#         return Response(
#             {"error": f"Erreur serveur: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )