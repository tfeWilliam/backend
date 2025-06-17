# # hairbnb/views/rendezvous_views.py

from datetime import timedelta
from django.utils.timezone import now
from rest_framework.decorators import api_view
from rest_framework.response import Response

from hairbnb.models import TblCoiffeuse, TblRendezVous
from hairbnb.serializers.reservation_light_serializers import ReservationLightSerializer
from hairbnb.utils.archive_rdv import archive_rendezvous_if_needed
from hairbnb.utils.pagination import CustomPagination
from hairbnb.business.business_logic import RendezVousManager

@api_view(['GET'])
def get_rendezvous_by_coiffeuse_id(request, coiffeuse_id):
    archive_rendezvous_if_needed()

    try:
        TblCoiffeuse.objects.get(idTblUser__idTblUser=coiffeuse_id)
    except TblCoiffeuse.DoesNotExist:
        return Response({"error": "Coiffeuse introuvable"}, status=404)

    periode = request.query_params.get("periode")
    statut = request.query_params.get("statut")

    manager = RendezVousManager(coiffeuse_id)
    queryset = manager.get_by_periode(periode, statut) if periode else manager.get_by_statut(statut)

    paginator = CustomPagination()
    page = paginator.paginate_queryset(queryset, request)

    # 🛠 Bloc de débogage ici
    try:
        data = ReservationLightSerializer(page, many=True).data
    except Exception as e:
        import traceback
        traceback.print_exc()  # affiche l'erreur dans la console
        return Response({'error': str(e)}, status=500)

    return paginator.get_paginated_response(data)


# hairbnb/views/rendezvous_views.py (suite)

@api_view(['GET'])
def get_archived_rendezvous_by_coiffeuse_id(request, coiffeuse_id):
    """
    📂 Endpoint : /api/get_archived_rendezvous_by_coiffeuse_id/<int:coiffeuse_id>/?periode=mois
    🔎 Retourne les rendez-vous archivés d’une coiffeuse, paginés + filtrés par période (optionnel)
    """
    try:
        TblCoiffeuse.objects.get(idTblUser__idTblUser=coiffeuse_id)
    except TblCoiffeuse.DoesNotExist:
        return Response({"error": "Coiffeuse introuvable"}, status=404)

    periode = request.query_params.get("periode")
    today = now().date()

    if periode == "jour":
        start = today
        end = today + timedelta(days=1)
    elif periode == "semaine":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
    elif periode == "mois":
        start = today.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
    elif periode == "annee":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
    else:
        start = end = None

    queryset = TblRendezVous.objects.filter(
        coiffeuse__idTblUser=coiffeuse_id,
        est_archive=True
    )
    if start and end:
        queryset = queryset.filter(date_heure__date__range=(start, end))

    queryset = queryset.order_by('-date_heure')

    paginator = CustomPagination()
    page = paginator.paginate_queryset(queryset, request)

    # 🛠 Bloc de débogage ici
    try:
        data = ReservationLightSerializer(page, many=True).data
    except Exception as e:
        import traceback
        traceback.print_exc()  # affiche l'erreur dans la console
        return Response({'error': str(e)}, status=500)

    return paginator.get_paginated_response(data)