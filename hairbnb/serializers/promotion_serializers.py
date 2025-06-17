################################################################################
#                                                                              #
#               SERIALIZER POUR LA GESTION DES PROMOTIONS                      #
#                                                                              #
#  Ce fichier contient le serializer de Django REST Framework nécessaire pour  #
#  la gestion des promotions sur les services. Il permet de formater les       #
#  données relatives aux offres promotionnelles pour les API.                  #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblPromotion


################################################################################
#                     SERIALIZER POUR LE MODÈLE PROMOTION                      #
################################################################################

class PromotionSerializer(serializers.ModelSerializer):
    """
    Sérialise les données d'une promotion.
    Ce serializer est utilisé pour convertir les objets du modèle `TblPromotion`
    en un format JSON simple et lisible par les applications clientes.
    """
    class Meta:
        """
        La classe Meta lie le serializer au modèle Django `TblPromotion` et
        définit les champs qui seront inclus dans la sortie JSON finale.
        """
        model = TblPromotion
        fields = [
            'id',
            'service',
            'discount_percentage',
            'start_date',
            'end_date'
        ]




# from hairbnb.models import TblPromotion
# from rest_framework import serializers
#
# class PromotionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblPromotion
#         fields = ['id', 'service', 'discount_percentage', 'start_date', 'end_date']