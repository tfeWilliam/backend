################################################################################
#                                                                              #
#         SERIALIZERS POUR LA GESTION DES RENDEZ-VOUS ET PAIEMENTS             #
#                                                                              #
#  Ce fichier regroupe les serializers de Django REST Framework essentiels     #
#  au processus de réservation. Ils permettent de formater les données pour    #
#  les API concernant les rendez-vous, les services qui les composent, les     #
#  paiements associés, et les indisponibilités des coiffeuses.                 #
#                                                                              #
################################################################################


from rest_framework import serializers

from hairbnb.models import TblRendezVous, TblRendezVousService, TblPaiement, TblIndisponibilite
from hairbnb.profil.profil_serializers import ClientSerializer, CoiffeuseSerializer
from hairbnb.salon.salon_serializers import ServiceSerializer, SalonSerializer


################################################################################
#           SERIALIZER POUR UN SERVICE SPÉCIFIQUE DANS UN RENDEZ-VOUS          #
################################################################################

class RendezVousServiceSerializer(serializers.ModelSerializer):
    """
    Sérialise un service tel qu'il est inclus dans un rendez-vous.
    Ce serializer agit sur la table de liaison `TblRendezVousService` et inclut
    le prix et la durée tels qu'ils étaient au moment de la réservation.
    """
    # Utilisation d'un serializer imbriqué pour afficher les détails complets du service.
    service = ServiceSerializer()

    class Meta:
        model = TblRendezVousService
        fields = [
            'idRendezVousService',
            'service',
            'prix_applique',    # Prix du service au moment de la réservation.
            'duree_estimee'     # Durée du service au moment de la réservation.
        ]


################################################################################
#                   SERIALIZER PRINCIPAL POUR UN RENDEZ-VOUS                   #
################################################################################

class RendezVousSerializer(serializers.ModelSerializer):
    """
    Sérialise un objet Rendez-vous complet en agrégeant toutes les informations
    liées : client, coiffeuse, salon, et la liste des services inclus.
    """
    # Champs imbriqués en lecture seule pour fournir des détails riches.
    client = ClientSerializer(source='client', read_only=True)
    coiffeuse = CoiffeuseSerializer(source='coiffeuse', read_only=True)
    salon = SalonSerializer(source='salon', read_only=True)
    # Liste des services du rendez-vous, utilisant le serializer défini ci-dessus.
    services = RendezVousServiceSerializer(source='rendez_vous_services', many=True, read_only=True)

    class Meta:
        model = TblRendezVous
        fields = [
            'idRendezVous',
            'client',
            'coiffeuse',
            'salon',
            'date_heure',
            'statut',
            'total_prix',
            'duree_totale',
            'services'
        ]


################################################################################
#                SERIALIZER POUR LES INDISPONIBILITÉS                          #
################################################################################

class IndisponibiliteSerializer(serializers.ModelSerializer):
    """
    Sérialise une période d'indisponibilité ponctuelle pour une coiffeuse.
    """
    class Meta:
        model = TblIndisponibilite
        # Note : le champ 'coiffeuse' n'est pas inclus ici, il est géré dans la vue.
        fields = ['id', 'date', 'heure_debut', 'heure_fin', 'motif']


################################################################################
#                     SERIALIZER POUR LES PAIEMENTS                            #
################################################################################

class PaiementSerializer(serializers.ModelSerializer):
    """
    Sérialise une transaction de paiement. Il inclut une représentation complète
    du rendez-vous associé pour un contexte maximal.
    """
    # Imbrication du RendezVousSerializer pour donner tous les détails du rendez-vous payé.
    rendez_vous = RendezVousSerializer(source='rendez_vous', read_only=True)

    class Meta:
        model = TblPaiement
        fields = [
            'idPaiement',
            'rendez_vous',
            'montant_paye',
            'date_paiement',
            'methode',
            'statut'
        ]










# from rest_framework import serializers
#
# from hairbnb.models import TblRendezVous, TblRendezVousService, TblPaiement,TblIndisponibilite
# from hairbnb.profil.profil_serializers import ClientSerializer, CoiffeuseSerializer
# from hairbnb.salon.salon_serializers import ServiceSerializer, SalonSerializer
#
#
# # 🔹 Serializer pour les services liés à un rendez-vous
# class RendezVousServiceSerializer(serializers.ModelSerializer):
#     service = ServiceSerializer()  # ✅ Remplace ServiceData par un Serializer DRF
#
#     class Meta:
#         model = TblRendezVousService
#         fields = ['idRendezVousService', 'service', 'prix_applique', 'duree_estimee']
#
#
# # 🔹 Serializer pour un rendez-vous
# class RendezVousSerializer(serializers.ModelSerializer):
#     client = ClientSerializer(source='client', read_only=True)
#     coiffeuse = CoiffeuseSerializer(source='coiffeuse', read_only=True)
#     salon = SalonSerializer(source='salon', read_only=True)  # ✅ Remplace SalonData
#     services = RendezVousServiceSerializer(source='rendez_vous_services', many=True, read_only=True)
#
#     class Meta:
#         model = TblRendezVous
#         fields = [
#             'idRendezVous', 'client', 'coiffeuse', 'salon', 'date_heure',
#             'statut', 'total_prix', 'duree_totale', 'services'
#         ]
#
#
# class IndisponibiliteSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblIndisponibilite
#         fields = ['id', 'date', 'heure_debut', 'heure_fin', 'motif']
#
#
# # 🔹 Serializer pour le paiement
# class PaiementSerializer(serializers.ModelSerializer):
#     rendez_vous = RendezVousSerializer(source='rendez_vous', read_only=True)
#
#     class Meta:
#         model = TblPaiement
#         fields = ['idPaiement', 'rendez_vous', 'montant_paye', 'date_paiement', 'methode', 'statut']
#
