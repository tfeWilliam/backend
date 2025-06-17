from django.urls import path

from hairbnb.card.card_views import get_cart, add_to_cart, remove_from_cart, clear_cart

urlpatterns = [
    path('get_cart/<int:user_id>/', get_cart, name="get_cart"),
    path('add_to_cart/', add_to_cart, name="add_to_cart"),
    path('remove_from_cart/', remove_from_cart, name="remove_from_cart"),
    path('clear_cart/', clear_cart, name="clear_cart"),

]