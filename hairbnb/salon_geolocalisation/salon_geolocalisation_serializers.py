################################################################################
#                                                                              #
#    SERIALIZER POUR L'AFFICHAGE DE SALONS AVEC GÉOLOCALISATION ET COIFFEUSES   #
#                                                                              #
#  Ce fichier définit `SalonSerializer`, une classe de serializer spécialisée  #
#  pour les objets `TblSalon`.                                                 #
#                                                                              #
#  Son rôle est de formater les données d'un salon pour des usages spécifiques,#
#  notamment :                                                                 #
#    - Extraire et séparer les coordonnées GPS (latitude, longitude) à partir #
#      d'un champ de position unique.                                          #
#    - Lister les coiffeuses associées à un salon, en fournissant à la fois   #
#      une simple liste de leurs IDs et leurs détails complets.                #
#    - Mapper les noms de champs du modèle (ex: `nom_salon`) vers des noms     #
#      plus clairs pour l'API (ex: `nom`).                                     #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblSalon, TblCoiffeuseSalon


class SalonSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les salons, optimisé pour fournir des données de
    géolocalisation et des informations détaillées sur les coiffeuses associées.
    """
    # --- Champs Calculés (via SerializerMethodField) ---

    # Champ calculé pour obtenir la liste des IDs de toutes les coiffeuses du salon.
    coiffeuse_ids = serializers.SerializerMethodField()
    # Champ calculé pour obtenir une liste d'objets avec les détails de chaque coiffeuse.
    coiffeuses_details = serializers.SerializerMethodField()
    # Champ calculé pour extraire la latitude depuis le champ 'position'.
    latitude = serializers.SerializerMethodField()
    # Champ calculé pour extraire la longitude depuis le champ 'position'.
    longitude = serializers.SerializerMethodField()

    # --- Champs Mappés (via l'argument 'source') ---

    # Le champ 'nom' de l'API est mappé sur le champ 'nom_salon' du modèle TblSalon.
    nom = serializers.CharField(source='nom_salon')
    slogan = serializers.CharField()
    # Le champ 'logo' de l'API est mappé sur le champ 'logo_salon' du modèle.
    logo = serializers.ImageField(source='logo_salon')

    class Meta:
        """
        La classe Meta lie le serializer au modèle Django et définit les champs
        qui seront inclus dans la sortie JSON finale.
        """
        model = TblSalon
        fields = [
            'idTblSalon',
            'nom',
            'slogan',
            'logo',
            'position',  # Le champ source de la géolocalisation est inclus pour référence.
            'latitude',
            'longitude',
            'coiffeuse_ids',
            'coiffeuses_details'
        ]

    def get_coiffeuse_ids(self, obj):
        """
        Récupère une liste simple contenant les IDs de toutes les coiffeuses
        travaillant dans le salon 'obj'.
        """
        # Requête sur la table de liaison pour trouver toutes les relations pour ce salon.
        relations = TblCoiffeuseSalon.objects.filter(salon=obj)
        # Retourne une liste des IDs utilisateur extraits de chaque relation.
        return [relation.coiffeuse.idTblUser.idTblUser for relation in relations]

    def get_coiffeuses_details(self, obj):
        """
        Construit et retourne une liste de dictionnaires, chacun contenant
        les détails complets d'une coiffeuse travaillant dans le salon 'obj'.
        """
        relations = TblCoiffeuseSalon.objects.filter(salon=obj)
        details = []
        for relation in relations:
            coiffeuse = relation.coiffeuse
            user = coiffeuse.idTblUser
            # Ajoute un dictionnaire structuré avec les informations utiles.
            details.append({
                "idTblCoiffeuse": user.idTblUser,
                "idTblUser": user.idTblUser,
                "uuid": user.uuid,
                "nom": user.nom,
                "prenom": user.prenom,
                "role": user.get_role(),
                "type": user.get_type(),
                # L'information de propriété vient directement de la table de liaison.
                "est_proprietaire": relation.est_proprietaire,
                "nom_commercial": coiffeuse.nom_commercial
            })
        return details

    def get_latitude(self, obj):
        """
        Extrait la valeur de la latitude à partir du champ 'position' du salon.
        Le champ 'position' est attendu au format "latitude,longitude".
        """
        try:
            # Vérifie que la position n'est pas nulle ou vide.
            if obj.position:
                # Sépare la chaîne par la virgule et convertit la première partie en float.
                lat, _ = map(float, obj.position.split(','))
                return lat
        except (ValueError, TypeError):
            # Gère les cas où la chaîne est mal formée ou si obj.position est None.
            return None
        return None

    def get_longitude(self, obj):
        """
        Extrait la valeur de la longitude à partir du champ 'position' du salon.
        Le champ 'position' est attendu au format "latitude,longitude".
        """
        try:
            # Vérifie que la position n'est pas nulle ou vide.
            if obj.position:
                # Sépare la chaîne par la virgule et convertit la seconde partie en float.
                _, lon = map(float, obj.position.split(','))
                return lon
        except (ValueError, TypeError):
            # Gère les cas où la chaîne est mal formée ou si obj.position est None.
            return None
        return None





# from rest_framework import serializers
# from hairbnb.models import TblSalon, TblCoiffeuseSalon
#
#
# class SalonSerializer(serializers.ModelSerializer):
#     """
#     Sérialiseur pour les salons avec géolocalisation et coiffeuses associées
#     """
#     # Récupérer les IDs des coiffeuses qui travaillent dans ce salon
#     coiffeuse_ids = serializers.SerializerMethodField()
#     # Récupérer les détails complets des coiffeuses
#     coiffeuses_details = serializers.SerializerMethodField()
#     # Récupérer les coordonnées de géolocalisation sous forme séparée
#     latitude = serializers.SerializerMethodField()
#     longitude = serializers.SerializerMethodField()
#     # Informations de base du salon
#     nom = serializers.CharField(source='nom_salon')
#     slogan = serializers.CharField()
#     logo = serializers.ImageField(source='logo_salon')
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'idTblSalon',
#             'nom',
#             'slogan',
#             'logo',
#             'position',
#             'latitude',
#             'longitude',
#             'coiffeuse_ids',
#             'coiffeuses_details'
#         ]
#
#     def get_coiffeuse_ids(self, obj):
#         """
#         Récupère la liste des IDs des coiffeuses travaillant dans ce salon
#         """
#         # Utiliser la relation ManyToMany via TblCoiffeuseSalon
#         relations = TblCoiffeuseSalon.objects.filter(salon=obj)
#         return [relation.coiffeuse.idTblUser.idTblUser for relation in relations]
#
#     def get_coiffeuses_details(self, obj):
#         """
#         Récupère les détails complets des coiffeuses travaillant dans ce salon
#         """
#         relations = TblCoiffeuseSalon.objects.filter(salon=obj)
#         details = []
#         for relation in relations:
#             coiffeuse = relation.coiffeuse
#             user = coiffeuse.idTblUser
#             details.append({
#                 "idTblCoiffeuse": user.idTblUser,
#                 "idTblUser": user.idTblUser,
#                 "uuid": user.uuid,
#                 "nom": user.nom,
#                 "prenom": user.prenom,
#                 "role": user.get_role(),
#                 "type": user.get_type(),
#                 "est_proprietaire": relation.est_proprietaire,
#                 "nom_commercial": coiffeuse.nom_commercial
#             })
#         return details
#
#     def get_latitude(self, obj):
#         """
#         Extrait la latitude de la position stockée
#         """
#         try:
#             if obj.position:
#                 lat, _ = map(float, obj.position.split(','))
#                 return lat
#         except (ValueError, TypeError):
#             return None
#         return None
#
#     def get_longitude(self, obj):
#         """
#         Extrait la longitude de la position stockée
#         """
#         try:
#             if obj.position:
#                 _, lon = map(float, obj.position.split(','))
#                 return lon
#         except (ValueError, TypeError):
#             return None
#         return None
