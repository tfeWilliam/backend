################################################################################
#                                                                              #
#         SÉRIALISEURS POUR LA PAGE DE DÉTAIL D'UN SALON (HAIRBNB)               #
#                                                                              #
#  Ce fichier définit un ensemble de sérialiseurs (serializers) dont le but    #
#  est de construire une réponse API complète et riche pour la page de détail  #
#  publique d'un salon.                                                        #
#                                                                              #
#  Le sérialiseur principal, `SalonDetailSerializer`, agit comme un            #
#  agrégateur de données, utilisant d'autres sérialiseurs "helpers" et de      #
#  nombreuses `SerializerMethodField` pour rassembler et formater les          #
#  informations provenant de divers modèles liés (Coiffeuse, Images, Avis,     #
#  Services, Horaires, Promotions, etc.).                                      #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers
# Utilitaire Django pour obtenir l'heure et la date actuelles avec gestion du fuseau horaire
from django.utils.timezone import now
# Importation des modèles de la base de données
from hairbnb.models import (
    TblUser, TblCoiffeuse, TblService, TblSalonImage,
    TblAvis, TblSalon, TblPromotion, TblHoraireCoiffeuse,
    TblSalonService, TblCoiffeuseSalon
)


# --- Sérialiseurs "Helpers" pour les relations ---

class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour les informations de base d'un utilisateur."""
    class Meta:
        model = TblUser
        fields = ['idTblUser', 'nom', 'prenom', 'photo_profil', 'numero_telephone']


class CoiffeuseSerializer(serializers.ModelSerializer):
    """Sérialiseur pour une coiffeuse, incluant les détails de l'utilisateur lié."""
    idTblUser = UserSerializer(read_only=True)
    class Meta:
        model = TblCoiffeuse
        fields = ['idTblUser', 'nom_commercial']


class SalonImageSerializer(serializers.ModelSerializer):
    """Sérialiseur pour une image de la galerie d'un salon."""
    class Meta:
        model = TblSalonImage
        fields = ['id', 'image']


class AvisSerializer(serializers.ModelSerializer):
    """Sérialiseur pour un avis client, avec des champs formatés."""
    # Champs dont la valeur est calculée par des méthodes personnalisées ci-dessous.
    client_nom = serializers.SerializerMethodField()
    date_format = serializers.SerializerMethodField()
    class Meta:
        model = TblAvis
        fields = ['note', 'commentaire', 'client_nom', 'date_format']

    def get_client_nom(self, obj):
        """Construit le nom complet du client qui a laissé l'avis."""
        if obj.client and hasattr(obj.client, 'idTblUser'):
            return f"{obj.client.idTblUser.prenom} {obj.client.idTblUser.nom}"
        return "Anonyme"

    def get_date_format(self, obj):
        """Formate la date de l'avis de manière relative (valeur statique dans ce code)."""
        return "about a year ago"


class ServiceWithPromotionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour un service qui inclut dynamiquement les informations
    d'une promotion si une est actuellement active.
    """
    prix = serializers.SerializerMethodField()
    duree = serializers.SerializerMethodField()
    promotion_active = serializers.SerializerMethodField()
    class Meta:
        model = TblService
        fields = ['idTblService', 'intitule_service', 'description', 'prix', 'duree', 'promotion_active']

    def get_prix(self, obj):
        """Récupère le prix de base du service."""
        service_prix = obj.service_prix.first()
        if service_prix and hasattr(service_prix, 'prix'):
            return service_prix.prix.prix
        return None

    def get_duree(self, obj):
        """Récupère la durée en minutes du service."""
        service_temps = obj.service_temps.first()
        if service_temps and hasattr(service_temps, 'temps'):
            return service_temps.temps.minutes
        return None

    def get_promotion_active(self, service):
        """
        Vérifie s'il existe une promotion active pour ce service à l'instant présent.
        """
        # Requête pour trouver une promotion dont la date actuelle est entre la date de début et de fin.
        promotion = TblPromotion.objects.filter(service=service, start_date__lte=now(), end_date__gte=now()).first()
        if promotion:
            return {"discount_percentage": str(promotion.discount_percentage), "start_date": promotion.start_date, "end_date": promotion.end_date}
        return None


# --- Sérialiseur Principal pour la Page de Détail du Salon ---
class SalonDetailSerializer(serializers.ModelSerializer):
    """
    Agrège toutes les informations nécessaires pour afficher la page de détail d'un salon.
    """
    # Utilisation de champs calculés et de sérialiseurs imbriqués pour construire la réponse.
    coiffeuse = serializers.SerializerMethodField()
    images = SalonImageSerializer(many=True, read_only=True)
    avis = AvisSerializer(many=True, read_only=True)
    services = serializers.SerializerMethodField()
    adresse = serializers.SerializerMethodField()
    horaires = serializers.SerializerMethodField()
    note_moyenne = serializers.SerializerMethodField()
    nombre_avis = serializers.SerializerMethodField()
    class Meta:
        model = TblSalon
        fields = [
            'idTblSalon', 'nom_salon', 'slogan', 'a_propos', 'logo_salon', 'position',
            'coiffeuse', 'adresse', 'horaires', 'note_moyenne', 'nombre_avis',
            'images', 'avis', 'services'
        ]

    def get_coiffeuse(self, obj):
        """Identifie et retourne les informations de la coiffeuse propriétaire du salon."""
        # Interroge la table de liaison pour trouver la relation où `est_proprietaire` est True.
        proprietaire_relation = TblCoiffeuseSalon.objects.filter(salon=obj, est_proprietaire=True).first()
        if proprietaire_relation and proprietaire_relation.coiffeuse:
            return CoiffeuseSerializer(proprietaire_relation.coiffeuse).data
        return None

    def get_services(self, obj):
        """Récupère la liste des services du salon et les sérialise avec la gestion des promotions."""
        services_relations = TblSalonService.objects.filter(salon=obj)
        services = [relation.service for relation in services_relations]
        # Utilise le sérialiseur qui vérifie les promotions pour chaque service.
        return ServiceWithPromotionSerializer(services, many=True).data

    def get_adresse(self, obj):
        """Formate l'adresse complète du salon en une seule chaîne de caractères."""
        if obj.adresse and hasattr(obj.adresse, 'rue') and hasattr(obj.adresse.rue, 'localite'):
            return f"{obj.adresse.numero} {obj.adresse.rue.nom_rue}, {obj.adresse.rue.localite.commune}, {obj.adresse.rue.localite.code_postal}"
        return None

    def get_horaires(self, obj):
        """Récupère les horaires de travail de la coiffeuse propriétaire et les formate."""
        proprietaire = obj.get_proprietaire()
        if proprietaire:
            horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=proprietaire).order_by('jour')
            if horaires.exists():
                jours = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
                # Construit une chaîne de caractères lisible pour les horaires.
                return ", ".join(f"{h.heure_debut.strftime('%I:%M %p')} - {h.heure_fin.strftime('%I:%M %p')} / {jours[h.jour]}" for h in horaires)
        # Retourne une valeur par défaut si aucun horaire n'est trouvé.
        return "10:00 AM - 6:00 PM / Mon - Fri"

    def get_note_moyenne(self, obj):
        """Calcule la note moyenne de tous los avis du salon."""
        avis = obj.avis.all()
        if avis.exists():
            return round(sum(a.note for a in avis) / avis.count(), 1)
        return 0

    def get_nombre_avis(self, obj):
        """Compte le nombre total d'avis pour le salon."""
        return obj.avis.count()








# from rest_framework import serializers
# from django.utils.timezone import now
# from hairbnb.models import (
#     TblUser, TblCoiffeuse, TblService, TblSalonImage,
#     TblAvis, TblSalon, TblPromotion, TblHoraireCoiffeuse,
#     TblSalonService, TblCoiffeuseSalon
# )
#
#
# # Serializer utilisateur
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblUser
#         fields = ['idTblUser', 'nom', 'prenom', 'photo_profil', 'numero_telephone']
#
#
# # Serializer coiffeuse
# class CoiffeuseSerializer(serializers.ModelSerializer):
#     idTblUser = UserSerializer(read_only=True)
#
#     class Meta:
#         model = TblCoiffeuse
#         fields = ['idTblUser', 'nom_commercial']
#
#
# # Serializer images du salon
# class SalonImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TblSalonImage
#         fields = ['id', 'image']
#
#
# # Serializer avis clients
# class AvisSerializer(serializers.ModelSerializer):
#     client_nom = serializers.SerializerMethodField()
#     date_format = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblAvis
#         fields = ['note', 'commentaire', 'client_nom', 'date_format']
#
#     def get_client_nom(self, obj):
#         if obj.client and hasattr(obj.client, 'idTblUser'):
#             return f"{obj.client.idTblUser.prenom} {obj.client.idTblUser.nom}"
#         return "Anonyme"
#
#     def get_date_format(self, obj):
#         return "about a year ago"  # à adapter selon le contexte
#
#
# # 🔁 Serializer pour les services avec promotion active
# class ServiceWithPromotionSerializer(serializers.ModelSerializer):
#     prix = serializers.SerializerMethodField()
#     duree = serializers.SerializerMethodField()
#     promotion_active = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblService
#         fields = [
#             'idTblService', 'intitule_service', 'description',
#             'prix', 'duree', 'promotion_active'
#         ]
#
#     def get_prix(self, obj):
#         service_prix = obj.service_prix.first()
#         if service_prix and hasattr(service_prix, 'prix'):
#             return service_prix.prix.prix
#         return None
#
#     def get_duree(self, obj):
#         service_temps = obj.service_temps.first()
#         if service_temps and hasattr(service_temps, 'temps'):
#             return service_temps.temps.minutes
#         return None
#
#     def get_promotion_active(self, service):
#         promotion = TblPromotion.objects.filter(
#             service=service,
#             start_date__lte=now(),
#             end_date__gte=now()
#         ).first()
#
#         if promotion:
#             return {
#                 "discount_percentage": str(promotion.discount_percentage),
#                 "start_date": promotion.start_date,
#                 "end_date": promotion.end_date
#             }
#         return None
#
#
# # 🏠 Serializer principal pour le salon
# class SalonDetailSerializer(serializers.ModelSerializer):
#     coiffeuse = serializers.SerializerMethodField()
#     images = SalonImageSerializer(many=True, read_only=True)
#     avis = AvisSerializer(many=True, read_only=True)
#     services = serializers.SerializerMethodField()
#     adresse = serializers.SerializerMethodField()
#     horaires = serializers.SerializerMethodField()
#     note_moyenne = serializers.SerializerMethodField()
#     nombre_avis = serializers.SerializerMethodField()
#
#     class Meta:
#         model = TblSalon
#         fields = [
#             'idTblSalon', 'nom_salon', 'slogan', 'a_propos', 'logo_salon', 'position',
#             'coiffeuse', 'adresse', 'horaires', 'note_moyenne', 'nombre_avis',
#             'images', 'avis', 'services'
#         ]
#
#     def get_coiffeuse(self, obj):
#         """
#         Récupère la coiffeuse propriétaire via la table de jonction.
#         """
#         proprietaire_relation = TblCoiffeuseSalon.objects.filter(
#             salon=obj,
#             est_proprietaire=True
#         ).first()
#
#         if proprietaire_relation and proprietaire_relation.coiffeuse:
#             return CoiffeuseSerializer(proprietaire_relation.coiffeuse).data
#         return None
#
#     def get_services(self, obj):
#         # Récupérer les services via la relation many-to-many
#         services_relations = TblSalonService.objects.filter(salon=obj)
#         services = [relation.service for relation in services_relations]
#         return ServiceWithPromotionSerializer(services, many=True).data
#
#     def get_adresse(self, obj):
#         # Utiliser l'adresse du salon si elle existe
#         if obj.adresse and hasattr(obj.adresse, 'rue') and hasattr(obj.adresse.rue, 'localite'):
#             return f"{obj.adresse.numero} {obj.adresse.rue.nom_rue}, {obj.adresse.rue.localite.commune}, {obj.adresse.rue.localite.code_postal}"
#         return None
#
#     def get_horaires(self, obj):
#         # Récupérer les horaires de la coiffeuse propriétaire
#         proprietaire = obj.get_proprietaire()
#         if proprietaire:
#             horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=proprietaire).order_by('jour')
#             if horaires.exists():
#                 jours = {
#                     0: "Mon", 1: "Tue", 2: "Wed",
#                     3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"
#                 }
#                 return ", ".join(
#                     f"{h.heure_debut.strftime('%I:%M %p')} - {h.heure_fin.strftime('%I:%M %p')} / {jours[h.jour]}"
#                     for h in horaires
#                 )
#         return "10:00 AM - 6:00 PM / Mon - Fri"
#
#     def get_note_moyenne(self, obj):
#         avis = obj.avis.all()
#         if avis.exists():
#             return round(sum(a.note for a in avis) / avis.count(), 1)
#         return 0
#
#     def get_nombre_avis(self, obj):
#         return obj.avis.count()
