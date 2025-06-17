################################################################################
#                                                                              #
#                   VUES DE L'API POUR LE SERVICE IA (HAIRBNB)                   #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API REST pour gérer  #
#  les conversations avec l'intelligence artificielle. Il utilise le           #
#  Django REST Framework pour créer des vues qui permettent de :               #
#    - Lister, créer et supprimer des conversations.                           #
#    - Récupérer les messages d'une conversation spécifique.                   #
#    - Envoyer un message à l'IA et recevoir une réponse.                      #
#                                                                              #
#  Toutes les vues sont protégées et nécessitent une authentification via      #
#  Firebase.                                                                   #
#                                                                              #
################################################################################

# Importations depuis Django et Django REST Framework
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Importations depuis les modules locaux de l'application
from decorators.decorators import firebase_authenticated  # Décorateur pour l'authentification Firebase
from .ai_service import AIService  # Le service qui communique avec l'API de l'IA
from .utils import get_database_context_for_query  # Utilitaire pour extraire le contexte de la BDD
from ..models import AIConversation, AIMessage  # Modèles de données pour les conversations et messages


@api_view(['GET'])
@firebase_authenticated
def get_conversations(request):
    """
    Vue API pour récupérer la liste de toutes les conversations
    de l'utilisateur actuellement authentifié.
    """
    try:
        # Récupère l'objet utilisateur attaché à la requête par le décorateur d'authentification.
        user = request.user

        # Filtre les conversations pour ne retourner que celles appartenant à l'utilisateur,
        # ordonnées par date de création décroissante.
        conversations = AIConversation.objects.filter(user=user).order_by('-created_at')

        # Prépare les données pour la sérialisation en JSON.
        # Pour chaque conversation, on crée un dictionnaire résumé.
        conversations_data = [{
            'id': conv.id,
            'created_at': conv.created_at.isoformat(),
            'tokens_used': conv.tokens_used,
            'last_message': conv.messages.last().content[:100] if conv.messages.exists() else None
        } for conv in conversations]

        # Retourne la liste des conversations avec un statut HTTP 200 OK.
        return Response({'conversations': conversations_data})

    except Exception as e:
        # En cas d'erreur inattendue, retourne une réponse d'erreur générique.
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@firebase_authenticated
def get_conversation_messages(request, conversation_id):
    """
    Vue API pour récupérer tous les messages d'une conversation spécifique,
    en vérifiant que celle-ci appartient bien à l'utilisateur.
    """
    try:
        # Récupère l'utilisateur authentifié.
        user = request.user

        # Tente de récupérer la conversation par son ID.
        # get_object_or_404 lève une erreur 404 si l'objet n'est pas trouvé
        # ou n'appartient pas à l'utilisateur.
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)

        # Récupère tous les messages liés à cette conversation, ordonnés par leur timestamp.
        messages = conversation.messages.all().order_by('timestamp')

        # Prépare la liste des messages pour la réponse JSON.
        messages_data = [{
            'id': msg.id,
            'content': msg.content,
            'is_user': msg.is_user,
            'timestamp': msg.timestamp.isoformat(),
            'tokens_in': msg.tokens_in,
            'tokens_out': msg.tokens_out
        } for msg in messages]

        # Retourne les détails de la conversation ainsi que la liste de ses messages.
        return Response({
            'conversation_id': conversation.id,
            'created_at': conversation.created_at.isoformat(),
            'tokens_used': conversation.tokens_used,
            'messages': messages_data
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@firebase_authenticated
def create_conversation(request):
    """
    Vue API pour créer une nouvelle conversation vide pour l'utilisateur.
    """
    try:
        # Récupère l'utilisateur authentifié.
        user = request.user

        # Crée une nouvelle instance du modèle AIConversation en base de données.
        conversation = AIConversation.objects.create(
            user=user,
            context_cache={},
            tokens_used=0
        )

        # Retourne l'ID et la date de création de la nouvelle conversation
        # avec un statut HTTP 201 CREATED.
        return Response({
            'conversation_id': conversation.id,
            'created_at': conversation.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@firebase_authenticated
def send_message(request):
    """
    Vue API principale pour envoyer un message, obtenir une réponse de l'IA,
    et sauvegarder l'échange en base de données.
    """
    try:
        # Extraction des données du corps de la requête POST.
        data = request.data
        conversation_id = data.get('conversation_id')
        message_content = data.get('message')

        # Validation simple pour s'assurer que le message n'est pas vide.
        if not message_content:
            return Response({'error': 'Le message est requis'}, status=status.HTTP_400_BAD_REQUEST)

        # Récupère l'utilisateur authentifié.
        user = request.user

        # Si un ID de conversation est fourni, on la récupère.
        # Sinon, une nouvelle conversation est créée à la volée.
        if conversation_id:
            conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)
        else:
            conversation = AIConversation.objects.create(
                user=user,
                context_cache={},
                tokens_used=0
            )

        # Instanciation du service IA qui gère la logique de communication avec Claude.
        ai_service = AIService()

        # Le message de l'utilisateur est enregistré en premier dans la BDD.
        tokens_in = ai_service.count_tokens(message_content)
        user_message = AIMessage.objects.create(
            conversation=conversation,
            content=message_content,
            is_user=True,
            tokens_in=tokens_in,
            tokens_out=0
        )

        # Construction de l'historique de la conversation pour le passer à l'IA.
        message_history = []
        # On ne prend que les 4 derniers messages pour limiter le nombre de tokens.
        recent_messages = conversation.messages.filter(id__lt=user_message.id).order_by('-timestamp')[:4]
        # On inverse la liste pour que l'ordre soit chronologique.
        for msg in reversed(list(recent_messages)):
            role = "user" if msg.is_user else "assistant"
            message_history.append({"role": role, "content": msg.content})

        # Appel à une fonction utilitaire pour extraire des données pertinentes de la BDD
        # en fonction du contenu de la question de l'utilisateur.
        db_context = get_database_context_for_query(message_content)

        # Appel au service IA pour obtenir la réponse.
        ai_result = ai_service.get_response(
            query=message_content,
            context=db_context,
            message_history=message_history
        )

        # Extraction des informations du résultat retourné par le service.
        ai_response = ai_result["response"]
        tokens_data = ai_result.get("tokens", {"input": tokens_in, "output": 0, "total": tokens_in})

        # La réponse de l'IA est à son tour enregistrée en base de données.
        ai_message = AIMessage.objects.create(
            conversation=conversation,
            content=ai_response,
            is_user=False,
            tokens_in=0,
            tokens_out=tokens_data["output"]
        )

        # Le coût total en tokens de cet échange est ajouté au total de la conversation.
        conversation.tokens_used += tokens_data["total"]
        conversation.save()

        # La réponse finale est envoyée au client.
        return Response({
            'conversation_id': conversation.id,
            'user_message_id': user_message.id,
            'ai_message_id': ai_message.id,
            'ai_response': ai_response,
            'tokens': tokens_data
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@firebase_authenticated
def delete_conversation(request, conversation_id):
    """
    Vue API pour supprimer une conversation et tous les messages associés.
    """
    try:
        # Récupère l'utilisateur authentifié.
        user = request.user

        # Récupère la conversation à supprimer, en s'assurant qu'elle appartient à l'utilisateur.
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)

        # Suppression de tous les objets AIMessage liés à cette conversation.
        conversation.messages.all().delete()

        # Suppression de l'objet AIConversation lui-même.
        conversation.delete()

        # Retourne une réponse avec le statut 204 NO CONTENT, indiquant que la
        # ressource a été supprimée avec succès et qu'il n'y a pas de contenu à renvoyer.
        return Response(status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# # hairbnb/ai_service/ai_views.py
# from django.shortcuts import get_object_or_404
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from decorators.decorators import firebase_authenticated
# from .ai_service import AIService
# from .utils import get_database_context_for_query
# from ..models import AIConversation, AIMessage
#
#
# # Vue pour récupérer toutes les conversations d'un utilisateur
# @api_view(['GET'])
# @firebase_authenticated
# def get_conversations(request):
#     try:
#         # Récupérer l'utilisateur connecté
#         user = request.user
#
#         # Récupérer toutes les conversations de l'utilisateur
#         conversations = AIConversation.objects.filter(user=user).order_by('-created_at')
#
#         # Préparer les données pour la réponse
#         conversations_data = [{
#             'id': conv.id,
#             'created_at': conv.created_at.isoformat(),
#             'tokens_used': conv.tokens_used,
#             'last_message': conv.messages.last().content[:100] if conv.messages.exists() else None
#         } for conv in conversations]
#
#         return Response({'conversations': conversations_data})
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # Vue pour récupérer les messages d'une conversation spécifique
# @api_view(['GET'])
# @firebase_authenticated
# def get_conversation_messages(request, conversation_id):
#     try:
#         # Récupérer l'utilisateur connecté
#         user = request.user
#
#         # Récupérer la conversation spécifiée
#         conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)
#
#         # Récupérer tous les messages de la conversation
#         messages = conversation.messages.all().order_by('timestamp')
#
#         # Préparer les données pour la réponse
#         messages_data = [{
#             'id': msg.id,
#             'content': msg.content,
#             'is_user': msg.is_user,
#             'timestamp': msg.timestamp.isoformat(),
#             'tokens_in': msg.tokens_in,
#             'tokens_out': msg.tokens_out
#         } for msg in messages]
#
#         return Response({
#             'conversation_id': conversation.id,
#             'created_at': conversation.created_at.isoformat(),
#             'tokens_used': conversation.tokens_used,
#             'messages': messages_data
#         })
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # Vue pour créer une nouvelle conversation
# @api_view(['POST'])
# @firebase_authenticated
# def create_conversation(request):
#     try:
#         # Récupérer l'utilisateur connecté
#         user = request.user
#
#         # Créer une nouvelle conversation
#         conversation = AIConversation.objects.create(
#             user=user,
#             context_cache={},  # Initialiser avec un objet vide
#             tokens_used=0
#         )
#
#         return Response({
#             'conversation_id': conversation.id,
#             'created_at': conversation.created_at.isoformat()
#         }, status=status.HTTP_201_CREATED)
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# # Vue pour envoyer un message et obtenir une réponse
# @api_view(['POST'])
# @firebase_authenticated
# def send_message(request):
#     try:
#         # Extraire les données de la requête
#         data = request.data
#         conversation_id = data.get('conversation_id')
#         message_content = data.get('message')
#
#         if not message_content:
#             return Response({'error': 'Le message est requis'}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Récupérer l'utilisateur connecté
#         user = request.user
#
#         # Récupérer ou créer la conversation
#         if conversation_id:
#             conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)
#         else:
#             conversation = AIConversation.objects.create(
#                 user=user,
#                 context_cache={},
#                 tokens_used=0
#             )
#
#         # Initialiser le service IA
#         ai_service = AIService()
#
#         # Enregistrer le message de l'utilisateur
#         tokens_in = ai_service.count_tokens(message_content)
#         user_message = AIMessage.objects.create(
#             conversation=conversation,
#             content=message_content,
#             is_user=True,
#             tokens_in=tokens_in,
#             tokens_out=0
#         )
#
#         # Récupérer l'historique des messages pour le contexte
#         message_history = []
#         # Limiter à quelques messages récents pour économiser des tokens
#         recent_messages = conversation.messages.filter(id__lt=user_message.id).order_by('-timestamp')[:4]
#         for msg in reversed(list(recent_messages)):
#             role = "user" if msg.is_user else "assistant"
#             message_history.append({"role": role, "content": msg.content})
#
#         # Extraire le contexte de la base de données en fonction de la requête
#         db_context = get_database_context_for_query(message_content)
#
#         # Obtenir une réponse de l'IA
#         ai_result = ai_service.get_response(
#             query=message_content,
#             context=db_context,
#             message_history=message_history
#         )
#
#         # Extraire la réponse et les statistiques de tokens
#         ai_response = ai_result["response"]
#         tokens_data = ai_result.get("tokens", {"input": tokens_in, "output": 0, "total": tokens_in})
#
#         # Enregistrer la réponse de l'IA
#         ai_message = AIMessage.objects.create(
#             conversation=conversation,
#             content=ai_response,
#             is_user=False,
#             tokens_in=0,
#             tokens_out=tokens_data["output"]
#         )
#
#         # Mettre à jour le nombre total de tokens pour la conversation
#         conversation.tokens_used += tokens_data["total"]
#         conversation.save()
#
#         # Renvoyer la réponse
#         return Response({
#             'conversation_id': conversation.id,
#             'user_message_id': user_message.id,
#             'ai_message_id': ai_message.id,
#             'ai_response': ai_response,
#             'tokens': tokens_data
#         })
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @api_view(['DELETE'])
# @firebase_authenticated
# def delete_conversation(request, conversation_id):
#     try:
#         # Récupérer l'utilisateur connecté
#         user = request.user
#
#         # Récupérer la conversation spécifiée
#         conversation = get_object_or_404(AIConversation, id=conversation_id, user=user)
#
#         # Supprimer les messages associés à la conversation
#         conversation.messages.all().delete()
#
#         # Supprimer la conversation
#         conversation.delete()
#
#         return Response(
#             status=status.HTTP_204_NO_CONTENT)  # 204 No Content est le code standard pour une suppression réussie
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)