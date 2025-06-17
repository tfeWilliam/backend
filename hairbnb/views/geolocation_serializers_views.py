from django.http import JsonResponse
from hairbnb.models import TblCoiffeuse
from math import radians, cos, sin, sqrt, atan2

from hairbnb.profil.profil_serializers import CoiffeuseSerializer


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcul de la distance entre deux points en kilomètres avec la formule de Haversine.
    """
    R = 6371  # Rayon moyen en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def coiffeuses_proches(request):
    """
    Récupère les coiffeuses proches d'une position donnée selon une distance max.
    """
    try:
        lat_client = float(request.GET.get('lat', 0))  # Latitude du client
        lon_client = float(request.GET.get('lon', 0))  # Longitude du client
        distance_max = float(request.GET.get('distance', 10))  # Distance max en km

        coiffeuses = []
        for coiffeuse in TblCoiffeuse.objects.all():
            if coiffeuse.position:
                try:
                    lat_coiffeuse, lon_coiffeuse = map(float, coiffeuse.position.split(","))
                    distance = haversine(lat_client, lon_client, lat_coiffeuse, lon_coiffeuse)

                    if distance <= distance_max:
                        coiffeuses.append(coiffeuse)
                except ValueError:
                    print(f"⚠️ Erreur conversion position pour {coiffeuse.idTblUser.nom}")

        serialized_coiffeuses = CoiffeuseSerializer(coiffeuses, many=True).data

        return JsonResponse({"status": "success", "coiffeuses": serialized_coiffeuses})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
