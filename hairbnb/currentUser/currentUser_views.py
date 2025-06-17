################################################################################
#                                                                              #
#             VUES DE L'API POUR LA GESTION DES UTILISATEURS                     #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour récupérer   #
#  les informations des utilisateurs. Il contient deux vues principales :      #
#                                                                              #
#  1. `get_current_user`: Récupère les données complètes de l'utilisateur       #
#     actuellement authentifié.                                                #
#  2. `get_user_by_id`: Récupère les données complètes d'un utilisateur         #
#     spécifique via son ID, en enrichissant les données si l'utilisateur      #
#     est une coiffeuse.                                                       #
#                                                                              #
#  Ces vues utilisent `CurrentUserSerializer` pour assurer un formatage        #
#  cohérent des données utilisateur.                                           #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework.decorators import api_view
from rest_framework.response import Response

from decorators.decorators import firebase_authenticated
# Importation du sérialiseur principal pour les utilisateurs
from hairbnb.currentUser.CurrentUser_serializer import CurrentUserSerializer


@api_view(['GET'])
# Le décorateur d'authentification est actuellement désactivé.
@firebase_authenticated
def get_current_user(request):
    """
    Récupère et renvoie les informations complètes de l'utilisateur
    actuellement authentifié, qui est supposé être dans `request.user`.
    """
    # Récupère l'objet utilisateur depuis la requête.
    user = request.user

    # Instructions de débogage laissées intentionnellement pour le développement.
    print(f"🔍 === get_current_user DEBUG ===")
    print(f"🔍 user: {user}")
    print(f"🔍 user.idTblUser: {getattr(user, 'idTblUser', 'N/A')}")
    print(f"🔍 user.type_ref: {getattr(user, 'type_ref', 'N/A')}")
    print(f"🔍 user.role: {getattr(user, 'role', 'N/A')}")

    # Vérifie si l'objet utilisateur est valide avant de continuer.
    if not user or not hasattr(user, 'uuid'):
        return Response({"status": "error", "message": "Utilisateur non trouvé"}, status=404)

    # Le contexte de la requête est passé au sérialiseur.
    # C'est essentiel pour que le sérialiseur puisse construire des URLs absolues (ex: pour les images).
    serializer = CurrentUserSerializer(user, context={'request': request})

    # Instruction de débogage pour inspecter le résultat de la sérialisation.
    result = serializer.data
    print(f"🔍 Résultat serializer: {result}")

    # Renvoie les données de l'utilisateur formatées dans une réponse de succès.
    return Response({"status": "success", "user": result}, status=200)


@api_view(['GET'])
# Le décorateur d'authentification est actuellement désactivé.
@firebase_authenticated
def get_user_by_id(request, id):
    """
    Récupère les informations complètes d'un utilisateur spécifique en utilisant
    son ID de base de données. Enrichit les données si l'utilisateur est une coiffeuse.
    """
    # L'importation est faite ici pour éviter les dépendances circulaires.
    from hairbnb.models import TblUser

    try:
        # Tente de récupérer l'utilisateur par son ID de base de données (clé primaire).
        user = TblUser.objects.get(idTblUser=id)

        # Instructions de débogage pour l'utilisateur trouvé.
        print(f"🔍 === get_user_by_id DEBUG ===")
        print(f"🔍 user trouvé: {user}")
        print(f"🔍 user.idTblUser: {user.idTblUser}")
        print(f"🔍 user.type_ref: {user.type_ref}")
        print(f"🔍 user.role: {user.role}")

        # Utilise le sérialiseur principal pour obtenir la structure de base des données utilisateur.
        serializer = CurrentUserSerializer(user, context={'request': request})
        # Crée une copie mutable du dictionnaire de données pour pouvoir l'enrichir.
        response_data = serializer.data.copy()

        # Instruction de débogage pour voir les données après la sérialisation initiale.
        print(f"🔍 response_data après serializer: {response_data}")

        # --- Logique d'enrichissement des données pour les coiffeuses ---
        # Vérifie si l'utilisateur est de type "coiffeuse".
        if user.type_ref and user.type_ref.libelle == 'coiffeuse' and hasattr(user, 'coiffeuse'):
            coiffeuse = user.coiffeuse

            # Importe le modèle de la table de liaison Coiffeuse-Salon.
            from hairbnb.models import TblCoiffeuseSalon
            # Récupère toutes les relations entre cette coiffeuse et les salons.
            salons_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)

            if salons_relations.exists():
                salon_list = []
                salon_principal = None

                # Boucle sur chaque relation pour construire la liste des salons.
                for relation in salons_relations:
                    salon_info = {
                        'idTblSalon': relation.salon.idTblSalon,
                        'nom_salon': relation.salon.nom_salon,
                        'slogan': relation.salon.slogan,
                        'logo_salon': relation.salon.logo_salon.url if relation.salon.logo_salon else None,
                        'numero_tva': relation.salon.numero_tva,
                        'est_proprietaire': relation.est_proprietaire
                    }

                    # Ajoute les détails de l'adresse du salon si elle existe.
                    if relation.salon.adresse:
                        salon_info['adresse'] = {
                            'numero': relation.salon.adresse.numero,
                            'rue': relation.salon.adresse.rue.nom_rue if relation.salon.adresse.rue else None,
                            'commune': relation.salon.adresse.rue.localite.commune if relation.salon.adresse.rue and relation.salon.adresse.rue.localite else None,
                            'code_postal': relation.salon.adresse.rue.localite.code_postal if relation.salon.adresse.rue and relation.salon.adresse.rue.localite else None
                        }

                    salon_list.append(salon_info)

                    # Identifie le salon principal (où la coiffeuse est propriétaire).
                    if relation.est_proprietaire:
                        salon_principal = salon_info

                # Injecte les informations de salons enrichies dans les données de la réponse.
                if 'coiffeuse' in response_data:
                    response_data['coiffeuse']['tous_salons'] = salon_list
                    response_data['coiffeuse']['salon_principal'] = salon_principal

        # Renvoie la réponse finale, potentiellement enrichie.
        return Response({"status": "success", "user": response_data}, status=200)

    except TblUser.DoesNotExist:
        # Gère le cas où aucun utilisateur ne correspond à l'ID fourni.
        return Response({"status": "error", "message": "Utilisateur introuvable"}, status=404)






# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from hairbnb.currentUser.CurrentUser_serializer import CurrentUserSerializer
#
#
# @api_view(['GET'])
# # @firebase_authenticated
# def get_current_user(request):
#     """
#     Récupère les informations de l'utilisateur actuellement authentifié.
#     Le décorateur firebase_authenticated garantit que request.user est correctement défini.
#     """
#     user = request.user
#
#     # ✅ AJOUT DEBUG
#     print(f"🔍 === get_current_user DEBUG ===")
#     print(f"🔍 user: {user}")
#     print(f"🔍 user.idTblUser: {getattr(user, 'idTblUser', 'N/A')}")
#     print(f"🔍 user.type_ref: {getattr(user, 'type_ref', 'N/A')}")
#     print(f"🔍 user.role: {getattr(user, 'role', 'N/A')}")
#
#     if not user or not hasattr(user, 'uuid'):
#         return Response({"status": "error", "message": "Utilisateur non trouvé"}, status=404)
#
#     # Passer le contexte de la requête au serializer pour construire des URLs absolues
#     serializer = CurrentUserSerializer(user, context={'request': request})
#
#     # ✅ AJOUT DEBUG RÉSULTAT
#     result = serializer.data
#     print(f"🔍 Résultat serializer: {result}")
#
#     return Response({"status": "success", "user": result}, status=200)
#
#
# @api_view(['GET'])
# #@firebase_authenticated
# def get_user_by_id(request, id):
#     """
#     Récupère les informations d'un utilisateur spécifique par son ID.
#     """
#     from hairbnb.models import TblUser
#
#     try:
#         user = TblUser.objects.get(idTblUser=id)
#
#         # ✅ AJOUT DEBUG
#         print(f"🔍 === get_user_by_id DEBUG ===")
#         print(f"🔍 user trouvé: {user}")
#         print(f"🔍 user.idTblUser: {user.idTblUser}")
#         print(f"🔍 user.type_ref: {user.type_ref}")
#         print(f"🔍 user.role: {user.role}")
#
#         # Passer le contexte de la requête au serializer pour construire des URLs absolues
#         serializer = CurrentUserSerializer(user, context={'request': request})
#         response_data = serializer.data.copy()
#
#         # ✅ AJOUT DEBUG RÉSULTAT
#         print(f"🔍 response_data après serializer: {response_data}")
#
#         # Enrichir les données pour les coiffeuses
#         if user.type_ref and user.type_ref.libelle == 'coiffeuse' and hasattr(user, 'coiffeuse'):
#             coiffeuse = user.coiffeuse
#
#             # Ajouter des informations détaillées sur les salons où travaille la coiffeuse
#             from hairbnb.models import TblCoiffeuseSalon
#             salons_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)
#
#             if salons_relations.exists():
#                 salon_list = []
#                 salon_principal = None
#
#                 for relation in salons_relations:
#                     salon_info = {
#                         'idTblSalon': relation.salon.idTblSalon,
#                         'nom_salon': relation.salon.nom_salon,
#                         'slogan': relation.salon.slogan,
#                         'logo_salon': relation.salon.logo_salon.url if relation.salon.logo_salon else None,
#                         'numero_tva': relation.salon.numero_tva,
#                         'est_proprietaire': relation.est_proprietaire
#                     }
#
#                     # Ajouter l'adresse du salon si disponible
#                     if relation.salon.adresse:
#                         salon_info['adresse'] = {
#                             'numero': relation.salon.adresse.numero,
#                             'rue': relation.salon.adresse.rue.nom_rue if relation.salon.adresse.rue else None,
#                             'commune': relation.salon.adresse.rue.localite.commune if relation.salon.adresse.rue and relation.salon.adresse.rue.localite else None,
#                             'code_postal': relation.salon.adresse.rue.localite.code_postal if relation.salon.adresse.rue and relation.salon.adresse.rue.localite else None
#                         }
#
#                     salon_list.append(salon_info)
#
#                     # Identifier le salon principal (où la coiffeuse est propriétaire)
#                     if relation.est_proprietaire:
#                         salon_principal = salon_info
#
#                 # Mettre à jour les données de réponse
#                 if 'coiffeuse' in response_data:
#                     response_data['coiffeuse']['tous_salons'] = salon_list
#                     response_data['coiffeuse']['salon_principal'] = salon_principal
#
#         return Response({"status": "success", "user": response_data}, status=200)
#
#     except TblUser.DoesNotExist:
#         return Response({"status": "error", "message": "Utilisateur introuvable"}, status=404)