import logging
from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

import json
from hairbnb.models import TblAdresse, TblRue, TblLocalite, TblCoiffeuse, TblClient, TblUser, TblServiceTemps, TblServicePrix, \
    TblPrix, TblTemps, TblService, TblSalon
from hairbnb.services.geolocation_service import GeolocationService
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return HttpResponse("Bienvenue sur l'API Hairbnb!")


@csrf_exempt
# ++++++++++++++++++++++++++++++++++++++Importanbt+++++++++++++++++++++++++++++++++++++++++++++
#### ATTENTION : A MODIFIER : A ne pas laissé ainsi en production,
# car cela peut entrainer des attaques de type Cross-Site Scripting (XSS),
# ce qui pourrait permettre aux attaquants de injecter du code malveillant dans la page web.
# Donc ce qu'il faut changer a la production est de modifier le decorator csrf_exempt par @csrf_protect
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@csrf_exempt
def get_id_and_type_from_uuid(request, uuid):
    try:
        # Rechercher l'utilisateur par UUID
        user = get_object_or_404(TblUser, uuid=uuid)

        # Retourner l'id et le type de l'utilisateur
        return JsonResponse({
            'success': True,
            'idTblUser': user.idTblUser,
            'type': user.type,  # Ajout du type
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

#*************************************************************************************************************



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

logger = logging.getLogger(__name__)

@csrf_exempt
def create_salon(request):
    """
    Crée un salon pour une coiffeuse en fonction des données envoyées via une requête POST.
    """
    if request.method == 'POST':
        try:
            # Déterminez si les données sont envoyées sous forme JSON ou via un formulaire (POST multipart)
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST

            # Logs pour débogage
            print("Requête reçue :", data)
            print("Fichiers reçus :", request.FILES)

            # Champs obligatoires
            user_uuid = data.get('userUuid')
            slogan = data.get('slogan')
            logo = request.FILES.get('logo_salon')  # Fichier logo

            # Validation des champs
            if not user_uuid or not slogan:
                return JsonResponse(
                    {"status": "error", "message": "UUID utilisateur et slogan sont obligatoires"},
                    status=400
                )

            # Vérifiez si l'utilisateur existe
            user = TblUser.objects.filter(uuid=user_uuid, type='coiffeuse').first()
            if not user:
                return JsonResponse(
                    {"status": "error", "message": "Utilisateur introuvable ou non autorisé"},
                    status=404
                )

            # Vérifiez si la coiffeuse existe
            coiffeuse = TblCoiffeuse.objects.filter(idTblUser=user).first()
            if not coiffeuse:
                return JsonResponse(
                    {"status": "error", "message": "Coiffeuse introuvable"},
                    status=404
                )

            # Créez ou mettez à jour le salon
            salon, created = TblSalon.objects.update_or_create(
                coiffeuse=coiffeuse,
                defaults={
                    'slogan': slogan,
                    'logo_salon': logo
                }
            )

            message = "Salon créé avec succès" if created else "Salon mis à jour avec succès"
            return JsonResponse(
                {"status": "success", "message": message, "salon_id": salon.idTblSalon},
                status=201
            )

        except Exception as e:
            print(f"Erreur : {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)

#*************************************************************************************************************

@csrf_exempt
def add_or_update_service(request, service_id=None):
    if request.method in ['POST', 'PUT']:
        try:
            # Log le corps brut de la requête
            logging.info(f"Requête reçue avec le corps brut : {request.body}")

            # Décoder les données JSON
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                logging.error("Erreur de décodage JSON.")
                return JsonResponse({'status': 'error', 'message': 'Format JSON invalide.'}, status=400)

            logging.info(f"Données JSON décodées : {data}")

            # Extraction des champs
            name = data.get('intitule_service') or data.get('name')
            description = data.get('description')
            minutes = data.get('temps_minutes') or data.get('minutes')
            price = data.get('prix') or data.get('price')

            logging.info(f"Champs extraits : name={name}, description={description}, minutes={minutes}, price={price}")

            # Vérification des champs obligatoires pour ajout
            if not service_id and not all([name, description, minutes, price]):
                logging.warning("Champs obligatoires manquants pour un nouveau service.")
                return JsonResponse({'status': 'error', 'message': 'Tous les champs sont obligatoires pour ajouter un nouveau service.'}, status=400)

            # Validation des types
            try:
                if minutes is not None:
                    minutes = int(minutes)
                if price is not None:
                    price = float(price)
            except ValueError:
                logging.warning("Minutes ou prix ont des valeurs invalides.")
                return JsonResponse({'status': 'error', 'message': 'Les champs minutes et prix doivent être numériques.'}, status=400)

            # Mise à jour
            if service_id:
                try:
                    service = TblService.objects.get(idTblService=service_id)
                except TblService.DoesNotExist:
                    logging.warning(f"Service avec ID {service_id} introuvable.")
                    return JsonResponse({'status': 'error', 'message': 'Service introuvable.'}, status=404)

                if name:
                    service.intitule_service = name
                if description:
                    service.description = description
                service.save()

                if minutes is not None:
                    TblServiceTemps.objects.filter(service=service).delete()
                    TblServiceTemps.objects.create(service=service, temps=TblTemps.objects.get_or_create(minutes=minutes)[0])
                if price is not None:
                    TblServicePrix.objects.filter(service=service).delete()
                    TblServicePrix.objects.create(service=service, prix=TblPrix.objects.get_or_create(prix=price)[0])

                logging.info("Service mis à jour avec succès.")
                return JsonResponse({'status': 'success', 'message': 'Service mis à jour avec succès.'}, status=200)

            # Ajout
            else:
                service = TblService.objects.create(
                    intitule_service=name,
                    description=description
                )
                TblServiceTemps.objects.create(service=service, temps=TblTemps.objects.create(minutes=minutes))
                TblServicePrix.objects.create(service=service, prix=TblPrix.objects.create(prix=price))

                logging.info("Nouveau service ajouté avec succès.")
                return JsonResponse({'status': 'success', 'message': 'Service ajouté avec succès.'}, status=201)

        except Exception as e:
            logging.error(f"Erreur serveur : {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Erreur serveur : {str(e)}'}, status=500)

    logging.warning("Méthode non autorisée.")
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée.'}, status=405)


@csrf_exempt
def list_coiffeuses(request):
    """
    Vue pour lister les coiffeuses disponibles avec leurs informations détaillées.
    """
    if request.method == 'GET':
        try:
            # Récupérer toutes les coiffeuses actives avec les informations liées
            coiffeuses = TblCoiffeuse.objects.select_related('idTblUser').all()

            # Préparer les données pour la réponse JSON
            data = []
            for coiffeuse in coiffeuses:
                user = coiffeuse.idTblUser
                data.append({
                    'id': coiffeuse.id,
                    'uuid': user.uuid,
                    'nom': user.nom,
                    'prenom': user.prenom,
                    'email': user.email,
                    'numero_telephone': user.numero_telephone,
                    'photo_profil': user.photo_profil.url if user.photo_profil else None,
                    'denomination_sociale': coiffeuse.denomination_sociale,
                    'tva': coiffeuse.tva,
                    'position': coiffeuse.position,
                })

            return JsonResponse({'status': 'success', 'data': data}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def coiffeuse_services(request, coiffeuse_id):
    try:

        # Obtenez la coiffeuse correspondant à l'ID utilisateur
        coiffeuse = TblCoiffeuse.objects.get(idTblUser_id=coiffeuse_id)

        # Récupérez le salon lié à cette coiffeuse
        salon = TblSalon.objects.get(coiffeuse=coiffeuse)

        # Traitez les services du salon ici...
        services = TblService.objects.filter(salons=salon).distinct().values(
            'idTblService',
            'intitule_service',
            'description',
        )
        # # Vérifier si le salon existe pour la coiffeuse
        # salon = TblSalon.objects.get(coiffeuse_id=coiffeuse_id)
        #
        # # Récupérer tous les services du salon
        # services = TblService.objects.filter(salons=salon).distinct().values(
        #     'idTblService',
        #     'intitule_service',
        #     'description',
        # )

        #services = TblService.objects.filter(salons=salon).prefetch_related('service_temps', 'service_prix')

        # Ajouter les relations avec temps et prix
        services_with_details = []
        for service in services:
            service_id = service['idTblService']

            # Récupérer la durée (temps)
            service_temps = TblServiceTemps.objects.filter(service_id=service_id).first()
            minutes = service_temps.temps.minutes if service_temps else None

            # Récupérer le prix
            service_prix = TblServicePrix.objects.filter(service_id=service_id).first()
            price = service_prix.prix.prix if service_prix else None

            # Ajouter les détails au service
            service['temps_minutes'] = minutes
            service['prix'] = price

            services_with_details.append(service)

        return JsonResponse(services_with_details, safe=False, status=200)
    except TblSalon.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Salon introuvable pour cette coiffeuse.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erreur serveur : {str(e)}'}, status=500)


@csrf_exempt
def ServicesListView(request):
    if request.method == 'GET':
        services = TblService.objects.all().values('idTblService', 'intitule_service', 'description')
        return JsonResponse(list(services), safe=False)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                                    #La gestion des serializers
# ++++++++++++++++++++++++++++++++++++++Vues pour les texte+++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt  # À modifier en production (utiliser @csrf_protect)
def check_user_profile(request):
    if request.method == 'POST':  # Accepter uniquement la méthode POST
        try:
            # Charger les données JSON envoyées
            data = json.loads(request.body)
            user_uuid = data.get('userUuid')

            # Vérifier si l'utilisateur existe avec cet UUID
            user_exists = TblUser.objects.filter(uuid=user_uuid).exists()

            if user_exists:
                return JsonResponse({"status": "exists"}, status=200)
            else:
                return JsonResponse({"status": "not_exists"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)

    #---------------------------------------------------------------------------------------------------------