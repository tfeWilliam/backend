################################################################################
#                                                                              #
#             SÉRIALISEURS POUR LE SYSTÈME D'AVIS (HAIRBNB)                     #
#                                                                              #
#  Ce fichier définit l'ensemble des sérialiseurs (serializers) nécessaires   #
#  au fonctionnement du système d'avis et de notation de l'application.        #
#  Il couvre tous les aspects :                                                #
#    - La création et validation de nouveaux avis.                             #
#    - L'affichage détaillé ou simplifié des avis.                             #
#    - La vérification des rendez-vous éligibles à un avis.                    #
#    - L'agrégation de statistiques sur les avis.                              #
#    - La consultation de l'historique personnel des avis d'un client.         #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers
from django.utils import timezone
from hairbnb.models import (
    TblAvis, TblAvisStatut, TblRendezVous, TblClient,
    TblSalon
)


# --- 1. SÉRIALISEUR POUR LES STATUTS D'AVIS ---
class AvisStatutSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simple pour le modèle TblAvisStatut.
    Utilisé pour afficher les détails d'un statut d'avis (ex: 'visible', 'en attente').
    """
    class Meta:
        # Lie ce sérialiseur au modèle TblAvisStatut.
        model = TblAvisStatut
        # Définit les champs du modèle à inclure dans la sortie JSON.
        fields = ['idTblAvisStatut', 'code', 'libelle', 'description']


# --- 2. SÉRIALISEURS LÉGERS POUR LES RELATIONS IMBRIQUÉES ---
# Ces sérialiseurs sont des "helpers" utilisés à l'intérieur d'autres sérialiseurs
# pour afficher des informations sur les objets liés (client, salon) de manière concise.

class ClientAvisSerializer(serializers.ModelSerializer):
    """
    Sérialiseur léger pour afficher les informations de base d'un client dans un avis.
    """
    # Utilise 'source' pour accéder aux champs du modèle TblUser lié.
    nom = serializers.CharField(source='idTblUser.nom', read_only=True)
    prenom = serializers.CharField(source='idTblUser.prenom', read_only=True)
    photo_profil = serializers.CharField(source='idTblUser.photo_profil', read_only=True)

    class Meta:
        model = TblClient
        fields = ['nom', 'prenom', 'photo_profil']


class SalonAvisSerializer(serializers.ModelSerializer):
    """
    Sérialiseur léger pour afficher les informations de base d'un salon dans un avis.
    """
    class Meta:
        model = TblSalon
        fields = ['idTblSalon', 'nom_salon', 'logo_salon']


class RendezVousAvisSerializer(serializers.ModelSerializer):
    """
    Sérialiseur léger pour afficher les informations de base d'un rendez-vous dans un avis.
    """
    class Meta:
        model = TblRendezVous
        fields = ['idRendezVous', 'date_heure', 'total_prix', 'duree_totale']


# --- 3. SÉRIALISEUR POUR LA CRÉATION D'UN NOUVEL AVIS ---
class AvisCreateSerializer(serializers.ModelSerializer):
    """
    Gère la création d'un nouvel avis. Ce sérialiseur valide les données
    entrantes d'une requête POST et crée l'objet TblAvis en base de données.
    """
    # Champ en écriture seule ('write_only') pour recevoir l'ID du rendez-vous.
    # Il ne sera pas inclus dans la réponse JSON.
    idRendezVous = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = TblAvis
        # Champs attendus dans la requête de création.
        fields = ['idRendezVous', 'note', 'commentaire']
        # Ajoute des contraintes de validation directement sur les champs.
        extra_kwargs = {
            'note': {'required': True},
            'commentaire': {'required': True, 'min_length': 10, 'max_length': 1000},
        }

    def validate_note(self, value):
        """Méthode de validation personnalisée pour le champ 'note'."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
        return value

    def validate_commentaire(self, value):
        """Méthode de validation personnalisée pour le champ 'commentaire'."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Le commentaire doit contenir au moins 10 caractères.")
        if len(value.strip()) > 1000:
            raise serializers.ValidationError("Le commentaire ne peut pas dépasser 1000 caractères.")
        return value.strip()

    def validate_idRendezVous(self, value):
        """
        Validation complexe pour l'ID du rendez-vous. Assure la sécurité et
        le respect des règles métier.
        """
        # Récupère la requête HTTP pour accéder à l'utilisateur connecté.
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Utilisateur non authentifié.")

        try:
            # Vérifie que l'utilisateur authentifié correspond bien à un client.
            client = TblClient.objects.get(idTblUser__uuid=request.user.uuid)

            # Vérifie que le rendez-vous existe et qu'il appartient bien à ce client.
            rdv = TblRendezVous.objects.get(
                idRendezVous=value,
                client=client
            )

            # Règle métier : on ne peut laisser un avis que pour un RDV terminé.
            if rdv.statut != 'terminé':
                raise serializers.ValidationError("Seuls les rendez-vous terminés peuvent recevoir un avis.")

            # Règle métier : un seul avis par rendez-vous.
            if TblAvis.objects.filter(rendez_vous=rdv).exists():
                raise serializers.ValidationError("Un avis a déjà été donné pour ce rendez-vous.")

            return value

        except TblClient.DoesNotExist:
            raise serializers.ValidationError("Client non trouvé.")
        except TblRendezVous.DoesNotExist:
            raise serializers.ValidationError("Rendez-vous non trouvé ou non autorisé.")

    def create(self, validated_data):
        """
        Logique de création de l'objet TblAvis après une validation réussie.
        """
        request = self.context.get('request')
        idRendezVous = validated_data.pop('idRendezVous')

        # Récupère les objets liés nécessaires à la création de l'avis.
        client = TblClient.objects.get(idTblUser__uuid=request.user.uuid)
        rdv = TblRendezVous.objects.get(idRendezVous=idRendezVous)
        statut_visible = TblAvisStatut.objects.get(code='visible')

        # Crée et sauvegarde l'instance de l'avis en base de données.
        avis = TblAvis.objects.create(
            rendez_vous=rdv,
            client=client,
            salon=rdv.salon,
            statut=statut_visible,
            **validated_data
        )

        return avis


# --- 4. SÉRIALISEUR POUR L'AFFICHAGE DÉTAILLÉ D'UN AVIS ---
class AvisDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher un avis avec toutes ses informations liées.
    Utilise les sérialiseurs légers définis plus haut pour un affichage riche.
    """
    client = ClientAvisSerializer(read_only=True)
    salon = SalonAvisSerializer(read_only=True)
    rendez_vous = RendezVousAvisSerializer(read_only=True)
    statut = AvisStatutSerializer(read_only=True)
    # Champ calculé dynamiquement par une méthode.
    date_formatted = serializers.SerializerMethodField()
    client_nom_complet = serializers.CharField(read_only=True)

    class Meta:
        model = TblAvis
        fields = [
            'id', 'note', 'commentaire', 'date', 'date_formatted',
            'client', 'salon', 'rendez_vous', 'statut', 'client_nom_complet'
        ]

    def get_date_formatted(self, obj):
        """Formate la date pour un affichage plus lisible."""
        return obj.date.strftime('%d/%m/%Y à %H:%M')


# --- 5. SÉRIALISEUR POUR LA LISTE PUBLIQUE DES AVIS ---
class AvisListSerializer(serializers.ModelSerializer):
    """
    Version allégée pour lister les avis publiquement (ex: sur la page d'un salon).
    N'expose que les informations non sensibles.
    """
    client_nom = serializers.CharField(source='client.idTblUser.prenom', read_only=True)
    client_photo = serializers.CharField(source='client.idTblUser.photo_profil', read_only=True)
    date_formatted = serializers.SerializerMethodField()

    class Meta:
        model = TblAvis
        fields = [
            'id', 'note', 'commentaire', 'date_formatted',
            'client_nom', 'client_photo'
        ]

    def get_date_formatted(self, obj):
        """Formate la date en version courte."""
        return obj.date.strftime('%d/%m/%Y')


# --- 6. SÉRIALISEUR POUR LES RENDEZ-VOUS ÉLIGIBLES À UN AVIS ---
class RdvEligibleAvisSerializer(serializers.ModelSerializer):
    """
    Sérialiseur très spécifique pour lister les rendez-vous d'un client
    pour lesquels il peut encore laisser un avis.
    """
    salon_nom = serializers.CharField(source='salon.nom_salon', read_only=True)
    salon_logo = serializers.CharField(source='salon.logo_salon', read_only=True)
    date_formatted = serializers.SerializerMethodField()
    services_noms = serializers.SerializerMethodField()
    est_eligible = serializers.SerializerMethodField()

    class Meta:
        model = TblRendezVous
        fields = [
            'idRendezVous', 'date_heure', 'date_formatted', 'total_prix',
            'duree_totale', 'salon_nom', 'salon_logo', 'services_noms', 'est_eligible'
        ]

    def get_date_formatted(self, obj):
        return obj.date_heure.strftime('%d/%m/%Y à %H:%M')

    def get_services_noms(self, obj):
        """Construit une liste des noms des services pour ce rendez-vous."""
        return [
            service.service.intitule_service
            for service in obj.rendez_vous_services.all()
        ]

    def get_est_eligible(self, obj):
        """
        Contient la logique métier pour déterminer si un avis peut être laissé.
        """
        from datetime import timedelta

        # Condition 1 : Le statut du RDV doit être 'terminé'.
        if obj.statut != 'terminé':
            return False

        # Condition 2 : Un délai de 2h doit s'être écoulé depuis la fin théorique du RDV.
        fin_theorique = obj.date_heure + timedelta(minutes=obj.duree_totale or 60)
        maintenant = timezone.now()
        if maintenant < fin_theorique + timedelta(hours=2):
            return False

        # Condition 3 : Aucun avis ne doit déjà exister pour ce RDV.
        return not obj.avis.exists()


# --- 7. SÉRIALISEUR POUR LES STATISTIQUES D'AVIS ---
class AvisStatistiquesSerializer(serializers.Serializer):
    """
    Sérialiseur non lié à un modèle, utilisé pour définir la structure
    des données d'un rapport de statistiques d'avis pour un salon.
    """
    moyenne_notes = serializers.FloatField()
    total_avis = serializers.IntegerField()
    repartition_notes = serializers.DictField()
    avis_recents = AvisListSerializer(many=True)

    note_5 = serializers.IntegerField()
    note_4 = serializers.IntegerField()
    note_3 = serializers.IntegerField()
    note_2 = serializers.IntegerField()
    note_1 = serializers.IntegerField()


# --- 8. SÉRIALISEUR POUR L'HISTORIQUE DES AVIS D'UN CLIENT ("MES AVIS") ---
class MesAvisSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la page où un client consulte l'historique de tous les
    avis qu'il a laissés.
    """
    salon_nom = serializers.CharField(source='salon.nom_salon', read_only=True)
    salon_logo = serializers.CharField(source='salon.logo_salon', read_only=True)
    rdv_date = serializers.CharField(source='rendez_vous.date_heure', read_only=True)
    date_formatted = serializers.SerializerMethodField()
    statut_libelle = serializers.CharField(source='statut.libelle', read_only=True)

    class Meta:
        model = TblAvis
        fields = [
            'id', 'note', 'commentaire', 'date', 'date_formatted',
            'salon_nom', 'salon_logo', 'rdv_date', 'statut_libelle'
        ]

    def get_date_formatted(self, obj):
        """Formate la date de l'avis."""
        return obj.date.strftime('%d/%m/%Y à %H:%M')







# # serializers.py - Système d'avis
#
# from rest_framework import serializers
# from django.utils import timezone
# from hairbnb.models import (
#     TblAvis, TblAvisStatut, TblRendezVous, TblClient,
#     TblSalon
# )
#
#
# # 1️⃣ SERIALIZER POUR LES STATUTS D'AVIS
# class AvisStatutSerializer(serializers.ModelSerializer):
#     """Serializer pour les statuts d'avis"""
#
#     class Meta:
#         model = TblAvisStatut
#         fields = ['idTblAvisStatut', 'code', 'libelle', 'description']
#
#
# # 2️⃣ SERIALIZERS LÉGERS POUR LES RELATIONS
# class ClientAvisSerializer(serializers.ModelSerializer):
#     """Serializer léger pour les infos client dans les avis"""
#     nom = serializers.CharField(source='idTblUser.nom', read_only=True)
#     prenom = serializers.CharField(source='idTblUser.prenom', read_only=True)
#     photo_profil = serializers.CharField(source='idTblUser.photo_profil', read_only=True)
#
#     class Meta:
#         model = TblClient
#         fields = ['nom', 'prenom', 'photo_profil']
#
#
# class SalonAvisSerializer(serializers.ModelSerializer):
#     """Serializer léger pour les infos salon dans les avis"""
#
#     class Meta:
#         model = TblSalon
#         fields = ['idTblSalon', 'nom_salon', 'logo_salon']
#
#
# class RendezVousAvisSerializer(serializers.ModelSerializer):
#     """Serializer léger pour les infos RDV dans les avis"""
#
#     class Meta:
#         model = TblRendezVous
#         fields = ['idRendezVous', 'date_heure', 'total_prix', 'duree_totale']
#
#
# # 3️⃣ SERIALIZER POUR CRÉER UN AVIS (avec auth Firebase)
# class AvisCreateSerializer(serializers.ModelSerializer):
#     """Serializer pour créer un nouvel avis - Avec authentification Firebase"""
#
#     # Le client sera automatiquement récupéré depuis request.user
#     # Le salon et RDV seront récupérés depuis le RDV sélectionné
#     idRendezVous = serializers.IntegerField(write_only=True, required=True)
#
#     class Meta:
#         model = TblAvis
#         fields = ['idRendezVous', 'note', 'commentaire']
#         extra_kwargs = {
#             'note': {'required': True},
#             'commentaire': {'required': True, 'min_length': 10, 'max_length': 1000},
#         }
#
#     def validate_note(self, value):
#         """Valider que la note est entre 1 et 5"""
#         if not (1 <= value <= 5):
#             raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
#         return value
#
#     def validate_commentaire(self, value):
#         """Valider la longueur du commentaire"""
#         if len(value.strip()) < 10:
#             raise serializers.ValidationError("Le commentaire doit contenir au moins 10 caractères.")
#         if len(value.strip()) > 1000:
#             raise serializers.ValidationError("Le commentaire ne peut pas dépasser 1000 caractères.")
#         return value.strip()
#
#     def validate_idRendezVous(self, value):
#         """Valider que le RDV existe et appartient au client connecté"""
#         request = self.context.get('request')
#         if not request or not request.user:
#             raise serializers.ValidationError("Utilisateur non authentifié.")
#
#         try:
#             # Récupérer le client depuis l'utilisateur Firebase connecté
#             client = TblClient.objects.get(idTblUser__uuid=request.user.uuid)
#
#             # Vérifier que le RDV existe et appartient à ce client
#             rdv = TblRendezVous.objects.get(
#                 idRendezVous=value,
#                 client=client
#             )
#
#             # Vérifier que le RDV est terminé
#             if rdv.statut != 'terminé':
#                 raise serializers.ValidationError("Seuls les rendez-vous terminés peuvent recevoir un avis.")
#
#             # Vérifier qu'aucun avis n'existe déjà pour ce RDV
#             if TblAvis.objects.filter(rendez_vous=rdv).exists():
#                 raise serializers.ValidationError("Un avis a déjà été donné pour ce rendez-vous.")
#
#             return value
#
#         except TblClient.DoesNotExist:
#             raise serializers.ValidationError("Client non trouvé.")
#         except TblRendezVous.DoesNotExist:
#             raise serializers.ValidationError("Rendez-vous non trouvé ou non autorisé.")
#
#     def create(self, validated_data):
#         """Créer l'avis avec les relations automatiques"""
#         request = self.context.get('request')
#         idRendezVous = validated_data.pop('idRendezVous')
#
#         # Récupérer le client depuis l'utilisateur connecté
#         client = TblClient.objects.get(idTblUser__uuid=request.user.uuid)
#
#         # Récupérer le RDV
#         rdv = TblRendezVous.objects.get(idRendezVous=idRendezVous)
#
#         # Récupérer le statut "visible" par défaut
#         statut_visible = TblAvisStatut.objects.get(code='visible')
#
#         # Créer l'avis
#         avis = TblAvis.objects.create(
#             rendez_vous=rdv,
#             client=client,
#             salon=rdv.salon,
#             statut=statut_visible,
#             **validated_data
#         )
#
#         return avis
#
#
# # 4️⃣ SERIALIZER POUR AFFICHER UN AVIS COMPLET
# class AvisDetailSerializer(serializers.ModelSerializer):
#     """Serializer détaillé pour afficher un avis"""
#     client = ClientAvisSerializer(read_only=True)
#     salon = SalonAvisSerializer(read_only=True)
#     rendez_vous = RendezVousAvisSerializer(read_only=True)
#     statut = AvisStatutSerializer(read_only=True)
#     date_formatted = serializers.SerializerMethodField()
#     client_nom_complet = serializers.CharField(read_only=True)
#
#     class Meta:
#         model = TblAvis
#         fields = [
#             'id', 'note', 'commentaire', 'date', 'date_formatted',
#             'client', 'salon', 'rendez_vous', 'statut', 'client_nom_complet'
#         ]
#
#     def get_date_formatted(self, obj):
#         """Formater la date d'avis"""
#         return obj.date.strftime('%d/%m/%Y à %H:%M')
#
#
# # 5️⃣ SERIALIZER POUR LISTER LES AVIS (version allégée)
# class AvisListSerializer(serializers.ModelSerializer):
#     """Serializer pour lister les avis - Version publique allégée"""
#     client_nom = serializers.CharField(source='client.idTblUser.prenom', read_only=True)
#     client_photo = serializers.CharField(source='client.idTblUser.photo_profil', read_only=True)
#     date_formatted = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblAvis
#         fields = [
#             'id', 'note', 'commentaire', 'date_formatted',
#             'client_nom', 'client_photo'
#         ]
#
#     def get_date_formatted(self, obj):
#         return obj.date.strftime('%d/%m/%Y')
#
#
# # 6️⃣ SERIALIZER POUR LES RDV ÉLIGIBLES AUX AVIS
# class RdvEligibleAvisSerializer(serializers.ModelSerializer):
#     """Serializer pour les RDV éligibles aux avis d'un client"""
#     salon_nom = serializers.CharField(source='salon.nom_salon', read_only=True)
#     salon_logo = serializers.CharField(source='salon.logo_salon', read_only=True)
#     date_formatted = serializers.SerializerMethodField()
#     services_noms = serializers.SerializerMethodField()
#     est_eligible = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblRendezVous
#         fields = [
#             'idRendezVous', 'date_heure', 'date_formatted', 'total_prix',
#             'duree_totale', 'salon_nom', 'salon_logo', 'services_noms', 'est_eligible'
#         ]
#
#     def get_date_formatted(self, obj):
#         return obj.date_heure.strftime('%d/%m/%Y à %H:%M')
#
#     def get_services_noms(self, obj):
#         """Récupérer les noms des services du RDV"""
#         return [
#             service.service.intitule_service
#             for service in obj.rendez_vous_services.all()
#         ]
#
#     def get_est_eligible(self, obj):
#         """Vérifier si le RDV est éligible aux avis"""
#         from datetime import timedelta
#
#         # RDV terminé + 2h passées + pas d'avis existant
#         if obj.statut != 'terminé':
#             return False
#
#         fin_theorique = obj.date_heure + timedelta(minutes=obj.duree_totale or 60)
#         maintenant = timezone.now()
#
#         if maintenant < fin_theorique + timedelta(hours=2):
#             return False
#
#         return not obj.avis.exists()
#
#
# # 7️⃣ SERIALIZER POUR LES STATISTIQUES D'AVIS
# class AvisStatistiquesSerializer(serializers.Serializer):
#     """Serializer pour les statistiques d'avis d'un salon"""
#     moyenne_notes = serializers.FloatField()
#     total_avis = serializers.IntegerField()
#     repartition_notes = serializers.DictField()
#     avis_recents = AvisListSerializer(many=True)
#
#     # Répartition par note
#     note_5 = serializers.IntegerField()
#     note_4 = serializers.IntegerField()
#     note_3 = serializers.IntegerField()
#     note_2 = serializers.IntegerField()
#     note_1 = serializers.IntegerField()
#
#
# # 8️⃣ SERIALIZER POUR MES AVIS (historique client)
# class MesAvisSerializer(serializers.ModelSerializer):
#     """Serializer pour l'historique des avis d'un client"""
#     salon_nom = serializers.CharField(source='salon.nom_salon', read_only=True)
#     salon_logo = serializers.CharField(source='salon.logo_salon', read_only=True)
#     rdv_date = serializers.CharField(source='rendez_vous.date_heure', read_only=True)
#     date_formatted = serializers.SerializerMethodField()
#     statut_libelle = serializers.CharField(source='statut.libelle', read_only=True)
#
#     class Meta:
#         model = TblAvis
#         fields = [
#             'id', 'note', 'commentaire', 'date', 'date_formatted',
#             'salon_nom', 'salon_logo', 'rdv_date', 'statut_libelle'
#         ]
#
#     def get_date_formatted(self, obj):
#         return obj.date.strftime('%d/%m/%Y à %H:%M')