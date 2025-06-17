from django.urls import path

from hairbnb.publicSalonDetail.view import PublicSalonDetailsView

urlpatterns = [
    # Détails d'un salon spécifique
    path('salons/<int:salon_id>/', PublicSalonDetailsView.as_view(), name='salon-detail'),
    # Liste de tous les salons
    path('salons/', PublicSalonDetailsView.as_view(), name='salon-list'),

]