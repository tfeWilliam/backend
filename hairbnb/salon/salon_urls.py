from django.urls import path

from hairbnb.salon.salon_views import get_salon_by_coiffeuse, ajout_salon

urlpatterns = [
    path('get_salon_by_coiffeuse/<int:coiffeuse_id>/', get_salon_by_coiffeuse, name='get_salon_by_coiffeuse'),
    path('ajout_salon/', ajout_salon, name='ajout_salon'),

]