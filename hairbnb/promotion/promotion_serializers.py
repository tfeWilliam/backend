################################################################################
#                                                                              #
#        SÉRIALISEUR POUR LA MISE À JOUR DES PROMOTIONS (HAIRBNB)                #
#                                                                              #
#  Ce fichier définit la classe `PromotionUpdateSerializer`, qui est           #
#  spécifiquement conçue pour gérer la modification d'une promotion            #
#  existante.                                                                  #
#                                                                              #
#  Sa responsabilité principale est de valider les données entrantes pour      #
#  s'assurer de leur format, de leur cohérence et du respect des règles        #
#  métier (ex: une date de fin ne peut pas être antérieure à la date de début). #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers
# Utilitaire Django pour rendre un objet datetime "conscient" du fuseau horaire
from django.utils.timezone import make_aware
from datetime import datetime
from hairbnb.models import TblPromotion


class PromotionUpdateSerializer(serializers.ModelSerializer):
    """
    Gère la validation et la mise à jour des données d'une promotion existante.
    """
    # --- Définition des champs avec des règles de validation spécifiques ---
    discount_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0.01,
        max_value=100.00,
        # Messages d'erreur personnalisés pour une meilleure expérience utilisateur.
        error_messages={
            'min_value': 'Le pourcentage doit être supérieur à 0%',
            'max_value': 'Le pourcentage ne peut pas dépasser 100%',
            'required': 'Le pourcentage de réduction est obligatoire'
        }
    )

    # Les dates sont reçues comme des chaînes de caractères et seront validées/converties.
    start_date = serializers.CharField(help_text="Format: YYYY-MM-DD")
    end_date = serializers.CharField(help_text="Format: YYYY-MM-DD")

    class Meta:
        # Lie ce sérialiseur au modèle TblPromotion.
        model = TblPromotion
        # Ne rend modifiables que ces trois champs.
        fields = ['discount_percentage', 'start_date', 'end_date']

    def validate_start_date(self, value):
        """
        Validation personnalisée : convertit la chaîne de caractères de la date de début
        en un objet datetime conscient du fuseau horaire.
        """
        try:
            # Ne garde que la partie date (YYYY-MM-DD) de la chaîne reçue.
            parsed_date = datetime.strptime(value.split("T")[0], "%Y-%m-%d")
            # Rend l'objet date "aware" en utilisant le fuseau horaire par défaut du projet.
            return make_aware(parsed_date)
        except ValueError:
            raise serializers.ValidationError("Format de date invalide. Utilisez YYYY-MM-DD")

    def validate_end_date(self, value):
        """
        Validation personnalisée : convertit la chaîne de caractères de la date de fin
        en un objet datetime conscient du fuseau horaire.
        """
        try:
            parsed_date = datetime.strptime(value.split("T")[0], "%Y-%m-%d")
            return make_aware(parsed_date)
        except ValueError:
            raise serializers.ValidationError("Format de date invalide. Utilisez YYYY-MM-DD")

    def validate(self, data):
        """
        Validation globale qui s'exécute après la validation de chaque champ individuel.
        Permet de vérifier la cohérence entre plusieurs champs.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # Règle métier : la date de fin doit toujours être postérieure à la date de début.
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'La date de fin doit être postérieure à la date de début'
            })

        return data








# from rest_framework import serializers
# from django.utils.timezone import make_aware
# from datetime import datetime
# from hairbnb.models import TblPromotion
#
#
# class PromotionUpdateSerializer(serializers.ModelSerializer):
#     """
#     Serializer pour la modification d'une promotion existante.
#     """
#
#     discount_percentage = serializers.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         min_value=0.01,
#         max_value=100.00,
#         error_messages={
#             'min_value': 'Le pourcentage doit être supérieur à 0%',
#             'max_value': 'Le pourcentage ne peut pas dépasser 100%',
#             'required': 'Le pourcentage de réduction est obligatoire'
#         }
#     )
#
#     start_date = serializers.CharField(help_text="Format: YYYY-MM-DD")
#     end_date = serializers.CharField(help_text="Format: YYYY-MM-DD")
#
#     class Meta:
#         model = TblPromotion
#         fields = ['discount_percentage', 'start_date', 'end_date']
#
#     def validate_start_date(self, value):
#         """Valider et convertir la date de début"""
#         try:
#             parsed_date = datetime.strptime(value.split("T")[0], "%Y-%m-%d")
#             return make_aware(parsed_date)
#         except ValueError:
#             raise serializers.ValidationError("Format de date invalide. Utilisez YYYY-MM-DD")
#
#     def validate_end_date(self, value):
#         """Valider et convertir la date de fin"""
#         try:
#             parsed_date = datetime.strptime(value.split("T")[0], "%Y-%m-%d")
#             return make_aware(parsed_date)
#         except ValueError:
#             raise serializers.ValidationError("Format de date invalide. Utilisez YYYY-MM-DD")
#
#     def validate(self, data):
#         """Validation globale des données"""
#         start_date = data.get('start_date')
#         end_date = data.get('end_date')
#
#         if start_date and end_date and end_date <= start_date:
#             raise serializers.ValidationError({
#                 'end_date': 'La date de fin doit être postérieure à la date de début'
#             })
#
#         return data