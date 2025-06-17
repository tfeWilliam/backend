from django.urls import path

from hairbnb.promotion.promotion_views import create_promotion, delete_promotion, get_promotions_for_service, \
    update_promotion

urlpatterns = [
    path('salon/<int:salon_id>/service/<int:service_id>/promotion/', create_promotion, name="create_promotion"),
    path('get_promotions_for_service/<int:service_id>/', get_promotions_for_service, name="get_promotions_for_service"),
    path('salon/<int:salon_id>/service/<int:service_id>/promotion/<int:promotion_id>/', update_promotion, name="update_promotion"),
    path('delete_promotion/<int:promotion_id>/', delete_promotion, name='delete_promotion'),

]