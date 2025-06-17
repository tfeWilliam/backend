# hairbnb/ai_service/coiffeuse_ai_urls.py
from django.urls import path
from . import coiffeuse_ai_views

urlpatterns = [
    # Routes spécifiques pour les coiffeuses propriétaires
    path('conversations/', coiffeuse_ai_views.get_coiffeuse_conversations, name='get_coiffeuse_conversations'),
    path('conversations/<int:conversation_id>/messages/', coiffeuse_ai_views.get_coiffeuse_conversation_messages, name='get_coiffeuse_conversation_messages'),
    path('conversations/create/', coiffeuse_ai_views.create_coiffeuse_conversation, name='create_coiffeuse_conversation'),
    path('messages/send/', coiffeuse_ai_views.send_coiffeuse_message, name='send_coiffeuse_message'),
    path('conversations/<int:conversation_id>/', coiffeuse_ai_views.delete_coiffeuse_conversation, name='delete_coiffeuse_conversation'),
]