from django.urls import path

from hairbnb.salon_services.category_services.category_views import (
    get_all_categories,
    get_category_with_services,
    get_services_by_category,
    create_service_with_category,
    add_existing_service_with_category,
    get_salon_services_by_category
)

urlpatterns = [
    # Routes pour les catégories
    path('categories/', get_all_categories, name='get_all_categories'),
    path('categories/<int:category_id>/', get_category_with_services, name='get_category_with_services'),
    path('categories/<int:category_id>/services/', get_services_by_category, name='get_services_by_category'),
    
    # Routes pour la gestion des services avec catégories
    path('services/create-with-category/', create_service_with_category, name='create_service_with_category'),
    path('services/add-existing-with-category/', add_existing_service_with_category, name='add_existing_service_with_category'),
    
    # Routes pour les services du salon
    path('salon/services-by-category/', get_salon_services_by_category, name='get_salon_services_by_category'),
]
