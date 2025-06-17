################################################################################
#                                                                              #
#              VUES DE L'API POUR LE SYSTÈME DE FAVORIS (HAIRBNB)               #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour la gestion  #
#  des salons favoris des utilisateurs. Il permet d'effectuer les opérations   #
#  CRUD (Create, Read, Update, Delete) de base sur les favoris :               #
#                                                                              #
#    - Lister les favoris d'un utilisateur.                                    #
#    - Ajouter un salon aux favoris.                                           #
#    - Supprimer un favori.                                                    #
#    - Vérifier si un salon spécifique est déjà en favori.                     #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from decorators.decorators import firebase_authenticated
# Importation des sérialiseurs spécifiques à cette fonctionnalité
from hairbnb.favorites.favorites_serializer import TblFavoriteSerializer, FavoriteCheckSerializer
# Importation des modèles de la base de données
from hairbnb.models import TblFavorite, TblSalon, TblUser
from django.shortcuts import get_object_or_404

@firebase_authenticated
@api_view(['GET'])
def get_favorites(request):
    """
    Récupère la liste des salons favoris pour un utilisateur donné.
    (Note : Version simple de la vue).
    """
    # Récupère l'ID de l'utilisateur depuis les paramètres de la requête GET.
    user_id = request.GET.get('user')
    # Valide la présence du paramètre 'user'.
    if not user_id:
        return Response({"error": "Paramètre 'user' requis"}, status=status.HTTP_400_BAD_REQUEST)

    # Filtre les favoris pour ne récupérer que ceux de l'utilisateur spécifié.
    favorites = TblFavorite.objects.filter(user__idTblUser=user_id)
    # Utilise le sérialiseur détaillé pour formater la réponse.
    serializer = TblFavoriteSerializer(favorites, many=True)
    return Response(serializer.data)

@firebase_authenticated
@api_view(['GET'])
def get_user_favorites(request):
    """
    Récupère la liste des salons favoris pour un utilisateur donné.
    (Note : Version optimisée avec select_related).
    """
    # Récupère l'ID de l'utilisateur depuis les paramètres de la requête GET.
    user_id = request.GET.get('user')
    if not user_id:
        return Response({"error": "Paramètre 'user' requis"}, status=status.HTTP_400_BAD_REQUEST)

    # Filtre les favoris. `.select_related('salon', 'user')` est une optimisation qui
    # pré-charge les données des modèles liés (TblSalon, TblUser) en une seule
    # requête SQL, évitant ainsi de multiples requêtes à la base de données.
    favorites = TblFavorite.objects.filter(user__idTblUser=user_id).select_related('salon', 'user')
    # Utilise le sérialiseur détaillé pour formater la réponse.
    serializer = TblFavoriteSerializer(favorites, many=True)
    return Response(serializer.data)

@firebase_authenticated
@api_view(['POST'])
def add_favorite(request):
    """
    Ajoute un salon aux favoris d'un utilisateur.
    Si le favori existe déjà, il ne fait rien et renvoie les données existantes.
    """
    # Récupère les IDs depuis le corps de la requête POST.
    user_id = request.data.get("user")
    salon_id = request.data.get("salon")
    if not user_id or not salon_id:
        return Response({"error": "Champs 'user' et 'salon' requis"}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie que l'utilisateur et le salon existent, sinon renvoie une erreur 404.
    user = get_object_or_404(TblUser, idTblUser=user_id)
    salon = get_object_or_404(TblSalon, idTblSalon=salon_id)

    # `get_or_create` est une méthode robuste : elle récupère le favori s'il existe,
    # ou le crée s'il n'existe pas. La variable 'created' est un booléen qui indique
    # si un nouvel objet a été créé.
    favorite, created = TblFavorite.objects.get_or_create(user=user, salon=salon)
    serializer = TblFavoriteSerializer(favorite)

    # Renvoie un statut HTTP 201 (Created) si le favori vient d'être créé,
    # ou 200 (OK) s'il existait déjà.
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

@firebase_authenticated
@api_view(['DELETE'])
def remove_favorite(request):
    """
    Supprime un favori en utilisant son ID unique (clé primaire de TblFavorite).
    """
    # Récupère l'ID du favori à supprimer depuis le corps de la requête DELETE.
    favorite_id = request.data.get("id")
    if not favorite_id:
        return Response({"error": "Le champ 'id' est requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Tente de trouver le favori par son ID.
        favorite = TblFavorite.objects.get(idTblFavorite=favorite_id)
        # Supprime l'objet de la base de données.
        favorite.delete()
        # Renvoie une réponse vide avec le statut 204 (No Content),
        # ce qui est la norme pour une suppression réussie.
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
    except TblFavorite.DoesNotExist:
        # Si le favori n'est pas trouvé, renvoie une erreur 404.
        return Response({"error": "Favori non trouvé"}, status=status.HTTP_404_NOT_FOUND)

@firebase_authenticated
@api_view(['GET'])
def check_favorite(request):
    """
    Vérifie si un salon spécifique est dans les favoris d'un utilisateur donné.
    Renvoie une réponse légère, optimisée pour des vérifications rapides.
    """
    # Récupère les IDs de l'utilisateur et du salon depuis les paramètres de la requête GET.
    user_id = request.GET.get("user")
    salon_id = request.GET.get("salon")
    if not user_id or not salon_id:
        return Response({"error": "Paramètres 'user' et 'salon' requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Tente de récupérer l'enregistrement exact du favori.
        # Si aucun objet n'est trouvé, une exception `DoesNotExist` est levée.
        favorite = TblFavorite.objects.get(user__idTblUser=user_id, salon__idTblSalon=salon_id)

        # Utilise le sérialiseur léger `FavoriteCheckSerializer` qui ne renvoie
        # que les IDs, rendant la réponse plus petite et plus performante.
        serializer = FavoriteCheckSerializer(favorite)
        return Response(serializer.data)
    except TblFavorite.DoesNotExist:
        # Si le favori n'est pas trouvé, renvoie une réponse 404,
        # ce qui signifie pour le client que le salon n'est pas en favori.
        return Response({"detail": "Favori non trouvé"}, status=status.HTTP_404_NOT_FOUND)









# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from hairbnb.favorites.favorites_serializer import TblFavoriteSerializer, FavoriteCheckSerializer
# from hairbnb.models import TblFavorite, TblSalon, TblUser
# from django.shortcuts import get_object_or_404
#
#
# @api_view(['GET'])
# def get_favorites(request):
#     user_id = request.GET.get('user')  # 🔄 Exemple : ?user=5
#     if not user_id:
#         return Response({"error": "Paramètre 'user' requis"}, status=status.HTTP_400_BAD_REQUEST)
#     favorites = TblFavorite.objects.filter(user__idTblUser=user_id)
#     serializer = TblFavoriteSerializer(favorites, many=True)
#     return Response(serializer.data)
#
#
# @api_view(['GET'])
# def get_user_favorites(request):
#     """
#     🔍 Vue qui retourne la liste des salons ajoutés en favoris par un utilisateur donné.
#     📥 Paramètre attendu dans l'URL :
#         - user (int) : ID de l'utilisateur (idTblUser)
#           Exemple : /api/favorites/?user=2
#     🔁 Traitement :
#         - Filtre les enregistrements dans TblFavorite où l'utilisateur correspond.
#         - Sérialise chaque favori en incluant les détails du salon (si le serializer est configuré ainsi).
#     📤 Rendu :
#         - Type : JSON
#         - Structure : Liste d'objets contenant les infos du favori
#           Exemple :
#           [
#               {
#                   "idTblFavorite": 1,
#                   "user": 2,
#                   "salon": {
#                       "idTblSalon": 3,
#                       "nom_salon": "Salon Chic",
#                       "slogan": "Beauté moderne",
#                       "logo_salon": "https://.../logo.jpg",
#                       ...
#                   },
#                   "added_at": "2025-04-18T09:00:00Z"
#               },
#               ...
#           ]
#     """
#     user_id = request.GET.get('user')  # Ex: /api/favorites/?user=2
#     if not user_id:
#         return Response({"error": "Paramètre 'user' requis"}, status=status.HTTP_400_BAD_REQUEST)
#     favorites = TblFavorite.objects.filter(user__idTblUser=user_id).select_related('salon', 'user')
#     serializer = TblFavoriteSerializer(favorites, many=True)
#     return Response(serializer.data)
#
#
# @api_view(['POST'])
# def add_favorite(request):
#     user_id = request.data.get("user")
#     salon_id = request.data.get("salon")
#     if not user_id or not salon_id:
#         return Response({"error": "Champs 'user' et 'salon' requis"}, status=status.HTTP_400_BAD_REQUEST)
#     # Vérifier que l'utilisateur et le salon existent
#     user = get_object_or_404(TblUser, idTblUser=user_id)
#     salon = get_object_or_404(TblSalon, idTblSalon=salon_id)
#     favorite, created = TblFavorite.objects.get_or_create(user=user, salon=salon)
#     serializer = TblFavoriteSerializer(favorite)
#     return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
#
#
# @api_view(['DELETE'])
# def remove_favorite(request):
#     favorite_id = request.data.get("id")
#     if not favorite_id:
#         return Response({"error": "Le champ 'id' est requis"}, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         favorite = TblFavorite.objects.get(idTblFavorite=favorite_id)
#         favorite.delete()
#         return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
#     except TblFavorite.DoesNotExist:
#         return Response({"error": "Favori non trouvé"}, status=status.HTTP_404_NOT_FOUND)
#
#
# # Nouvel endpoint pour vérifier si un salon est en favori pour un utilisateur donné
# @api_view(['GET'])
# def check_favorite(request):
#     """
#     Vérifie si un salon est en favori pour un utilisateur donné.
#     Renvoie le favori au format compatible avec le modèle Flutter.
#     """
#     user_id = request.GET.get("user")
#     salon_id = request.GET.get("salon")
#
#     if not user_id or not salon_id:
#         return Response({"error": "Paramètres 'user' et 'salon' requis"}, status=status.HTTP_400_BAD_REQUEST)
#
#     try:
#         favorite = TblFavorite.objects.get(user__idTblUser=user_id, salon__idTblSalon=salon_id)
#         # Utilise le serializer spécial qui convertit salon en entier
#         serializer = FavoriteCheckSerializer(favorite)
#         return Response(serializer.data)
#     except TblFavorite.DoesNotExist:
#         return Response({"detail": "Favori non trouvé"}, status=status.HTTP_404_NOT_FOUND)
