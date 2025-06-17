################################################################################
#                                                                              #
#     CLASSE DE LOGIQUE MÉTIER POUR L'UTILISATEUR ACTUEL (CURRENTUSERDATA)     #
#                                                                              #
#  Ce fichier définit la classe centrale `CurrentUserData`. Son rôle est de    #
#  créer une représentation complète et structurée de l'utilisateur            #
#  actuellement connecté, quelle que soit sa nature (client, coiffeuse, etc.). #
#                                                                              #
#  Elle agit comme un "Data Transfer Object" (DTO) universel qui :             #
#    1. Rassemble les informations de base communes à tous les utilisateurs.   #
#    2. Charge dynamiquement des données supplémentaires (`extra_data`) en     #
#       fonction du type de l'utilisateur.                                     #
#    3. Gère la logique complexe de récupération des informations liées,       #
#       comme les salons d'une coiffeuse.                                      #
#                                                                              #
################################################################################

# --- Importations ---
# Importation de la classe de données pour un client, pour réutilisation
from hairbnb.business.business_logic import ClientData
# Importation des modèles de la base de données
from hairbnb.models import TblCoiffeuse, TblClient


class CurrentUserData:
    """
    Crée un objet structuré représentant l'utilisateur connecté avec toutes
    ses données, y compris les informations spécifiques à son rôle.
    """
    def __init__(self, user):
        # --- 1. Informations de base (communes à tous les types d'utilisateurs) ---
        self.idTblUser = user.idTblUser
        self.uuid = user.uuid
        self.nom = user.nom
        self.prenom = user.prenom
        self.email = user.email
        self.numero_telephone = user.numero_telephone
        self.date_naissance = user.date_naissance
        # Accès sécurisé aux champs des tables de référence pour éviter les erreurs si non définis.
        self.sexe = user.sexe_ref.libelle if user.sexe_ref else None
        self.is_active = user.is_active
        self.photo_profil = user.photo_profil.url if user.photo_profil else None
        self.type = user.type_ref.libelle if user.type_ref else None

        # --- 2. Informations d'adresse de l'utilisateur ---
        if user.adresse:
            self.adresse = {
                'numero': user.adresse.numero,
                'rue': user.adresse.rue.nom_rue if user.adresse.rue else None,
                'commune': user.adresse.rue.localite.commune if user.adresse.rue and user.adresse.rue.localite else None,
                'code_postal': user.adresse.rue.localite.code_postal if user.adresse.rue and user.adresse.rue.localite else None
            }
        else:
            self.adresse = None

        # --- 3. Données supplémentaires spécifiques au type d'utilisateur ---
        # Charge dynamiquement des informations différentes en fonction du rôle de l'utilisateur.
        if self.type == "coiffeuse":
            try:
                coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
                # Appelle une méthode privée pour récupérer les données complexes de la coiffeuse.
                self.extra_data = self._get_coiffeuse_data(coiffeuse)
            except TblCoiffeuse.DoesNotExist:
                self.extra_data = None
        elif self.type == "client":
            try:
                client = TblClient.objects.get(idTblUser=user)
                # Réutilise la classe ClientData pour formater les données du client.
                self.extra_data = ClientData(client).to_dict()
            except TblClient.DoesNotExist:
                self.extra_data = None
        else:
            self.extra_data = None

    def _get_coiffeuse_data(self, coiffeuse):
        """
        Méthode privée pour rassembler toutes les informations spécifiques à une coiffeuse,
        notamment ses salons.
        """
        data = {
            'nom_commercial': coiffeuse.nom_commercial,
        }

        # L'importation est faite ici pour éviter les problèmes de dépendances circulaires.
        from hairbnb.models import TblCoiffeuseSalon

        # --- Récupération du salon principal (celui où la coiffeuse est propriétaire) ---
        salon_principal_relation = TblCoiffeuseSalon.objects.filter(
            coiffeuse=coiffeuse,
            est_proprietaire=True
        ).first()

        salon_principal_data = None
        if salon_principal_relation:
            salon = salon_principal_relation.salon
            salon_principal_data = {
                'idTblSalon': salon.idTblSalon,
                'nom_salon': salon.nom_salon,
                'slogan': salon.slogan,
                'a_propos': salon.a_propos,
                'logo_salon': salon.logo_salon.url if salon.logo_salon else None,
                'position': salon.position,
                'numero_tva': salon.numero_tva
            }

            # Ajoute l'adresse du salon si elle existe.
            if salon.adresse:
                salon_principal_data['adresse'] = {
                    'numero': salon.adresse.numero,
                    'rue': salon.adresse.rue.nom_rue if salon.adresse.rue else None,
                    'commune': salon.adresse.rue.localite.commune if salon.adresse.rue and salon.adresse.rue.localite else None,
                    'code_postal': salon.adresse.rue.localite.code_postal if salon.adresse.rue and salon.adresse.rue.localite else None
                }

        data['salon_principal'] = salon_principal_data

        # --- Récupération de tous les salons où la coiffeuse travaille ---
        salons_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)

        if salons_relations.exists():
            data['tous_salons'] = []
            # Boucle sur chaque relation pour construire la liste des salons.
            for relation in salons_relations:
                salon_info = {
                    'idTblSalon': relation.salon.idTblSalon,
                    'nom_salon': relation.salon.nom_salon,
                    'est_proprietaire': relation.est_proprietaire,
                    'numero_tva': relation.salon.numero_tva
                }
                data['tous_salons'].append(salon_info)
        else:
            data['tous_salons'] = []

        return data

    def to_dict(self):
        """
        Convertit l'instance complète de la classe (y compris les données extra)
        en un dictionnaire simple pour la sérialisation en JSON.
        """
        return self.__dict__






# from hairbnb.business.business_logic import ClientData
# from hairbnb.models import TblCoiffeuse, TblClient
#
#
# class CurrentUserData:
#     def __init__(self, user):
#         self.idTblUser = user.idTblUser
#         self.uuid = user.uuid
#         self.nom = user.nom
#         self.prenom = user.prenom
#         self.email = user.email
#         self.numero_telephone = user.numero_telephone
#         self.date_naissance = user.date_naissance
#         self.sexe = user.sexe_ref.libelle if user.sexe_ref else None
#         self.is_active = user.is_active
#         self.photo_profil = user.photo_profil.url if user.photo_profil else None
#         self.type = user.type_ref.libelle if user.type_ref else None
#
#         # Ajouter les données d'adresse
#         if user.adresse:
#             self.adresse = {
#                 'numero': user.adresse.numero,
#                 'rue': user.adresse.rue.nom_rue if user.adresse.rue else None,
#                 'commune': user.adresse.rue.localite.commune if user.adresse.rue and user.adresse.rue.localite else None,
#                 'code_postal': user.adresse.rue.localite.code_postal if user.adresse.rue and user.adresse.rue.localite else None
#             }
#         else:
#             self.adresse = None
#
#         # Vérifier le type pour charger les données extra
#         if self.type == "coiffeuse":
#             try:
#                 coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
#                 self.extra_data = self._get_coiffeuse_data(coiffeuse)
#             except TblCoiffeuse.DoesNotExist:
#                 self.extra_data = None
#         elif self.type == "client":
#             try:
#                 client = TblClient.objects.get(idTblUser=user)
#                 self.extra_data = ClientData(client).to_dict()
#             except TblClient.DoesNotExist:
#                 self.extra_data = None
#         else:
#             self.extra_data = None
#
#     def _get_coiffeuse_data(self, coiffeuse):
#         """
#         Récupère les données spécifiques à une coiffeuse avec le nouveau modèle.
#         """
#         data = {
#             'nom_commercial': coiffeuse.nom_commercial,
#         }
#
#         # Récupérer le salon principal (salon où la coiffeuse est propriétaire)
#         from hairbnb.models import TblCoiffeuseSalon
#         salon_principal_relation = TblCoiffeuseSalon.objects.filter(
#             coiffeuse=coiffeuse,
#             est_proprietaire=True
#         ).first()
#
#         salon_principal_data = None
#         if salon_principal_relation:
#             salon = salon_principal_relation.salon
#             salon_principal_data = {
#                 'idTblSalon': salon.idTblSalon,
#                 'nom_salon': salon.nom_salon,
#                 'slogan': salon.slogan,
#                 'a_propos': salon.a_propos,
#                 'logo_salon': salon.logo_salon.url if salon.logo_salon else None,
#                 'position': salon.position,
#                 'numero_tva': salon.numero_tva  # Maintenant directement dans le salon
#             }
#
#             # Ajouter l'adresse du salon si disponible
#             if salon.adresse:
#                 salon_principal_data['adresse'] = {
#                     'numero': salon.adresse.numero,
#                     'rue': salon.adresse.rue.nom_rue if salon.adresse.rue else None,
#                     'commune': salon.adresse.rue.localite.commune if salon.adresse.rue and salon.adresse.rue.localite else None,
#                     'code_postal': salon.adresse.rue.localite.code_postal if salon.adresse.rue and salon.adresse.rue.localite else None
#                 }
#
#         data['salon_principal'] = salon_principal_data
#
#         # Ajouter tous les salons où la coiffeuse travaille
#         salons_relations = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)
#
#         if salons_relations.exists():
#             data['tous_salons'] = []
#             for relation in salons_relations:
#                 salon_info = {
#                     'idTblSalon': relation.salon.idTblSalon,
#                     'nom_salon': relation.salon.nom_salon,
#                     'est_proprietaire': relation.est_proprietaire,
#                     'numero_tva': relation.salon.numero_tva  # TVA maintenant dans le salon
#                 }
#                 data['tous_salons'].append(salon_info)
#         else:
#             data['tous_salons'] = []
#
#         return data
#
#     def to_dict(self):
#         return self.__dict__