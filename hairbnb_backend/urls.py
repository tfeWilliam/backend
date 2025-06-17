from django.contrib import admin
from django.urls import path, include

from hairbnb import views
from hairbnb.views import home, check_user_profile, ServicesListView, add_or_update_service, \
    coiffeuse_services, list_coiffeuses
from hairbnb.salon_geolocalisation.salon_geolocalisation_views import get_all_salons

urlpatterns = [
    path('ghost/', admin.site.urls),
    path('api/check-user-profile/', views.views.check_user_profile, name='check_user_profile'),
    path('api/create_salon/', views.views.create_salon, name='create_salon'),
    path('api/services/', ServicesListView, name='services-list'),
    path('api/add_or_update_service/<int:service_id>/', views.add_or_update_service, name='add_or_update_service'),
    path('api/add_or_update_service/', views.views.add_or_update_service, name='add_or_update_service_without_id'),
    path('api/coiffeuse_services/<int:coiffeuse_id>/', coiffeuse_services, name='coiffeuse_services'),
    path('api/list_coiffeuses/', list_coiffeuses, name='list_coiffeuses'),
    path('api/salons-list/', get_all_salons, name='salons_list'),  # Endpoint pour lister tous les salons
    path('api/get_id_and_type_from_uuid/<str:uuid>/', views.views.get_id_and_type_from_uuid, name='get_id_and_type_from_uuid'),
    path('api/', include('hairbnb.urls.serializers_urls')),  # Inclure les routes de serializers_urls.py
    path('api/', include('hairbnb.promotion.promotion_urls')),  # Inclure les routes de promotion_urls.py
    path('api/', include('hairbnb.publicSalonDetail.urls')),  # Inclure les routes de publicSalonDetail_urls.py
    path('api/', include('hairbnb.gallery.gallery_urls')),  # Inclure les routes de gallery_urls.py
    path('api/', include('hairbnb.favorites.favorites_urls')),  # Inclure les routes de favorites_urls.py
    path('api/', include('hairbnb.currentUser.currentUser_urls')),  # Inclure les routes de currentUser_urls.py
    path('api/', include('hairbnb.card.card_urls')),  # Inclure les routes de card_urls.py
    path('api/', include('hairbnb.payment.payment_urls')),  # Inclure les routes de payment_urls.py
    path('api/', include('hairbnb.order.order_urls')),  # Inclure les routes de order_urls.py
    path('api/', include('hairbnb.emails.email_urls')),  # Inclure les routes de email_urls.py
    path('api/', include('hairbnb.ai_service.ai_urls')),  # Inclure les routes de ai_urls.py
    path('api/', include('hairbnb.profil.profil_urls')),  # Inclure les routes de profil_urls.py
    path('api/', include('hairbnb.coiffeuse.coiffeuse_urls')),  # Inclure les routes de coiffeuse_urls.py
    path('api/', include('hairbnb.salon.salon_urls')),  # Inclure les routes de salon_urls.py
    path('api/', include('hairbnb.salon_services.salon_services_urls')),  # Inclure les routes de salon_services_urls.py
    path('api/', include('hairbnb.salon_services.category_services.category_urls')),  # Inclure les routes de category_urls.py
    path('api/', include('hairbnb.salon_geolocalisation.salon_geolocalisation_urls')),  # Inclure les routes de salon_geolocalisation_urls.py
    path('api/', include('hairbnb.dispinibilites.disponibilite_urls')),  # Inclure les routes de disponibilites_urls.py
    path('api/coiffeuse/ai/', include('hairbnb.ai_service.coiffeuse_ai.coiffeuse_ai_urls')),  # Inclure les routes de coiffeuse_ai_urls.py
    path('api/', include('hairbnb.avis.avis_urls')),# Inclure les routes de avis_urls.py

]
