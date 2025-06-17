################################################################################
#                                                                              #
#             FICHIER DE SERIALIZERS POUR LES MODÈLES DE HAIRBNB                 #
#                                                                              #
#  Ce fichier regroupe plusieurs classes de "serializers" de Django REST       #
#  Framework. Un serializer a pour rôle de convertir des données complexes,    #
#  comme les objets des modèles Django, en types de données natifs Python      #
#  (généralement des dictionnaires) qui peuvent ensuite être facilement rendus #
#  en JSON pour les API. Il gère également la validation des données entrantes.#
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import (
    TblSalon, TblSalonService, TblSalonImage, TblAvis, TblService,
    TblCoiffeuse, TblAdresse, TblCoiffeuseSalon
)
from hairbnb.serializers.salon_services_serializers import ServiceSerializer


################################################################################
#     SERIALIZER POUR L'AFFICHAGE DÉTAILLÉ ET PUBLIC D'UN SALON                #
################################################################################

class SalonSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour afficher les détails d'un salon.
    Il enrichit le modèle TblSalon avec des champs calculés comme la liste
    des services, le propriétaire et une adresse formatée.
    Il assure également la compatibilité avec l'ancien nommage des champs.
    """

    # Champ calculé pour obtenir la liste des services du salon.
    services = serializers.SerializerMethodField()
    # Champ calculé pour identifier la coiffeuse propriétaire.
    proprietaire = serializers.SerializerMethodField()
    # Champ calculé pour formater l'adresse de manière sécurisée et structurée.
    adresse_formatee = serializers.SerializerMethodField()

    class Meta:
        model = TblSalon
        fields = [
            'idTblSalon', 'proprietaire', 'services', 'nom_salon',
            'slogan', 'a_propos', 'logo_salon', 'position',
            'numero_tva', 'adresse_formatee'
        ]

    def get_services(self, obj):
        """
        Récupère et sérialise la liste des services associés à ce salon.
        """
        salon_services = TblSalonService.objects.filter(salon=obj)
        # Extrait les objets 'service' de la table de liaison 'TblSalonService'.
        services = [ss.service for ss in salon_services]
        # Utilise un autre serializer (ServiceSerializer) pour formater la liste.
        return ServiceSerializer(services, many=True).data

    def get_proprietaire(self, obj):
        """
        Récupère l'ID de la coiffeuse propriétaire du salon.
        Fait appel à une méthode `get_proprietaire()` définie sur le modèle TblSalon.
        """
        try:
            proprietaire = obj.get_proprietaire()
            if proprietaire:
                return proprietaire.idTblUser.idTblUser
            return None
        except Exception as e:
            return None

    def get_adresse_formatee(self, obj):
        """
        Construit un dictionnaire structuré pour l'adresse du salon.
        Vérifie l'existence de chaque partie de l'adresse pour éviter les erreurs.
        """
        try:
            if obj.adresse:
                return {
                    'numero': obj.adresse.numero,
                    'rue': obj.adresse.rue.nom_rue if obj.adresse.rue else None,
                    'commune': obj.adresse.rue.localite.commune if obj.adresse.rue and obj.adresse.rue.localite else None,
                    'code_postal': obj.adresse.rue.localite.code_postal if obj.adresse.rue and obj.adresse.rue.localite else None
                }
            return None
        except Exception as e:
            return None

    def to_representation(self, instance):
        """
        Modifie la représentation finale (le dictionnaire) avant de l'envoyer.
        Utilisé ici pour assurer la rétrocompatibilité avec le front-end.
        """
        # Appelle la méthode parente pour obtenir la représentation standard.
        data = super().to_representation(instance)
        # Renomme la clé 'proprietaire' en 'coiffeuse'.
        data['coiffeuse'] = data.pop('proprietaire')
        # Renomme la clé 'adresse_formatee' en 'adresse'.
        data['adresse'] = data.pop('adresse_formatee')
        return data


################################################################################
#          SERIALIZER POUR L'AFFICHAGE SIMPLIFIÉ D'UN SALON (LISTE)            #
################################################################################

class TblSalonSerializer(serializers.ModelSerializer):
    """
    Serializer plus léger pour TblSalon, utilisé probablement dans des listes
    où tous les détails (comme la liste complète des services) ne sont pas nécessaires.
    """
    proprietaire = serializers.SerializerMethodField()
    adresse_formatee = serializers.SerializerMethodField()

    class Meta:
        model = TblSalon
        fields = [
            'idTblSalon', 'proprietaire', 'nom_salon',
            'slogan', 'logo_salon', 'position',
            'numero_tva', 'adresse_formatee'
        ]

    def get_proprietaire(self, obj):
        """
        Récupère l'ID de la coiffeuse propriétaire.
        """
        try:
            proprietaire = obj.get_proprietaire()
            if proprietaire:
                return proprietaire.idTblUser.idTblUser
            return None
        except Exception as e:
            return None

    def get_adresse_formatee(self, obj):
        """
        Construit un dictionnaire structuré pour l'adresse.
        """
        try:
            if obj.adresse:
                return {
                    'numero': obj.adresse.numero,
                    'rue': obj.adresse.rue.nom_rue if obj.adresse.rue else None,
                    'commune': obj.adresse.rue.localite.commune if obj.adresse.rue and obj.adresse.rue.localite else None,
                    'code_postal': obj.adresse.rue.localite.code_postal if obj.adresse.rue and obj.adresse.rue.localite else None
                }
            return None
        except Exception as e:
            return None

    def to_representation(self, instance):
        """
        Assure la rétrocompatibilité du nommage des champs 'coiffeuse' et 'adresse'.
        """
        data = super().to_representation(instance)
        data['coiffeuse'] = data.pop('proprietaire')
        data['adresse'] = data.pop('adresse_formatee')
        return data


################################################################################
#                   SERIALIZERS SIMPLES POUR MODÈLES LIÉS                      #
################################################################################

class TblSalonImageSerializer(serializers.ModelSerializer):
    """Serializer simple pour le modèle des images de salon."""

    class Meta:
        model = TblSalonImage
        fields = ['id', 'salon', 'image']


class TblAvisSerializer(serializers.ModelSerializer):
    """Serializer simple pour le modèle des avis clients."""

    class Meta:
        model = TblAvis
        fields = ['id', 'salon', 'client', 'note', 'commentaire', 'date']
        read_only_fields = ['date']


################################################################################
#             SERIALIZER DÉDIÉ À LA CRÉATION D'UN NOUVEAU SALON                #
################################################################################

class SalonCreateSerializer(serializers.ModelSerializer):
    """
    Serializer spécifiquement conçu pour la création d'un nouveau salon.
    Il inclut une logique de validation et de création personnalisée pour gérer
    la relation propriétaire via la table de liaison `TblCoiffeuseSalon`.
    """

    # Champ en écriture seule pour recevoir l'ID de la coiffeuse qui crée le salon.
    # Il ne sera pas affiché dans la réponse finale.
    coiffeuse_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TblSalon
        fields = [
            'nom_salon', 'slogan', 'a_propos', 'logo_salon',
            'numero_tva', 'adresse', 'position', 'coiffeuse_id'
        ]
        # Configuration pour rendre certains champs optionnels lors de la création.
        extra_kwargs = {
            'nom_salon': {'required': True}, 'slogan': {'required': False},
            'a_propos': {'required': False}, 'logo_salon': {'required': False},
            'numero_tva': {'required': False}, 'adresse': {'required': False},
            'position': {'required': False}
        }

    def validate_coiffeuse_id(self, value):
        """
        Méthode de validation pour le champ `coiffeuse_id`.
        Vérifie si une coiffeuse avec l'ID fourni existe bien en base de données.
        """
        try:
            TblCoiffeuse.objects.get(idTblUser=value)
            return value
        except TblCoiffeuse.DoesNotExist:
            raise serializers.ValidationError("La coiffeuse spécifiée n'existe pas.")

    def validate_numero_tva(self, value):
        """
        Valide que le numéro de TVA est unique s'il est fourni.
        """
        if value and TblSalon.objects.filter(numero_tva=value).exists():
            raise serializers.ValidationError("Ce numéro de TVA est déjà utilisé.")
        return value

    def validate_adresse(self, value):
        """
        Valide que l'objet Adresse existe s'il est fourni.
        """
        if value:
            try:
                TblAdresse.objects.get(idTblAdresse=value.idTblAdresse)
            except TblAdresse.DoesNotExist:
                raise serializers.ValidationError("L'adresse spécifiée n'existe pas.")
        return value

    def create(self, validated_data):
        """
        Logique de création personnalisée.
        Cette méthode est appelée lorsque `.save()` est exécuté sur le serializer.
        """
        # Sépare l'ID de la coiffeuse du reste des données du salon.
        coiffeuse_id = validated_data.pop('coiffeuse_id')
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=coiffeuse_id)

        # 1. Crée l'objet Salon avec les données restantes.
        salon = TblSalon.objects.create(**validated_data)

        # 2. Crée la relation de propriété dans la table de liaison.
        TblCoiffeuseSalon.objects.create(
            coiffeuse=coiffeuse,
            salon=salon,
            est_proprietaire=True
        )

        return salon

    def to_representation(self, instance):
        """
        Définit le format de la réponse après une création réussie.
        Réutilise `SalonSerializer` pour renvoyer une vue détaillée et cohérente
        du salon qui vient d'être créé.
        """
        return SalonSerializer(instance, context=self.context).data


################################################################################
#         SERIALIZER OPTIMISÉ POUR LES LISTES DÉROULANTES (DROPDOWNS)          #
################################################################################

class ServiceDropdownSerializer(serializers.ModelSerializer):
    """
    Serializer léger et optimisé pour afficher les services dans une liste
    déroulante (dropdown), par exemple dans une application front-end.
    Il aplatit la structure en incluant l'ID et le nom de la catégorie directement.
    """
    categorie_id = serializers.SerializerMethodField()
    categorie_nom = serializers.SerializerMethodField()

    class Meta:
        model = TblService
        fields = [
            'idTblService',
            'intitule_service',
            'categorie_id',
            'categorie_nom'
        ]

    def get_categorie_id(self, obj):
        """Récupère l'ID de la catégorie du service."""
        return obj.categorie.idTblCategorie if obj.categorie else None

    def get_categorie_nom(self, obj):
        """Récupère le nom de la catégorie du service."""
        return obj.categorie.intitule_categorie if obj.categorie else "Sans catégorie"




# from rest_framework import serializers
# from hairbnb.models import TblSalon, TblSalonService, TblSalonImage, TblAvis, TblService
# from hairbnb.serializers.salon_services_serializers import ServiceSerializer
#
#
# class SalonSerializer(serializers.ModelSerializer):
#     services = serializers.SerializerMethodField()
#     proprietaire = serializers.SerializerMethodField()
#     adresse_formatee = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'idTblSalon', 'proprietaire', 'services', 'nom_salon',
#             'slogan', 'a_propos', 'logo_salon', 'position',
#             'numero_tva', 'adresse_formatee'
#         ]
#
#     def get_services(self, obj):
#         # Récupérer les services via la table de liaison
#         salon_services = TblSalonService.objects.filter(salon=obj)
#         services = [ss.service for ss in salon_services]
#         return ServiceSerializer(services, many=True).data
#
#     def get_proprietaire(self, obj):
#         # Récupérer la coiffeuse propriétaire du salon
#         try:
#             proprietaire = obj.get_proprietaire()
#             if proprietaire:
#                 return proprietaire.idTblUser.idTblUser
#             return None
#         except Exception as e:
#             print(f"❌ Erreur get_proprietaire: {e}")  # Debug
#             return None
#
#     def get_adresse_formatee(self, obj):
#         """Sérialise l'adresse de manière sécurisée"""
#         try:
#             if obj.adresse:
#                 return {
#                     'numero': obj.adresse.numero,
#                     'rue': obj.adresse.rue.nom_rue if obj.adresse.rue else None,
#                     'commune': obj.adresse.rue.localite.commune if obj.adresse.rue and obj.adresse.rue.localite else None,
#                     'code_postal': obj.adresse.rue.localite.code_postal if obj.adresse.rue and obj.adresse.rue.localite else None
#                 }
#             return None
#         except Exception as e:
#             print(f"❌ Erreur adresse: {e}")  # Debug
#             return None
#
#     def to_representation(self, instance):
#         # Conversion standard en dictionnaire
#         data = super().to_representation(instance)
#         # Pour la compatibilité avec l'ancien code, renommer proprietaire en coiffeuse
#         data['coiffeuse'] = data.pop('proprietaire')
#         # Renommer adresse_formatee en adresse pour compatibilité
#         data['adresse'] = data.pop('adresse_formatee')
#         return data
#
#
# class TblSalonSerializer(serializers.ModelSerializer):
#     proprietaire = serializers.SerializerMethodField()
#     adresse_formatee = serializers.SerializerMethodField()  # ✅ Ajouté
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'idTblSalon', 'proprietaire', 'nom_salon',
#             'slogan', 'logo_salon', 'position',
#             'numero_tva', 'adresse_formatee'
#         ]
#
#     def get_proprietaire(self, obj):
#         # Récupérer la coiffeuse propriétaire du salon
#         try:
#             proprietaire = obj.get_proprietaire()
#             if proprietaire:
#                 return proprietaire.idTblUser.idTblUser
#             return None
#         except Exception as e:
#             print(f"❌ Erreur get_proprietaire: {e}")  # Debug
#             return None
#
#     def get_adresse_formatee(self, obj):
#         """Sérialise l'adresse de manière sécurisée"""
#         try:
#             if obj.adresse:
#                 return {
#                     'numero': obj.adresse.numero,
#                     'rue': obj.adresse.rue.nom_rue if obj.adresse.rue else None,
#                     'commune': obj.adresse.rue.localite.commune if obj.adresse.rue and obj.adresse.rue.localite else None,
#                     'code_postal': obj.adresse.rue.localite.code_postal if obj.adresse.rue and obj.adresse.rue.localite else None
#                 }
#             return None
#         except Exception as e:
#             print(f"❌ Erreur adresse: {e}")  # Debug
#             return None
#
#     def to_representation(self, instance):
#         # Conversion standard en dictionnaire
#         data = super().to_representation(instance)
#         # Pour la compatibilité avec l'ancien code, renommer proprietaire en coiffeuse
#         data['coiffeuse'] = data.pop('proprietaire')
#         # Renommer adresse_formatee en adresse pour compatibilité
#         data['adresse'] = data.pop('adresse_formatee')
#         return data
#
#
# class TblSalonImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblSalonImage
#         fields = ['id', 'salon', 'image']
#
#
# class TblAvisSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblAvis
#         fields = ['id', 'salon', 'client', 'note', 'commentaire', 'date']
#         read_only_fields = ['date']
#
#
# from rest_framework import serializers
# from hairbnb.models import TblSalon, TblCoiffeuse, TblAdresse, TblCoiffeuseSalon
#
#
# class SalonCreateSerializer(serializers.ModelSerializer):
#     """
#     Serializer spécialement conçu pour la création de salons.
#     Gère automatiquement la relation propriétaire via TblCoiffeuseSalon.
#     """
#
#     # Champ obligatoire pour identifier la coiffeuse propriétaire
#     coiffeuse_id = serializers.IntegerField(write_only=True)
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'nom_salon',
#             'slogan',
#             'a_propos',
#             'logo_salon',
#             'numero_tva',
#             'adresse',
#             'position',
#             'coiffeuse_id'  # Champ pour identifier le propriétaire
#         ]
#         extra_kwargs = {
#             'nom_salon': {'required': True},
#             'slogan': {'required': False},
#             'a_propos': {'required': False},
#             'logo_salon': {'required': False},
#             'numero_tva': {'required': False},
#             'adresse': {'required': False},
#             'position': {'required': False}
#         }
#
#     def validate_coiffeuse_id(self, value):
#         """Valide que la coiffeuse existe"""
#         try:
#             coiffeuse = TblCoiffeuse.objects.get(idTblUser=value)
#             return value
#         except TblCoiffeuse.DoesNotExist:
#             raise serializers.ValidationError("La coiffeuse spécifiée n'existe pas.")
#
#     def validate_numero_tva(self, value):
#         """Valide l'unicité du numéro de TVA si fourni"""
#         if value and TblSalon.objects.filter(numero_tva=value).exists():
#             raise serializers.ValidationError("Ce numéro de TVA est déjà utilisé.")
#         return value
#
#     def validate_adresse(self, value):
#         """Valide que l'adresse existe si fournie"""
#         if value:
#             try:
#                 TblAdresse.objects.get(idTblAdresse=value.idTblAdresse)
#             except TblAdresse.DoesNotExist:
#                 raise serializers.ValidationError("L'adresse spécifiée n'existe pas.")
#         return value
#
#     def create(self, validated_data):
#         """
#         Crée le salon et établit automatiquement la relation propriétaire.
#         """
#         # Extraire l'ID de la coiffeuse des données validées
#         coiffeuse_id = validated_data.pop('coiffeuse_id')
#
#         # Récupérer l'objet coiffeuse
#         coiffeuse = TblCoiffeuse.objects.get(idTblUser=coiffeuse_id)
#
#         # Créer le salon
#         salon = TblSalon.objects.create(**validated_data)
#
#         # Créer la relation propriétaire dans TblCoiffeuseSalon
#         TblCoiffeuseSalon.objects.create(
#             coiffeuse=coiffeuse,
#             salon=salon,
#             est_proprietaire=True
#         )
#
#         return salon
#
#     def to_representation(self, instance):
#         """
#         Retourne une représentation complète du salon créé.
#         Utilise le SalonSerializer existant pour la réponse.
#         """
#         return SalonSerializer(instance, context=self.context).data
#
#
# class ServiceDropdownSerializer(serializers.ModelSerializer):
#     """
#     Serializer optimisé pour les dropdowns Flutter.
#     ID service, nom service, ID catégorie, nom catégorie.
#     """
#     categorie_id = serializers.SerializerMethodField()
#     categorie_nom = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblService
#         fields = [
#             'idTblService',
#             'intitule_service',
#             'categorie_id',
#             'categorie_nom'
#         ]
#
#     def get_categorie_id(self, obj):
#         return obj.categorie.idTblCategorie if obj.categorie else None
#
#     def get_categorie_nom(self, obj):
#         return obj.categorie.intitule_categorie if obj.categorie else "Sans catégorie"