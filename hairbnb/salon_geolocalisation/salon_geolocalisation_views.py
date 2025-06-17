################################################################################
#                                                                              #
#        VUES API POUR LA GÉOLOCALISATION ET LA CONSULTATION DES SALONS          #
#                                                                              #
#  Ce fichier contient les vues API relatives à la recherche de salons,        #
#  notamment basées sur la proximité géographique.                             #
#                                                                              #
#  Fonctionnalités :                                                           #
#    - `haversine`: Une fonction utilitaire pour calculer la distance entre    #
#      deux points GPS.                                                        #
#    - `salons_proches`: Retourne les salons dans un rayon donné autour d'une  #
#      position client.                                                        #
#    - `get_salon_details`: Fournit les détails complets d'un salon spécifique.#
#    - `get_all_salons`: Retourne une liste de tous les salons existants.      #
#                                                                              #
################################################################################


from django.http import JsonResponse

from decorators.decorators import firebase_authenticated
from hairbnb.models import TblSalon, TblCoiffeuseSalon
from math import radians, cos, sin, sqrt, atan2

from hairbnb.salon_geolocalisation.salon_geolocalisation_serializers import SalonSerializer


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points géographiques (latitude, longitude)
    en utilisant la formule de Haversine, qui tient compte de la courbure de la Terre.

    Args:
        lat1 (float): Latitude du premier point.
        lon1 (float): Longitude du premier point.
        lat2 (float): Latitude du second point.
        lon2 (float): Longitude du second point.

    Returns:
        float: La distance entre les deux points en kilomètres.
    """
    R = 6371  # Rayon moyen de la Terre en kilomètres
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


################################################################################
#           VUE POUR TROUVER LES SALONS PROCHES D'UNE POSITION DONNÉE          #
################################################################################

@firebase_authenticated
def salons_proches(request):
    """
    Récupère une liste de salons situés dans un rayon de distance maximal
    par rapport à une position GPS fournie par le client.
    Nécessite une authentification Firebase pour être utilisée.
    """
    try:
        # Étape 1 : Récupération et conversion des paramètres de la requête GET.
        lat_client = float(request.GET.get('lat', 0))
        lon_client = float(request.GET.get('lon', 0))
        distance_max = float(request.GET.get('distance', 10))  # Distance en km

        salons_eligibles = []

        # Étape 2 : Itération sur tous les salons de la base de données.
        # Note : Pour de grandes bases de données, une requête géospatiale (ex: PostGIS)
        # serait beaucoup plus performante.
        for salon in TblSalon.objects.all():
            if salon.position and salon.position != "0,0":
                try:
                    # Extraction des coordonnées GPS du salon depuis le champ texte.
                    lat_salon, lon_salon = map(float, salon.position.split(","))

                    # Calcul de la distance entre le client et le salon.
                    distance = haversine(lat_client, lon_client, lat_salon, lon_salon)

                    # Si le salon est dans le rayon souhaité, on le garde.
                    if distance <= distance_max:
                        # Ajout de la distance calculée comme attribut temporaire à l'objet.
                        salon.distance = round(distance, 2)
                        salons_eligibles.append(salon)
                except ValueError:
                    # Gère le cas où le champ `position` du salon est mal formaté.
                    print(f"⚠️ Erreur de conversion de la position pour le salon {salon.nom_salon}")

        # Étape 3 : Tri des salons trouvés par ordre de distance croissante.
        salons_eligibles.sort(key=lambda s: getattr(s, 'distance', float('inf')))

        # Étape 4 : Sérialisation des données et ajout manuel de la distance.
        # Le serializer ne connaît pas l'attribut `distance` ajouté dynamiquement.
        serialized_data = []
        for salon in salons_eligibles:
            salon_data = SalonSerializer(salon).data
            salon_data['distance'] = getattr(salon, 'distance', 0)
            serialized_data.append(salon_data)

        # Étape 5 : Retour de la réponse JSON finale.
        return JsonResponse({
            "status": "success",
            "count": len(salons_eligibles),
            "salons": serialized_data
        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


################################################################################
#                VUE POUR OBTENIR LES DÉTAILS D'UN SALON SPÉCIFIQUE            #
################################################################################

@firebase_authenticated
def get_salon_details(request, salon_id):
    """
    Récupère et retourne les informations détaillées d'un seul salon,
    y compris les détails des coiffeuses qui y travaillent.
    """
    try:
        # Récupération du salon par son ID.
        salon = TblSalon.objects.get(idTblSalon=salon_id)

        # Utilisation du serializer pour obtenir les données de base du salon.
        salon_data = SalonSerializer(salon).data

        # Note : La logique ci-dessous pour récupérer les détails des coiffeuses est
        # redondante car `SalonSerializer` le fait déjà. Cette section surcharge
        # les données du serializer avec une structure légèrement différente.
        coiffeuses_data = []
        relations = TblCoiffeuseSalon.objects.filter(salon=salon)

        for relation in relations:
            coiffeuse = relation.coiffeuse
            user = coiffeuse.idTblUser

            coiffeuses_data.append({
                "idTblCoiffeuse": coiffeuse.idTblUser.idTblUser,
                "nom": user.nom,
                "prenom": user.prenom,
                "photo_profil": request.build_absolute_uri(user.photo_profil.url) if user.photo_profil else None,
                "est_proprietaire": relation.est_proprietaire,
                "nom_commercial": coiffeuse.nom_commercial
            })

        # Remplacement des détails des coiffeuses dans la réponse finale.
        salon_data['coiffeuses_details'] = coiffeuses_data

        return JsonResponse({
            "status": "success",
            "salon": salon_data
        })

    # Gestion de l'erreur si le salon n'existe pas.
    except TblSalon.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "Salon non trouvé"
        }, status=404)
    # Gestion des autres erreurs potentielles.
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


################################################################################
#                  VUE POUR OBTENIR LA LISTE DE TOUS LES SALONS                #
################################################################################

@firebase_authenticated
def get_all_salons(request):
    """
    Récupère une liste complète de tous les salons disponibles, sans filtre
    ni authentification.
    """
    try:
        # Récupération de tous les objets TblSalon.
        salons = TblSalon.objects.all()

        # Sérialisation de la liste des salons.
        # Utiliser `many=True` dans le serializer serait plus direct :
        # `SalonSerializer(salons, many=True).data`
        serialized_data = []
        for salon in salons:
            salon_data = SalonSerializer(salon).data
            serialized_data.append(salon_data)

        return JsonResponse({
            "status": "success",
            "count": len(salons),
            "salons": serialized_data
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)







# from django.http import JsonResponse
#
# from decorators.decorators import firebase_authenticated
# from hairbnb.models import TblSalon, TblCoiffeuseSalon
# from math import radians, cos, sin, sqrt, atan2
#
# from hairbnb.salon_geolocalisation.salon_geolocalisation_serializers import SalonSerializer
#
#
# def haversine(lat1, lon1, lat2, lon2):
#     """
#     Calcul de la distance entre deux points en kilomètres avec la formule de Haversine.
#     """
#     R = 6371  # Rayon moyen de la Terre en km
#     dlat = radians(lat2 - lat1)
#     dlon = radians(lon2 - lon1)
#     a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
#     return R * c
#
#
# @firebase_authenticated
# def salons_proches(request):
#     """
#     Récupère les salons proches d'une position donnée selon une distance max.
#     Nécessite une authentification Firebase.
#     """
#     try:
#         # Récupération des paramètres
#         lat_client = float(request.GET.get('lat', 0))  # Latitude du client
#         lon_client = float(request.GET.get('lon', 0))  # Longitude du client
#         distance_max = float(request.GET.get('distance', 10))  # Distance max en km
#
#         # Liste pour stocker les salons proches
#         salons = []
#
#         # Parcourir tous les salons
#         for salon in TblSalon.objects.all():
#             if salon.position and salon.position != "0,0":
#                 try:
#                     # Extraire coordonnées du salon
#                     lat_salon, lon_salon = map(float, salon.position.split(","))
#
#                     # Calculer la distance
#                     distance = haversine(lat_client, lon_client, lat_salon, lon_salon)
#
#                     # Si le salon est dans le rayon demandé
#                     if distance <= distance_max:
#                         # Stocker la distance comme attribut temporaire
#                         salon.distance = round(distance, 2)
#                         salons.append(salon)
#                 except ValueError:
#                     print(f"⚠️ Erreur conversion position pour salon {salon.nom_salon}")
#
#         # Trier les salons par distance
#         salons.sort(key=lambda s: getattr(s, 'distance', float('inf')))
#
#         # Créer une liste pour stocker les résultats sérialisés
#         serialized_data = []
#
#         # Sérialiser chaque salon et ajouter la distance
#         for salon in salons:
#             salon_data = SalonSerializer(salon).data
#             salon_data['distance'] = getattr(salon, 'distance', 0)
#             serialized_data.append(salon_data)
#
#         # Retourner la réponse JSON
#         return JsonResponse({
#             "status": "success",
#             "count": len(salons),
#             "salons": serialized_data
#         })
#
#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=400)
#
#
# @firebase_authenticated
# def get_salon_details(request, salon_id):
#     """
#     Récupère les détails d'un salon spécifique.
#     Nécessite une authentification Firebase.
#     """
#     try:
#         # Récupérer le salon
#         salon = TblSalon.objects.get(idTblSalon=salon_id)
#
#         # Sérialiser le salon
#         salon_data = SalonSerializer(salon).data
#
#         # Récupérer les détails des coiffeuses qui travaillent dans ce salon
#         coiffeuses_data = []
#         relations = TblCoiffeuseSalon.objects.filter(salon=salon)
#
#         for relation in relations:
#             coiffeuse = relation.coiffeuse
#             user = coiffeuse.idTblUser
#
#             coiffeuses_data.append({
#                 "idTblCoiffeuse": coiffeuse.idTblUser.idTblUser,
#                 "nom": user.nom,
#                 "prenom": user.prenom,
#                 "photo_profil": request.build_absolute_uri(user.photo_profil.url) if user.photo_profil else None,
#                 "est_proprietaire": relation.est_proprietaire,
#                 "nom_commercial": coiffeuse.nom_commercial
#             })
#
#         # Ajouter les informations des coiffeuses au salon
#         salon_data['coiffeuses_details'] = coiffeuses_data
#
#         return JsonResponse({
#             "status": "success",
#             "salon": salon_data
#         })
#
#     except TblSalon.DoesNotExist:
#         return JsonResponse({
#             "status": "error",
#             "message": "Salon non trouvé"
#         }, status=404)
#     except Exception as e:
#         return JsonResponse({
#             "status": "error",
#             "message": str(e)
#         }, status=500)
#
#
# def get_all_salons(request):
#     """
#     Récupère tous les salons disponibles.
#     """
#     try:
#         # Récupérer tous les salons
#         salons = TblSalon.objects.all()
#
#         # Sérialiser tous les salons
#         serialized_data = []
#         for salon in salons:
#             salon_data = SalonSerializer(salon).data
#             serialized_data.append(salon_data)
#
#         return JsonResponse({
#             "status": "success",
#             "count": len(salons),
#             "salons": serialized_data
#         })
#
#     except Exception as e:
#         return JsonResponse({
#             "status": "error",
#             "message": str(e)
#         }, status=500)