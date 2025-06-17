from django.urls import path

from hairbnb.favorites.favorites_views import get_favorites, add_favorite, remove_favorite, get_user_favorites, \
    check_favorite

urlpatterns = [
    path('favorites/', get_favorites),
    path('favorites/add/', add_favorite),
    path('favorites/remove/', remove_favorite, name='remove_favorite'),
    path('get_user_favorites/', get_user_favorites, name='get_user_favorites'),
    path('check_favorite/', check_favorite, name='check_favorite'),

]