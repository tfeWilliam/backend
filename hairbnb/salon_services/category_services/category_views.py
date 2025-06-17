from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from decorators.decorators import firebase_authenticated, is_owner
from hairbnb.models import (
    TblUser, TblCoiffeuse, TblService, TblSalonService,
    TblPrix, TblTemps, TblServicePrix, TblServiceTemps, TblCoiffeuseSalon,
    TblCategorie
)
from hairbnb.salon_services.category_services.category_serializers import (
    CategorySerializer,
    ServiceWithCategorySerializer, 
    CategoryWithServicesSerializer,
    CategoryWithServicesCountSerializer,
    ServiceCreateWithCategorySerializer,
    ServiceAddExistingWithCategorySerializer
)


@api_view(['GET'])
@firebase_authenticated
def get_all_categories(request):
    """
    Récupère toutes les catégories disponibles.
    Peut inclure le nombre de services par catégorie selon le paramètre 'with_count'.
    
    Query params:
    - with_count: true/false (inclut le nombre de services par catégorie)
    """
    try:
        with_count = request.GET.get('with_count', 'false').lower() == 'true'
        
        categories = TblCategorie.objects.all().order_by('intitule_categorie')
        
        if with_count:
            serializer = CategoryWithServicesCountSerializer(categories, many=True)
        else:
            serializer = CategorySerializer(categories, many=True)
        
        return Response({
            "status": "success",
            "message": "Catégories récupérées avec succès",
            "categories": serializer.data,
            "count": categories.count()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Erreur lors de la récupération des catégories: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET']) 
@firebase_authenticated
def get_category_with_services(request, category_id):
    """
    Récupère une catégorie avec tous ses services.
    
    Params:
    - category_id: ID de la catégorie
    """
    try:
        category = TblCategorie.objects.get(idTblCategorie=category_id)
        serializer = CategoryWithServicesSerializer(category)
        
        return Response({
            "status": "success",
            "message": f"Catégorie '{category.intitule_categorie}' récupérée avec succès",
            "category": serializer.data
        }, status=status.HTTP_200_OK)
    
    except TblCategorie.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Catégorie non trouvée"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            "status": "error", 
            "message": f"Erreur: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@firebase_authenticated
def get_services_by_category(request, category_id):
    """
    Récupère tous les services d'une catégorie spécifique.
    Plus léger que get_category_with_services car ne retourne que les services.
    
    Params:
    - category_id: ID de la catégorie
    
    Query params:
    - search: terme de recherche dans les services de cette catégorie
    """
    try:
        # Vérifier que la catégorie existe
        try:
            category = TblCategorie.objects.get(idTblCategorie=category_id)
        except TblCategorie.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Catégorie non trouvée"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Récupérer les services de cette catégorie
        services = TblService.objects.filter(categorie=category)
        
        # Filtrage par recherche si fourni
        search_term = request.GET.get('search', '').strip()
        if search_term:
            services = services.filter(
                Q(intitule_service__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        serializer = ServiceWithCategorySerializer(services, many=True)
        
        return Response({
            "status": "success",
            "message": f"Services de la catégorie '{category.intitule_categorie}' récupérés",
            "category_name": category.intitule_categorie,
            "services": serializer.data,
            "count": services.count()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Erreur: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@firebase_authenticated
@is_owner(param_name="userId")
def create_service_with_category(request):
    """
    Crée un nouveau service global avec catégorie et l'ajoute au salon de la coiffeuse.
    
    Body attendu:
    {
        "userId": int,
        "intitule_service": str,
        "description": str,
        "categorie_id": int,
        "prix": float,
        "temps_minutes": int
    }
    """
    serializer = ServiceCreateWithCategorySerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "status": "error",
            "message": "Données invalides",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Extraire les données validées
        user_id = serializer.validated_data['userId']
        service_name = serializer.validated_data['intitule_service']
        service_description = serializer.validated_data['description']
        categorie_id = serializer.validated_data['categorie_id']
        prix = serializer.validated_data['prix']
        temps_minutes = serializer.validated_data['temps_minutes']
        
        # Récupérer l'utilisateur et vérifier qu'il est une coiffeuse
        user = TblUser.objects.get(idTblUser=user_id)
        if user.type_ref.libelle != 'Coiffeuse':
            return Response({
                "status": "error",
                "message": "L'utilisateur n'est pas une coiffeuse"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer la coiffeuse et son salon
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        coiffeuse_salon = TblCoiffeuseSalon.objects.filter(
            coiffeuse=coiffeuse,
            est_proprietaire=True
        ).first()
        
        if not coiffeuse_salon:
            return Response({
                "status": "error",
                "message": "Vous n'êtes pas propriétaire d'un salon"
            }, status=status.HTTP_404_NOT_FOUND)
        
        salon = coiffeuse_salon.salon
        
        # Récupérer la catégorie
        categorie = TblCategorie.objects.get(idTblCategorie=categorie_id)
        
        # Vérifier si un service avec ce nom existe déjà
        if TblService.objects.filter(intitule_service__iexact=service_name).exists():
            return Response({
                "status": "error",
                "message": f"Un service nommé '{service_name}' existe déjà"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le nouveau service global
        service = TblService.objects.create(
            intitule_service=service_name,
            description=service_description,
            categorie=categorie
        )
        
        # Créer ou récupérer le prix et le temps
        prix_obj, _ = TblPrix.objects.get_or_create(prix=prix)
        temps_obj, _ = TblTemps.objects.get_or_create(minutes=temps_minutes)
        
        # Associer le service au salon
        salon_service = TblSalonService.objects.create(
            salon=salon,
            service=service
        )
        
        # Créer les relations prix et temps
        TblServicePrix.objects.create(
            service=service,
            prix=prix_obj
        )
        
        TblServiceTemps.objects.create(
            service=service,
            temps=temps_obj
        )
        
        return Response({
            "status": "success",
            "message": "Nouveau service créé et ajouté au salon avec succès",
            "service": ServiceWithCategorySerializer(service).data,
            "salon_id": salon.idTblSalon,
            "prix": prix,
            "duree_minutes": temps_minutes
        }, status=status.HTTP_201_CREATED)
    
    except TblUser.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Utilisateur non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except TblCoiffeuse.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Profil de coiffeuse non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except TblCategorie.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Catégorie non trouvée"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Erreur inattendue: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@firebase_authenticated  
@is_owner(param_name="userId")
def add_existing_service_with_category(request):
    """
    Ajoute un service existant au salon avec prix et durée personnalisés.
    
    Body attendu:
    {
        "userId": int,
        "service_id": int,
        "prix": float,
        "temps_minutes": int
    }
    """
    serializer = ServiceAddExistingWithCategorySerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "status": "error",
            "message": "Données invalides",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Extraire les données validées
        user_id = serializer.validated_data['userId']
        service_id = serializer.validated_data['service_id']
        prix = serializer.validated_data['prix']
        temps_minutes = serializer.validated_data['temps_minutes']
        
        # Récupérer l'utilisateur et vérifier qu'il est une coiffeuse
        user = TblUser.objects.get(idTblUser=user_id)
        if user.type_ref.libelle != 'Coiffeuse':
            return Response({
                "status": "error",
                "message": "L'utilisateur n'est pas une coiffeuse"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer la coiffeuse et son salon
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        coiffeuse_salon = TblCoiffeuseSalon.objects.filter(
            coiffeuse=coiffeuse,
            est_proprietaire=True
        ).first()
        
        if not coiffeuse_salon:
            return Response({
                "status": "error",
                "message": "Vous n'êtes pas propriétaire d'un salon"
            }, status=status.HTTP_404_NOT_FOUND)
        
        salon = coiffeuse_salon.salon
        
        # Récupérer le service existant
        service = TblService.objects.get(idTblService=service_id)
        
        # Vérifier si le service n'est pas déjà associé au salon
        if TblSalonService.objects.filter(salon=salon, service=service).exists():
            return Response({
                "status": "error",
                "message": "Ce service est déjà proposé par votre salon"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer ou récupérer le prix et le temps
        prix_obj, _ = TblPrix.objects.get_or_create(prix=prix)
        temps_obj, _ = TblTemps.objects.get_or_create(minutes=temps_minutes)
        
        # Associer le service au salon
        salon_service = TblSalonService.objects.create(
            salon=salon,
            service=service
        )
        
        # Créer les relations prix et temps pour ce salon
        TblServicePrix.objects.create(
            service=service,
            prix=prix_obj
        )
        
        TblServiceTemps.objects.create(
            service=service,
            temps=temps_obj
        )
        
        return Response({
            "status": "success",
            "message": "Service existant ajouté au salon avec succès",
            "service": ServiceWithCategorySerializer(service).data,
            "salon_id": salon.idTblSalon,
            "prix": prix,
            "duree_minutes": temps_minutes
        }, status=status.HTTP_201_CREATED)
    
    except TblUser.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Utilisateur non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except TblCoiffeuse.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Profil de coiffeuse non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except TblService.DoesNotExist:
        return Response({
            "status": "error",
            "message": "Service non trouvé"
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Erreur inattendue: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@firebase_authenticated
#@is_owner(param_name="userId")
def get_salon_services_by_category(request):
    """
    Récupère tous les services d'un salon organisés par catégorie.
    
    Query params:
    - userId: ID de l'utilisateur (coiffeuse)
    """
    try:
        user_id = request.GET.get('userId')
        if not user_id:
            return Response({
                "status": "error",
                "message": "userId est requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer l'utilisateur et son salon
        user = TblUser.objects.get(idTblUser=user_id)
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        coiffeuse_salon = TblCoiffeuseSalon.objects.filter(
            coiffeuse=coiffeuse,
            est_proprietaire=True
        ).first()
        
        if not coiffeuse_salon:
            return Response({
                "status": "error",
                "message": "Salon non trouvé"
            }, status=status.HTTP_404_NOT_FOUND)
        
        salon = coiffeuse_salon.salon
        
        # Récupérer tous les services du salon avec leurs catégories
        salon_services = TblSalonService.objects.filter(
            salon=salon
        ).select_related('service__categorie')
        
        # Organiser par catégorie
        services_by_category = {}
        
        for salon_service in salon_services:
            service = salon_service.service
            category_name = service.categorie.intitule_categorie if service.categorie else "Sans catégorie"
            
            if category_name not in services_by_category:
                services_by_category[category_name] = {
                    "category_id": service.categorie.idTblCategorie if service.categorie else None,
                    "category_name": category_name,
                    "services": []
                }
            
            # Récupérer prix et durée pour ce service
            service_prix = TblServicePrix.objects.filter(service=service).first()
            service_temps = TblServiceTemps.objects.filter(service=service).first()
            
            service_data = ServiceWithCategorySerializer(service).data
            service_data['salon_service_id'] = salon_service.idSalonService
            service_data['prix'] = service_prix.prix.prix if service_prix else None
            service_data['duree_minutes'] = service_temps.temps.minutes if service_temps else None
            
            services_by_category[category_name]["services"].append(service_data)
        
        return Response({
            "status": "success",
            "message": "Services du salon récupérés par catégorie",
            "salon_id": salon.idTblSalon,
            "services_by_category": list(services_by_category.values()),
            "total_services": salon_services.count()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status": "error",
            "message": f"Erreur: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
