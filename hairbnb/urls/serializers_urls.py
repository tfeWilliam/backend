from django.urls import path

from hairbnb.views.coiffeuse_rdvs_by_id_view import get_rendezvous_by_coiffeuse_id, \
    get_archived_rendezvous_by_coiffeuse_id
from hairbnb.views.geolocation_serializers_views import coiffeuses_proches
#from hairbnb.views.geolocation_serializers_views import coiffeuses_proches
from hairbnb.views.horaire_serializers_views import get_horaires_coiffeuse, set_horaire_coiffeuse, \
    delete_horaire_coiffeuse
from hairbnb.views.indisponibilite_coiffeuse_views import get_indisponibilites, update_indisponibilite, \
    delete_indisponibilite, add_indisponibilite
#from hairbnb.payment.paiement_serializerss import create_payment_intent
from hairbnb.views.rdvs_serializers_views import create_rendez_vous
from hairbnb.views.salon_services_serializers_views import delete_service, add_service_to_coiffeuse
from hairbnb.views.users_serializers_views import get_coiffeuse_by_uuid, get_client_by_uuid, update_coiffeuse, \
    update_client

urlpatterns = [
    path('get_coiffeuse_by_uuid/<str:uuid>/', get_coiffeuse_by_uuid, name='get_coiffeuse_by_uuid'),
    path('get_client_by_uuid/<str:uuid>/', get_client_by_uuid, name='get_client_by_uuid'),
    path('update_coiffeuse/<str:uuid>/', update_coiffeuse, name='update_coiffeuse'),
    path('update_client/<str:uuid>/', update_client, name='update_client'),
    # path('get_services_by_coiffeuse/<int:coiffeuse_id>/', get_services_by_coiffeuse, name='get_services_by_coiffeuse'),
    path('add_service_to_coiffeuse/<int:coiffeuse_id>/', add_service_to_coiffeuse, name='add_service_to_coiffeuse'),
    # path('update_service/<int:service_id>/', update_service, name='update_service'),
    path('delete_service/<int:service_id>/', delete_service, name='delete_service'),
    path('coiffeuses_proches/', coiffeuses_proches, name='coiffeuses_proches'),
    #path('get_current_user/<str:uuid>/', get_current_user, name='get_current_user'),
    #path('get_coiffeuses_info/', get_coiffeuses_info, name="get_coiffeuses_info"),
    # path('get_cart/<int:user_id>/', get_cart, name="get_cart" ),
    # path('add_to_cart/', add_to_cart, name="add_to_cart"),
    # path('remove_from_cart/', remove_from_cart, name="remove_from_cart"),
    # path('clear_cart/', clear_cart, name="clear_cart"),
    # path('create_promotion/<int:service_id>/', create_promotion, name="create_promotion"),
    path('create_rendez_vous/', create_rendez_vous, name="create_rendez_vous"),
    #path("create_payment/", create_payment_intent, name="create_payment"),
    path('get_indisponibilites/<int:coiffeuse_id>/', get_indisponibilites, name='get_indisponibilites'),
    path('add_indisponibilite/', add_indisponibilite, name='add_indisponibilite'),
    path('update_indisponibilite/<int:indispo_id>/', update_indisponibilite, name='update_indisponibilite'),
    path('delete_indisponibilite/<int:indispo_id>/', delete_indisponibilite, name='delete_indisponibilite'),
    path('get_horaires_coiffeuse/<int:coiffeuse_id>/', get_horaires_coiffeuse, name='get_horaires_coiffeuse'),
    path('set_horaire_coiffeuse/', set_horaire_coiffeuse, name='set_horaire_coiffeuse'),
    path('delete_horaire_coiffeuse/<int:coiffeuse_id>/<int:jour>/', delete_horaire_coiffeuse,name='delete_horaire_coiffeuse'),
    # path('get_disponibilites_client/<int:idUser>/', get_disponibilites_client, name='get_disponibilites_client'),
    path('get_rendezvous_by_coiffeuse_id/<int:coiffeuse_id>/', get_rendezvous_by_coiffeuse_id, name='get_rendezvous_by_coiffeuse_id'),
    path('get_archived_rendezvous_by_coiffeuse_id/<int:coiffeuse_id>/',
     get_archived_rendezvous_by_coiffeuse_id,name='get_archived_rendezvous_by_coiffeuse_id'),
    # path('ajout_salon_serializer_view/', ajout_salon_serializer_view, name='ajout_salon'),
    #path('get_salon_by_coiffeuse/<int:coiffeuse_id>/', get_salon_by_coiffeuse, name='get_salon_by_coiffeuse'),
    # path('add_images_to_salon/', add_images_to_salon, name='add_images_to_salon'),
]
