from rest_framework import serializers
from hairbnb.models import TblCategorie, TblService


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer simple pour les catégories.
    Utilisé pour lister toutes les catégories disponibles.
    """
    class Meta:
        model = TblCategorie
        fields = ['idTblCategorie', 'intitule_categorie']


class ServiceWithCategorySerializer(serializers.ModelSerializer):
    """
    Serializer pour un service avec les informations de sa catégorie.
    Utilisé pour afficher un service avec sa catégorie.
    """
    categorie_id = serializers.IntegerField(source='categorie.idTblCategorie', read_only=True)
    categorie_nom = serializers.CharField(source='categorie.intitule_categorie', read_only=True)
    
    class Meta:
        model = TblService
        fields = [
            'idTblService',
            'intitule_service', 
            'description',
            'categorie_id',
            'categorie_nom'
        ]


class CategoryWithServicesSerializer(serializers.ModelSerializer):
    """
    Serializer pour une catégorie avec la liste de ses services.
    Utilisé pour afficher une catégorie et tous ses services.
    """
    services = ServiceWithCategorySerializer(
        source='tblservice_set', 
        many=True, 
        read_only=True
    )
    nb_services = serializers.SerializerMethodField()
    
    class Meta:
        model = TblCategorie
        fields = [
            'idTblCategorie',
            'intitule_categorie',
            'nb_services',
            'services'
        ]
    
    def get_nb_services(self, obj):
        """Retourne le nombre de services dans cette catégorie."""
        return obj.tblservice_set.count()


class CategoryWithServicesCountSerializer(serializers.ModelSerializer):
    """
    Serializer léger pour une catégorie avec juste le nombre de services.
    Utilisé pour lister les catégories avec compteur sans charger tous les services.
    """
    nb_services = serializers.SerializerMethodField()
    
    class Meta:
        model = TblCategorie
        fields = [
            'idTblCategorie',
            'intitule_categorie',
            'nb_services'
        ]
    
    def get_nb_services(self, obj):
        """Retourne le nombre de services dans cette catégorie."""
        return obj.tblservice_set.count()


class ServiceCreateWithCategorySerializer(serializers.Serializer):
    """
    Serializer pour créer un nouveau service avec catégorie.
    Utilisé dans les vues de création de service.
    """
    userId = serializers.IntegerField()
    intitule_service = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=600)
    categorie_id = serializers.IntegerField()
    prix = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    temps_minutes = serializers.IntegerField(min_value=1)
    
    def validate_categorie_id(self, value):
        """Valide que la catégorie existe."""
        try:
            TblCategorie.objects.get(idTblCategorie=value)
        except TblCategorie.DoesNotExist:
            raise serializers.ValidationError("Catégorie inexistante.")
        return value


class ServiceAddExistingWithCategorySerializer(serializers.Serializer):
    """
    Serializer pour ajouter un service existant à un salon.
    Utilisé pour associer un service existant avec prix/durée personnalisés.
    """
    userId = serializers.IntegerField()
    service_id = serializers.IntegerField()
    prix = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    temps_minutes = serializers.IntegerField(min_value=1)
    
    def validate_service_id(self, value):
        """Valide que le service existe."""
        try:
            TblService.objects.get(idTblService=value)
        except TblService.DoesNotExist:
            raise serializers.ValidationError("Service inexistant.")
        return value
