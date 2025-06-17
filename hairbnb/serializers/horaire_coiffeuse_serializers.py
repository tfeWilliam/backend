################################################################################
#                                                                              #
#         SERIALIZERS POUR LA GESTION DES HORAIRES ET INDISPONIBILITÉS         #
#                                                                              #
#  Ce fichier contient les serializers de Django REST Framework nécessaires    #
#  pour la gestion des plannings des coiffeuses. Il permet de formater les     #
#  données relatives aux horaires de travail hebdomadaires et aux périodes     #
#  d'indisponibilité exceptionnelles.                                          #
#                                                                              #
#  Classes définies :                                                          #
#    - `HoraireCoiffeuseSerializer`: Formate les horaires récurrents.          #
#    - `IndisponibiliteSerializer`: Formate les plages d'indisponibilité       #
#      spécifiques.                                                            #
#                                                                              #
################################################################################


from rest_framework import serializers
from hairbnb.models import TblHoraireCoiffeuse, TblIndisponibilite


################################################################################
#                  SERIALIZER POUR LES HORAIRES DE LA COIFFEUSE                #
################################################################################

class HoraireCoiffeuseSerializer(serializers.ModelSerializer):
    """
    Sérialise les données d'un horaire de travail hebdomadaire pour une coiffeuse.
    Il ajoute un champ 'jour_label' pour fournir une version lisible par l'homme
    du jour de la semaine.
    """

    # Champ calculé pour afficher le nom complet du jour (ex: "Lundi")
    # au lieu de sa valeur numérique (ex: 1).
    jour_label = serializers.SerializerMethodField()

    class Meta:
        """
        La classe Meta lie le serializer au modèle Django et définit les champs
        qui seront inclus dans la sortie JSON finale.
        """
        model = TblHoraireCoiffeuse
        fields = ['id', 'coiffeuse', 'jour', 'jour_label', 'heure_debut', 'heure_fin']

    def get_jour_label(self, obj):
        """
        Méthode pour calculer la valeur du champ 'jour_label'.
        Elle utilise la fonctionnalité intégrée de Django `get_jour_display()`
        pour obtenir le nom lisible du champ 'jour' qui est un `Choices` field.
        """
        return obj.get_jour_display()


################################################################################
#                SERIALIZER POUR LES INDISPONIBILITÉS DE LA COIFFEUSE          #
################################################################################

class IndisponibiliteSerializer(serializers.ModelSerializer):
    """
    Sérialise les données d'une période d'indisponibilité spécifique
    (ex: vacances, rendez-vous personnel) pour une coiffeuse.
    """

    class Meta:
        """
        La classe Meta lie le serializer au modèle Django et définit les champs
        à inclure dans la sortie JSON.
        """
        model = TblIndisponibilite
        fields = ['id', 'coiffeuse', 'date', 'heure_debut', 'heure_fin', 'motif']





# from rest_framework import serializers
# from hairbnb.models import TblHoraireCoiffeuse, TblIndisponibilite
#
#
# class HoraireCoiffeuseSerializer(serializers.ModelSerializer):
#     jour_label = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblHoraireCoiffeuse
#         fields = ['id', 'coiffeuse', 'jour', 'jour_label', 'heure_debut', 'heure_fin']
#
#     def get_jour_label(self, obj):
#         return obj.get_jour_display()
#
#
# class IndisponibiliteSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblIndisponibilite
#         fields = ['id', 'coiffeuse', 'date', 'heure_debut', 'heure_fin', 'motif']
