################################################################################
#                                                                              #
#              LOGIQUE MÉTIER ET CLASSES DE DONNÉES (HAIRBNB)                  #
#                                                                              #
#  Ce fichier constitue la couche de logique métier (Business Logic Layer) de  #
#  l'application. Il contient deux types de classes principaux :               #
#                                                                              #
#  1. Classes de Données (DTOs) : Des classes comme `CoiffeuseData`,           #
#     `ClientData`, `RendezVousData`, etc. Leur rôle est de transformer les    #
#     modèles de données bruts de Django en objets Python propres et           #
#     structurés. Cela permet de standardiser et de simplifier la              #
#     manipulation des données dans le reste de l'application.                 #
#                                                                              #
#  2. Classes "Manager" : Des classes comme `DisponibiliteManager` et          #
#     `RendezVousManager` qui encapsulent des logiques complexes, comme le     #
#     calcul des créneaux de disponibilité ou le filtrage avancé des           #
#     rendez-vous.                                                             #
#                                                                              #
################################################################################

# --- Importations ---
from datetime import datetime, timedelta
import stripe
from hairbnb.models import TblRendezVous, TblHoraireCoiffeuse, TblIndisponibilite
from hairbnb.salon.salon_business_logic import SalonData
from hairbnb.salon_services.salon_services_business_logic import ServiceData
from hairbnb_backend import settings_test_secure


# class CoiffeuseData:
class CoiffeuseData:
    """
    Représente une coiffeuse avec toutes ses informations (profil, utilisateur, adresse).
    """

    def __init__(self, coiffeuse):
        # --- Données du modèle Coiffeuse ---
        self.idTblCoiffeuse = coiffeuse.pk
        self.idTblUser = coiffeuse.idTblUser.idTblUser
        self.denomination_sociale = coiffeuse.denomination_sociale
        self.tva = coiffeuse.tva
        self.position = coiffeuse.position

        # --- Données du modèle User lié ---
        user = coiffeuse.idTblUser
        self.uuid = user.uuid
        self.nom = user.nom
        self.prenom = user.prenom
        self.email = user.email
        self.numero_telephone = user.numero_telephone
        self.date_naissance = user.date_naissance
        self.sexe = user.sexe
        self.is_active = user.is_active
        self.photo_profil = user.photo_profil.url if user.photo_profil else None

        # --- Données de l'adresse liée à l'utilisateur ---
        adresse = user.adresse
        if adresse:
            self.numero = adresse.numero
            self.boite_postale = adresse.boite_postale
            self.nom_rue = adresse.rue.nom_rue
            self.commune = adresse.rue.localite.commune
            self.code_postal = adresse.rue.localite.code_postal
        else:
            self.numero = None
            self.boite_postale = None
            self.nom_rue = None
            self.commune = None
            self.code_postal = None

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


class FullSalonServiceData:
    """
    Représente un service offert par un salon, avec tous les détails
    (service, temps, prix, salon, coiffeuse).
    """

    def __init__(self, salon_service):
        # --- Informations sur le service de base ---
        self.idTblService = salon_service.service.idTblService
        self.intitule_service = salon_service.service.intitule_service
        self.description = salon_service.service.description

        # --- Temps et prix récupérés via les tables de liaison ---
        service_temps = salon_service.service.service_temps.first()
        self.temps_minutes = service_temps.temps.minutes if service_temps else None

        service_prix = salon_service.service.service_prix.first()
        self.prix = service_prix.prix.prix if service_prix else None

        # --- Informations sur le salon et la coiffeuse associés ---
        self.idTblSalon = salon_service.salon.idTblSalon
        self.coiffeuse_id = salon_service.salon.coiffeuse.idTblUser.idTblUser

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


class ClientData:
    """
    Représente un client avec toutes ses informations (profil, utilisateur, adresse).
    """

    def __init__(self, client):
        self.idTblUser = client.idTblUser.idTblUser

        # --- Données du modèle User lié ---
        user = client.idTblUser
        self.uuid = user.uuid
        self.nom = user.nom
        self.prenom = user.prenom
        self.email = user.email
        self.numero_telephone = user.numero_telephone
        self.date_naissance = user.date_naissance
        self.sexe = user.sexe
        self.is_active = user.is_active
        self.photo_profil = user.photo_profil.url if user.photo_profil else None

        # --- Données de l'adresse liée à l'utilisateur ---
        adresse = user.adresse
        if adresse:
            self.numero = adresse.numero
            self.boite_postale = adresse.boite_postale
            self.nom_rue = adresse.rue.nom_rue
            self.commune = adresse.rue.localite.commune
            self.code_postal = adresse.rue.localite.code_postal
        else:
            self.numero = None
            self.boite_postale = None
            self.nom_rue = None
            self.commune = None
            self.code_postal = None

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


from django.utils.timezone import now


class PromotionData:
    """
    Représente une promotion avec son statut d'activité.
    """

    def __init__(self, promotion):
        self.idPromotion = promotion.idPromotion
        self.service_id = promotion.service.idTblService
        self.discount_percentage = promotion.discount_percentage
        self.start_date = promotion.start_date
        self.end_date = promotion.end_date
        # Appelle la méthode du modèle pour savoir si la promotion est active.
        self.is_active = promotion.is_active()

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


class RendezVousServiceData:
    """
    Structure les informations d'un service spécifique au sein d'un rendez-vous.
    """

    def __init__(self, service_instance):
        self.idRendezVousService = service_instance.idRendezVousService
        # Utilise une autre classe de données (ServiceData) pour les détails du service.
        self.service = ServiceData(service_instance.service).to_dict()
        self.prix_applique = service_instance.prix_applique
        self.duree_estimee = service_instance.duree_estimee

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


class RendezVousData:
    """
    Structure un rendez-vous complet avec toutes ses relations (client, coiffeuse, salon, services).
    """

    def __init__(self, rdv):
        self.idRendezVous = rdv.idRendezVous
        # Utilise les autres classes de données pour formater les objets liés.
        self.client = ClientData(rdv.client).to_dict()
        self.coiffeuse = CoiffeuseData(rdv.coiffeuse).to_dict()
        self.salon = SalonData(rdv.salon).to_dict()
        self.date_heure = rdv.date_heure.isoformat()
        self.statut = rdv.statut
        self.total_prix = rdv.total_prix
        self.duree_totale = rdv.duree_totale
        # Construit la liste des services inclus dans le rendez-vous.
        self.services = [RendezVousServiceData(s).to_dict() for s in rdv.rendez_vous_services.all()]

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


# Configuration de la clé API secrète pour les interactions avec Stripe.
stripe.api_key = settings_test_secure.STRIPE_SECRET_KEY


class HoraireCoiffeuseData:
    """
    Représente un horaire de travail d'une coiffeuse pour un jour de la semaine.
    """

    def __init__(self, horaire):
        self.id = horaire.id
        self.coiffeuse_id = horaire.coiffeuse.idTblUser.idTblUser
        # Le jour de la semaine est stocké comme un entier (0 pour Lundi).
        self.jour = horaire.jour
        # Récupère le libellé textuel du jour (ex: "Lundi").
        self.jour_label = horaire.get_jour_display()
        # Formate les heures pour un affichage "HH:MM".
        self.heure_debut = horaire.heure_debut.strftime("%H:%M")
        self.heure_fin = horaire.heure_fin.strftime("%H:%M")

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


class IndisponibiliteData:
    """
    Représente une période d'indisponibilité exceptionnelle pour une coiffeuse.
    """

    def __init__(self, indispo):
        self.id = indispo.id
        self.coiffeuse_id = indispo.coiffeuse.idTblUser.idTblUser

        # S'assure que les dates et heures sont bien formatées en chaînes de caractères.
        self.date = indispo.date.isoformat() if hasattr(indispo.date, 'isoformat') else str(indispo.date)
        self.heure_debut = indispo.heure_debut.strftime("%H:%M") if hasattr(indispo.heure_debut, 'strftime') else str(
            indispo.heure_debut)
        self.heure_fin = indispo.heure_fin.strftime("%H:%M") if hasattr(indispo.heure_fin, 'strftime') else str(
            indispo.heure_fin)

        self.motif = indispo.motif

    def to_dict(self):
        """Convertit l'instance de la classe en dictionnaire."""
        return self.__dict__


class DisponibiliteManager:
    """
    Encapsule la logique complexe de calcul des créneaux de disponibilité
    pour une coiffeuse donnée.
    """

    def __init__(self, coiffeuse):
        self.coiffeuse = coiffeuse

    def get_jours_ouverts(self):
        """Récupère les jours de la semaine où la coiffeuse travaille."""
        return list(
            TblHoraireCoiffeuse.objects.filter(coiffeuse=self.coiffeuse).values_list("jour", flat=True)
        )

    def get_dispos_pour_jour(self, date, duree_minutes=30):
        """
        Calcule tous les créneaux disponibles pour une date et une durée données.
        """
        jour = date.weekday()  # Lundi = 0, Dimanche = 6

        # Étape 1 : Vérifier si la coiffeuse travaille ce jour-là.
        horaire = TblHoraireCoiffeuse.objects.filter(coiffeuse=self.coiffeuse, jour=jour).first()
        if not horaire:
            print("⛔️ Aucune horaire configurée ce jour-là")
            return []

        heure_debut = datetime.combine(date, horaire.heure_debut)
        heure_fin = datetime.combine(date, horaire.heure_fin)

        # Étape 2 : Générer tous les créneaux possibles de la journée.
        slots = []
        current = heure_debut
        while current + timedelta(minutes=duree_minutes) <= heure_fin:
            slot_debut = current
            slot_fin = current + timedelta(minutes=duree_minutes)

            # Étape 3 : Vérifier les conflits pour chaque créneau.
            # Conflit avec une indisponibilité exceptionnelle ?
            indispo = TblIndisponibilite.objects.filter(
                coiffeuse=self.coiffeuse,
                date=date,
                heure_debut__lt=slot_fin.time(),
                heure_fin__gt=slot_debut.time()
            ).exists()

            # Conflit avec un rendez-vous déjà existant ?
            rdv = TblRendezVous.objects.filter(
                coiffeuse=self.coiffeuse,
                date_heure__lt=slot_fin,
                date_heure__gte=slot_debut
            ).exists()

            print("🧪 Créneaux retournés :", [(d.strftime("%H:%M"), f.strftime("%H:%M")) for d, f in slots])

            # Étape 4 : Si aucun conflit, le créneau est disponible.
            if not indispo and not rdv:
                slots.append((slot_debut, slot_fin))

            # Passer au créneau suivant.
            current += timedelta(minutes=duree_minutes)

        return slots


class RendezVousManager:
    """
    Fournit des méthodes simplifiées pour interroger et filtrer les rendez-vous.
    """

    def __init__(self, coiffeuse_id):
        self.coiffeuse_id = coiffeuse_id

    def get_by_statut(self, statut):
        """
        Récupère les rendez-vous d'une coiffeuse filtrés par statut
        (et exclut les rendez-vous archivés).
        """
        queryset = TblRendezVous.objects.filter(
            coiffeuse__idTblUser=self.coiffeuse_id,
            est_archive=False
        )
        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset.order_by('-date_heure')

    def get_by_periode(self, periode, statut=None):
        """

        Récupère les rendez-vous d'une coiffeuse sur une période donnée
        (jour, semaine, mois, année) et optionnellement par statut.
        """
        today = now().date()

        # Définit les dates de début et de fin en fonction de la période demandée.
        if periode == "jour":
            start = today
            end = today + timedelta(days=1)
        elif periode == "semaine":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=7)
        elif periode == "mois":
            start = today.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1)
        elif periode == "annee":
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
        else:
            return TblRendezVous.objects.none()

        # Applique les filtres à la requête.
        queryset = TblRendezVous.objects.filter(
            coiffeuse__idTblUser=self.coiffeuse_id,
            date_heure__date__range=(start, end),
            est_archive=False
        )

        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset.order_by('-date_heure')















# from datetime import datetime, timedelta
# import stripe
# from hairbnb.models import TblRendezVous, TblHoraireCoiffeuse, TblIndisponibilite
# from hairbnb.salon.salon_business_logic import SalonData
# from hairbnb.salon_services.salon_services_business_logic import ServiceData
# from hairbnb_backend import settings_test_old, settings_test
#
#
# # class CoiffeuseData:
# class CoiffeuseData:
#     def __init__(self, coiffeuse):
#         self.idTblCoiffeuse = coiffeuse.pk  # 🔥 Clé primaire
#         self.idTblUser = coiffeuse.idTblUser.idTblUser
#         self.denomination_sociale = coiffeuse.denomination_sociale
#         self.tva = coiffeuse.tva
#         self.position = coiffeuse.position
#
#         # Infos utilisateur
#         user = coiffeuse.idTblUser
#         self.uuid = user.uuid
#         self.nom = user.nom
#         self.prenom = user.prenom
#         self.email = user.email
#         self.numero_telephone = user.numero_telephone
#         self.date_naissance = user.date_naissance
#         self.sexe = user.sexe
#         self.is_active = user.is_active
#         self.photo_profil = user.photo_profil.url if user.photo_profil else None
#
#         # Adresse
#         adresse = user.adresse
#         if adresse:
#             self.numero = adresse.numero
#             self.boite_postale = adresse.boite_postale
#             self.nom_rue = adresse.rue.nom_rue
#             self.commune = adresse.rue.localite.commune
#             self.code_postal = adresse.rue.localite.code_postal
#         else:
#             self.numero = None
#             self.boite_postale = None
#             self.nom_rue = None
#             self.commune = None
#             self.code_postal = None
#
#     def to_dict(self):
#         return self.__dict__
#
# class FullSalonServiceData:
#     def __init__(self, salon_service):
#         # Informations sur le service
#         self.idTblService = salon_service.service.idTblService
#         self.intitule_service = salon_service.service.intitule_service
#         self.description = salon_service.service.description
#
#         # Temps et prix liés au service (via la table de jonction)
#         service_temps = salon_service.service.service_temps.first()
#         self.temps_minutes = service_temps.temps.minutes if service_temps else None
#
#         service_prix = salon_service.service.service_prix.first()
#         self.prix = service_prix.prix.prix if service_prix else None
#
#         # Informations sur le salon et la coiffeuse
#         self.idTblSalon = salon_service.salon.idTblSalon
#         self.coiffeuse_id = salon_service.salon.coiffeuse.idTblUser.idTblUser
#
#     def to_dict(self):
#         return self.__dict__
#
#
# class ClientData:
#     def __init__(self, client):
#         self.idTblUser = client.idTblUser.idTblUser  # ID lié à l'utilisateur
#
#         # Infos utilisateur
#         user = client.idTblUser
#         self.uuid = user.uuid
#         self.nom = user.nom
#         self.prenom = user.prenom
#         self.email = user.email
#         self.numero_telephone = user.numero_telephone
#         self.date_naissance = user.date_naissance
#         self.sexe = user.sexe
#         self.is_active = user.is_active
#         self.photo_profil = user.photo_profil.url if user.photo_profil else None
#
#         # Adresse
#         adresse = user.adresse
#         if adresse:
#             self.numero = adresse.numero
#             self.boite_postale = adresse.boite_postale
#             self.nom_rue = adresse.rue.nom_rue
#             self.commune = adresse.rue.localite.commune
#             self.code_postal = adresse.rue.localite.code_postal
#         else:
#             self.numero = None
#             self.boite_postale = None
#             self.nom_rue = None
#             self.commune = None
#             self.code_postal = None
#
#     def to_dict(self):
#         return self.__dict__
#
#
# from django.utils.timezone import now
#
#
# class PromotionData:
#     def __init__(self, promotion):
#         self.idPromotion = promotion.idPromotion
#         self.service_id = promotion.service.idTblService
#         self.discount_percentage = promotion.discount_percentage
#         self.start_date = promotion.start_date
#         self.end_date = promotion.end_date
#         self.is_active = promotion.is_active()
#
#     def to_dict(self):
#         return self.__dict__
#
# class RendezVousServiceData:
#     """Classe pour structurer un service dans un rendez-vous."""
#
#     def __init__(self, service_instance):
#         self.idRendezVousService = service_instance.idRendezVousService
#         self.service = ServiceData(service_instance.service).to_dict()  # Utilise ServiceData pour les détails
#         self.prix_applique = service_instance.prix_applique
#         self.duree_estimee = service_instance.duree_estimee  # Durée estimée en minutes
#
#     def to_dict(self):
#         return self.__dict__
#
#
# class RendezVousData:
#     """Classe pour structurer un rendez-vous."""
#
#     def __init__(self, rdv):
#         self.idRendezVous = rdv.idRendezVous
#         self.client = ClientData(rdv.client).to_dict()
#         self.coiffeuse = CoiffeuseData(rdv.coiffeuse).to_dict()
#         self.salon = SalonData(rdv.salon).to_dict()
#         self.date_heure = rdv.date_heure.isoformat()
#         self.statut = rdv.statut
#         self.total_prix = rdv.total_prix
#         self.duree_totale = rdv.duree_totale
#         self.services = [RendezVousServiceData(s).to_dict() for s in rdv.rendez_vous_services.all()]
#
#     def to_dict(self):
#         return self.__dict__
#
# stripe.api_key = settings_test.STRIPE_SECRET_KEY
#
# class HoraireCoiffeuseData:
#     def __init__(self, horaire):
#         self.id = horaire.id
#         self.coiffeuse_id = horaire.coiffeuse.idTblUser.idTblUser
#         self.jour = horaire.jour  # int (0 = lundi)
#         self.jour_label = horaire.get_jour_display()  # ex: "Lundi"
#         self.heure_debut = horaire.heure_debut.strftime("%H:%M")
#         self.heure_fin = horaire.heure_fin.strftime("%H:%M")
#
#     def to_dict(self):
#         return self.__dict__
#
#
# class IndisponibiliteData:
#     def __init__(self, indispo):
#         self.id = indispo.id
#         self.coiffeuse_id = indispo.coiffeuse.idTblUser.idTblUser
#
#         # ✅ Sécurise le format, que ce soit déjà une string ou non
#         self.date = indispo.date.isoformat() if hasattr(indispo.date, 'isoformat') else str(indispo.date)
#         self.heure_debut = indispo.heure_debut.strftime("%H:%M") if hasattr(indispo.heure_debut, 'strftime') else str(indispo.heure_debut)
#         self.heure_fin = indispo.heure_fin.strftime("%H:%M") if hasattr(indispo.heure_fin, 'strftime') else str(indispo.heure_fin)
#
#         self.motif = indispo.motif
#
#     def to_dict(self):
#         return self.__dict__
#
# class DisponibiliteManager:
#     def __init__(self, coiffeuse):
#         self.coiffeuse = coiffeuse
#
#     def get_jours_ouverts(self):
#         return list(
#             TblHoraireCoiffeuse.objects.filter(coiffeuse=self.coiffeuse).values_list("jour", flat=True)
#         )
#
#     def get_dispos_pour_jour(self, date, duree_minutes=30):
#         jour = date.weekday()  # 0 = lundi, ..., 6 = dimanche
#
#         # 🔒 Vérifie si un horaire existe pour ce jour
#         horaire = TblHoraireCoiffeuse.objects.filter(coiffeuse=self.coiffeuse, jour=jour).first()
#         if not horaire:
#             print("⛔️ Aucune horaire configurée ce jour-là")
#             return []  # Salon fermé ce jour-là
#
#         heure_debut = datetime.combine(date, horaire.heure_debut)
#         heure_fin = datetime.combine(date, horaire.heure_fin)
#
#         # ⏱ Génère les créneaux valides
#         slots = []
#         current = heure_debut
#
#         while current + timedelta(minutes=duree_minutes) <= heure_fin:
#             slot_debut = current
#             slot_fin = current + timedelta(minutes=duree_minutes)
#
#             # ❌ Indisponibilité exceptionnelle
#             indispo = TblIndisponibilite.objects.filter(
#                 coiffeuse=self.coiffeuse,
#                 date=date,
#                 heure_debut__lt=slot_fin.time(),
#                 heure_fin__gt=slot_debut.time()
#             ).exists()
#
#             # ❌ Créneau déjà réservé
#             rdv = TblRendezVous.objects.filter(
#                 coiffeuse=self.coiffeuse,
#                 date_heure__lt=slot_fin,
#                 date_heure__gte=slot_debut
#             ).exists()
#
#             print("🧪 Créneaux retournés :", [(d.strftime("%H:%M"), f.strftime("%H:%M")) for d, f in slots])
#
#             if not indispo and not rdv:
#                 slots.append((slot_debut, slot_fin))
#
#             current += timedelta(minutes=duree_minutes)
#
#         return slots
#
# class RendezVousManager:
#     def __init__(self, coiffeuse_id):
#         self.coiffeuse_id = coiffeuse_id
#
#     def get_by_statut(self, statut):
#         """
#         🔍 Renvoie un queryset filtré par statut (et non archivé).
#         """
#         queryset = TblRendezVous.objects.filter(
#             coiffeuse__idTblUser=self.coiffeuse_id,
#             est_archive=False
#         )
#         if statut:
#             queryset = queryset.filter(statut=statut)
#
#         return queryset.order_by('-date_heure')
#
#     def get_by_periode(self, periode, statut=None):
#         """
#         🔄 Renvoie un queryset filtré par période + statut (et non archivé).
#         """
#         today = now().date()
#
#         if periode == "jour":
#             start = today
#             end = today + timedelta(days=1)
#         elif periode == "semaine":
#             start = today - timedelta(days=today.weekday())
#             end = start + timedelta(days=7)
#         elif periode == "mois":
#             start = today.replace(day=1)
#             end = (start + timedelta(days=32)).replace(day=1)
#         elif periode == "annee":
#             start = today.replace(month=1, day=1)
#             end = today.replace(month=12, day=31)
#         else:
#             return TblRendezVous.objects.none()  # aucun résultat
#
#         queryset = TblRendezVous.objects.filter(
#             coiffeuse__idTblUser=self.coiffeuse_id,
#             date_heure__date__range=(start, end),
#             est_archive=False
#         )
#
#         if statut:
#             queryset = queryset.filter(statut=statut)
#
#         return queryset.order_by('-date_heure')
