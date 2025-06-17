import logging
from datetime import datetime
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import TblAdresse, TblRue, TblLocalite, TblCoiffeuse, TblClient, TblUser, TblServiceTemps, TblServicePrix, \
    TblPrix, TblTemps, TblService, TblSalon, TblSalonService
from .services.geolocation_service import GeolocationService
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError


def home(request):
    return HttpResponse("Bienvenue sur l'API Hairbnb!")


@csrf_exempt
# ++++++++++++++++++++++++++++++++++++++Importanbt+++++++++++++++++++++++++++++++++++++++++++++
#### ATTENTION : A MODIFIER : A ne pas laissé ainsi en production,
# car cela peut entrainer des attaques de type Cross-Site Scripting (XSS),
# ce qui pourrait permettre aux attaquants de injecter du code malveillant dans la page web.
# Donc ce qu'il faut changer a la production est de modifier le decorator csrf_exempt par @csrf_protect
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# def create_user_profile(request):
#     """
#     Crée un profil utilisateur en fonction des données envoyées via une requête POST.
#     """
#     if request.method == 'POST':
#         try:
#             # Vérifiez si la requête contient des fichiers (multipart/form-data)
#             if request.content_type.startswith('multipart/form-data'):
#                 # Utilisez request.POST et request.FILES
#                 data = request.POST
#                 photo_profil = request.FILES.get('photo_profil')
#             else:
#                 # Sinon, lisez les données JSON dans request.body
#                 data = json.loads(request.body)
#                 photo_profil = None
#
#             # Debugging: Afficher les données reçues
#             print("Données reçues :", data)
#             print("Fichiers reçus :", request.FILES)
#
#             # Champs obligatoires pour tous les utilisateurs
#             required_fields = [
#                 'userUuid', 'email', 'role', 'nom', 'prenom', 'sexe',
#                 'telephone', 'code_postal', 'commune', 'rue', 'numero', 'date_naissance'
#             ]
#             for field in required_fields:
#                 if not data.get(field):
#                     return JsonResponse({"status": "error", "message": f"Le champ {field} est obligatoire."}, status=400)
#
#             # Validation spécifique pour la date de naissance
#             try:
#                 date_naissance = datetime.strptime(data['date_naissance'], '%d-%m-%Y').date()
#             except ValueError:
#                 return JsonResponse(
#                     {"status": "error", "message": "Le format de la date de naissance doit être DD-MM-YYYY."},
#                     status=400,
#                 )
#
#             # Vérifier si l'utilisateur existe déjà
#             user_uuid = data['userUuid']
#             if TblUser.objects.filter(uuid=user_uuid).exists():
#                 return JsonResponse({"status": "error", "message": "Utilisateur déjà existant"}, status=400)
#
#             # Étape 2 : Gérer l'adresse
#             localite, _ = TblLocalite.objects.get_or_create(
#                 commune=data['commune'], code_postal=data['code_postal']
#             )
#             rue_obj, _ = TblRue.objects.get_or_create(nom_rue=data['rue'], localite=localite)
#             adresse = TblAdresse.objects.create(
#                 numero=data['numero'], boite_postale=data.get('boite_postale', None), rue=rue_obj
#             )
#
#             # Étape 3 : Calculer les coordonnées géographiques avec le service
#             adresse_complete = f"{data['numero']}, {data['rue']}, {data['commune']}, {data['code_postal']}"
#             latitude, longitude = GeolocationService.geocode_address(adresse_complete)
#
#             # Étape 4 : Créer un utilisateur de base
#             user = TblUser.objects.create(
#                 uuid=user_uuid,
#                 nom=data['nom'],
#                 prenom=data['prenom'],
#                 email=data['email'],
#                 type=data['role'],
#                 sexe=data['sexe'],
#                 numero_telephone=data['telephone'],
#                 adresse=adresse,
#                 date_naissance=date_naissance,
#                 photo_profil=photo_profil  # Ajouter la photo de profil si elle existe
#             )
#
#             # Étape 5 : Gérer les rôles spécifiques
#             if data['role'] == 'coiffeuse':
#                 TblCoiffeuse.objects.create(
#                     idTblUser=user,
#                     denomination_sociale=data.get('denomination_sociale'),
#                     tva=data.get('tva'),
#                     position=f"{latitude}, {longitude}" if latitude and longitude else None,
#
#                 )
#             elif data['role'] == 'client':
#                 TblClient.objects.create(
#                     idTblUser=user
#                 )
#
#             # Réponse de succès
#             return JsonResponse({"status": "success", "message": "Profil créé avec succès!"}, status=201)
#
#         except Exception as e:
#             # Gestion des erreurs générales
#             print(f"Erreur : {str(e)}")
#             return JsonResponse({"status": "error", "message": str(e)}, status=400)
#
#     return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)
#
# #*************************************************************************************************************

@csrf_exempt
def get_id_and_type_from_uuid(request, uuid):
    try:
        # Rechercher l'utilisateur par UUID
        user = get_object_or_404(TblUser, uuid=uuid)

        # Récupérer le type à partir de type_ref s'il existe
        user_type = None
        if hasattr(user, 'type_ref') and user.type_ref:
            user_type = user.type_ref.libelle

        # Retourner l'id et le type de l'utilisateur
        return JsonResponse({
            'success': True,
            'idTblUser': user.idTblUser,
            'type': user_type,  # Utilisation du type récupéré de type_ref
        }, status=200)
    except Exception as e:
        # Ajout du traceback pour débogage
        import traceback
        print(f"Error in get_id_and_type_from_uuid: {str(e)}")
        print(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

#*************************************************************************************************************

logger = logging.getLogger(__name__)
@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserProfileView(View):
    def patch(self, request, uuid):
        try:
            logger.info(f"Requête PATCH reçue pour l'utilisateur {uuid}")

            # Charger les données de la requête
            data = json.loads(request.body)

            logger.info(f"Données reçues : {data}")

            # Récupérer l'utilisateur par UUID
            user = TblUser.objects.get(uuid=uuid)

            # Logs avant la mise à jour
            logger.info(f"Avant mise à jour : {user.nom}, {user.prenom}")

            # Mise à jour des champs généraux
            user.nom = data.get('nom', user.nom)
            user.prenom = data.get('prenom', user.prenom)
            user.numero_telephone = data.get('numero_telephone', user.numero_telephone)
            user.type = data.get('type', user.type)

            if 'email' in data:
                try:
                    validate_email(data['email'])
                    user.email = data['email']
                except ValidationError:
                    return JsonResponse({"success": False, "message": "Email non valide."}, status=400)

            # Mise à jour de l'adresse
            if 'adresse' in data:
                adresse_data = data['adresse']
                if isinstance(adresse_data, dict):
                    # Utiliser l'adresse existante ou créer une nouvelle
                    adresse = user.adresse or TblAdresse()

                    # Mise à jour des champs de l'adresse
                    adresse.numero = adresse_data.get('numero', adresse.numero)
                    adresse.boite_postale = adresse_data.get('boite_postale', adresse.boite_postale)

                    # Vérifier et mettre à jour la rue associée
                    if 'rue_id' in adresse_data:
                        try:
                            rue = TblRue.objects.get(idTblRue=adresse_data['rue_id'])
                            adresse.rue = rue
                        except TblRue.DoesNotExist:
                            return JsonResponse(
                                {"success": False, "message": f"Rue avec ID {adresse_data['rue_id']} introuvable."},
                                status=400
                            )

                    adresse.save()
                    user.adresse = adresse

            # Mise à jour des champs spécifiques pour les coiffeuses
            if user.type == 'coiffeuse' and hasattr(user, 'coiffeuse'):
                coiffeuse = user.coiffeuse
                coiffeuse.denomination_sociale = data.get('denomination_sociale', coiffeuse.denomination_sociale)
                coiffeuse.tva = data.get('tva', coiffeuse.tva)
                coiffeuse.position = data.get('position', coiffeuse.position)
                coiffeuse.save()

            # Sauvegarder les modifications de l'utilisateur
            user.save()
            # Logs après la mise à jour
            logger.info(f"Après mise à jour : {user.nom}, {user.prenom}")

            return JsonResponse({"success": True, "message": "Profil mis à jour avec succès."})

        except TblUser.DoesNotExist:
            logger.error(f"Utilisateur avec UUID {uuid} introuvable.")
            return JsonResponse({"success": False, "message": "Utilisateur introuvable."}, status=404)
        except Exception as e:
            logger.error(f"Erreur : {str(e)}")
            return JsonResponse({"success": False, "message": f"Erreur: {str(e)}"}, status=400)

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
def add_service_to_salon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Récupérer l'ID utilisateur (idTblUser) ou de la coiffeuse
            user_id = data.get('userId')  # Vérifiez que `userId` est bien envoyé depuis Flutter
            service_name = data.get('intitule_service')
            service_description = data.get('description')
            prix = data.get('prix')
            temps_minutes = data.get('temps_minutes')

            # Vérifiez si tous les champs requis sont fournis
            if not all([user_id, service_name, service_description, prix, temps_minutes]):
                return JsonResponse({"status": "error", "message": "Tous les champs sont obligatoires"}, status=400)

            # Récupérez l'utilisateur et la coiffeuse via `idTblUser`
            try:
                user = TblUser.objects.get(idTblUser=user_id, type='coiffeuse')
                coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
            except TblUser.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Utilisateur non trouvé ou non autorisé"}, status=404)
            except TblCoiffeuse.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Cette coiffeuse n'existe pas"}, status=404)

            # Vérifiez si la coiffeuse possède un salon
            try:
                salon = TblSalon.objects.get(coiffeuse=coiffeuse)
            except TblSalon.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Cette coiffeuse ne possède pas de salon"}, status=404)

            # Vérifiez si le service existe déjà
            service, created = TblService.objects.get_or_create(
                intitule_service=service_name,
                defaults={"description": service_description}
            )

            # Créez ou récupérez un enregistrement dans TblSalonService
            salon_service, salon_service_created = TblSalonService.objects.get_or_create(
                salon=salon,
                service=service
            )

            # Ajoutez le prix et le temps à ce service
            prix_obj, prix_created = TblPrix.objects.get_or_create(prix=prix)
            temps_obj, temps_created = TblTemps.objects.get_or_create(minutes=temps_minutes)

            # Associez le service à son prix et temps
            TblServicePrix.objects.get_or_create(service=service, prix=prix_obj)
            TblServiceTemps.objects.get_or_create(service=service, temps=temps_obj)

            return JsonResponse({
                "status": "success",
                "message": "Service ajouté au salon avec succès",
                "service_id": service.idTblService,
                "salon_id": salon.idTblSalon
            }, status=201)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)

#********************************************************************************************************

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
                    'id': coiffeuse.id,  # ID de la coiffeuse
                    'uuid': user.uuid,  # UUID de l'utilisateur
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
@csrf_exempt
def list_salon_with_coiffeuse(request):
    try:
        # Récupérer tous les salons et les IDs des coiffeuses associées
        salons = TblSalon.objects.all().values(
            'idTblSalon',  # ID du salon
            'coiffeuse__idTblUser__idTblUser',  # ID de la coiffeuse associée
        )

        # Construire une liste avec les données des salons
        salon_list = [
            {
                "salon_id": salon['idTblSalon'],
                "coiffeuse_id": salon['coiffeuse__idTblUser__idTblUser']
            }
            for salon in salons
        ]

        return JsonResponse({"status": "success", "data": salon_list}, safe=False, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Erreur serveur : {str(e)}"}, status=500)
