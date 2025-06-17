################################################################################
#                                                                              #
#              VUES DE L'API POUR LE PANIER D'ACHAT (HAIRBNB)                    #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour la gestion  #
#  du panier d'achat des utilisateurs. Il permet d'effectuer les opérations    #
#  suivantes :                                                                 #
#    - Consulter le contenu du panier.                                         #
#    - Ajouter un service au panier (ou incrémenter sa quantité).              #
#    - Retirer un service spécifique du panier.                                #
#    - Vider complètement le panier.                                           #
#                                                                              #
#  La sécurité est gérée par l'authentification Firebase et le décorateur      #
#  personnalisé `@is_owner` pour s'assurer qu'un utilisateur ne peut           #
#  modifier que son propre panier.                                             #
#                                                                              #
################################################################################

# --- Importations ---
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

# Importations des modules personnalisés de l'application
from decorators.decorators import firebase_authenticated, is_owner
# Classes de logique métier pour formater les données du panier en réponse
from hairbnb.card.card_business_logic import CartItemData, CartData
# Modèles de données de la base de données
from hairbnb.models import TblCart, TblCartItem, TblService, TblUser


@api_view(['GET'])
@firebase_authenticated
@is_owner("user_id")
def get_cart(request, user_id):
    """
    Récupère le contenu du panier pour un utilisateur donné.
    Crée un panier vide si aucun n'existe.
    """
    try:
        # Récupère l'utilisateur ou renvoie une erreur 404.
        user = TblUser.objects.get(idTblUser=user_id)
        # Utilise get_or_create pour récupérer le panier de l'utilisateur ou en créer un
        # s'il n'en a pas. C'est une méthode robuste pour éviter les erreurs.
        cart, created = TblCart.objects.get_or_create(user=user)

        # Si le panier est vide, renvoie une réponse vide structurée.
        if not cart.items.exists():
            return Response({"items": [], "coiffeuse_id": None}, status=200)

        # Détermine la coiffeuse associée au panier en se basant sur le premier service.
        # Cela implique une règle métier où un panier ne peut contenir que des services d'une seule coiffeuse.
        first_service = cart.items.first().service
        first_salon_service = first_service.salon_service.first()
        coiffeuse_id = first_salon_service.salon.coiffeuse.idTblUser.idTblUser if first_salon_service else None

        # Utilise la classe de logique métier CartItemData pour formater chaque article.
        # Ceci permet d'appliquer automatiquement les promotions.
        return Response({
            "items": [CartItemData(item).to_dict() for item in cart.items.all()],
            "coiffeuse_id": coiffeuse_id
        }, status=200)

    except TblUser.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)
    except Exception as e:
        return Response({"error": f"Erreur interne : {str(e)}"}, status=500)


@api_view(['POST'])
@firebase_authenticated
@is_owner("user_id")
def add_to_cart(request):
    """
    Ajoute un service au panier d'un utilisateur.
    Si le service est déjà présent, sa quantité est incrémentée.
    """
    # Récupère les informations depuis le corps de la requête POST.
    user_id = request.data.get('user_id')
    service_id = request.data.get('service_id')
    quantity = int(request.data.get('quantity', 1))

    # Valide l'existence de l'utilisateur et du service.
    user = get_object_or_404(TblUser, idTblUser=user_id)
    service = get_object_or_404(TblService, idTblService=service_id)

    # Récupère ou crée le panier pour l'utilisateur.
    cart, created = TblCart.objects.get_or_create(user=user)

    # Récupère ou crée l'article dans le panier.
    # Si 'created' est False, l'article existait déjà.
    cart_item, created = TblCartItem.objects.get_or_create(cart=cart, service=service)
    if not created:
        # Si l'article existait, on augmente simplement la quantité.
        cart_item.quantity += quantity
    cart_item.save()

    # Retourne un message de succès et l'état complet et à jour du panier.
    return Response({"message": "Service ajouté au panier ✅", "cart": CartData(cart).to_dict()}, status=200)


@csrf_exempt
@api_view(['DELETE'])
@firebase_authenticated
@is_owner("user_id")
def remove_from_cart(request):
    """
    Supprime un article spécifique du panier d'un utilisateur.
    """
    # Récupère les IDs depuis le corps de la requête DELETE.
    user_id = request.data.get('user_id')
    service_id = request.data.get('service_id')

    # Récupère les objets nécessaires de la base de données.
    user = get_object_or_404(TblUser, idTblUser=user_id)
    cart = get_object_or_404(TblCart, user=user)
    cart_item = get_object_or_404(TblCartItem, cart=cart, service_id=service_id)

    # Supprime l'article du panier.
    cart_item.delete()

    # Retourne un message de succès et l'état à jour du panier.
    return Response({"message": "Service supprimé du panier ✅", "cart": CartData(cart).to_dict()}, status=200)


@api_view(['DELETE'])
def clear_cart(request):
    """
    Supprime tous les articles du panier d'un utilisateur.
    NOTE : Cette vue n'a pas de décorateur d'authentification dans le code fourni.
    """
    # Récupère l'ID utilisateur depuis le corps de la requête.
    user_id = request.data.get('user_id')

    # Récupère le panier de l'utilisateur.
    user = get_object_or_404(TblUser, idTblUser=user_id)
    cart = get_object_or_404(TblCart, user=user)

    # Supprime tous les objets TblCartItem liés à ce panier.
    cart.items.all().delete()

    # Retourne un message de succès et le panier désormais vide.
    return Response({"message": "Panier vidé ✅", "cart": CartData(cart).to_dict()}, status=200)









# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# from django.shortcuts import get_object_or_404
#
# from decorators.decorators import firebase_authenticated, is_owner
# from hairbnb.card.card_business_logic import CartItemData, CartData
# from hairbnb.models import TblCart, TblCartItem, TblService, TblUser
#
# @api_view(['GET'])
# @firebase_authenticated
# @is_owner("user_id")
# def get_cart(request, user_id):
#     try:
#         user = TblUser.objects.get(idTblUser=user_id)  # Vérifie l'utilisateur
#         cart, created = TblCart.objects.get_or_create(user=user)  # Récupère ou crée le panier
#
#         if not cart.items.exists():
#             return Response({"items": [], "coiffeuse_id": None}, status=200)
#
#         # ✅ Correction : Récupérer la coiffeuse via la table de liaison
#         first_service = cart.items.first().service
#         first_salon_service = first_service.salon_service.first()  # Prend la première relation
#         coiffeuse_id = first_salon_service.salon.coiffeuse.idTblUser.idTblUser if first_salon_service else None
#
#         return Response({
#             "items": [CartItemData(item).to_dict() for item in cart.items.all()],  # ✅ Inclut maintenant la promo
#             "coiffeuse_id": coiffeuse_id
#         }, status=200)
#
#     except TblUser.DoesNotExist:
#         return Response({"error": "Utilisateur introuvable"}, status=404)
#
#     except Exception as e:
#         return Response({"error": f"Erreur interne : {str(e)}"}, status=500)
#
#
# # ➕ **Ajouter un service au panier**
# @api_view(['POST'])
# @firebase_authenticated
# @is_owner("user_id")
# def add_to_cart(request):
#     """
#     Ajouter un service au panier via l'ID utilisateur et l'ID service.
#     """
#     user_id = request.data.get('user_id')  # Récupère l'ID utilisateur envoyé dans la requête
#     service_id = request.data.get('service_id')
#     quantity = int(request.data.get('quantity', 1))
#
#     user = get_object_or_404(TblUser, idTblUser=user_id)  # Vérifie si l'utilisateur existe
#     service = get_object_or_404(TblService, idTblService=service_id)  # Vérifie si le service existe
#
#     cart, created = TblCart.objects.get_or_create(user=user)  # Récupère ou crée le panier
#
#     # Vérifier si le service est déjà dans le panier
#     cart_item, created = TblCartItem.objects.get_or_create(cart=cart, service=service)
#     if not created:
#         cart_item.quantity += quantity  # Incrémente si déjà présent
#     cart_item.save()
#
#     return Response({"message": "Service ajouté au panier ✅", "cart": CartData(cart).to_dict()}, status=200)
#
#
# # ❌ **Supprimer un service du panier**
# @csrf_exempt
# @api_view(['DELETE'])
# @firebase_authenticated
# @is_owner("user_id")
# def remove_from_cart(request):
#     """
#     Supprime un service du panier d'un utilisateur spécifique.
#     """
#     user_id = request.data.get('user_id')  # Récupère l'ID utilisateur
#     service_id = request.data.get('service_id')  # Récupère l'ID du service
#
#     user = get_object_or_404(TblUser, idTblUser=user_id)
#     cart = get_object_or_404(TblCart, user=user)  # Récupère le panier de l'utilisateur
#     cart_item = get_object_or_404(TblCartItem, cart=cart, service_id=service_id)  # Récupère l'élément à supprimer
#
#     cart_item.delete()  # Supprime l'article du panier
#
#     return Response({"message": "Service supprimé du panier ✅", "cart": CartData(cart).to_dict()}, status=200)
#
#
# # 🗑 **Vider complètement le panier d'un utilisateur**
# @api_view(['DELETE'])
# def clear_cart(request):
#     """
#     Vide le panier d'un utilisateur via son ID.
#     """
#     user_id = request.data.get('user_id')  # Récupère l'ID utilisateur
#
#     user = get_object_or_404(TblUser, idTblUser=user_id)
#     cart = get_object_or_404(TblCart, user=user)
#     cart.items.all().delete()  # Supprime tous les articles du panier
#
#     return Response({"message": "Panier vidé ✅", "cart": CartData(cart).to_dict()}, status=200)
