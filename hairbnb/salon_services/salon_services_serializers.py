################################################################################
#                                                                              #
#         FICHIER DE SERIALIZERS POUR LA GESTION DES SERVICES                  #
#                                                                              #
#  Ce fichier contient les serializers de Django REST Framework nécessaires    #
#  pour la manipulation des services. Il couvre un large éventail d'opérations:#
#                                                                              #
#  - Création de nouveaux services dans le catalogue général.                  #
#  - Ajout de services existants à un salon spécifique avec un prix/temps      #
#    personnalisé.                                                             #
#  - Mise à jour des détails (prix/temps) d'un service dans un salon.          #
#  - Sérialisation des services pour les réponses API, en tenant compte du     #
#    contexte (ex: afficher le prix spécifique à un salon).                    #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblService, TblSalonService, TblServicePrix, TblServiceTemps, TblSalon


################################################################################
#                   SERIALIZER POUR LA CRÉATION D'UN SERVICE                   #
################################################################################

class ServiceCreateSerializer(serializers.Serializer):
    """
    Serializer pour valider les données requises lors de la création d'un
    tout nouveau service dans le catalogue général de l'application.
    """
    userId = serializers.IntegerField(required=True)
    intitule_service = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    prix = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    temps_minutes = serializers.IntegerField(required=True)
    categorie_id = serializers.IntegerField(required=True)

    class Meta:
        fields = ['userId', 'intitule_service', 'description', 'prix', 'temps_minutes', 'categorie_id']


################################################################################
#         SERIALIZER POUR AJOUTER UN SERVICE EXISTANT À UN SALON               #
################################################################################

class AddExistingServiceSerializer(serializers.Serializer):
    """
    Valide les données nécessaires pour lier un service existant du catalogue
    à un salon spécifique, en définissant un prix et une durée propres à ce salon.
    """
    userId = serializers.IntegerField(required=True)
    service_id = serializers.IntegerField(required=True)
    prix = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    temps_minutes = serializers.IntegerField(required=True)

    def validate_userId(self, value):
        """Vérifie que l'utilisateur existe et qu'il s'agit bien d'une coiffeuse."""
        from hairbnb.models import TblUser
        try:
            user = TblUser.objects.get(idTblUser=value)
            if user.type_ref.libelle != 'Coiffeuse':
                raise serializers.ValidationError("L'utilisateur n'est pas une coiffeuse")
            return value
        except TblUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé")

    def validate_service_id(self, value):
        """Vérifie que le service que l'on souhaite ajouter existe bien."""
        try:
            TblService.objects.get(idTblService=value)
            return value
        except TblService.DoesNotExist:
            raise serializers.ValidationError("Service non trouvé")

    def validate_prix(self, value):
        """Vérifie que le prix fourni est une valeur positive."""
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0")
        return value

    def validate_temps_minutes(self, value):
        """Vérifie que la durée fournie est une valeur positive."""
        if value <= 0:
            raise serializers.ValidationError("La durée doit être supérieure à 0")
        return value


################################################################################
#                 SERIALIZERS POUR LA STRUCTURATION DES RÉPONSES API           #
################################################################################

class AddExistingServiceResponseSerializer(serializers.Serializer):
    """Définit la structure de la réponse JSON après l'ajout réussi d'un service à un salon."""
    status = serializers.CharField()
    message = serializers.CharField()
    service = serializers.DictField()
    salon_id = serializers.IntegerField()
    salon_nom = serializers.CharField()
    prix = serializers.DecimalField(max_digits=5, decimal_places=2)
    duree_minutes = serializers.IntegerField()


class ServiceResponseSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet Service, avec la capacité d'afficher un prix et une durée
    spécifiques à un salon si un `salon_id` est fourni dans son contexte.
    """
    prix = serializers.SerializerMethodField()
    temps_minutes = serializers.SerializerMethodField()
    salon_nom = serializers.SerializerMethodField()

    class Meta:
        model = TblService
        fields = ['idTblService', 'intitule_service', 'description', 'prix', 'temps_minutes', 'salon_nom']

    def get_prix(self, obj):
        """Récupère le prix. Priorise le prix du salon si `salon_id` est dans le contexte."""
        salon_id = self.context.get('salon_id')
        service_prix = obj.service_prix.filter(salon_id=salon_id).first() if salon_id else obj.service_prix.first()
        return float(service_prix.prix.prix) if service_prix else 0.0

    def get_temps_minutes(self, obj):
        """Récupère la durée. Priorise la durée du salon si `salon_id` est dans le contexte."""
        salon_id = self.context.get('salon_id')
        service_temps = obj.service_temps.filter(salon_id=salon_id).first() if salon_id else obj.service_temps.first()
        return service_temps.temps.minutes if service_temps else 0

    def get_salon_nom(self, obj):
        """Récupère le nom du salon si `salon_id` est fourni dans le contexte."""
        salon_id = self.context.get('salon_id')
        if salon_id:
            try:
                salon = TblSalon.objects.get(idTblSalon=salon_id)
                return salon.nom_salon
            except TblSalon.DoesNotExist:
                return None
        return None


################################################################################
#          SERIALIZER POUR LES SERVICES DANS LE CONTEXTE D'UN SALON            #
################################################################################

class SalonServiceSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet de la table de liaison `TblSalonService`.
    Il représente un service tel qu'il existe DANS un salon, avec son prix et
    sa durée spécifiques à ce salon.
    """
    # Utilisation de `source` pour accéder aux attributs du modèle `TblService` lié.
    service_id = serializers.IntegerField(source='service.idTblService')
    intitule_service = serializers.CharField(source='service.intitule_service')
    description = serializers.CharField(source='service.description')
    category_id = serializers.IntegerField(source='service.categorie.idTblCategorie', allow_null=True)
    # Champs calculés pour obtenir le prix et la durée spécifiques à la relation salon-service.
    prix = serializers.SerializerMethodField()
    duree_minutes = serializers.SerializerMethodField()

    class Meta:
        model = TblSalonService
        fields = ['service_id', 'intitule_service', 'description', 'prix', 'duree_minutes', 'category_id']

    def get_prix(self, obj):
        """Récupère le prix de ce service défini spécifiquement pour ce salon."""
        service_prix = TblServicePrix.objects.filter(service=obj.service, salon=obj.salon).first()
        return float(service_prix.prix.prix) if service_prix else 0.0

    def get_duree_minutes(self, obj):
        """Récupère la durée de ce service définie spécifiquement pour ce salon."""
        service_temps = TblServiceTemps.objects.filter(service=obj.service, salon=obj.salon).first()
        return service_temps.temps.minutes if service_temps else 0


class SalonServicesListResponseSerializer(serializers.Serializer):
    """Définit la structure de la réponse JSON pour la liste des services d'un salon."""
    status = serializers.CharField()
    services = SalonServiceSerializer(many=True)
    total = serializers.IntegerField()


################################################################################
#            SERIALIZER POUR LA MISE À JOUR D'UN SERVICE DANS UN SALON         #
################################################################################

class ServiceUpdateSerializer(serializers.Serializer):
    """
    Valide les données pour la mise à jour du prix et/ou de la durée d'un
    service. Contient également la logique de mise à jour.
    """
    userId = serializers.IntegerField(required=True)
    # Les champs ne sont pas requis car on peut mettre à jour l'un ou l'autre.
    prix = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    temps_minutes = serializers.IntegerField(required=False)

    def validate_userId(self, value):
        """Valide l'identité de la coiffeuse effectuant la mise à jour."""
        from hairbnb.models import TblUser
        try:
            user = TblUser.objects.get(idTblUser=value)
            if user.type_ref.libelle != 'Coiffeuse':
                raise serializers.ValidationError("L'utilisateur n'est pas une coiffeuse")
            return value
        except TblUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé")

    def validate_prix(self, value):
        """Valide le prix s'il est fourni."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0")
        return value

    def validate_temps_minutes(self, value):
        """Valide la durée si elle est fournie."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("La durée doit être supérieure à 0")
        return value

    def validate(self, attrs):
        """Validation au niveau de l'objet pour s'assurer qu'au moins un champ est mis à jour."""
        if not attrs.get('prix') and not attrs.get('temps_minutes'):
            raise serializers.ValidationError("Au moins un champ (prix ou temps_minutes) doit être fourni pour la mise à jour")
        return attrs

    def update_service(self, service_id, validated_data):
        """
        Méthode personnalisée contenant la logique de mise à jour.
        NOTE: Cette méthode met à jour le prix/temps de base du service, pas
        celui spécifique à un salon. Un `salon_id` serait nécessaire pour cela.
        """
        from hairbnb.models import TblTemps, TblPrix

        try:
            service = TblService.objects.get(idTblService=service_id)

            # Mise à jour du temps.
            if 'temps_minutes' in validated_data:
                # `get_or_create` évite les doublons d'objets Temps.
                temps, _ = TblTemps.objects.get_or_create(minutes=validated_data['temps_minutes'])
                # `update_or_create` met à jour la liaison service-temps.
                TblServiceTemps.objects.update_or_create(service=service, defaults={'temps': temps})

            # Mise à jour du prix.
            if 'prix' in validated_data:
                prix_obj, _ = TblPrix.objects.get_or_create(prix=validated_data['prix'])
                TblServicePrix.objects.update_or_create(service=service, defaults={'prix': prix_obj})

            return service

        except TblService.DoesNotExist:
            raise serializers.ValidationError("Service introuvable")








# # serializers.py
# from rest_framework import serializers
# from rest_framework.decorators import api_view
# from rest_framework.pagination import PageNumberPagination
# from rest_framework.response import Response
#
# from decorators.decorators import firebase_authenticated
# from hairbnb.models import TblService, TblSalonService, TblServicePrix, TblServiceTemps, TblSalon, TblCoiffeuse, \
#     TblCoiffeuseSalon
# from hairbnb.salon.salon_business_logic import SalonData
#
#
# class ServiceCreateSerializer(serializers.Serializer):
#     userId = serializers.IntegerField(required=True)
#     intitule_service = serializers.CharField(required=True)
#     description = serializers.CharField(required=True)
#     prix = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
#     temps_minutes = serializers.IntegerField(required=True)
#     categorie_id = serializers.IntegerField(required=True)
#
#     class Meta:
#         fields = ['userId', 'intitule_service', 'description', 'prix', 'temps_minutes', 'categorie_id']
#
#
# # ✅ Serializer pour ajouter un service existant à un salon
# class AddExistingServiceSerializer(serializers.Serializer):
#     userId = serializers.IntegerField(required=True)
#     service_id = serializers.IntegerField(required=True)
#     prix = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
#     temps_minutes = serializers.IntegerField(required=True)
#
#     def validate_userId(self, value):
#         """Valide que l'utilisateur existe et est une coiffeuse"""
#         from hairbnb.models import TblUser
#         try:
#             user = TblUser.objects.get(idTblUser=value)
#             if user.type_ref.libelle != 'Coiffeuse':
#                 raise serializers.ValidationError("L'utilisateur n'est pas une coiffeuse")
#             return value
#         except TblUser.DoesNotExist:
#             raise serializers.ValidationError("Utilisateur non trouvé")
#
#     def validate_service_id(self, value):
#         """Valide que le service existe"""
#         try:
#             TblService.objects.get(idTblService=value)
#             return value
#         except TblService.DoesNotExist:
#             raise serializers.ValidationError("Service non trouvé")
#
#     def validate_prix(self, value):
#         """Valide que le prix est positif"""
#         if value <= 0:
#             raise serializers.ValidationError("Le prix doit être supérieur à 0")
#         return value
#
#     def validate_temps_minutes(self, value):
#         """Valide que le temps est positif"""
#         if value <= 0:
#             raise serializers.ValidationError("La durée doit être supérieure à 0")
#         return value
#
#
# # ✅ Serializer pour la réponse après ajout d'un service
# class AddExistingServiceResponseSerializer(serializers.Serializer):
#     status = serializers.CharField()
#     message = serializers.CharField()
#     service = serializers.DictField()
#     salon_id = serializers.IntegerField()
#     salon_nom = serializers.CharField()
#     prix = serializers.DecimalField(max_digits=5, decimal_places=2)
#     duree_minutes = serializers.IntegerField()
#
#
# # ✅ ServiceResponseSerializer pour prendre en compte le salon
# class ServiceResponseSerializer(serializers.ModelSerializer):
#     prix = serializers.SerializerMethodField()
#     temps_minutes = serializers.SerializerMethodField()
#     salon_nom = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblService
#         fields = ['idTblService', 'intitule_service', 'description', 'prix', 'temps_minutes', 'salon_nom']
#
#     def get_prix(self, obj):
#         """Récupère le prix pour un salon spécifique si fourni dans le contexte"""
#         salon_id = self.context.get('salon_id')
#         if salon_id:
#             service_prix = obj.service_prix.filter(salon_id=salon_id).first()
#         else:
#             service_prix = obj.service_prix.first()
#         return float(service_prix.prix.prix) if service_prix else 0.0
#
#     def get_temps_minutes(self, obj):
#         """Récupère la durée pour un salon spécifique si fourni dans le contexte"""
#         salon_id = self.context.get('salon_id')
#         if salon_id:
#             service_temps = obj.service_temps.filter(salon_id=salon_id).first()
#         else:
#             service_temps = obj.service_temps.first()
#         return service_temps.temps.minutes if service_temps else 0
#
#     def get_salon_nom(self, obj):
#         """Récupère le nom du salon si fourni dans le contexte"""
#         salon_id = self.context.get('salon_id')
#         if salon_id:
#             try:
#                 salon = TblSalon.objects.get(idTblSalon=salon_id)
#                 return salon.nom_salon
#             except TblSalon.DoesNotExist:
#                 return None
#         return None
#
#
# # ✅ Serializer pour les services d'un salon spécifique
# class SalonServiceSerializer(serializers.ModelSerializer):
#     service_id = serializers.IntegerField(source='service.idTblService')
#     intitule_service = serializers.CharField(source='service.intitule_service')
#     description = serializers.CharField(source='service.description')
#     prix = serializers.SerializerMethodField()
#     duree_minutes = serializers.SerializerMethodField()
#     category_id = serializers.IntegerField(source='service.categorie.idTblCategorie', allow_null=True)
#
#     class Meta:
#         model = TblSalonService
#         fields = ['service_id', 'intitule_service', 'description', 'prix', 'duree_minutes', 'category_id']
#
#     def get_prix(self, obj):
#         """Récupère le prix de ce service dans ce salon"""
#         service_prix = TblServicePrix.objects.filter(
#             service=obj.service,
#             salon=obj.salon
#         ).first()
#         return float(service_prix.prix.prix) if service_prix else 0.0
#
#     def get_duree_minutes(self, obj):
#         """Récupère la durée de ce service dans ce salon"""
#         service_temps = TblServiceTemps.objects.filter(
#             service=obj.service,
#             salon=obj.salon
#         ).first()
#         return service_temps.temps.minutes if service_temps else 0
#
#
# # ✅ Serializer pour lister les services d'un salon
# class SalonServicesListResponseSerializer(serializers.Serializer):
#     status = serializers.CharField()
#     services = SalonServiceSerializer(many=True)
#     total = serializers.IntegerField()
#
#
# # ✅ Serializer pour mettre à jour un service
# class ServiceUpdateSerializer(serializers.Serializer):
#     userId = serializers.IntegerField(required=True)
#     prix = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
#     temps_minutes = serializers.IntegerField(required=False)
#
#     def validate_userId(self, value):
#         """Valide que l'utilisateur existe et est une coiffeuse"""
#         from hairbnb.models import TblUser
#         try:
#             user = TblUser.objects.get(idTblUser=value)
#             if user.type_ref.libelle != 'Coiffeuse':
#                 raise serializers.ValidationError("L'utilisateur n'est pas une coiffeuse")
#             return value
#         except TblUser.DoesNotExist:
#             raise serializers.ValidationError("Utilisateur non trouvé")
#
#     def validate_prix(self, value):
#         """Valide que le prix est positif"""
#         if value is not None and value <= 0:
#             raise serializers.ValidationError("Le prix doit être supérieur à 0")
#         return value
#
#     def validate_temps_minutes(self, value):
#         """Valide que le temps est positif"""
#         if value is not None and value <= 0:
#             raise serializers.ValidationError("La durée doit être supérieure à 0")
#         return value
#
#     def validate(self, attrs):
#         """Validation globale - au moins un champ doit être fourni"""
#         if not attrs.get('prix') and not attrs.get('temps_minutes'):
#             raise serializers.ValidationError(
#                 "Au moins un champ (prix ou temps_minutes) doit être fourni pour la mise à jour"
#             )
#         return attrs
#
#     def update_service(self, service_id, validated_data):
#         """Met à jour le service avec les données validées"""
#         from hairbnb.models import TblService, TblTemps, TblServiceTemps, TblPrix, TblServicePrix
#
#         try:
#             service = TblService.objects.get(idTblService=service_id)
#
#             # Gestion du temps
#             if 'temps_minutes' in validated_data:
#                 temps, _ = TblTemps.objects.get_or_create(minutes=validated_data['temps_minutes'])
#                 TblServiceTemps.objects.update_or_create(service=service, defaults={'temps': temps})
#
#             # Gestion du prix
#             if 'prix' in validated_data:
#                 prix_obj, _ = TblPrix.objects.get_or_create(prix=validated_data['prix'])
#                 TblServicePrix.objects.update_or_create(service=service, defaults={'prix': prix_obj})
#
#             return service
#
#         except TblService.DoesNotExist:
#             raise serializers.ValidationError("Service introuvable")