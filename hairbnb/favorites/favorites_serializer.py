################################################################################
#                                                                              #
#            SÉRIALISEURS POUR LE SYSTÈME DE FAVORIS (HAIRBNB)                  #
#                                                                              #
#  Ce fichier définit les sérialiseurs (serializers) pour la gestion des       #
#  salons favoris des utilisateurs.                                            #
#                                                                              #
#  Il contient deux sérialiseurs distincts pour le même modèle `TblFavorite`,  #
#  chacun étant optimisé pour un cas d'usage différent :                       #
#    - `TblFavoriteSerializer`: Fournit une réponse détaillée incluant         #
#      l'objet salon complet.                                                  #
#    - `FavoriteCheckSerializer`: Fournit une réponse légère retournant        #
#      uniquement l'ID du salon, idéal pour des vérifications rapides.         #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers
from hairbnb.models import TblFavorite
# Importation du sérialiseur de salon pour l'imbrication
from hairbnb.salon.salon_serializers import TblSalonSerializer


class TblFavoriteSerializer(serializers.ModelSerializer):
    """
    Sérialiseur principal et détaillé pour un objet `TblFavorite`.
    Il est conçu pour renvoyer des informations riches, y compris l'objet salon complet.
    """
    # Champ imbriqué qui utilise TblSalonSerializer pour inclure toutes les informations
    # du salon associé à ce favori.
    salon = TblSalonSerializer(read_only=True)

    # Ajoute explicitement l'ID de l'utilisateur à la réponse.
    # 'source' indique que la valeur provient du champ 'idTblUser' de l'objet 'user' lié.
    user = serializers.IntegerField(source='user.idTblUser', read_only=True)

    # Ajoute la date de création du favori et la formate selon la norme ISO 8601.
    added_at = serializers.DateTimeField(source='added_at', read_only=True, format='%Y-%m-%dT%H:%M:%S')

    class Meta:
        # Lie ce sérialiseur au modèle TblFavorite.
        model = TblFavorite
        # Définit les champs à inclure dans la sortie JSON.
        fields = ['idTblFavorite', 'user', 'salon', 'added_at']


class FavoriteCheckSerializer(serializers.ModelSerializer):
    """
    Sérialiseur léger et optimisé pour vérifier si un salon est en favori.
    Il ne renvoie que les IDs, ce qui rend la réponse de l'API plus petite et plus rapide.
    """
    # Contrairement au sérialiseur précédent, ce champ ne renvoie que l'ID entier du salon.
    # 'source' pointe vers la clé primaire ('idTblSalon') de l'objet salon lié.
    salon = serializers.IntegerField(source='salon.idTblSalon', read_only=True)
    # Renvoie l'ID de l'utilisateur.
    user = serializers.IntegerField(source='user.idTblUser', read_only=True)

    class Meta:
        # Lie ce sérialiseur au modèle TblFavorite.
        model = TblFavorite
        # Définit les champs à inclure dans la sortie JSON.
        fields = ['idTblFavorite', 'user', 'salon', 'added_at']








# # hairbnb/serializers/favorites_serializers.py
# from rest_framework import serializers
# from hairbnb.models import TblFavorite
# from hairbnb.salon.salon_serializers import TblSalonSerializer
#
#
# class TblFavoriteSerializer(serializers.ModelSerializer):
#     # Conserver l'objet salon complet pour les endpoints existants
#     salon = TblSalonSerializer(read_only=True)
#
#     # Ajouter explicitement le champ user pour le rendre compatible avec le modèle Flutter
#     user = serializers.IntegerField(source='user.idTblUser', read_only=True)
#
#     # Ajouter le champ added_at pour correspondre au modèle Flutter
#     added_at = serializers.DateTimeField(source='added_at', read_only=True, format='%Y-%m-%dT%H:%M:%S')
#
#     class Meta:
#         model = TblFavorite
#         fields = ['idTblFavorite', 'user', 'salon', 'added_at']
#
#
# # Nouveau serializer spécifique pour l'endpoint de vérification de favoris
# class FavoriteCheckSerializer(serializers.ModelSerializer):
#     # Pour ce serializer, on transforme le salon en ID entier
#     salon = serializers.IntegerField(source='salon.idTblSalon', read_only=True)
#     user = serializers.IntegerField(source='user.idTblUser', read_only=True)
#
#     class Meta:
#         model = TblFavorite
#         fields = ['idTblFavorite', 'user', 'salon', 'added_at']
