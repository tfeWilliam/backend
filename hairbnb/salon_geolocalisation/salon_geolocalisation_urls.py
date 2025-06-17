from django.urls import path

from hairbnb.salon_geolocalisation.salon_geolocalisation_views import get_salon_details, salons_proches, get_all_salons

urlpatterns = [
    # URLs nécessitant une authentification Firebase
    path('salons-proches-public/', salons_proches, name='salons_proches'),
    path('salon-public/<int:salon_id>/', get_salon_details, name='get_salon_details'),
    path('salons-list/', get_all_salons, name='get_all_salons'),

]