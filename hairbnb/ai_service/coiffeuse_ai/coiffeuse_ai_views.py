################################################################################
#                                                                              #
#        VUES DE L'API POUR L'IA DÉDIÉE AUX COIFFEUSES (HAIRBNB)                #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API spécifiquement  #
#  conçus pour les utilisateurs de type "coiffeuse". Il fournit une interface  #
#  sécurisée pour que les coiffeuses puissent gérer leurs conversations avec   #
#  l'IA et lui poser des questions sur leurs propres données commerciales.     #
#                                                                              #
#  La sécurité est assurée par des décorateurs comme `@is_owner_coiffeuse`     #
#  qui garantissent qu'une coiffeuse ne peut accéder qu'à ses propres         #
#  conversations et à son propre contexte de données.                          #
#                                                                              #
################################################################################

# --- Importations ---
# Outils de base de Django et Django REST Framework
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Décorateurs personnalisés pour la sécurité et la vérification des rôles
from decorators.decorators import firebase_authenticated, is_owner_coiffeuse
# Le service principal qui communique avec l'API de l'IA
from hairbnb.ai_service.ai_service import AIService
# Les sérialiseurs spécifiques à ces vues pour formater les données
from hairbnb.ai_service.coiffeuse_ai.coiffeuse_ai_serializers import AIConversationSerializer, \
    SendMessageRequestSerializer
# L'utilitaire qui extrait le contexte de la base de données de manière sécurisée
from hairbnb.ai_service.utils import get_database_context_for_query
# Les modèles de données de la base de données
from hairbnb.models import AIConversation, AIMessage


# --- VUES POUR LA GESTION DES CONVERSATIONS (CRUD) ---

# Le décorateur @api_view définit le type de requête HTTP acceptée (ici, GET).
# Le décorateur @firebase_authenticated vérifie que l'utilisateur est bien connecté.
# Le décorateur @is_owner_coiffeuse vérifie que l'utilisateur est une coiffeuse.
@api_view(['GET'])
@firebase_authenticated
@is_owner_coiffeuse
def get_coiffeuse_conversations(request):
    """
    Récupère la liste de toutes les conversations de la coiffeuse connectée.
    """
    # Filtre les conversations pour ne retourner que celles appartenant à l'utilisateur authentifié.
    conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')

    # La réponse est construite manuellement pour ajouter un titre dynamique à chaque conversation.
    data = []
    for conv in conversations:
        last_message = conv.messages.last()
        data.append({
            'id': conv.id,
            'created_at': conv.created_at,
            'tokens_used': conv.tokens_used,
            # Le titre est un aperçu du dernier message, ou un texte par défaut.
            'title': last_message.content[:50] + '...' if last_message else 'Nouvelle Conversation'
        })
    return Response(data)


@api_view(['POST'])
@firebase_authenticated
@is_owner_coiffeuse
def create_coiffeuse_conversation(request):
    """
    Crée une nouvelle conversation vide pour la coiffeuse connectée.
    """
    # Crée une nouvelle instance du modèle AIConversation liée à l'utilisateur actuel.
    conversation = AIConversation.objects.create(user=request.user)
    # Retourne les informations de la nouvelle conversation avec un statut HTTP 201 (Created).
    return Response({'id': conversation.id, 'created_at': conversation.created_at}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@firebase_authenticated
@is_owner_coiffeuse
def get_coiffeuse_conversation_messages(request, conversation_id):
    """
    Récupère tous les messages d'une conversation spécifique.
    Vérifie que la conversation demandée appartient bien à la coiffeuse connectée.
    """
    # get_object_or_404 lève une erreur 404 si la conversation n'est pas trouvée
    # OU si elle n'appartient pas à request.user, ce qui assure la sécurité.
    conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
    # Utilise un sérialiseur pour formater la conversation et ses messages en JSON.
    serializer = AIConversationSerializer(conversation)
    return Response(serializer.data)


@api_view(['DELETE'])
@firebase_authenticated
@is_owner_coiffeuse
def delete_coiffeuse_conversation(request, conversation_id):
    """
    Supprime une conversation spécifique et tous les messages qui y sont liés.
    """
    # Vérifie que la coiffeuse est bien propriétaire de la conversation avant de la supprimer.
    conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
    # La suppression de la conversation entraîne la suppression en cascade des messages associés.
    conversation.delete()
    # Retourne une réponse vide avec le statut 204 (No Content), standard pour une suppression réussie.
    return Response(status=status.HTTP_204_NO_CONTENT)


# --- VUE PRINCIPALE POUR L'INTERACTION AVEC L'IA ---

@api_view(['POST'])
@firebase_authenticated
@is_owner_coiffeuse
def send_coiffeuse_message(request):
    """
    Point d'entrée principal pour l'interaction avec l'IA. Reçoit un message,
    le traite et renvoie la réponse de l'IA.
    """
    # Étape 1 : Valider les données de la requête entrante.
    request_serializer = SendMessageRequestSerializer(data=request.data)
    # Si la validation échoue, renvoie une erreur 400 avec les détails.
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = request_serializer.validated_data
    message_content = validated_data['message']
    conversation_id = validated_data.get('conversation_id')

    # Étape 2 : Récupérer ou créer la conversation.
    if conversation_id:
        # Si un ID est fourni, on récupère la conversation en vérifiant qu'elle appartient à l'utilisateur.
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
    else:
        # Sinon, une nouvelle conversation est créée pour cet utilisateur.
        conversation = AIConversation.objects.create(user=request.user)

    # Étape 3 : Sauvegarder le message de la coiffeuse dans la base de données.
    user_message = AIMessage.objects.create(
        conversation=conversation,
        content=message_content,
        is_user=True
    )

    # Étape 4 : Préparer l'historique des messages pour donner du contexte à l'IA.
    message_history = []
    # On récupère les 4 derniers messages pour limiter le nombre de tokens envoyés.
    recent_messages = conversation.messages.filter(id__lt=user_message.id).order_by('-timestamp')[:4]
    # On les remet dans l'ordre chronologique pour l'IA.
    for msg in reversed(list(recent_messages)):
        message_history.append({"role": "user" if msg.is_user else "assistant", "content": msg.content})

    # Appel à l'utilitaire qui extrait les données. En passant 'request.user',
    # on s'assure qu'il ne récupérera que les données liées à CETTE coiffeuse (ses rdv, son salon, etc.).
    db_context = get_database_context_for_query(message_content, request.user)

    # Étape 5 : Appeler le service IA pour obtenir une réponse.
    ai_service = AIService()
    ai_result = ai_service.get_response(
        query=message_content,
        context=db_context,
        message_history=message_history
    )

    ai_response = ai_result["response"]
    tokens_data = ai_result.get("tokens", {})

    # Étape 6 : Sauvegarder la réponse de l'IA et mettre à jour le coût en tokens.
    AIMessage.objects.create(
        conversation=conversation,
        content=ai_response,
        is_user=False,
        tokens_in=tokens_data.get("input", 0),
        tokens_out=tokens_data.get("output", 0)
    )
    # Ajoute le coût de cet échange au total de la conversation.
    conversation.tokens_used += tokens_data.get("total", 0)
    conversation.save()

    # Étape 7 : Renvoyer la réponse finale à l'application cliente.
    return Response({
        'conversation_id': conversation.id,
        'ai_response': ai_response,
        'tokens': tokens_data
    })








# # hairbnb/ai_service/coiffeuse_ai_views.py
# from django.shortcuts import get_object_or_404
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
#
# # Imports des décorateurs et des modèles/services nécessaires
# from decorators.decorators import firebase_authenticated, is_owner_coiffeuse
# from hairbnb.ai_service.ai_service import AIService
# from hairbnb.ai_service.coiffeuse_ai.coiffeuse_ai_serializers import AIConversationSerializer, \
#     SendMessageRequestSerializer
# from hairbnb.ai_service.utils import get_database_context_for_query
# from hairbnb.models import AIConversation, AIMessage
#
#
# # --- VUES POUR LA GESTION DES CONVERSATIONS ---
#
# @api_view(['GET'])
# @firebase_authenticated
# @is_owner_coiffeuse
# def get_coiffeuse_conversations(request):
#     """Récupère la liste des conversations pour la coiffeuse propriétaire connectée."""
#     conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')
#
#     # On construit la réponse manuellement pour ajouter des détails utiles
#     data = []
#     for conv in conversations:
#         last_message = conv.messages.last()
#         data.append({
#             'id': conv.id,
#             'created_at': conv.created_at,
#             'tokens_used': conv.tokens_used,
#             'title': last_message.content[:50] + '...' if last_message else 'Nouvelle Conversation'
#         })
#     return Response(data)
#
#
# @api_view(['POST'])
# @firebase_authenticated
# @is_owner_coiffeuse
# def create_coiffeuse_conversation(request):
#     """Crée une nouvelle conversation pour la coiffeuse propriétaire."""
#     conversation = AIConversation.objects.create(user=request.user)
#     return Response({'id': conversation.id, 'created_at': conversation.created_at}, status=status.HTTP_201_CREATED)
#
#
# @api_view(['GET'])
# @firebase_authenticated
# @is_owner_coiffeuse
# def get_coiffeuse_conversation_messages(request, conversation_id):
#     """Récupère les messages d'une conversation spécifique, en vérifiant que la coiffeuse en est propriétaire."""
#     conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
#     serializer = AIConversationSerializer(conversation)
#     return Response(serializer.data)
#
#
# @api_view(['DELETE'])
# @firebase_authenticated
# @is_owner_coiffeuse
# def delete_coiffeuse_conversation(request, conversation_id):
#     """Supprime une conversation et ses messages pour la coiffeuse propriétaire."""
#     conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
#     conversation.delete()
#     return Response(status=status.HTTP_204_NO_CONTENT)
#
#
# # --- VUE PRINCIPALE POUR L'INTERACTION AVEC L'IA ---
#
# @api_view(['POST'])
# @firebase_authenticated
# @is_owner_coiffeuse
# def send_coiffeuse_message(request):
#     """
#     Le point d'entrée principal. Reçoit un message d'une coiffeuse propriétaire,
#     récupère le contexte de ses données, interroge l'IA et renvoie la réponse.
#     """
#     # 1. Valider la requête
#     request_serializer = SendMessageRequestSerializer(data=request.data)
#     if not request_serializer.is_valid():
#         return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     validated_data = request_serializer.validated_data
#     message_content = validated_data['message']
#     conversation_id = validated_data.get('conversation_id')
#
#     # 2. Gérer la conversation
#     if conversation_id:
#         # Sécurité : on vérifie que la conversation appartient bien à l'utilisateur
#         conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
#     else:
#         conversation = AIConversation.objects.create(user=request.user)
#
#     # 3. Sauvegarder le message de l'utilisateur
#     user_message = AIMessage.objects.create(
#         conversation=conversation,
#         content=message_content,
#         is_user=True
#     )
#
#     # 4. Préparer le contexte pour l'IA
#     message_history = []
#     recent_messages = conversation.messages.filter(id__lt=user_message.id).order_by('-timestamp')[:4]
#     for msg in reversed(list(recent_messages)):
#         message_history.append({"role": "user" if msg.is_user else "assistant", "content": msg.content})
#
#     # ✅ APPEL À L'UTILITAIRE SÉCURISÉ
#     db_context = get_database_context_for_query(message_content, request.user)
#
#     # 5. Appeler le service IA (le service lui-même est générique et n'a pas besoin de changer)
#     ai_service = AIService()
#     ai_result = ai_service.get_response(
#         query=message_content,
#         context=db_context,
#         message_history=message_history
#     )
#
#     ai_response = ai_result["response"]
#     tokens_data = ai_result.get("tokens", {})
#
#     # 6. Sauvegarder la réponse de l'IA et mettre à jour les tokens
#     AIMessage.objects.create(
#         conversation=conversation,
#         content=ai_response,
#         is_user=False,
#         tokens_in=tokens_data.get("input", 0),
#         tokens_out=tokens_data.get("output", 0)
#     )
#     conversation.tokens_used += tokens_data.get("total", 0)
#     conversation.save()
#
#     # 7. Renvoyer la réponse à l'application
#     return Response({
#         'conversation_id': conversation.id,
#         'ai_response': ai_response,
#         'tokens': tokens_data
#     })