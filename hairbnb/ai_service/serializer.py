################################################################################
#                                                                              #
#              SÉRIALISEURS POUR L'API IA (DJANGO REST FRAMEWORK)              #
#                                                                              #
#  Ce fichier définit les sérialiseurs (serializers) utilisés par le Django    #
#  REST Framework pour convertir les objets complexes, comme les instances de #
#  modèles Django (`AIConversation`, `AIMessage`), en types de données Python  #
#  natifs qui peuvent ensuite être facilement rendus en JSON.                  #
#                                                                              #
#  Ils gèrent également la validation des données entrantes pour les requêtes #
#  POST et PUT. Chaque classe correspond à une structure de données            #
#  spécifique pour l'API.                                                      #
#                                                                              #
################################################################################

# Importation du module de sérialiseurs de Django REST Framework.
from rest_framework import serializers
# Importation des modèles de données de l'application.
from hairbnb.models import AIConversation, AIMessage


class AIMessageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle AIMessage.
    Utilisé pour représenter un seul message dans une conversation.
    """
    class Meta:
        # Spécifie le modèle Django auquel ce sérialiseur est lié.
        model = AIMessage
        # Liste des champs du modèle à inclure dans la représentation sérialisée.
        fields = ['id', 'content', 'is_user', 'timestamp']
        # Spécifie que certains champs sont en lecture seule (ne peuvent pas être modifiés via l'API).
        read_only_fields = ['id', 'timestamp']


class AIConversationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle AIConversation.
    Fournit une vue détaillée d'une conversation, incluant tous ses messages.
    """
    # Champ imbriqué pour inclure une liste de messages dans la conversation.
    # 'many=True' indique qu'il s'agit d'une liste de plusieurs objets AIMessage.
    # 'read_only=True' car les messages sont gérés par d'autres vues.
    messages = AIMessageSerializer(many=True, read_only=True)

    class Meta:
        # Liaison avec le modèle AIConversation.
        model = AIConversation
        # Champs à inclure : l'ID de la conversation, l'ID de l'utilisateur, la date de création
        # et la liste imbriquée des messages.
        fields = ['id', 'user_id', 'created_at', 'messages']
        # Champs en lecture seule.
        read_only_fields = ['id', 'created_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour lister les conversations.
    Ne renvoie que les informations essentielles pour un affichage en liste,
    afin de garder la réponse de l'API légère.
    """
    class Meta:
        # Liaison avec le modèle AIConversation.
        model = AIConversation
        # Ne contient que l'ID et la date de création.
        fields = ['id', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateConversationResponseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour formater la réponse JSON lors de la création d'une
    nouvelle conversation.
    """
    # Renomme le champ 'id' du modèle en 'conversation_id' dans la réponse JSON
    # pour une meilleure clarté de l'API. 'source' indique le champ d'origine du modèle.
    conversation_id = serializers.IntegerField(source='id')

    class Meta:
        # Liaison avec le modèle AIConversation.
        model = AIConversation
        # Définit les champs de la réponse.
        fields = ['conversation_id', 'created_at']
        read_only_fields = ['conversation_id', 'created_at']


class SendMessageRequestSerializer(serializers.Serializer):
    """
    Sérialiseur pour valider les données de la REQUÊTE lors de l'envoi d'un message.
    Il n'est pas lié à un modèle (n'hérite pas de ModelSerializer) car il définit
    uniquement la structure des données attendues en entrée de la vue 'send_message'.
    """
    # L'ID de la conversation est optionnel ('required=False') car une nouvelle
    # conversation peut être créée si aucun ID n'est fourni.
    conversation_id = serializers.IntegerField(required=False)
    # Le contenu du message est obligatoire.
    message = serializers.CharField(required=True)


class SendMessageResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour formater les données de la RÉPONSE après l'envoi d'un message.
    Comme le précédent, il n'est pas lié à un modèle et définit la structure
    des données de sortie de la vue 'send_message'.
    """
    # Définit les champs qui seront présents dans la réponse JSON.
    conversation_id = serializers.IntegerField()
    user_message_id = serializers.IntegerField()
    ai_message_id = serializers.IntegerField()
    ai_response = serializers.CharField()







# # hairbnb/claud_ai/serializers.py
# from rest_framework import serializers
# from hairbnb.models import AIConversation, AIMessage
#
#
# class AIMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AIMessage
#         fields = ['id', 'content', 'is_user', 'timestamp']
#         read_only_fields = ['id', 'timestamp']
#
#
# class AIConversationSerializer(serializers.ModelSerializer):
#     messages = AIMessageSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = AIConversation
#         fields = ['id', 'user_id', 'created_at', 'messages']
#         read_only_fields = ['id', 'created_at']
#
#
# class ConversationListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AIConversation
#         fields = ['id', 'created_at']
#         read_only_fields = ['id', 'created_at']
#
#
# class CreateConversationResponseSerializer(serializers.ModelSerializer):
#     conversation_id = serializers.IntegerField(source='id')
#
#     class Meta:
#         model = AIConversation
#         fields = ['conversation_id', 'created_at']
#         read_only_fields = ['conversation_id', 'created_at']
#
#
# class SendMessageRequestSerializer(serializers.Serializer):
#     conversation_id = serializers.IntegerField(required=False)
#     message = serializers.CharField(required=True)
#
#
# class SendMessageResponseSerializer(serializers.Serializer):
#     conversation_id = serializers.IntegerField()
#     user_message_id = serializers.IntegerField()
#     ai_message_id = serializers.IntegerField()
#     ai_response = serializers.CharField()