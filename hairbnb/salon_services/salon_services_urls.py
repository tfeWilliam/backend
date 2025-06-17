from django.urls import path

from hairbnb.salon_services.salon_services_views import add_existing_service_to_salon, search_global_services, \
    remove_service_from_salon, services_dropdown_list, update_service, get_salon_services, \
    get_salon_services_by_salon_id, get_services_by_coiffeuse
from hairbnb.salon_services.services_views import get_all_services, create_new_global_service

urlpatterns = [
    path('services/all/', get_all_services, name='get_all_services'),
    path('services/search/', search_global_services, name='search_global_services'),
    path('services/add-existing/', add_existing_service_to_salon, name='add_existing_service_to_salon'),
    path('services/create-new/', create_new_global_service, name='create_new_global_service'),
    path('services/salon/', get_salon_services, name='get_salon_services'),
    path('services/dropdown/', services_dropdown_list, name='services_dropdown_list'),

    path('get_services_by_coiffeuse/<int:coiffeuse_id>/', get_services_by_coiffeuse, name='get_services_by_coiffeuse'),
    path('services/remove/<int:salon_service_id>/', remove_service_from_salon, name='remove_service_from_salon'),
    path('update_service/<int:service_id>/', update_service, name='update_service'),
    path('salon/<int:salon_id>/services-by-category/', get_salon_services_by_salon_id, name='get_salon_services_by_salon_id')
]