from django.urls import path

from hairbnb.currentUser.currentUser_views import get_current_user, get_user_by_id

urlpatterns = [
    path('get_current_user/', get_current_user, name='get_current_user'),
    path('get_user_by_id/<int:id>/', get_user_by_id, name='get_user_by_id'),

]