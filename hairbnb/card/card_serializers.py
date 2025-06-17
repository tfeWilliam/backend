################################################################################
#                                                                              #
#         SÉRIALISEURS POUR LE PANIER D'ACHAT (DJANGO REST FRAMEWORK)          #
#                                                                              #
#  Ce fichier définit les sérialiseurs (serializers) pour les modèles du      #
#  panier d'achat (`TblCart` et `TblCartItem`). Leur rôle est de convertir      #
#  les données de la base de données en un format JSON structuré pour les      #
#  réponses de l'API.                                                          #
#                                                                              #
#  Ils gèrent l'inclusion de données provenant de modèles liés (comme le nom   #
#  du service ou de l'utilisateur) et de champs calculés (comme le prix       #
#  total du panier).                                                           #
#                                                                              #
################################################################################

# --- Importations ---
# Importation du module de sérialiseurs de Django REST Framework.
from rest_framework import serializers
# Importation des modèles de données pour le panier et ses articles.
from hairbnb.models import TblCart, TblCartItem

class CartItemSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle TblCartItem.
    Représente un article unique dans le panier.
    """
    # Champ en lecture seule qui récupère le nom du service via la relation ForeignKey.
    # 'source' indique le chemin d'accès à l'attribut sur le modèle lié.
    service_name = serializers.CharField(source='service.intitule_service', read_only=True)
    # Champ dont la valeur est calculée par une méthode personnalisée de ce sérialiseur.
    service_price = serializers.SerializerMethodField()

    class Meta:
        # Lie ce sérialiseur au modèle TblCartItem.
        model = TblCartItem
        # Définit les champs du modèle et les champs personnalisés à inclure dans la sortie JSON.
        fields = ['idTblCartItem', 'cart', 'service', 'service_name', 'service_price', 'quantity']

    def get_service_price(self, obj):
        """
        Méthode personnalisée pour calculer la valeur du champ 'service_price'.
        Elle navigue à travers les relations pour trouver le prix associé au service.
        """
        try:
            # Tente d'accéder au prix en suivant le chemin des relations.
            return obj.service.service_prix.first().prix.prix
        except AttributeError:
            # Si un des objets liés n'existe pas (ex: pas de prix défini),
            # on retourne None pour éviter une erreur serveur.
            return None

class CartSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle TblCart.
    Représente le panier d'achat dans son ensemble, incluant tous ses articles.
    """
    # Champ en lecture seule pour afficher le nom de l'utilisateur propriétaire du panier.
    user_name = serializers.CharField(source='user.nom', read_only=True)
    # Champ calculé par la méthode 'get_total_price'.
    total_price = serializers.SerializerMethodField()
    # Champ imbriqué qui utilise CartItemSerializer pour afficher une liste de tous les articles du panier.
    # 'many=True' indique qu'il s'agit d'une liste.
    # 'read_only=True' car les articles sont gérés séparément.
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        # Lie ce sérialiseur au modèle TblCart.
        model = TblCart
        # Champs à inclure dans la représentation JSON du panier.
        fields = ['idTblCart', 'user', 'user_name', 'created_at', 'total_price', 'items']

    def get_total_price(self, obj):
        """
        Calcule le prix total du panier en appelant une méthode définie sur le modèle TblCart.
        Cela permet de centraliser la logique de calcul dans le modèle lui-même.
        """
        return obj.total_price()










# from rest_framework import serializers
# from hairbnb.models import TblCart, TblCartItem
#
# class CartItemSerializer(serializers.ModelSerializer):
#     service_name = serializers.CharField(source='service.intitule_service', read_only=True)
#     service_price = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblCartItem
#         fields = ['idTblCartItem', 'cart', 'service', 'service_name', 'service_price', 'quantity']
#
#     def get_service_price(self, obj):
#         """ Récupère le prix du service via la relation `TblServicePrix` """
#         try:
#             return obj.service.service_prix.first().prix.prix
#         except AttributeError:
#             return None
#
# class CartSerializer(serializers.ModelSerializer):
#     user_name = serializers.CharField(source='user.nom', read_only=True)
#     total_price = serializers.SerializerMethodField()
#     items = CartItemSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = TblCart
#         fields = ['idTblCart', 'user', 'user_name', 'created_at', 'total_price', 'items']
#
#     def get_total_price(self, obj):
#         """ Calcule le prix total du panier """
#         return obj.total_price()
