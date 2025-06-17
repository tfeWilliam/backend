################################################################################
#                                                                              #
#         SERIALIZERS POUR LA GESTION ET L'AFFICHAGE DES RÉSERVATIONS          #
#                                                                              #
#  Ce fichier contient les serializers de Django REST Framework pour           #
#  la gestion des réservations (Rendez-vous). Il permet de formater les        #
#  données de manière structurée pour les API, en incluant les détails du      #
#  client et la liste des services associés à chaque réservation.              #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblRendezVous, TblRendezVousService


################################################################################
#           SERIALIZER POUR UN SERVICE SPÉCIFIQUE DANS UNE RÉSERVATION         #
################################################################################

class RendezVousServiceSerializer(serializers.ModelSerializer):
    """
    Sérialise les informations d'un service tel qu'il est lié à un rendez-vous
    via la table de liaison `TblRendezVousService`.
    """
    class Meta:
        """
        La classe Meta lie le serializer au modèle et définit les champs à inclure.
        - 'service': L'ID du service global concerné.
        - 'prix_applique': Le prix facturé pour ce service au moment de la réservation.
        - 'duree_estimee': La durée estimée pour ce service au moment de la réservation.
        """
        model = TblRendezVousService
        fields = ['service', 'prix_applique', 'duree_estimee']


################################################################################
#                   SERIALIZER PRINCIPAL POUR UNE RÉSERVATION                  #
################################################################################

class ReservationSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet Rendez-vous (réservation) en fournissant les détails
    principaux de la réservation, des informations clés sur le client, et la
    liste complète des services inclus.
    """
    # --- Champs extraits via les relations (en lecture seule) ---
    # `source` est utilisé pour "aplatir" les données et accéder directement
    # au nom et prénom de l'utilisateur lié au client.
    client_nom = serializers.CharField(source='client.idTblUser.nom', read_only=True)
    client_prenom = serializers.CharField(source='client.idTblUser.prenom', read_only=True)

    # --- Champ imbriqué pour la liste des services ---
    # Utilise le serializer ci-dessus pour représenter chaque service dans la réservation.
    # `many=True` indique qu'il s'agit d'une liste de plusieurs services.
    services = RendezVousServiceSerializer(source='rendez_vous_services', many=True)

    class Meta:
        """
        La classe Meta lie le serializer au modèle `TblRendezVous` et définit
        l'ensemble des champs qui composeront la sortie JSON.
        """
        model = TblRendezVous
        fields = [
            'idRendezVous',
            'client_nom',
            'client_prenom',
            'date_heure',
            'statut',
            'total_prix',
            'duree_totale',
            'services'
        ]







# # serializers/reservation_serializer.py
#
# from rest_framework import serializers
# from hairbnb.models import TblRendezVous, TblRendezVousService
#
# class RendezVousServiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblRendezVousService
#         fields = ['service', 'prix_applique', 'duree_estimee']
#
# class ReservationSerializer(serializers.ModelSerializer):
#     client_nom = serializers.CharField(source='client.idTblUser.nom', read_only=True)
#     client_prenom = serializers.CharField(source='client.idTblUser.prenom', read_only=True)
#     services = RendezVousServiceSerializer(source='rendez_vous_services', many=True)
#
#     class Meta:
#         model = TblRendezVous
#         fields = [
#             'idRendezVous',
#             'client_nom',
#             'client_prenom',
#             'date_heure',
#             'statut',
#             'total_prix',
#             'duree_totale',
#             'services'
#         ]
