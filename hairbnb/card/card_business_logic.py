################################################################################
#                                                                              #
#         LOGIQUE MÉTIER ET CLASSES DE DONNÉES POUR LE PANIER D'ACHAT            #
#                                                                              #
#  Ce fichier définit la logique métier et les structures de données (DTOs)    #
#  pour la fonctionnalité de panier d'achat de l'application "hairbnb".        #
#                                                                              #
#  Sa responsabilité principale est de transformer les modèles de données      #
#  bruts en objets structurés, tout en encapsulant la logique complexe         #
#  d'application des promotions actives aux services contenus dans le panier.  #
#                                                                              #
################################################################################

# --- Importations ---
# Classe de données pour l'utilisateur actuellement connecté
from hairbnb.currentUser.currentUser_business_logic import CurrentUserData
# Modèle de données pour les promotions
from hairbnb.models import TblPromotion
# Utilitaire Django pour obtenir l'heure et la date actuelles avec gestion du fuseau horaire
from django.utils.timezone import now
# Type de données pour des calculs monétaires précis, évitant les erreurs d'arrondi
from decimal import Decimal


class CartItemData:
    """
    Représente un article unique dans le panier d'achat.
    Cette classe gère les détails du service et applique automatiquement
    toute promotion active pour calculer le prix final.
    """
    def __init__(self, cart_item):
        # Initialise les propriétés de base de l'article du panier.
        self.id = cart_item.idTblCartItem
        # Appelle une méthode privée pour récupérer et traiter les données du service associé.
        self.service = self._get_service_data(cart_item.service)
        self.quantity = cart_item.quantity

    def _get_service_data(self, service):
        """
        Méthode privée pour récupérer les informations d'un service et
        appliquer la logique de promotion.
        """
        # Récupère le prix standard du service depuis la base de données.
        prix_standard = service.service_prix.first().prix.prix if service.service_prix.exists() else Decimal("0.00")

        # Recherche une promotion active pour ce service.
        # Une promotion est active si la date actuelle est entre sa date de début et de fin.
        promo = TblPromotion.objects.filter(
            service=service,
            start_date__lte=now(),
            end_date__gte=now()
        ).first()

        # Applique la promotion si une promotion active a été trouvée.
        if promo:
            # Calcule le montant de la réduction et le prix final.
            reduction = (promo.discount_percentage / Decimal("100")) * prix_standard
            prix_final = prix_standard - reduction
            # Structure les données de la promotion pour les inclure dans la réponse.
            promo_data = {
                "idPromotion": promo.idPromotion,
                "service_id": service.idTblService,
                "discount_percentage": promo.discount_percentage,
                "start_date": promo.start_date,
                "end_date": promo.end_date,
                "is_active": promo.is_active()
            }
        else:
            # S'il n'y a pas de promotion, le prix final est le prix standard.
            prix_final = prix_standard
            promo_data = None

        # Retourne un dictionnaire structuré avec toutes les informations du service,
        # y compris le prix original et le prix final après promotion.
        return {
            "idTblService": service.idTblService,
            "intitule_service": service.intitule_service,
            "description": service.description,
            "temps_minutes": service.service_temps.first().temps.minutes if service.service_temps.exists() else 0,
            "prix": float(prix_standard),
            "promotion": promo_data,
            "prix_final": float(prix_final)
        }

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__



class CartData:
    """
    Représente l'ensemble du panier d'achat, y compris l'utilisateur
    et la liste de tous les articles qu'il contient.
    """
    def __init__(self, cart):
        self.idTblCart = cart.idTblCart
        # Réutilise la classe CurrentUserData pour formater les informations de l'utilisateur.
        self.user = CurrentUserData(cart.user).to_dict()
        # Crée une liste de tous les articles du panier, en utilisant CartItemData pour chacun.
        self.items = [CartItemData(item).to_dict() for item in cart.items.all()]
        # Appelle une méthode du modèle 'TblCart' pour calculer le prix total du panier.
        self.total_price = cart.total_price()

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__








# from hairbnb.currentUser.currentUser_business_logic import CurrentUserData
# from hairbnb.models import TblPromotion
# from django.utils.timezone import now
# from decimal import Decimal
#
#
# class CartItemData:
#     def __init__(self, cart_item):
#         self.id = cart_item.idTblCartItem
#         self.service = self._get_service_data(cart_item.service)
#         self.quantity = cart_item.quantity
#
#     def _get_service_data(self, service):
#         """ Récupère les informations du service et applique la promotion si disponible """
#         prix_standard = service.service_prix.first().prix.prix if service.service_prix.exists() else Decimal("0.00")
#
#         # Vérifier s'il y a une promotion active
#         promo = TblPromotion.objects.filter(
#             service=service,
#             start_date__lte=now(),
#             end_date__gte=now()
#         ).first()
#
#         if promo:  # Appliquer la réduction
#             reduction = (promo.discount_percentage / Decimal("100")) * prix_standard
#             prix_final = prix_standard - reduction
#             promo_data = {
#                 "idPromotion": promo.idPromotion,
#                 "service_id": service.idTblService,
#                 "discount_percentage": promo.discount_percentage,
#                 "start_date": promo.start_date,
#                 "end_date": promo.end_date,
#                 "is_active": promo.is_active()
#             }
#         else:  # Pas de promo
#             prix_final = prix_standard
#             promo_data = None
#
#         return {
#             "idTblService": service.idTblService,
#             "intitule_service": service.intitule_service,
#             "description": service.description,
#             "temps_minutes": service.service_temps.first().temps.minutes if service.service_temps.exists() else 0,
#             "prix": float(prix_standard),
#             "promotion": promo_data,
#             "prix_final": float(prix_final)  # ✅ Prix recalculé avec promo appliquée
#         }
#
#     def to_dict(self):
#         return self.__dict__
#
#
#
# class CartData:
#     def __init__(self, cart):
#         self.idTblCart = cart.idTblCart
#         self.user = CurrentUserData(cart.user).to_dict()  # Réutilise CurrentUserData
#         self.items = [CartItemData(item).to_dict() for item in cart.items.all()]
#         self.total_price = cart.total_price()  # Méthode qui calcule le total
#
#     def to_dict(self):
#         return self.__dict__