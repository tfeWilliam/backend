################################################################################
#                                                                              #
#         CLASSE DE FORMATAGE DES DONNÉES POUR UN SALON (DTO)                    #
#                                                                              #
#  Ce fichier définit la classe `SalonData`, qui agit comme un "formateur"     #
#  ou un Objet de Transfert de Données (DTO - Data Transfer Object).           #
#                                                                              #
#  Son rôle est de prendre un objet complexe du modèle Django (`TblSalon`) et   #
#  de le transformer en une structure Python simple (un dictionnaire), facile  #
#  à utiliser, notamment pour la sérialisation en JSON dans une API.           #
#                                                                              #
#  Logiques clés implémentées :                                                #
#    - Recherche robuste de l'ID de la coiffeuse propriétaire.                 #
#    - Gestion flexible de la liste des services pour supporter la pagination. #
#                                                                              #
################################################################################

# Importation de la classe de formatage pour les services, assurant une conception modulaire.
from hairbnb.salon_services.salon_services_business_logic import ServiceData


class SalonData:
    """
    Formate les données d'un objet salon pour une utilisation simplifiée.
    """

    def __init__(self, salon, filtered_services=None):
        """
        Initialise l'objet de données à partir d'un modèle Salon.

        Args:
            salon (TblSalon): L'objet du modèle Salon à formater.
            filtered_services (list, optional): Une liste de services déjà filtrée
                (par exemple, pour la pagination). Si None, tous les services
                du salon seront récupérés.
        """

        # Copie directe de l'identifiant du salon.
        self.idTblSalon = salon.idTblSalon

        # --- GESTION DE LA RELATION AVEC LA COIFFEUSE PROPRIÉTAIRE ---
        # Cette logique complexe trouve l'ID de la propriétaire de manière robuste.

        # Voie n°1 (optimale) : Vérifie si une relation directe `salon.coiffeuse` existe.
        if hasattr(salon, 'coiffeuse') and salon.coiffeuse:
            self.coiffeuse_id = salon.coiffeuse.idTblUser.idTblUser
        else:
            # Voie n°2 (fallback) : Si la relation directe échoue, on cherche dans la
            # table de liaison `TblCoiffeuseSalon`.
            from hairbnb.models import TblCoiffeuseSalon
            proprietaire = TblCoiffeuseSalon.objects.filter(salon=salon, est_proprietaire=True).first()

            if proprietaire:
                # Si une propriétaire est trouvée via la table de liaison.
                self.coiffeuse_id = proprietaire.coiffeuse.idTblUser.idTblUser
            else:
                # Voie n°3 (sécurité) : Si aucune propriétaire n'est trouvée, on assigne None.
                self.coiffeuse_id = None

        # --- GESTION DE LA LISTE DES SERVICES ---
        # Cette section détermine la source des services à inclure.

        # Utilise la liste `filtered_services` si elle est fournie (pour la performance, ex: pagination),
        # sinon, requête tous les services liés au salon depuis la base de données.
        services_source = filtered_services if filtered_services is not None else salon.salon_service.all().order_by(
            'service__intitule_service')

        # Crée une liste de services formatés. Chaque service est lui-même transformé
        # en dictionnaire par la classe `ServiceData` pour une structure propre.
        self.services = [ServiceData(service.service).to_dict() for service in services_source]

    def to_dict(self):
        """
        Convertit l'instance de la classe en un dictionnaire simple.

        Returns:
            dict: Une représentation de l'objet sous forme de dictionnaire.
        """
        return self.__dict__









# from hairbnb.salon_services.salon_services_business_logic import ServiceData
#
#
# class SalonData:
#     def __init__(self, salon, filtered_services=None):
#         self.idTblSalon = salon.idTblSalon
#
#         # Gestion de la relation avec la coiffeuse (adaptation au nouveau modèle)
#         # Vérifier si le salon a toujours une coiffeuse propriétaire principale
#         if hasattr(salon, 'coiffeuse') and salon.coiffeuse:
#             self.coiffeuse_id = salon.coiffeuse.idTblUser.idTblUser
#         else:
#             # Sinon, essayer de trouver la coiffeuse propriétaire via TblCoiffeuseSalon
#             from hairbnb.models import TblCoiffeuseSalon
#             proprietaire = TblCoiffeuseSalon.objects.filter(salon=salon, est_proprietaire=True).first()
#             if proprietaire:
#                 self.coiffeuse_id = proprietaire.coiffeuse.idTblUser.idTblUser
#             else:
#                 # Fallback si aucune coiffeuse propriétaire n'est trouvée
#                 self.coiffeuse_id = None
#
#         # ✅ Soit on utilise les services filtrés (pagination), soit tous
#         services_source = filtered_services if filtered_services is not None else salon.salon_service.all().order_by(
#             'service__intitule_service')
#         self.services = [ServiceData(service.service).to_dict() for service in services_source]
#
#     def to_dict(self):
#         return self.__dict__
