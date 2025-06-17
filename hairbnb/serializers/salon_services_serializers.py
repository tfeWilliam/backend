################################################################################
#                                                                              #
#         SERIALIZERS DE BASE POUR LES SERVICES, PRIX ET TEMPS                 #
#                                                                              #
#  Ce fichier définit les serializers fondamentaux pour les entités de base    #
#  de l'application : Service, Temps (durée) et Prix. Ces serializers sont     #
#  souvent utilisés comme des briques de base, imbriqués dans d'autres         #
#  serializers plus complexes pour fournir des informations détaillées.        #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblService, TblTemps, TblPrix, TblSalonService, TblSalon, TblSalonImage, TblAvis


################################################################################
#                       SERIALIZER POUR LES DURÉES (TEMPS)                     #
################################################################################

class TempsSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet `TblTemps`, qui représente une durée en minutes.
    """
    class Meta:
        """
        Lie le serializer au modèle `TblTemps` et spécifie les champs à exposer.
        """
        model = TblTemps
        fields = ['idTblTemps', 'minutes']


################################################################################
#                         SERIALIZER POUR LES PRIX                             #
################################################################################

class PrixSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet `TblPrix`, qui représente une valeur monétaire.
    """
    class Meta:
        """
        Lie le serializer au modèle `TblPrix` et spécifie les champs à exposer.
        """
        model = TblPrix
        fields = ['idTblPrix', 'prix']


################################################################################
#                  SERIALIZER PRINCIPAL POUR UN SERVICE GLOBAL                 #
################################################################################

class ServiceSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet `TblService` du catalogue global.
    Il fournit une représentation complète du service en imbriquant les
    serializers pour son prix et sa durée de base (par défaut).
    """
    # --- Champs imbriqués pour les données liées (en lecture seule) ---

    # `source` navigue à travers les relations inverses pour trouver le temps associé :
    # Service -> TblServiceTemps (via related_name 'service_temps') -> TblTemps (via Fk 'temps')
    temps = TempsSerializer(source="service_temps.temps", read_only=True)

    # `source` navigue de la même manière pour trouver le prix associé :
    # Service -> TblServicePrix (via related_name 'service_prix') -> TblPrix (via Fk 'prix')
    prix = PrixSerializer(source="service_prix.prix", read_only=True)

    class Meta:
        """
        Lie le serializer au modèle `TblService` et définit la structure de
        la sortie JSON, incluant les champs imbriqués `temps` et `prix`.
        """
        model = TblService
        fields = ['idTblService', 'intitule_service', 'description', 'temps', 'prix']






# from rest_framework import serializers
# from hairbnb.models import TblService, TblTemps, TblPrix, TblSalonService, TblSalon, TblSalonImage, TblAvis
#
#
# class TempsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblTemps
#         fields = ['idTblTemps', 'minutes']
#
#
# class PrixSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblPrix
#         fields = ['idTblPrix', 'prix']
#
#
# class ServiceSerializer(serializers.ModelSerializer):
#     temps = TempsSerializer(source="service_temps.temps", read_only=True)
#     prix = PrixSerializer(source="service_prix.prix", read_only=True)
#
#     class Meta:
#         model = TblService
#         fields = ['idTblService', 'intitule_service', 'description', 'temps', 'prix']