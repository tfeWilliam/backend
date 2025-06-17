from django.urls import path

from hairbnb.order.order_views import mes_commandes, commandes_coiffeuse, update_statut_commande, \
    update_date_heure_commande

urlpatterns = [
    path('mes-commandes/<int:idUser>/', mes_commandes, name='mes_commandes'),

    # Récupérer les commandes d'une coiffeuse
    path('coiffeuse-commandes/<int:idUser>/', commandes_coiffeuse, name='commandes_coiffeuse'),

    # Mettre à jour le statut d'une commande
    path('update-statut-commande/<int:idRendezVous>/', update_statut_commande, name='update_statut_commande'),

    # Mettre à jour la date et l'heure d'une commande
    path('update-date-heure-commande/<int:idRendezVous>/', update_date_heure_commande,
         name='update_date_heure_commande'),
]