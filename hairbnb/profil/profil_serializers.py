################################################################################
#                                                                              #
#         SÉRIALISEURS CENTRAUX POUR LA GESTION DES UTILISATEURS                #
#                                                                              #
#  Ce fichier définit un ensemble complet de sérialiseurs (serializers) pour   #
#  gérer les données principales de l'application. Il couvre trois domaines    #
#  fonctionnels majeurs :                                                      #
#                                                                              #
#  1. Sérialiseurs de Lecture : Classes pour afficher les données des modèles  #
#     de base (Utilisateur, Salon, Adresse, etc.) dans les réponses d'API.     #
#                                                                              #
#  2. Création de Profil (`UserCreationSerializer`): Un sérialiseur complexe   #
#     qui gère la création d'un utilisateur complet avec toutes ses données    #
#     liées (adresse, profil client/coiffeuse) en une seule transaction.       #
#                                                                              #
#  3. Suppression de Profil (`DeleteProfileSerializer`): Un sérialiseur        #
#     critique et destructif qui orchestre la suppression complète d'un        #
#     utilisateur et de toutes ses données associées à travers l'application.  #
#                                                                              #
################################################################################


from django.db import transaction
from rest_framework import serializers
from hairbnb.models import (
    TblUser, TblCoiffeuse, TblClient, TblRue, TblLocalite, TblAdresse,
    TblRole, TblSexe, TblType, TblSalon, TblCoiffeuseSalon, TblAvis, TblFavorite, TblCart, TblPaiement, TblRendezVous,
    TblSalonImage, TblIndisponibilite, TblHoraireCoiffeuse, TblEmailNotification, AIConversation, TblCartItem
)
from datetime import datetime




# 🔹 Serializer pour la Localité
class LocaliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TblLocalite
        fields = ['idTblLocalite', 'commune', 'code_postal']


# 🔹 Serializer pour la Rue
class RueSerializer(serializers.ModelSerializer):
    localite = LocaliteSerializer()

    class Meta:
        model = TblRue
        fields = ['idTblRue', 'nom_rue', 'localite']


# 🔹 Serializer pour l'Adresse
class AdresseSerializer(serializers.ModelSerializer):
    rue = RueSerializer()

    class Meta:
        model = TblAdresse
        fields = ['idTblAdresse', 'numero', 'rue']


# 🔹 Serializer pour le Rôle
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TblRole
        fields = ['idTblRole', 'nom']


# 🔹 Serializer pour le Sexe
class SexeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TblSexe
        fields = ['idTblSexe', 'libelle']


# 🔹 Serializer pour le Type
class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TblType
        fields = ['idTblType', 'libelle']


# 🔹 Serializer pour l'Utilisateur (User)
class UserSerializer(serializers.ModelSerializer):
    adresse = AdresseSerializer()
    role = RoleSerializer()
    sexe_ref = SexeSerializer()
    type_ref = TypeSerializer()

    class Meta:
        model = TblUser
        fields = [
            'idTblUser', 'uuid', 'nom', 'prenom', 'email', 'numero_telephone',
            'date_naissance', 'is_active', 'photo_profil', 'adresse',
            'role', 'sexe_ref', 'type_ref'
        ]


# 🔹 Serializer simple pour la Coiffeuse (sans user details)
class CoiffeuseSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TblCoiffeuse
        fields = ['idTblUser', 'nom_commercial']


# 🔹 Serializer COMPLET pour la Coiffeuse
class CoiffeuseSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='idTblUser')

    class Meta:
        model = TblCoiffeuse
        fields = [
            'idTblUser', 'nom_commercial', 'user'
        ]


# 🔹 Serializer COMPLET pour le Client
class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='idTblUser')

    class Meta:
        model = TblClient
        fields = ['idTblUser', 'user']


# 🔹 Serializer simple pour le Salon
class SalonSimpleSerializer(serializers.ModelSerializer):
    adresse = AdresseSerializer(read_only=True)

    class Meta:
        model = TblSalon
        fields = [
            'idTblSalon', 'nom_salon', 'slogan', 'logo_salon',
            'adresse', 'position', 'numero_tva'
        ]


# 🔹 Serializer COMPLET pour le Salon
class SalonSerializer(serializers.ModelSerializer):
    adresse = AdresseSerializer(read_only=True)
    coiffeuses = CoiffeuseSimpleSerializer(many=True, read_only=True)
    proprietaire = serializers.SerializerMethodField()

    class Meta:
        model = TblSalon
        fields = [
            'idTblSalon', 'nom_salon', 'slogan', 'a_propos',
            'logo_salon', 'adresse', 'position', 'numero_tva',
            'coiffeuses', 'proprietaire'
        ]

    def get_proprietaire(self, obj):
        """Récupère la coiffeuse propriétaire du salon"""
        proprietaire = obj.get_proprietaire()
        if proprietaire:
            return CoiffeuseSimpleSerializer(proprietaire).data
        return None


# 🔹 Serializer pour la relation Coiffeuse-Salon
class CoiffeuseSalonSerializer(serializers.ModelSerializer):
    coiffeuse = CoiffeuseSimpleSerializer(read_only=True)
    salon = SalonSimpleSerializer(read_only=True)

    class Meta:
        model = TblCoiffeuseSalon
        fields = ['idCoiffeuseSalon', 'coiffeuse', 'salon', 'est_proprietaire']


# 🔹 Serializer pour la création complète d'un profil utilisateur (Client ou Coiffeuse)
class UserCreationSerializer(serializers.Serializer):
    """
    Serialiser pour la création complète d'un profil utilisateur.
    Gère la création de l'utilisateur et des objets liés (adresse, type spécifique),
    sans inclure la création de salon ou la relation TblCoiffeuseSalon à ce stade.
    Le rôle par défaut est 'user'.
    """

    # Champs obligatoires de base de l'utilisateur (pour TblUser)
    userUuid = serializers.CharField(max_length=40)
    email = serializers.EmailField()
    # Le 'type' ici correspond à 'Client' ou 'Coiffeuse' dans TblType
    type = serializers.CharField(max_length=15)
    nom = serializers.CharField(max_length=50)
    prenom = serializers.CharField(max_length=50)
    sexe = serializers.CharField(max_length=10)  # 'homme' ou 'femme' (en minuscules)
    telephone = serializers.CharField(max_length=20)
    date_naissance = serializers.CharField()  # Attendu au format DD-MM-YYYY

    # Champs d'adresse (pour TblAdresse, TblRue, TblLocalite)
    code_postal = serializers.CharField(max_length=6)
    commune = serializers.CharField(max_length=40)
    rue = serializers.CharField(max_length=100)
    numero = serializers.CharField(max_length=5)
    boite_postale = serializers.CharField(max_length=10, required=False, allow_blank=True)

    # Champ optionnel pour la coiffeuse (pour TblCoiffeuse)
    nom_commercial = serializers.CharField(max_length=50, required=False, allow_blank=True)

    # Photo de profil (fichier)
    photo_profil = serializers.ImageField(required=False, allow_null=True)  # Temporaire pour tester

    def validate_userUuid(self, value):
        """Vérifie que l'UUID n'existe pas déjà."""
        if TblUser.objects.filter(uuid=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet UUID existe déjà.")
        return value

    def validate_email(self, value):
        """Vérifie que l'email n'existe pas déjà."""
        if TblUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

    def validate_type(self, value):
        """Vérifie que le type (Client/Coiffeuse) existe dans la table TblType."""
        # CHANGEMENT : Suppression de value_lower = value.lower()
        if value not in ['Client', 'Coiffeuse']: # CHANGEMENT : Les valeurs attendues sont avec majuscule
            raise serializers.ValidationError("Le type doit être 'Client' ou 'Coiffeuse'.")
        try:
            TblType.objects.get(libelle=value) # CHANGEMENT : Recherche avec la valeur exacte reçue
        except TblType.DoesNotExist:
            raise serializers.ValidationError(f"Le type '{value}' n'existe pas dans la table de référence TblType.")
        return value # Retourne la valeur telle quelle

    def validate_sexe(self, value):
        """Vérifie que le sexe existe dans la table de référence."""
        # CHANGEMENT : Suppression de value_lower = value.lower()
        if value not in ['Homme', 'Femme']: # CHANGEMENT : Les valeurs attendues sont avec majuscule
             raise serializers.ValidationError("Le sexe doit être 'Homme' ou 'Femme'.")
        try:
            TblSexe.objects.get(libelle=value) # CHANGEMENT : Recherche avec la valeur exacte reçue
        except TblSexe.DoesNotExist:
            raise serializers.ValidationError(f"Le sexe '{value}' n'existe pas dans la table de référence TblSexe.")
        return value # Retourne la valeur telle quelle

    def validate_date_naissance(self, value):
        """Valide et convertit la date de naissance du format DD-MM-YYYY en objet Date."""
        try:
            date_obj = datetime.strptime(value, '%d-%m-%Y').date()
            return date_obj
        except ValueError:
            raise serializers.ValidationError("Le format de la date de naissance doit être DD-MM-YYYY.")

    def validate(self, attrs):
        """Validation croisée pour les champs dépendant du type d'utilisateur."""
        # Pour une coiffeuse, le nom_commercial est obligatoire
        if attrs['type'] == 'coiffeuse' and not attrs.get('nom_commercial'):
            raise serializers.ValidationError({
                'nom_commercial': 'Le nom commercial est obligatoire pour un type coiffeuse.'
            })
        return attrs

    def create(self, validated_data):
        """Crée un utilisateur complet, son adresse, son rôle par défaut et son profil spécifique (Coiffeuse/Client)."""
        
        # 🔍 DEBUG: Vérifier la photo dans validated_data
        print("=== DEBUG SERIALIZER CREATE ===")
        print(f"validated_data keys: {list(validated_data.keys())}")
        if 'photo_profil' in validated_data:
            photo = validated_data['photo_profil']
            print(f"📷 Photo dans validated_data: {photo}, type: {type(photo)}")
            if hasattr(photo, 'name'):
                print(f"📷 Nom du fichier: {photo.name}, taille: {photo.size}")
        else:
            print("⚠️ AUCUNE PHOTO dans validated_data !")
        print("===================================")
        
        with transaction.atomic():
            # Récupérer les objets de référence basés sur les valeurs validées
            # Le rôle par défaut pour les utilisateurs créés via cette API est 'user'
            role_obj = TblRole.objects.get(nom='user') # Le rôle par défaut est 'user'
            sexe_obj = TblSexe.objects.get(libelle=validated_data['sexe'])
            type_obj = TblType.objects.get(libelle=validated_data['type'])

            # Créer ou récupérer la localité
            localite, _ = TblLocalite.objects.get_or_create(
                commune=validated_data['commune'],
                code_postal=validated_data['code_postal']
            )

            # Créer ou récupérer la rue
            rue, _ = TblRue.objects.get_or_create(
                nom_rue=validated_data['rue'],
                localite=localite
            )

            # Gérer le format du numéro de rue (avec ou sans boîte postale)
            numero_rue_complet = validated_data['numero']
            if validated_data.get('boite_postale'):
                numero_rue_complet = f"{numero_rue_complet}/{validated_data['boite_postale']}"

            # Créer l'adresse
            adresse = TblAdresse.objects.create(
                numero=numero_rue_complet,
                rue=rue
            )

            # Créer l'utilisateur principal
            # Préparer les données utilisateur de base
            user_data = {
                'uuid': validated_data['userUuid'],
                'nom': validated_data['nom'],
                'prenom': validated_data['prenom'],
                'email': validated_data['email'],
                'numero_telephone': validated_data['telephone'],
                'date_naissance': validated_data['date_naissance'],
                'adresse': adresse,
                'role': role_obj,
                'sexe_ref': sexe_obj,
                'type_ref': type_obj
            }

            # Ajouter la photo seulement si elle est fournie
            photo_profil = validated_data.get('photo_profil')
            if photo_profil:
                user_data['photo_profil'] = photo_profil

            # Créer l'utilisateur
            user = TblUser.objects.create(**user_data)

            # Créer l'objet spécifique au type (Coiffeuse ou Client)
            if validated_data['type'] == 'Coiffeuse':
                TblCoiffeuse.objects.create(
                    idTblUser=user,
                    nom_commercial=validated_data.get('nom_commercial')
                )
            elif validated_data['type'] == 'Client':
                TblClient.objects.create(idTblUser=user)

            return user

    def to_representation(self, instance):
        """Personnalise la réponse de sortie après la création de l'utilisateur."""
        return {
            'user_id': instance.idTblUser,
            'uuid': instance.uuid,
            'nom': instance.nom,
            'prenom': instance.prenom,
            'email': instance.email,
            'type': instance.get_type(), # Appelle la méthode get_type() de TblUser
            'role': instance.get_role(), # Appelle la méthode get_role() de TblUser
            'created': True
        }


class DeleteProfileSerializer(serializers.Serializer):
    """
    Serializer pour gérer la suppression complète du profil d'un utilisateur.

    Cette suppression inclut :
    - Tous les rendez-vous (client et coiffeuse)
    - Tous les paiements et transactions associés
    - Le panier et ses articles
    - Les avis donnés ou reçus
    - Les favoris
    - Les horaires et indisponibilités (pour les coiffeuses)
    - Les salons possédés et leurs données associées
    - Les notifications email
    - Les conversations IA
    - L'utilisateur lui-même
    """

    # Champ optionnel pour confirmation (sécurité supplémentaire)
    confirmation = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Tapez 'SUPPRIMER' pour confirmer la suppression définitive"
    )

    # Champ pour indiquer si on veut garder les données anonymisées des avis
    anonymize_reviews = serializers.BooleanField(
        default=True,
        help_text="Si True, les avis seront anonymisés au lieu d'être supprimés"
    )

    def validate_confirmation(self, value):
        """Valide que l'utilisateur a bien tapé 'SUPPRIMER' pour confirmer."""
        if value and value.upper() != 'SUPPRIMER':
            raise serializers.ValidationError(
                "Vous devez tapez 'SUPPRIMER' pour confirmer la suppression."
            )
        return value

    def validate(self, attrs):
        """Validation globale du serializer."""
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("Aucun utilisateur spécifié pour la suppression.")

        # Vérifier que l'utilisateur existe dans TblUser
        try:
            tbl_user = TblUser.objects.get(id=user.id)
        except TblUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable dans la base de données.")

        return attrs

    @transaction.atomic
    def delete_user_profile(self, user_id):
        """
        Supprime complètement le profil d'un utilisateur et toutes ses données associées.

        Args:
            user_id (int): ID de l'utilisateur à supprimer

        Returns:
            dict: Résumé des éléments supprimés
        """
        try:
            tbl_user = TblUser.objects.get(id=user_id)
        except TblUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")

        deletion_summary = {
            'user_id': user_id,
            'user_name': f"{tbl_user.nom} {tbl_user.prenom}",
            'deleted_items': {}
        }

        # 1. Supprimer les conversations IA
        ai_conversations = AIConversation.objects.filter(user=tbl_user)
        deletion_summary['deleted_items']['ai_conversations'] = ai_conversations.count()
        ai_conversations.delete()

        # 2. Supprimer les notifications email
        email_notifications = TblEmailNotification.objects.filter(destinataire=tbl_user)
        deletion_summary['deleted_items']['email_notifications'] = email_notifications.count()
        email_notifications.delete()

        # 3. Vérifier si l'utilisateur est une coiffeuse
        try:
            coiffeuse = TblCoiffeuse.objects.get(idTblUser=tbl_user)
            deletion_summary.update(self._delete_coiffeuse_data(coiffeuse))
        except TblCoiffeuse.DoesNotExist:
            # Ce n'est pas une coiffeuse, vérifier si c'est un client
            pass

        # 4. Supprimer les données client (rendez-vous pris, favoris, panier, etc.)
        deletion_summary.update(self._delete_client_data(tbl_user))

        # 5. Gérer les avis selon la préférence
        anonymize_reviews = self.validated_data.get('anonymize_reviews', True)
        if anonymize_reviews:
            deletion_summary.update(self._anonymize_user_reviews(tbl_user))
        else:
            deletion_summary.update(self._delete_user_reviews(tbl_user))

        # 6. Supprimer les fichiers média
        media_summary = self._delete_user_media_files(tbl_user)
        deletion_summary['deleted_items'].update(media_summary.get('deleted_items', {}))

        # 7. Supprimer l'enregistrement TblUser (cela supprimera aussi l'enregistrement User Django par CASCADE)
        tbl_user.delete()
        deletion_summary['deleted_items']['user_account'] = 1

        return deletion_summary

    def _delete_coiffeuse_data(self, coiffeuse):
        """Supprime toutes les données spécifiques à une coiffeuse."""
        summary = {'deleted_items': {}}

        # Supprimer les horaires
        horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['horaires'] = horaires.count()
        horaires.delete()

        # Supprimer les indisponibilités
        indisponibilites = TblIndisponibilite.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['indisponibilites'] = indisponibilites.count()
        indisponibilites.delete()

        # Supprimer les rendez-vous en tant que coiffeuse
        rdv_coiffeuse = TblRendezVous.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['rdv_as_coiffeuse'] = rdv_coiffeuse.count()

        # Supprimer les paiements liés à ces rendez-vous
        paiements_coiffeuse = TblPaiement.objects.filter(rendez_vous__in=rdv_coiffeuse)
        summary['deleted_items']['paiements_coiffeuse'] = paiements_coiffeuse.count()
        paiements_coiffeuse.delete()  # Les transactions seront supprimées par CASCADE

        rdv_coiffeuse.delete()

        # Récupérer les salons où la coiffeuse est propriétaire
        salons_proprietaire = TblSalon.objects.filter(
            employes__coiffeuse=coiffeuse,
            employes__est_proprietaire=True
        )

        summary['deleted_items']['salons_owned'] = salons_proprietaire.count()

        # Pour chaque salon, supprimer toutes les données associées
        for salon in salons_proprietaire:
            summary.update(self._delete_salon_data(salon))

        # Supprimer les relations coiffeuse-salon
        relations_salon = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['coiffeuse_salon_relations'] = relations_salon.count()
        relations_salon.delete()

        return summary

    def _delete_salon_data(self, salon):
        """Supprime toutes les données associées à un salon."""
        summary = {'deleted_items': {}}

        # Supprimer les images du salon
        salon_images = TblSalonImage.objects.filter(salon=salon)
        summary['deleted_items']['salon_images'] = salon_images.count()
        salon_images.delete()

        # Supprimer les avis du salon (ils seront gérés séparément pour l'anonymisation)
        # Les avis seront traités dans _anonymize_user_reviews ou _delete_user_reviews

        # Supprimer les favoris pointant vers ce salon
        favoris_salon = TblFavorite.objects.filter(salon=salon)
        summary['deleted_items']['favoris_salon'] = favoris_salon.count()
        favoris_salon.delete()

        # Le salon sera supprimé par CASCADE quand la coiffeuse sera supprimée
        return summary

    def _delete_client_data(self, tbl_user):
        """Supprime toutes les données client d'un utilisateur."""
        summary = {'deleted_items': {}}

        # Récupérer tous les clients liés à cet utilisateur
        clients = TblClient.objects.filter(idTblUser=tbl_user)

        for client in clients:
            # Supprimer les rendez-vous en tant que client
            rdv_client = TblRendezVous.objects.filter(client=client)
            summary['deleted_items']['rdv_as_client'] = rdv_client.count()

            # Supprimer les paiements liés à ces rendez-vous
            paiements_client = TblPaiement.objects.filter(rendez_vous__in=rdv_client)
            summary['deleted_items']['paiements_client'] = paiements_client.count()
            paiements_client.delete()  # Les transactions seront supprimées par CASCADE

            rdv_client.delete()

        # Supprimer le panier et ses articles
        try:
            cart = TblCart.objects.get(user=tbl_user)
            cart_items = TblCartItem.objects.filter(cart=cart)
            summary['deleted_items']['cart_items'] = cart_items.count()
            cart_items.delete()
            cart.delete()
            summary['deleted_items']['cart'] = 1
        except TblCart.DoesNotExist:
            summary['deleted_items']['cart'] = 0
            summary['deleted_items']['cart_items'] = 0

        # Supprimer les favoris de l'utilisateur
        favoris_user = TblFavorite.objects.filter(user=tbl_user)
        summary['deleted_items']['favoris_user'] = favoris_user.count()
        favoris_user.delete()

        return summary

    def _anonymize_user_reviews(self, tbl_user):
        """Anonymise les avis de l'utilisateur au lieu de les supprimer."""
        summary = {'deleted_items': {}}

        # Récupérer tous les clients liés à cet utilisateur
        clients = TblClient.objects.filter(idTblUser=tbl_user)

        avis_count = 0
        for client in clients:
            # Anonymiser les avis donnés par ce client
            avis_donnes = TblAvis.objects.filter(client=client)
            avis_count += avis_donnes.count()

            # Mettre client=None pour anonymiser
            avis_donnes.update(client=None)

        summary['deleted_items']['avis_anonymized'] = avis_count
        return summary

    def _delete_user_reviews(self, tbl_user):
        """Supprime complètement les avis de l'utilisateur."""
        summary = {'deleted_items': {}}

        # Récupérer tous les clients liés à cet utilisateur
        clients = TblClient.objects.filter(idTblUser=tbl_user)

        avis_count = 0
        for client in clients:
            # Supprimer les avis donnés par ce client
            avis_donnes = TblAvis.objects.filter(client=client)
            avis_count += avis_donnes.count()
            avis_donnes.delete()

        summary['deleted_items']['avis_deleted'] = avis_count
        return summary

    def _delete_user_media_files(self, tbl_user):
        """Supprime les fichiers média associés à l'utilisateur."""
        summary = {'deleted_items': {}}

        # Si l'utilisateur a une photo de profil
        if hasattr(tbl_user, 'photo_profil') and tbl_user.photo_profil:
            try:
                # Supprimer le fichier physique
                if tbl_user.photo_profil.storage.exists(tbl_user.photo_profil.name):
                    tbl_user.photo_profil.delete(save=False)
                    summary['deleted_items']['profile_photo'] = 1
                else:
                    summary['deleted_items']['profile_photo'] = 0
            except Exception as e:
                # Logger l'erreur mais continuer la suppression
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erreur lors de la suppression de la photo de profil: {str(e)}")
                summary['deleted_items']['profile_photo'] = 0

        return summary

    def save(self):
        """
        Exécute la suppression du profil utilisateur.

        Returns:
            dict: Résumé détaillé des suppressions effectuées
        """
        user = self.context.get('user')
        return self.delete_user_profile(user.id)


class DeleteProfileResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de suppression de profil."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    deletion_summary = serializers.DictField()
    timestamp = serializers.DateTimeField()

    class Meta:
        read_only_fields = ['success', 'message', 'deletion_summary', 'timestamp']


class DeleteProfileUserSerializer(serializers.Serializer):
    """
    Serialiseur pour gérer la suppression complète du profil d'un utilisateur.
    """
    confirmation = serializers.CharField(
        max_length=20,
        required=False,
        help_text="Tapez 'SUPPRIMER' pour confirmer la suppression définitive"
    )

    anonymize_reviews = serializers.BooleanField(
        default=True,
        help_text="Si True, les avis seront anonymisés au lieu d'être supprimés"
    )

    def validate_confirmation(self, value):
        """Valide que l'utilisateur a bien tapé 'SUPPRIMER' pour confirmer."""
        if value and value.upper() != 'SUPPRIMER':
            raise serializers.ValidationError(
                "Vous devez taper 'SUPPRIMER' pour confirmer la suppression."
            )
        return value

    def validate(self, attrs):
        """Validation globale du serializer."""
        user_authentifie = self.context.get('user')
        id_cible_url = self.context.get('id_cible')

        if not user_authentifie:
            raise serializers.ValidationError("Authentification requise.")

        if not id_cible_url:
            raise serializers.ValidationError("L'ID du profil à supprimer est manquant.")

        # Vérifier que l'utilisateur CIBLE existe dans TblUser
        try:
            tbl_user = TblUser.objects.get(idTblUser=id_cible_url)
        except TblUser.DoesNotExist:
            raise serializers.ValidationError(f"Utilisateur avec l'ID {id_cible_url} introuvable.")

        return attrs

    @transaction.atomic
    def delete_user_profile(self, user_id):
        """
        Supprime complètement le profil d'un utilisateur et toutes ses données associées.
        """
        try:
            tbl_user = TblUser.objects.get(idTblUser=user_id)
        except TblUser.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable lors de la suppression finale.")

        deletion_summary = {
            'user_id': user_id,
            'user_name': f"{tbl_user.nom} {tbl_user.prenom}",
            'deleted_items': {}
        }

        try:
            # 1. Supprimer les conversations IA
            ai_conversations = AIConversation.objects.filter(user=tbl_user)
            deletion_summary['deleted_items']['ai_conversations'] = ai_conversations.count()
            ai_conversations.delete()

            # 2. Supprimer les notifications email
            email_notifications = TblEmailNotification.objects.filter(destinataire=tbl_user)
            deletion_summary['deleted_items']['email_notifications'] = email_notifications.count()
            email_notifications.delete()

            # 3. Vérifier si l'utilisateur est une coiffeuse
            try:
                coiffeuse = TblCoiffeuse.objects.get(idTblUser=tbl_user)
                coiffeuse_summary = self._delete_coiffeuse_data(coiffeuse)
                deletion_summary['deleted_items'].update(coiffeuse_summary.get('deleted_items', {}))
            except TblCoiffeuse.DoesNotExist:
                pass

            # 4. Supprimer les données client
            client_summary = self._delete_client_data(tbl_user)
            deletion_summary['deleted_items'].update(client_summary.get('deleted_items', {}))

            # 5. Gérer les avis selon la préférence
            anonymize_reviews = self.validated_data.get('anonymize_reviews', True)
            if anonymize_reviews:
                reviews_summary = self._anonymize_user_reviews(tbl_user)
            else:
                reviews_summary = self._delete_user_reviews(tbl_user)
            deletion_summary['deleted_items'].update(reviews_summary.get('deleted_items', {}))

            # 6. Supprimer les fichiers média
            media_summary = self._delete_user_media_files(tbl_user)
            deletion_summary['deleted_items'].update(media_summary.get('deleted_items', {}))

            # 7. Supprimer l'enregistrement TblUser
            tbl_user.delete()
            deletion_summary['deleted_items']['user_account'] = 1

            return deletion_summary

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur dans delete_user_profile: {str(e)}")
            raise serializers.ValidationError(f"Erreur lors de la suppression: {str(e)}")

    def _delete_coiffeuse_data(self, coiffeuse):
        """Supprime toutes les données spécifiques à une coiffeuse."""
        summary = {'deleted_items': {}}

        # Supprimer les horaires
        horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['horaires'] = horaires.count()
        horaires.delete()

        # Supprimer les indisponibilités
        indisponibilites = TblIndisponibilite.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['indisponibilites'] = indisponibilites.count()
        indisponibilites.delete()

        # Supprimer les rendez-vous en tant que coiffeuse
        rdv_coiffeuse = TblRendezVous.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['rdv_as_coiffeuse'] = rdv_coiffeuse.count()

        # Supprimer les paiements liés à ces rendez-vous
        paiements_coiffeuse = TblPaiement.objects.filter(rendez_vous__in=rdv_coiffeuse)
        summary['deleted_items']['paiements_coiffeuse'] = paiements_coiffeuse.count()
        paiements_coiffeuse.delete()
        rdv_coiffeuse.delete()

        # Supprimer les salons dont elle est propriétaire
        salons_proprietaire = TblSalon.objects.filter(
            employes__coiffeuse=coiffeuse,
            employes__est_proprietaire=True
        )
        summary['deleted_items']['salons_owned'] = salons_proprietaire.count()

        for salon in salons_proprietaire:
            salon_summary = self._delete_salon_data(salon)
            # Fusionner les données de suppression du salon
            for key, value in salon_summary.get('deleted_items', {}).items():
                if key in summary['deleted_items']:
                    summary['deleted_items'][key] += value
                else:
                    summary['deleted_items'][key] = value

        # Supprimer les relations coiffeuse-salon
        relations_salon = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse)
        summary['deleted_items']['coiffeuse_salon_relations'] = relations_salon.count()
        relations_salon.delete()

        return summary

    def _delete_salon_data(self, salon):
        """Supprime toutes les données associées à un salon."""
        summary = {'deleted_items': {}}

        # Supprimer les images du salon (fichiers ET enregistrements)
        salon_images = TblSalonImage.objects.filter(salon=salon)
        images_count = salon_images.count()
        files_deleted = 0

        for image in salon_images:
            # Supprimer le fichier physique si il existe
            if hasattr(image, 'image') and image.image:
                try:
                    if image.image.storage.exists(image.image.name):
                        image.image.delete(save=False)
                        files_deleted += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Erreur lors de la suppression du fichier image: {str(e)}")

        # Supprimer les enregistrements en base
        salon_images.delete()
        summary['deleted_items']['salon_images'] = images_count
        summary['deleted_items']['salon_image_files'] = files_deleted

        # Supprimer les favoris du salon
        favoris_salon = TblFavorite.objects.filter(salon=salon)
        summary['deleted_items']['favoris_salon'] = favoris_salon.count()
        favoris_salon.delete()

        # Supprimer le salon lui-même
        salon.delete()
        summary['deleted_items']['salons'] = 1

        return summary

    def _delete_client_data(self, tbl_user):
        """Supprime toutes les données client d'un utilisateur."""
        summary = {'deleted_items': {}}

        # Récupérer tous les enregistrements client pour cet utilisateur
        clients = TblClient.objects.filter(idTblUser=tbl_user)
        summary['deleted_items']['client_records'] = clients.count()

        total_rdv_client = 0
        total_paiements_client = 0

        for client in clients:
            # Supprimer les rendez-vous en tant que client
            rdv_client = TblRendezVous.objects.filter(client=client)
            total_rdv_client += rdv_client.count()

            # Supprimer les paiements liés à ces rendez-vous
            paiements_client = TblPaiement.objects.filter(rendez_vous__in=rdv_client)
            total_paiements_client += paiements_client.count()
            paiements_client.delete()
            rdv_client.delete()

        summary['deleted_items']['rdv_as_client'] = total_rdv_client
        summary['deleted_items']['paiements_client'] = total_paiements_client

        # Supprimer le panier
        try:
            cart = TblCart.objects.get(user=tbl_user)
            cart_items = TblCartItem.objects.filter(cart=cart)
            summary['deleted_items']['cart_items'] = cart_items.count()
            cart_items.delete()
            cart.delete()
            summary['deleted_items']['cart'] = 1
        except TblCart.DoesNotExist:
            summary['deleted_items']['cart'] = 0
            summary['deleted_items']['cart_items'] = 0

        # Supprimer les favoris de l'utilisateur
        favoris_user = TblFavorite.objects.filter(user=tbl_user)
        summary['deleted_items']['favoris_user'] = favoris_user.count()
        favoris_user.delete()

        # Supprimer les enregistrements client
        clients.delete()

        return summary

    def _anonymize_user_reviews(self, tbl_user):
        """Anonymise les avis de l'utilisateur au lieu de les supprimer."""
        summary = {'deleted_items': {}}

        clients = TblClient.objects.filter(idTblUser=tbl_user)
        avis_count = 0

        for client in clients:
            avis_donnes = TblAvis.objects.filter(client=client)
            avis_count += avis_donnes.count()
            # Anonymiser en mettant client=None
            avis_donnes.update(client=None)

        summary['deleted_items']['avis_anonymized'] = avis_count
        return summary

    def _delete_user_reviews(self, tbl_user):
        """Supprime complètement les avis de l'utilisateur."""
        summary = {'deleted_items': {}}

        clients = TblClient.objects.filter(idTblUser=tbl_user)
        avis_count = 0

        for client in clients:
            avis_donnes = TblAvis.objects.filter(client=client)
            avis_count += avis_donnes.count()
            avis_donnes.delete()

        summary['deleted_items']['avis_deleted'] = avis_count
        return summary

    def _delete_user_media_files(self, tbl_user):
        """Supprime les fichiers média associés à l'utilisateur."""
        summary = {'deleted_items': {}}

        # Si l'utilisateur a une photo de profil
        if hasattr(tbl_user, 'photo_profil') and tbl_user.photo_profil:
            try:
                # Supprimer le fichier physique
                if tbl_user.photo_profil.storage.exists(tbl_user.photo_profil.name):
                    tbl_user.photo_profil.delete(save=False)
                    summary['deleted_items']['profile_photo'] = 1
                else:
                    summary['deleted_items']['profile_photo'] = 0
            except Exception as e:
                # Logger l'erreur mais continuer la suppression
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erreur lors de la suppression de la photo de profil: {str(e)}")
                summary['deleted_items']['profile_photo'] = 0

        return summary

    def save(self):
        """
        Exécute la suppression du profil utilisateur.
        """
        id_cible_url = self.context.get('id_cible')
        return self.delete_user_profile(id_cible_url)