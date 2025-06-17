from django.urls import path

from hairbnb.payment import paiement_views
from hairbnb.payment.paiement_views import stripe_webhook, rembourser_paiement, paiement_info

urlpatterns = [
    # Création de la session de paiement Stripe
    path('paiement/create-checkout-session/', paiement_views.create_checkout_session, name='create_checkout_session'),

    # Webhook Stripe pour mise à jour automatique après paiement
    path('webhook/', stripe_webhook, name='stripe-webhook'),

    # Vérification du statut de paiement (pour Flutter)
    path('paiement/status/<int:rendez_vous_id>/', paiement_views.check_payment_status, name='check_payment_status'),

    # Succès du paiement
    path('paiement-success/', paiement_views.paiement_success, name='paiement_success'),

    # Erreur de paiement
    path('paiement-error/', paiement_views.paiement_error, name='paiement_error'),

    # Rembourser un paiement
    path('remboursement/', rembourser_paiement, name='remboursement-stripe'),

    # Informations sur un paiement
    path('paiement-info/<int:id_rendez_vous>/', paiement_info, name='paiement_info'),
]