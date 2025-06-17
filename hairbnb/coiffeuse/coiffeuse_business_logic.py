################################################################################
#                                                                              #
#        CLASSE DE DONNÉES MINIMALES POUR UNE COIFFEUSE (HAIRBNB)                #
#                                                                              #
#  Ce fichier définit la classe de logique métier `MinimalCoiffeuseData`.      #
#  Son rôle est de créer une représentation "légère" et essentielle d'une      #
#  coiffeuse.                                                                  #
#                                                                              #
#  Elle est conçue pour être utilisée dans des contextes où toutes les         #
#  informations ne sont pas nécessaires (ex: listes, résultats de recherche), #
#  afin d'optimiser les performances. Elle gère la récupération des            #
#  informations de base de l'utilisateur et la logique complexe pour lister   #
#  le ou les salons associés à la coiffeuse.                                   #
#                                                                              #
################################################################################

# --- Importations ---
from datetime import datetime, timedelta
import stripe
# Importation des modèles de la base de données
from hairbnb.models import TblRendezVous, TblHoraireCoiffeuse, TblIndisponibilite
from hairbnb.salon.salon_business_logic import SalonData
from hairbnb.salon_services.salon_services_business_logic import ServiceData


class MinimalCoiffeuseData:
    """
    Crée un objet structuré contenant les informations essentielles d'une coiffeuse,
    y compris son salon principal et les autres salons où elle travaille.
    """

    def __init__(self, coiffeuse):
        # --- Informations de base depuis le modèle User lié ---
        user = coiffeuse.idTblUser
        self.idTblUser = user.idTblUser
        self.uuid = user.uuid
        self.nom = user.nom
        self.prenom = user.prenom

        # Gère le cas où la photo de profil n'existe pas pour éviter les erreurs.
        if user.photo_profil:
            self.photo_profil = user.photo_profil.url
        else:
            self.photo_profil = None

        # --- Informations spécifiques au modèle Coiffeuse ---
        self.nom_commercial = coiffeuse.nom_commercial

        # --- Logique pour le salon principal ("direct") de la coiffeuse ---
        # Vérifie si la coiffeuse a une relation directe avec un salon principal.
        if hasattr(coiffeuse, 'salon_direct') and coiffeuse.salon_direct:
            salon = coiffeuse.salon_direct
            self.salon = {
                'idTblSalon': salon.idTblSalon,
                'nom_salon': salon.nom_salon,
                'slogan': salon.slogan,
                'logo_salon': salon.logo_salon.url if salon.logo_salon else None,
                'position': salon.position if hasattr(salon, 'position') else None
            }
        else:
            self.salon = None

        # --- Logique pour les autres salons où la coiffeuse travaille (via table de liaison) ---
        # L'importation est faite ici pour éviter les dépendances circulaires.
        from hairbnb.models import TblCoiffeuseSalon
        # Interroge la table de liaison pour trouver toutes les relations coiffeuse-salon.
        salons_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)

        if salons_relations.exists():
            self.autres_salons = []
            # Boucle sur chaque relation pour extraire les informations du salon.
            for relation in salons_relations:
                salon = relation.salon
                salon_info = {
                    'idTblSalon': salon.idTblSalon,
                    'nom_salon': salon.nom_salon,
                    # Inclut le statut de propriété de la coiffeuse dans ce salon.
                    'est_proprietaire': relation.est_proprietaire
                }
                self.autres_salons.append(salon_info)
        else:
            self.autres_salons = []

    def to_dict(self):
        """
        Convertit l'instance de la classe en un dictionnaire simple,
        facile à sérialiser en JSON pour une réponse d'API.
        """
        return self.__dict__











# class MinimalCoiffeuseData:
#     """
#     Classe pour récupérer et formater les informations essentielles d'une coiffeuse.
#     Renvoie les URLs d'images sous forme de chemins relatifs pour une meilleure
#     compatibilité avec l'application cliente.
#     """
#
#     def __init__(self, coiffeuse):
#         # Récupération de l'utilisateur associé à la coiffeuse
#         user = coiffeuse.idTblUser
#         self.idTblUser = user.idTblUser
#         self.uuid = user.uuid
#         self.nom = user.nom
#         self.prenom = user.prenom
#
#         # Photo de profil : stocker le chemin relatif uniquement
#         if user.photo_profil:
#             self.photo_profil = user.photo_profil.url
#         else:
#             self.photo_profil = None
#
#         # Informations spécifiques à la coiffeuse
#         # Si position est un attribut de coiffeuse dans le modèle actuel
#         self.nom_commercial = coiffeuse.nom_commercial
#
#         # Si salon_direct existe dans le modèle actuel de coiffeuse
#         if hasattr(coiffeuse, 'salon_direct') and coiffeuse.salon_direct:
#             salon = coiffeuse.salon_direct
#             self.salon = {
#                 'idTblSalon': salon.idTblSalon,
#                 'nom_salon': salon.nom_salon,
#                 'slogan': salon.slogan,
#                 'logo_salon': salon.logo_salon.url if salon.logo_salon else None,
#                 'position': salon.position if hasattr(salon, 'position') else None
#             }
#         else:
#             self.salon = None
#
#         # Ajouter les salons où la coiffeuse travaille
#         from hairbnb.models import TblCoiffeuseSalon
#         salons_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)
#
#         if salons_relations.exists():
#             self.autres_salons = []
#             for relation in salons_relations:
#                 salon = relation.salon
#                 salon_info = {
#                     'idTblSalon': salon.idTblSalon,
#                     'nom_salon': salon.nom_salon,
#                     'est_proprietaire': relation.est_proprietaire
#                 }
#                 self.autres_salons.append(salon_info)
#         else:
#             self.autres_salons = []
#
#     def to_dict(self):
#         """
#         Convertit l'objet en dictionnaire.
#         """
#         return self.__dict__