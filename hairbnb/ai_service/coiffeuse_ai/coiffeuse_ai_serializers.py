################################################################################
#                                                                              #
#              SÉRIALISEURS POUR L'API IA (DJANGO REST FRAMEWORK)              #
#                                                                              #
#  Ce fichier définit les sérialiseurs (serializers) utilisés par le Django    #
#  REST Framework. Leur rôle est de convertir les objets de la base de données #
#  (modèles Django) en un format simple comme le JSON pour pouvoir les envoyer #
#  via l'API, et inversement, de valider les données reçues.                   #
#                                                                              #
#  Chaque classe correspond à une structure de données précise pour l'API de   #
#  conversation avec l'IA.                                                     #
#                                                                              #
################################################################################

# Importation du module de sérialiseurs de Django REST Framework.
from rest_framework import serializers
# Importation des modèles de données depuis l'application hairbnb.
from hairbnb.models import AIConversation, AIMessage


class AIMessageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle AIMessage.
    Il transforme une instance du modèle de message en données JSON.
    """
    class Meta:
        # Indique que ce sérialiseur est basé sur le modèle AIMessage.
        model = AIMessage
        # Liste les champs du modèle à inclure dans la représentation JSON.
        fields = ['id', 'content', 'is_user', 'timestamp']
        # Précise que les champs 'id' et 'timestamp' sont générés par le serveur
        # et ne peuvent pas être modifiés par une requête API.
        read_only_fields = ['id', 'timestamp']


class AIConversationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle AIConversation.
    Fournit une vue détaillée d'une conversation, incluant tous ses messages.
    """
    # Crée un champ "messages" qui est une liste de messages sérialisés.
    # 'many=True' indique qu'il s'agit d'une relation "un-à-plusieurs".
    # 'read_only=True' signifie que cette liste est lue mais pas modifiée directement ici.
    messages = AIMessageSerializer(many=True, read_only=True)

    class Meta:
        # Indique que ce sérialiseur est basé sur le modèle AIConversation.
        model = AIConversation
        # Liste les champs à inclure dans la réponse JSON.
        fields = ['id', 'user_id', 'created_at', 'messages']
        read_only_fields = ['id', 'created_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour lister les conversations.
    Ne renvoie que des informations minimales pour un affichage en liste,
    ce qui rend la réponse de l'API plus légère et rapide.
    """
    class Meta:
        # Basé sur le modèle AIConversation.
        model = AIConversation
        # Ne contient que les champs essentiels pour une liste.
        fields = ['id', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateConversationResponseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur spécifique pour formater la réponse JSON lors de la
    création d'une nouvelle conversation.
    """
    # Crée un champ 'conversation_id' dans le JSON.
    # L'option 'source="id"' indique que la valeur de ce champ doit provenir
    # du champ 'id' du modèle, le renommant pour plus de clarté dans l'API.
    conversation_id = serializers.IntegerField(source='id')

    class Meta:
        # Basé sur le modèle AIConversation.
        model = AIConversation
        # Champs à inclure dans la réponse.
        fields = ['conversation_id', 'created_at']
        read_only_fields = ['conversation_id', 'created_at']


class SendMessageRequestSerializer(serializers.Serializer):
    """
    Sérialiseur pour valider les données de la REQUÊTE envoyée par l'utilisateur.
    Il n'est pas lié à un modèle (n'hérite pas de ModelSerializer) car son seul rôle
    est de définir la structure et les règles des données entrantes.
    """
    # L'ID de la conversation est optionnel ('required=False') car l'utilisateur
    # peut envoyer un premier message sans avoir d'ID de conversation.
    conversation_id = serializers.IntegerField(required=False)
    # Le contenu du message est toujours obligatoire.
    message = serializers.CharField(required=True)


class SendMessageResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour formater la structure de la RÉPONSE envoyée au client.
    Comme le précédent, il n'est pas lié à un modèle et sert à définir
    le format des données de sortie de l'API.
    """
    # Définit les champs que le client recevra dans la réponse JSON.
    conversation_id = serializers.IntegerField()
    user_message_id = serializers.IntegerField()
    ai_message_id = serializers.IntegerField()
    ai_response = serializers.CharField()






# from rest_framework import serializers
# from hairbnb.models import AIConversation, AIMessage
#
#
# class AIMessageSerializer(serializers.ModelSerializer):
#     """
#     S'occupe de la sérialisation d'un seul message.
#     """
#     class Meta:
#         model = AIMessage
#         fields = ['id', 'content', 'is_user', 'timestamp']
#         read_only_fields = ['id', 'timestamp']
#
#
# class AIConversationSerializer(serializers.ModelSerializer):
#     """
#     S'occupe de la sérialisation d'une conversation complète avec tous ses messages.
#     """
#     messages = AIMessageSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = AIConversation
#         fields = ['id', 'user_id', 'created_at', 'messages']
#         read_only_fields = ['id', 'created_at']
#
#
# class ConversationListSerializer(serializers.ModelSerializer):
#     """
#     S'occupe de la sérialisation d'un élément dans la liste des conversations (plus léger).
#     """
#     class Meta:
#         model = AIConversation
#         fields = ['id', 'created_at']
#         read_only_fields = ['id', 'created_at']
#
#
# class CreateConversationResponseSerializer(serializers.ModelSerializer):
#     """
#     Formate la réponse lors de la création d'une nouvelle conversation.
#     """
#     conversation_id = serializers.IntegerField(source='id')
#
#     class Meta:
#         model = AIConversation
#         fields = ['conversation_id', 'created_at']
#         read_only_fields = ['conversation_id', 'created_at']
#
#
# class SendMessageRequestSerializer(serializers.Serializer):
#     """
#     Valide les données reçues lors de l'envoi d'un message.
#     """
#     conversation_id = serializers.IntegerField(required=False)
#     message = serializers.CharField(required=True)
#
#
# class SendMessageResponseSerializer(serializers.Serializer):
#     """
#     Formate la réponse envoyée au front-end après une question à l'IA.
#     """
#     conversation_id = serializers.IntegerField()
#     user_message_id = serializers.IntegerField()
#     ai_message_id = serializers.IntegerField()
#     ai_response = serializers.CharField()