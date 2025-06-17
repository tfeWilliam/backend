from django.urls import path

from hairbnb.coiffeuse.coiffeuse_views import get_coiffeuses_info

urlpatterns = [
    path('get_coiffeuses_info/', get_coiffeuses_info, name="get_coiffeuses_info"),

]