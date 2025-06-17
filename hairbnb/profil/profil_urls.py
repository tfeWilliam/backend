from django.urls import path

from hairbnb.profil.profil_views import get_user_profile, update_user_phone, update_user_address, create_user_profile, \
    delete_user_profile, delete_my_profile_firebase

urlpatterns = [

    path('get_user_profile/<str:userUuid>/', get_user_profile, name='get_user_profile'),
    path('create-profile/', create_user_profile, name='create_user_profile'),
    path('update_user_phone/<str:uuid>/', update_user_phone, name='update_user_phone'),

    path('users/<str:uuid>/address/', update_user_address, name='update_user_address'),

    path('delete_my_profile_firebase/', delete_my_profile_firebase, name='delete_my_profile_firebase'),

    path('delete-user-profile/<int:idTblUser>/', delete_user_profile, name='delete_profile'),
]