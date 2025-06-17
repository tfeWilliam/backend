################################################################################
#                                                                              #
#    CLASSES DE FORMATAGE DE DONNÉES (DTO) POUR SERVICES ET SALONS AVEC PROMOS   #
#                                                                              #
#  Ce fichier contient des classes Python (Data Transfer Objects) conçues      #
#  pour transformer les modèles complexes de Django en dictionnaires Python    #
#  structurés et prêts à l'emploi, notamment pour les API.                     #
#                                                                              #
#  - ServiceData: Formate un service individuel en y agrégeant son prix, son   #
#    temps, et surtout, en calculant et classifiant ses promotions (actives,   #
#    futures, expirées).                                                       #
#                                                                              #
#  - SalonDataWithPromotions: Formate un salon complet, en se concentrant sur  #
#    le traitement des services. Elle les groupe par catégorie, calcule les    #
#    prix et promotions spécifiques à ce salon, et génère des statistiques.    #
#                                                                              #
################################################################################

from django.utils import timezone
from django.utils.timezone import now
from decimal import Decimal
from hairbnb.models import TblPromotion, TblSalonService


################################################################################
#                   CLASSE DE FORMATAGE POUR UN SERVICE UNIQUE                 #
################################################################################

class ServiceData:
    """
    Formate les données d'un objet service individuel, en y incluant la
    logique complexe de gestion et de classification de ses promotions.
    """
    def __init__(self, service):
        # --- Initialisation des données de base du service ---
        self.idTblService = service.idTblService
        self.intitule_service = service.intitule_service
        self.description = service.description

        # --- Récupération des données de la catégorie liée ---
        self.category_id = service.categorie.idTblCategorie if service.categorie else None
        self.category_name = service.categorie.intitule_categorie if service.categorie else None

        # --- Récupération du temps et du prix de base du service ---
        # On utilise .first() car on suppose une relation principale pour le temps/prix de base.
        service_temps = service.service_temps.first()
        self.temps_minutes = service_temps.temps.minutes if service_temps else None
        service_prix = service.service_prix.first()
        self.prix = service_prix.prix.prix if service_prix else None

        # --- Logique de traitement des promotions ---
        self.promotion_active = None
        self.promotions_a_venir = []
        self.promotions_expirees = []
        self.prix_final = self.prix  # Le prix final est initialisé au prix de base.

        now_date = now()

        # 1. Recherche de la promotion actuellement active pour ce service.
        active_promo = service.promotions.filter(
            start_date__lte=now_date,
            end_date__gte=now_date
        ).first()
        if active_promo:
            self.promotion_active = self._format_promotion(active_promo)
            # Si une promotion est active, on calcule le prix final avec la réduction.
            self.prix_final = self.prix * (1 - (active_promo.discount_percentage / 100))

        # 2. Recherche de toutes les promotions futures, triées par date de début.
        future_promos = service.promotions.filter(
            start_date__gt=now_date
        ).order_by('start_date')
        for promo in future_promos:
            self.promotions_a_venir.append(self._format_promotion(promo))

        # 3. Recherche des promotions expirées les plus récentes (avec une limite).
        # On calcule combien de places il reste pour ne pas dépasser 10 promotions au total.
        remaining_slots = 10 - (1 if active_promo else 0) - len(self.promotions_a_venir)
        if remaining_slots > 0:
            expired_promos = service.promotions.filter(
                end_date__lt=now_date
            ).order_by('-end_date')[:remaining_slots]  # Les plus récentes d'abord.
            for promo in expired_promos:
                self.promotions_expirees.append(self._format_promotion(promo))

    def _format_promotion(self, promo):
        """
        Méthode utilitaire pour formater un objet TblPromotion en un dictionnaire standardisé.
        """
        now_date = now()
        # Détermine le statut de la promotion en comparant ses dates avec la date actuelle.
        status = "active" if promo.start_date <= now_date <= promo.end_date else (
            "future" if promo.start_date > now_date else "expired"
        )
        return {
            "idPromotion": promo.idPromotion,
            "service_id": promo.service.idTblService,
            "discount_percentage": promo.discount_percentage,
            "start_date": promo.start_date.isoformat(),
            "end_date": promo.end_date.isoformat(),
            "status": status
        }

    def to_dict(self):
        """Convertit l'instance de la classe en un dictionnaire."""
        return self.__dict__


################################################################################
#          CLASSE DE FORMATAGE POUR UN SALON AVEC GESTION DES PROMOTIONS       #
################################################################################

class SalonDataWithPromotions:
    """
    Classe de formatage pour les données complètes d'un salon. Sa principale
    responsabilité est de traiter les services en appliquant les prix et
    promotions spécifiques au salon, puis de les grouper par catégorie.
    """

    def __init__(self, salon, filtered_services=None):
        self.salon = salon
        self.filtered_services = filtered_services

    def to_dict(self):
        """
        Construit la représentation complète du salon sous forme de dictionnaire.
        """
        # --- Étape 1 : Récupération des services ---
        # Soit on utilise une liste pré-filtrée, soit on fait une requête optimisée.
        if self.filtered_services is not None:
            salon_services = self.filtered_services
        else:
            # Requête optimisée pour charger en avance les données liées nécessaires.
            salon_services = TblSalonService.objects.filter(
                salon=self.salon
            ).select_related(
                'service', 'service__categorie'
            ).prefetch_related(
                'service__service_prix__prix', 'service__service_temps__temps',
                'service__promotions'
            ).order_by('service__intitule_service')

        # --- Étape 2 : Traitement des services et regroupement par catégorie ---
        services_by_category = {}

        for salon_service in salon_services:
            service = salon_service.service
            category_name = service.categorie.intitule_categorie if service.categorie else "Sans catégorie"

            # Recherche du prix et du temps SPÉCIFIQUES à ce salon pour ce service.
            prix_obj = service.service_prix.filter(salon=self.salon).first()
            temps_obj = service.service_temps.filter(salon=self.salon).first()

            # On ignore le service s'il n'a pas de prix ou de temps défini pour ce salon.
            if not prix_obj or not temps_obj:
                continue

            prix_original = float(prix_obj.prix.prix)
            duree_minutes = temps_obj.temps.minutes

            # Recherche d'une promotion active SPÉCIFIQUE à ce salon ET à ce service.
            promotion_active = TblPromotion.objects.filter(
                salon=self.salon,
                service=service,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).first()

            # Calcul du prix final en fonction de la présence d'une promotion active.
            if promotion_active and promotion_active.is_active():
                prix_final = float(promotion_active.get_prix_avec_promotion(Decimal(str(prix_original))))
                economie = float(promotion_active.get_montant_economise(Decimal(str(prix_original))))
                promotion_data = {
                    "id": promotion_active.idPromotion, "pourcentage": float(promotion_active.discount_percentage),
                    "prix_original": prix_original, "prix_final": prix_final, "economie": economie,
                    "date_debut": promotion_active.start_date.isoformat(), "date_fin": promotion_active.end_date.isoformat(),
                    "est_active": True
                }
            else:
                prix_final = prix_original
                promotion_data = None

            # Construction du dictionnaire de données pour ce service.
            service_data = {
                "idTblService": service.idTblService, "intitule_service": service.intitule_service,
                "description": service.description, "categorie_id": service.categorie.idTblCategorie if service.categorie else None,
                "categorie_nom": category_name, "salon_service_id": salon_service.idSalonService,
                "prix": prix_original, "prix_final": prix_final, "duree_minutes": duree_minutes,
                "promotion": promotion_data
            }

            # Ajout du service à la bonne catégorie dans le dictionnaire de regroupement.
            if category_name not in services_by_category:
                services_by_category[category_name] = {
                    "category_id": service.categorie.idTblCategorie if service.categorie else 0,
                    "category_name": category_name, "services": []
                }
            services_by_category[category_name]["services"].append(service_data)

        # --- Étape 3 : Calcul des statistiques par catégorie ---
        categories_list = []
        for category_name, category_data in services_by_category.items():
            services = category_data["services"]
            if services:
                prix_finaux = [s["prix_final"] for s in services]
                # Ajout des statistiques au dictionnaire de la catégorie.
                category_data.update({
                    "service_count": len(services), "prix_minimum": min(prix_finaux), "prix_maximum": max(prix_finaux)
                })
                categories_list.append(category_data)

        # --- Étape 4 : Construction de l'objet final du salon ---
        return {
            "salon_id": self.salon.idTblSalon, "nom_salon": self.salon.nom_salon,
            "slogan": self.salon.slogan, "a_propos": self.salon.a_propos,
            "logo_salon": self.salon.logo_salon.url if self.salon.logo_salon else None,
            "adresse": self._get_adresse_data(), "position": self.salon.position,
            "proprietaire": self._get_proprietaire_data(),
            "services_by_category": categories_list,
            "total_services": sum(len(cat["services"]) for cat in categories_list),
            "total_categories": len(categories_list)
        }

    def _get_adresse_data(self):
        """Méthode utilitaire pour formater les données d'adresse du salon."""
        if not self.salon.adresse: return None
        adresse = self.salon.adresse
        return {
            "numero": adresse.numero, "rue": adresse.rue.nom_rue,
            "commune": adresse.rue.localite.commune, "code_postal": adresse.rue.localite.code_postal,
            "adresse_complete": str(adresse)
        }

    def _get_proprietaire_data(self):
        """Méthode utilitaire pour formater les données du propriétaire du salon."""
        proprietaire = self.salon.get_proprietaire()
        if not proprietaire: return None
        user = proprietaire.idTblUser
        return {
            "idTblUser": user.idTblUser, "nom": user.nom, "prenom": user.prenom,
            "email": user.email, "photo_profil": user.photo_profil.url if user.photo_profil else None
        }







# from django.utils import timezone
# from django.utils.timezone import now
# from decimal import Decimal
# from hairbnb.models import TblPromotion, TblSalonService
#
#
# # class ServiceData:
# class ServiceData:
#     def __init__(self, service):
#         self.idTblService = service.idTblService
#         self.intitule_service = service.intitule_service
#         self.description = service.description
#
#         # ✅ NOUVEAU : Ajout de la catégorie
#         self.category_id = service.categorie.idTblCategorie if service.categorie else None
#         self.category_name = service.categorie.intitule_categorie if service.categorie else None
#
#         # Récupération du temps
#         service_temps = service.service_temps.first()
#         self.temps_minutes = service_temps.temps.minutes if service_temps else None
#         # Récupération du prix
#         service_prix = service.service_prix.first()
#         self.prix = service_prix.prix.prix if service_prix else None
#         # Variables pour stocker les promotions
#         self.promotion_active = None
#         self.promotions_a_venir = []
#         self.promotions_expirees = []
#         self.prix_final = self.prix
#         # Récupère toutes les promotions pour le service
#         now_date = now()
#         # 1. Récupérer la promotion active
#         active_promo = service.promotions.filter(
#             start_date__lte=now_date,
#             end_date__gte=now_date
#         ).first()
#         if active_promo:
#             self.promotion_active = self._format_promotion(active_promo)
#             # Calcul du prix final avec la réduction active
#             self.prix_final = self.prix * (1 - (active_promo.discount_percentage / 100))
#         # 2. Récupérer les promotions à venir (max toutes)
#         future_promos = service.promotions.filter(
#             start_date__gt=now_date
#         ).order_by('start_date')
#         for promo in future_promos:
#             self.promotions_a_venir.append(self._format_promotion(promo))
#         # 3. Récupérer les promotions expirées
#         # Calculer combien on peut encore prendre pour atteindre le total de 10
#         remaining_slots = 10 - (1 if active_promo else 0) - len(self.promotions_a_venir)
#         if remaining_slots > 0:
#             expired_promos = service.promotions.filter(
#                 end_date__lt=now_date
#             ).order_by('-end_date')[:remaining_slots]  # Trier par date de fin décroissante (récentes d'abord)
#             for promo in expired_promos:
#                 self.promotions_expirees.append(self._format_promotion(promo))
#
#     def _format_promotion(self, promo):
#         """Formate une promotion en dictionnaire"""
#         now_date = now()
#         status = "active" if promo.start_date <= now_date <= promo.end_date else (
#             "future" if promo.start_date > now_date else "expired"
#         )
#         return {
#             "idPromotion": promo.idPromotion,
#             "service_id": promo.service.idTblService,
#             "discount_percentage": promo.discount_percentage,
#             "start_date": promo.start_date.isoformat(),
#             "end_date": promo.end_date.isoformat(),
#             "status": status
#         }
#
#     def to_dict(self):
#         return self.__dict__
#
#
# class SalonDataWithPromotions:
#     """
#     Classe pour sérialiser les données d'un salon avec gestion des promotions.
#     Remplace ou complète la classe SalonData originale.
#     """
#
#     def __init__(self, salon, filtered_services=None):
#         self.salon = salon
#         self.filtered_services = filtered_services
#
#     def to_dict(self):
#         """
#         Convertit les données du salon en dictionnaire avec promotions intégrées.
#         """
#         # Récupérer les services
#         if self.filtered_services is not None:
#             salon_services = self.filtered_services
#         else:
#             salon_services = TblSalonService.objects.filter(
#                 salon=self.salon
#             ).select_related(
#                 'service',
#                 'service__categorie'
#             ).prefetch_related(
#                 'service__service_prix__prix',
#                 'service__service_temps__temps',
#                 'service__promotions'
#             ).order_by('service__intitule_service')
#
#         # Grouper par catégorie avec promotions
#         services_by_category = {}
#
#         for salon_service in salon_services:
#             service = salon_service.service
#             category_name = service.categorie.intitule_categorie if service.categorie else "Sans catégorie"
#
#             # ✅ Récupérer le prix et le temps pour ce salon spécifique
#             prix_obj = service.service_prix.filter(salon=self.salon).first()
#             temps_obj = service.service_temps.filter(salon=self.salon).first()
#
#             if not prix_obj or not temps_obj:
#                 continue  # Skip si pas de prix/temps défini pour ce salon
#
#             prix_original = float(prix_obj.prix.prix)
#             duree_minutes = temps_obj.temps.minutes
#
#             # ✅ Vérifier les promotions actives pour ce salon et ce service
#             promotion_active = TblPromotion.objects.filter(
#                 salon=self.salon,
#                 service=service,
#                 start_date__lte=timezone.now(),
#                 end_date__gte=timezone.now()
#             ).first()
#
#             # ✅ Calculer le prix final et les économies
#             if promotion_active and promotion_active.is_active():
#                 prix_final = float(promotion_active.get_prix_avec_promotion(Decimal(str(prix_original))))
#                 economie = float(promotion_active.get_montant_economise(Decimal(str(prix_original))))
#
#                 promotion_data = {
#                     "id": promotion_active.idPromotion,
#                     "pourcentage": float(promotion_active.discount_percentage),
#                     "prix_original": prix_original,
#                     "prix_final": prix_final,
#                     "economie": economie,
#                     "date_debut": promotion_active.start_date.isoformat(),
#                     "date_fin": promotion_active.end_date.isoformat(),
#                     "est_active": True
#                 }
#             else:
#                 prix_final = prix_original
#                 promotion_data = None
#
#             # ✅ Structure des données du service avec promotions
#             service_data = {
#                 "idTblService": service.idTblService,
#                 "intitule_service": service.intitule_service,
#                 "description": service.description,
#                 "categorie_id": service.categorie.idTblCategorie if service.categorie else None,
#                 "categorie_nom": category_name,
#                 "salon_service_id": salon_service.idSalonService,
#                 "prix": prix_original,
#                 "prix_final": prix_final,  # ✅ Prix après promotion
#                 "duree_minutes": duree_minutes,
#                 "promotion": promotion_data  # ✅ Données de promotion si applicable
#             }
#
#             # Ajouter à la catégorie
#             if category_name not in services_by_category:
#                 services_by_category[category_name] = {
#                     "category_id": service.categorie.idTblCategorie if service.categorie else 0,
#                     "category_name": category_name,
#                     "services": []
#                 }
#
#             services_by_category[category_name]["services"].append(service_data)
#
#         # ✅ Convertir en liste et calculer les statistiques par catégorie
#         categories_list = []
#         for category_name, category_data in services_by_category.items():
#             services = category_data["services"]
#             if services:  # Seulement si la catégorie a des services
#                 prix_finaux = [s["prix_final"] for s in services]
#                 category_data.update({
#                     "service_count": len(services),
#                     "prix_minimum": min(prix_finaux),
#                     "prix_maximum": max(prix_finaux)
#                 })
#                 categories_list.append(category_data)
#
#         # ✅ Données complètes du salon
#         return {
#             "salon_id": self.salon.idTblSalon,
#             "nom_salon": self.salon.nom_salon,
#             "slogan": self.salon.slogan,
#             "a_propos": self.salon.a_propos,
#             "logo_salon": self.salon.logo_salon.url if self.salon.logo_salon else None,
#             "adresse": self._get_adresse_data(),
#             "position": self.salon.position,
#             "proprietaire": self._get_proprietaire_data(),
#             "services_by_category": categories_list,
#             "total_services": sum(len(cat["services"]) for cat in categories_list),
#             "total_categories": len(categories_list)
#         }
#
#     def _get_adresse_data(self):
#         """Récupère les données d'adresse du salon."""
#         if not self.salon.adresse:
#             return None
#
#         adresse = self.salon.adresse
#         return {
#             "numero": adresse.numero,
#             "rue": adresse.rue.nom_rue,
#             "commune": adresse.rue.localite.commune,
#             "code_postal": adresse.rue.localite.code_postal,
#             "adresse_complete": str(adresse)
#         }
#
#     def _get_proprietaire_data(self):
#         """Récupère les données du propriétaire du salon."""
#         proprietaire = self.salon.get_proprietaire()
#         if not proprietaire:
#             return None
#
#         user = proprietaire.idTblUser
#         return {
#             "idTblUser": user.idTblUser,
#             "nom": user.nom,
#             "prenom": user.prenom,
#             "email": user.email,
#             "photo_profil": user.photo_profil.url if user.photo_profil else None
#         }