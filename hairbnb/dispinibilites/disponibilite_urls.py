from django.urls import path

from hairbnb.dispinibilites.disponibilites_views import get_disponibilites_client, get_creneaux_jour

urlpatterns = [
    path('get_disponibilites_client/<int:coiffeuse_id>/',get_disponibilites_client,name='get_disponibilites_client'),

    path('get_creneaux_jour/<int:coiffeuse_id>/',get_creneaux_jour,name='get_creneaux_jour'),

]