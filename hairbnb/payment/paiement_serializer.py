################################################################################
#                                                                              #
#             SÉRIALISEURS POUR LE SYSTÈME DE PAIEMENT (HAIRBNB)                #
#                                                                              #
#  Ce fichier définit l'ensemble des sérialiseurs (serializers) nécessaires    #
#  au fonctionnement du système de paiement de l'application. Il gère toutes   #
#  les facettes du processus de paiement via l'API :                           #
#                                                                              #
#    - La création d'un nouvel enregistrement de paiement.                     #
#    - L'affichage détaillé des informations d'un paiement.                    #
#    - La validation des requêtes pour des actions spécifiques comme les       #
#      remboursements.                                                         #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers
from hairbnb.models import TblPaiement, TblPaiementStatut, TblMethodePaiement, TblRendezVous, TblUser


# --- Sérialiseurs pour les modèles de référence (Statut, Méthode) ---

class PaiementStatutSerializer(serializers.ModelSerializer):
    """Sérialiseur standard pour le statut d'un paiement."""
    class Meta:
        model = TblPaiementStatut
        fields = ['idTblPaiementStatut', 'code', 'libelle']


class MethodePaiementSerializer(serializers.ModelSerializer):
    """Sérialiseur standard pour une méthode de paiement."""
    class Meta:
        model = TblMethodePaiement
        fields = ['idTblMethodePaiement', 'code', 'libelle']

# Versions "Nested" (sans ID) pour l'imbrication dans d'autres sérialiseurs.
class PaiementStatutNestedSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour le statut d'un paiement, utilisé pour l'imbrication."""
    class Meta:
        model = TblPaiementStatut
        fields = ['code', 'libelle']


class MethodePaiementNestedSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour une méthode de paiement, utilisé pour l'imbrication."""
    class Meta:
        model = TblMethodePaiement
        fields = ['code', 'libelle']


# --- Sérialiseurs pour l'affichage des paiements ---

class PaiementSerializer(serializers.ModelSerializer):
    """
    Sérialiseur complet pour afficher un enregistrement de paiement avec
    les détails de son statut et de sa méthode.
    """
    # Champs imbriqués pour afficher les détails des objets liés.
    statut = PaiementStatutSerializer(read_only=True)
    methode = MethodePaiementSerializer(read_only=True)

    class Meta:
        model = TblPaiement
        # Liste de tous les champs à inclure dans la réponse JSON.
        fields = [
            'idTblPaiement', 'rendez_vous', 'utilisateur', 'montant_paye', 'date_paiement',
            'statut', 'methode', 'stripe_payment_intent_id', 'stripe_charge_id',
            'stripe_customer_id', 'stripe_checkout_session_id', 'email_client', 'receipt_url'
        ]


class PaiementDetailSerializer(serializers.ModelSerializer):
    """
    Autre sérialiseur détaillé pour un paiement, utilisant des versions "Nested"
    des sérialiseurs de statut et de méthode.
    """
    statut = PaiementStatutNestedSerializer(read_only=True)
    methode = MethodePaiementNestedSerializer(read_only=True)
    # Utilise StringRelatedField pour afficher une représentation textuelle simple de l'utilisateur.
    utilisateur = serializers.StringRelatedField(read_only=True)
    # Utilise 'source' pour récupérer l'ID du rendez-vous lié.
    rendez_vous_id = serializers.IntegerField(source='rendez_vous.idRendezVous', read_only=True)

    class Meta:
        model = TblPaiement
        fields = [
            'idTblPaiement', 'rendez_vous_id', 'utilisateur', 'montant_paye', 'date_paiement',
            'statut', 'methode', 'stripe_payment_intent_id', 'stripe_checkout_session_id',
            'email_client', 'receipt_url'
        ]


# --- Sérialiseurs pour les actions (Création, Remboursement) ---

class PaiementCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la CRÉATION d'un nouvel enregistrement de paiement.
    Il valide les données entrantes et gère la création de l'objet en base de données.
    """
    # Champs en écriture seule ('write_only') pour recevoir les IDs et les codes.
    # Ils sont utilisés pour la validation et la création, mais ne sont pas affichés dans la réponse.
    rendez_vous_id = serializers.IntegerField(write_only=True)
    utilisateur_id = serializers.IntegerField(write_only=True)
    statut_code = serializers.CharField(write_only=True)
    methode_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = TblPaiement
        # Définit les champs attendus dans la requête de création.
        fields = [
            'rendez_vous_id', 'utilisateur_id', 'montant_paye', 'statut_code', 'methode_code',
            'stripe_payment_intent_id', 'stripe_checkout_session_id', 'email_client'
        ]

    def create(self, validated_data):
        """
        Surcharge la méthode create pour gérer la logique de création de l'objet
        Paiement à partir des IDs et codes fournis.
        """
        # --- Récupération des objets liés à partir des IDs et codes ---
        rendez_vous = TblRendezVous.objects.get(idRendezVous=validated_data.pop('rendez_vous_id'))
        utilisateur = TblUser.objects.get(idTblUser=validated_data.pop('utilisateur_id'))
        statut = TblPaiementStatut.objects.get(code=validated_data.pop('statut_code'))
        methode = None

        if 'methode_code' in validated_data:
            try:
                methode = TblMethodePaiement.objects.get(code=validated_data.pop('methode_code'))
            except TblMethodePaiement.DoesNotExist:
                raise serializers.ValidationError("Méthode de paiement invalide")

        # Crée et sauvegarde la nouvelle instance de TblPaiement avec les objets récupérés.
        return TblPaiement.objects.create(
            rendez_vous=rendez_vous,
            utilisateur=utilisateur,
            statut=statut,
            methode=methode,
            **validated_data
        )


class RefundSerializer(serializers.Serializer):
    """
    Sérialiseur non-modèle utilisé uniquement pour valider les données d'une
    requête de remboursement. Il ne fait que définir la structure attendue.
    """
    # L'ID du paiement à rembourser est obligatoire.
    id_paiement = serializers.IntegerField(required=True)
    # Le montant est optionnel. Si non fourni, cela implique un remboursement total.
    montant = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        help_text="Montant à rembourser (laisser vide pour remboursement total)"
    )








# from rest_framework import serializers
# from hairbnb.models import TblPaiement, TblPaiementStatut, TblMethodePaiement
#
#
# class PaiementStatutSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblPaiementStatut
#         fields = ['idTblPaiementStatut', 'code', 'libelle']
#
#
# class MethodePaiementSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblMethodePaiement
#         fields = ['idTblMethodePaiement', 'code', 'libelle']
#
#
# class PaiementSerializer(serializers.ModelSerializer):
#     statut = PaiementStatutSerializer(read_only=True)
#     methode = MethodePaiementSerializer(read_only=True)
#
#     class Meta:
#         model = TblPaiement
#         fields = [
#             'idTblPaiement',
#             'rendez_vous',
#             'utilisateur',
#             'montant_paye',
#             'date_paiement',
#             'statut',
#             'methode',
#             'stripe_payment_intent_id',
#             'stripe_charge_id',
#             'stripe_customer_id',
#             'stripe_checkout_session_id',
#             'email_client',
#             'receipt_url'
#         ]
#
#
# from rest_framework import serializers
# from hairbnb.models import TblPaiement, TblPaiementStatut, TblMethodePaiement, TblRendezVous, TblUser
#
#
# class PaiementCreateSerializer(serializers.ModelSerializer):
#     rendez_vous_id = serializers.IntegerField(write_only=True)
#     utilisateur_id = serializers.IntegerField(write_only=True)
#     statut_code = serializers.CharField(write_only=True)
#     methode_code = serializers.CharField(write_only=True, required=False)
#
#     class Meta:
#         model = TblPaiement
#         fields = [
#             'rendez_vous_id',
#             'utilisateur_id',
#             'montant_paye',
#             'statut_code',
#             'methode_code',
#             'stripe_payment_intent_id',
#             'stripe_checkout_session_id',
#             'email_client'
#         ]
#
#     def create(self, validated_data):
#         # Récupération des objets liés
#         rendez_vous = TblRendezVous.objects.get(idRendezVous=validated_data.pop('rendez_vous_id'))
#         utilisateur = TblUser.objects.get(idTblUser=validated_data.pop('utilisateur_id'))
#         statut = TblPaiementStatut.objects.get(code=validated_data.pop('statut_code'))
#         methode = None
#
#         if 'methode_code' in validated_data:
#             try:
#                 methode = TblMethodePaiement.objects.get(code=validated_data.pop('methode_code'))
#             except TblMethodePaiement.DoesNotExist:
#                 raise serializers.ValidationError("Méthode de paiement invalide")
#
#         return TblPaiement.objects.create(
#             rendez_vous=rendez_vous,
#             utilisateur=utilisateur,
#             statut=statut,
#             methode=methode,
#             **validated_data
#         )
#
#
# from rest_framework import serializers
# from hairbnb.models import TblPaiement, TblPaiementStatut, TblMethodePaiement, TblRendezVous, TblUser
#
#
# class PaiementStatutNestedSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblPaiementStatut
#         fields = ['code', 'libelle']
#
#
# class MethodePaiementNestedSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblMethodePaiement
#         fields = ['code', 'libelle']
#
#
# class PaiementDetailSerializer(serializers.ModelSerializer):
#     statut = PaiementStatutNestedSerializer(read_only=True)
#     methode = MethodePaiementNestedSerializer(read_only=True)
#     utilisateur = serializers.StringRelatedField(read_only=True)
#     rendez_vous_id = serializers.IntegerField(source='rendez_vous.idRendezVous', read_only=True)
#
#     class Meta:
#         model = TblPaiement
#         fields = [
#             'idTblPaiement',
#             'rendez_vous_id',
#             'utilisateur',
#             'montant_paye',
#             'date_paiement',
#             'statut',
#             'methode',
#             'stripe_payment_intent_id',
#             'stripe_checkout_session_id',
#             'email_client',
#             'receipt_url'
#         ]
#
#
# class RefundSerializer(serializers.Serializer):
#     id_paiement = serializers.IntegerField(required=True)
#     montant = serializers.DecimalField(
#         max_digits=10, decimal_places=2, required=False,
#         help_text="Montant à rembourser (laisser vide pour remboursement total)"
#     )
#
#
