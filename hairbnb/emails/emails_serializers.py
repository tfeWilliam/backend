################################################################################
#                                                                              #
#             SÉRIALISEURS POUR LE SYSTÈME D'EMAILS (HAIRBNB)                    #
#                                                                              #
#  Ce fichier définit l'ensemble des sérialiseurs (serializers) nécessaires    #
#  au fonctionnement du système de notifications par email. Il contient deux   #
#  types de sérialiseurs :                                                     #
#                                                                              #
#  1. Sérialiseurs de Modèles : Des classes comme                              #
#     `EmailNotificationSerializer` et ses "helpers" minimaux, qui servent à   #
#     convertir les données de la base de données en format JSON pour les      #
#     réponses de l'API.                                                       #
#                                                                              #
#  2. Sérialiseur de Requête : La classe `EmailNotificationCreateSerializer`   #
#     qui valide les données entrantes des requêtes API pour s'assurer         #
#     qu'elles sont correctes avant de déclencher l'envoi d'un email.          #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers

# Importation des modèles de la base de données
from hairbnb.models import TblEmailType, TblEmailStatus, TblUser, TblSalon, TblRendezVous, TblEmailNotification


# --- Sérialiseurs minimaux pour les relations ---
# Ces sérialiseurs sont utilisés pour imbriquer des informations de base
# sur les objets liés sans surcharger la réponse de l'API.

class EmailTypeSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle TblEmailType."""
    class Meta:
        model = TblEmailType
        fields = ['idTblEmailType', 'code', 'libelle']

class EmailStatusSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le modèle TblEmailStatus."""
    class Meta:
        model = TblEmailStatus
        fields = ['idTblEmailStatus', 'code', 'libelle']

class UserMinimalSerializer(serializers.ModelSerializer):
    """Sérialiseur minimal pour TblUser, utilisé dans les relations."""
    class Meta:
        model = TblUser
        fields = ['idTblUser', 'nom', 'prenom', 'email']

class SalonMinimalSerializer(serializers.ModelSerializer):
    """Sérialiseur minimal pour TblSalon, utilisé dans les relations."""
    class Meta:
        model = TblSalon
        fields = ['idTblSalon', 'nom_salon']

class RendezVousMinimalSerializer(serializers.ModelSerializer):
    """Sérialiseur minimal pour TblRendezVous, utilisé dans les relations."""
    class Meta:
        model = TblRendezVous
        fields = ['idRendezVous', 'date_heure', 'statut']


# --- Sérialiseur principal pour l'affichage des notifications ---

class EmailNotificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur complet pour afficher une notification d'email avec
    toutes ses informations et relations détaillées.
    """
    # Champs imbriqués qui utilisent les sérialiseurs minimaux définis ci-dessus.
    destinataire = UserMinimalSerializer(read_only=True)
    salon = SalonMinimalSerializer(read_only=True)
    rendez_vous = RendezVousMinimalSerializer(read_only=True)
    type_email = EmailTypeSerializer(read_only=True)
    statut = EmailStatusSerializer(read_only=True)

    class Meta:
        model = TblEmailNotification
        # Liste de tous les champs à inclure dans la réponse JSON.
        fields = [
            'idTblEmailNotification', 'destinataire', 'salon', 'rendez_vous',
            'type_email', 'statut', 'sujet', 'contenu', 'date_creation',
            'date_envoi', 'tentatives', 'email_id'
        ]


# --- Sérialiseur pour la validation des requêtes de création ---

class EmailNotificationCreateSerializer(serializers.Serializer):
    """
    Sérialiseur non lié à un modèle, utilisé pour valider les données de la
    requête POST reçue par l'API d'envoi d'email.
    """
    # Définit les champs attendus dans le corps de la requête et leurs règles.
    toEmail = serializers.EmailField(required=True)
    toName = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField(required=False, allow_blank=True)
    templateId = serializers.CharField(required=True)
    templateData = serializers.JSONField(required=False, default=dict)
    rendezVousId = serializers.IntegerField(required=False, allow_null=True)

    def validate_templateId(self, value):
        """
        Méthode de validation personnalisée pour le champ 'templateId'.
        Vérifie que le code du template existe bien dans la base de données.
        """
        try:
            TblEmailType.objects.get(code=value)
            return value
        except TblEmailType.DoesNotExist:
            raise serializers.ValidationError(f"Le template ID '{value}' n'existe pas")

    def validate_rendezVousId(self, value):
        """
        Méthode de validation personnalisée pour le champ 'rendezVousId'.
        Vérifie que le rendez-vous existe si son ID est fourni.
        """
        if value is not None:
            try:
                TblRendezVous.objects.get(idRendezVous=value)
                return value
            except TblRendezVous.DoesNotExist:
                raise serializers.ValidationError(f"Le rendez-vous avec ID {value} n'existe pas")
        return value






# # Fichier: serializers.py (à créer ou compléter)
#
# from rest_framework import serializers
#
# from hairbnb.models import TblEmailType, TblEmailStatus, TblUser, TblSalon, TblRendezVous, TblEmailNotification
#
#
# class EmailTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblEmailType
#         fields = ['idTblEmailType', 'code', 'libelle']
#
# class EmailStatusSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblEmailStatus
#         fields = ['idTblEmailStatus', 'code', 'libelle']
#
# class UserMinimalSerializer(serializers.ModelSerializer):
#     """Serializer minimal pour TblUser, utilisé dans les relations."""
#     class Meta:
#         model = TblUser
#         fields = ['idTblUser', 'nom', 'prenom', 'email']
#
# class SalonMinimalSerializer(serializers.ModelSerializer):
#     """Serializer minimal pour TblSalon, utilisé dans les relations."""
#     class Meta:
#         model = TblSalon
#         fields = ['idTblSalon', 'nom_salon']
#
# class RendezVousMinimalSerializer(serializers.ModelSerializer):
#     """Serializer minimal pour TblRendezVous, utilisé dans les relations."""
#     class Meta:
#         model = TblRendezVous
#         fields = ['idRendezVous', 'date_heure', 'statut']
#
# class EmailNotificationSerializer(serializers.ModelSerializer):
#     """Serializer complet pour TblEmailNotification."""
#     destinataire = UserMinimalSerializer(read_only=True)
#     salon = SalonMinimalSerializer(read_only=True)
#     rendez_vous = RendezVousMinimalSerializer(read_only=True)
#     type_email = EmailTypeSerializer(read_only=True)
#     statut = EmailStatusSerializer(read_only=True)
#
#     class Meta:
#         model = TblEmailNotification
#         fields = [
#             'idTblEmailNotification', 'destinataire', 'salon', 'rendez_vous',
#             'type_email', 'statut', 'sujet', 'contenu', 'date_creation',
#             'date_envoi', 'tentatives', 'email_id'
#         ]
#
# class EmailNotificationCreateSerializer(serializers.Serializer):
#     """
#     Serializer pour la création d'une notification email via l'API.
#     C'est un serializer non basé sur un modèle pour permettre plus de flexibilité.
#     """
#     toEmail = serializers.EmailField(required=True)
#     toName = serializers.CharField(required=False, allow_blank=True)
#     subject = serializers.CharField(required=False, allow_blank=True)
#     templateId = serializers.CharField(required=True)
#     templateData = serializers.JSONField(required=False, default=dict)
#     rendezVousId = serializers.IntegerField(required=False, allow_null=True)
#
#     def validate_templateId(self, value):
#         """Vérifie que le template ID existe dans la base de données."""
#         try:
#             TblEmailType.objects.get(code=value)
#             return value
#         except TblEmailType.DoesNotExist:
#             raise serializers.ValidationError(f"Le template ID '{value}' n'existe pas")
#
#     def validate_rendezVousId(self, value):
#         """Vérifie que le rendez-vous existe si un ID est fourni."""
#         if value is not None:
#             try:
#                 TblRendezVous.objects.get(idRendezVous=value)
#                 return value
#             except TblRendezVous.DoesNotExist:
#                 raise serializers.ValidationError(f"Le rendez-vous avec ID {value} n'existe pas")
#         return value