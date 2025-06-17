from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from hairbnb.gallery.gallery_views import SalonImageListView, SalonImageDeleteView, add_images_to_salon

urlpatterns = [
    path('salon/<int:salon_id>/images/', SalonImageListView.as_view(), name='salon-image-list'),
    path('add_images_to_salon/', add_images_to_salon, name='add_images_to_salon'),
    path('salon/images/<int:id>/delete/', SalonImageDeleteView.as_view(), name='salon-image-delete'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
