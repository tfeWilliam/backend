# hairbnb/ai_service/ai_urls.py
from django.urls import path
from .ai_views import get_conversations, get_conversation_messages, create_conversation, send_message, \
    delete_conversation

urlpatterns = [
    path('conversations/', get_conversations, name='get_conversations'),
    path('conversations/<int:conversation_id>/messages/', get_conversation_messages, name='get_conversation_messages'),
    path('conversations/create/', create_conversation, name='create_conversation'),
    path('messages/send/', send_message, name='send_message'),
    path('delconversations/<int:conversation_id>/', delete_conversation, name='delete_conversation'),
]