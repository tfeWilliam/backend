################################################################################
#                                                                              #
#         SERIALIZER ALLÉGÉ POUR L'AFFICHAGE DES RÉSERVATIONS                  #
#                                                                              #
#  Ce fichier contient un serializer de Django REST Framework optimisé pour    #
#  fournir une vue d'ensemble concise d'un rendez-vous. Il est idéal pour les  #
#  listes ou les tableaux de bord où les détails complets ne sont pas          #
#  nécessaires, améliorant ainsi les performances.                             #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblRendezVous


################################################################################
#             SERIALIZER "LÉGER" POUR UN RENDEZ-VOUS (RÉSERVATION)             #
################################################################################

class ReservationLightSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet Rendez-vous de manière "légère" en ne sélectionnant
    que les informations essentielles et en aplatissant les données du client
    pour un accès direct et simplifié.
    """
    # --- Champs extraits via la relation avec le client ---
    # L'argument `source` permet de naviguer à travers les relations des modèles Django:
    # obj.client -> obj.client.idTblUser -> obj.client.idTblUser.nom
    client_nom = serializers.CharField(source='client.idTblUser.nom')
    client_prenom = serializers.CharField(source='client.idTblUser.prenom')
    client_photo = serializers.ImageField(source='client.idTblUser.photo_profil', allow_null=True)

    # --- Champs directs du modèle RendezVous ---
    date_heure = serializers.DateTimeField()
    statut = serializers.CharField()
    total_prix = serializers.FloatField()
    duree_totale = serializers.IntegerField()

    class Meta:
        """
        La classe Meta lie le serializer au modèle `TblRendezVous` et définit
        la liste des champs qui composeront la sortie JSON finale.
        """
        model = TblRendezVous
        fields = [
            'idRendezVous',
            'client_nom',
            'client_prenom',
            'client_photo',
            'date_heure',
            'statut',
            'total_prix',
            'duree_totale',
        ]








# from rest_framework import serializers
#
# from hairbnb.models import TblRendezVous
#
#
# class ReservationLightSerializer(serializers.ModelSerializer):
#     #idRendezVous = serializers.IntegerField()
#     client_nom = serializers.CharField(source='client.idTblUser.nom')
#     client_prenom = serializers.CharField(source='client.idTblUser.prenom')
#     client_photo = serializers.ImageField(source='client.idTblUser.photo_profil', allow_null=True)
#     date_heure = serializers.DateTimeField()
#     statut = serializers.CharField()
#     total_prix = serializers.FloatField()
#     duree_totale = serializers.IntegerField()
#
#     class Meta:
#         model = TblRendezVous
#         fields = [
#             'idRendezVous',
#             'client_nom',
#             'client_prenom',
#             'client_photo',
#             'date_heure',
#             'statut',
#             'total_prix',
#             'duree_totale',
#         ]
