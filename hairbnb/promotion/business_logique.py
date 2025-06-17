################################################################################
#                                                                              #
#         LOGIQUE MÉTIER POUR LA GESTION DES PROMOTIONS (HAIRBNB)              #
#                                                                              #
#  Ce fichier définit la classe `PromotionManager`, qui encapsule toute la     #
#  logique métier liée à la gestion des promotions pour un service donné.      #
#                                                                              #
#  Lors de son initialisation, elle récupère et catégorise efficacement       #
#  toutes les promotions (actives, à venir, expirées) en une seule fois pour   #
#  éviter des requêtes multiples à la base de données.                         #
#                                                                              #
#  Elle fournit ensuite des méthodes simples pour accéder à ces données de     #
#  manière structurée, y compris la pagination pour les promotions expirées.   #
#                                                                              #
################################################################################

# --- Importations ---
# Utilitaire Django pour obtenir l'heure et la date actuelles avec gestion du fuseau horaire
from django.utils.timezone import now
# Classe de Django pour gérer la pagination des listes de résultats
from django.core.paginator import Paginator


class PromotionManager:
    """
    Gère et organise les promotions pour un service spécifique.
    """
    def __init__(self, service):
        # Stocke le service concerné et l'heure actuelle pour les comparaisons.
        self.service = service
        self.now = now()

        # --- Étape 1 : Récupération et Catégorisation des Promotions ---
        # Récupère toutes les promotions liées à ce service en une seule requête,
        # triées par date de début pour un traitement logique.
        self.promos = list(service.promotions.all().order_by('-start_date'))

        # Initialise des listes pour chaque catégorie de promotion.
        self.active = []
        self.upcoming = []
        self.expired = []

        # Itère sur la liste pré-chargée pour trier chaque promotion dans la bonne catégorie.
        for promo in self.promos:
            if promo.start_date <= self.now <= promo.end_date:
                self.active.append(promo)  # La promotion est actuellement en cours.
            elif promo.start_date > self.now:
                self.upcoming.append(promo) # La promotion commencera dans le futur.
            else:
                self.expired.append(promo)  # La promotion est terminée.

        # Calcule et stocke le nombre de promotions dans chaque catégorie.
        self.count_upcoming = len(self.upcoming)
        self.count_expired = len(self.expired)

    def serialize(self, promo, status):
        """
        Méthode utilitaire pour formater un objet promotion en un dictionnaire propre.
        """
        return {
            "idPromotion": promo.idPromotion,
            "service_id": promo.service.idTblService,
            "discount_percentage": float(promo.discount_percentage),
            "start_date": promo.start_date.isoformat(),
            "end_date": promo.end_date.isoformat(),
            "status": status
        }

    def get_active(self):
        """
        Retourne la promotion actuellement active, s'il y en a une.
        (Suppose qu'il ne peut y avoir qu'une seule promotion active à la fois).
        """
        if self.active:
            return self.serialize(self.active[0], "active")
        return None

    def get_upcoming(self, limit=4):
        """
        Retourne une liste des prochaines promotions, avec une limite optionnelle.
        """
        return [self.serialize(p, "upcoming") for p in self.upcoming[:limit]]

    def get_expired(self, page=1, page_size=5):
        """
        Retourne une liste paginée des promotions expirées.
        """
        # Utilise le Paginator de Django pour gérer la découpe en pages.
        paginator = Paginator(self.expired, page_size)
        page_obj = paginator.get_page(page)

        # Construit une réponse structurée avec les résultats et les métadonnées de pagination.
        return {
            "results": [self.serialize(p, "expired") for p in page_obj],
            "page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_items": paginator.count,
        }

    def get_counts(self):
        """
        Retourne le nombre de promotions dans chaque catégorie.
        """
        return {
            "upcoming": self.count_upcoming,
            "expired": self.count_expired,
            "active": 1 if self.active else 0,
        }







# from django.utils.timezone import now
# from django.core.paginator import Paginator
#
# class PromotionManager:
#     def __init__(self, service):
#         self.service = service
#         self.now = now()
#
#         # Préchargement de toutes les promotions, triées par date de début
#         self.promos = list(service.promotions.all().order_by('-start_date'))
#
#         # Séparation par catégorie
#         self.active = []
#         self.upcoming = []
#         self.expired = []
#
#         for promo in self.promos:
#             if promo.start_date <= self.now <= promo.end_date:
#                 self.active.append(promo)
#             elif promo.start_date > self.now:
#                 self.upcoming.append(promo)
#             else:
#                 self.expired.append(promo)
#
#         # Comptages
#         self.count_upcoming = len(self.upcoming)
#         self.count_expired = len(self.expired)
#
#     def serialize(self, promo, status):
#         return {
#             "idPromotion": promo.idPromotion,
#             "service_id": promo.service.idTblService,
#             "discount_percentage": float(promo.discount_percentage),
#             "start_date": promo.start_date.isoformat(),
#             "end_date": promo.end_date.isoformat(),
#             "status": status
#         }
#
#     def get_active(self):
#         if self.active:
#             return self.serialize(self.active[0], "active")
#         return None
#
#     def get_upcoming(self, limit=4):
#         return [self.serialize(p, "upcoming") for p in self.upcoming[:limit]]
#
#     def get_expired(self, page=1, page_size=5):
#         paginator = Paginator(self.expired, page_size)
#         page_obj = paginator.get_page(page)
#         return {
#             "results": [self.serialize(p, "expired") for p in page_obj],
#             "page": page_obj.number,
#             "total_pages": paginator.num_pages,
#             "total_items": paginator.count,
#         }
#
#     def get_counts(self):
#         return {
#             "upcoming": self.count_upcoming,
#             "expired": self.count_expired,
#             "active": 1 if self.active else 0,
#         }
