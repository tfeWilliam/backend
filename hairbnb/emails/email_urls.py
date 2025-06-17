# Fichier: urls.py (ajoutez à votre configuration d'URL existante)

from django.urls import path

from hairbnb.emails.email_views import EmailNotificationAPIView

urlpatterns = [
    # Autres URLs...
    path('email-notifications/', EmailNotificationAPIView.as_view(), name='email_notifications'),
]