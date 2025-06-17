################################################################################
#                                                                              #
#           VUES DE L'API POUR LA GESTION DES IMAGES DE SALON (HAIRBNB)          #
#                                                                              #
#  Ce fichier définit les points d'accès (endpoints) de l'API pour gérer la    #
#  galerie d'images d'un salon. Il combine des vues basées sur les classes     #
#  génériques de Django REST Framework pour la simplicité et des vues          #
#  basées sur des fonctions pour une logique plus personnalisée.                #
#                                                                              #
#  Fonctionnalités :                                                           #
#    - `SalonImageListView`: Lister toutes les images d'un salon.              #
#    - `add_images_to_salon`: Télécharger plusieurs images pour un salon en     #
#      une seule requête.                                                      #
#    - `SalonImageDeleteView`: Supprimer une image spécifique.                 #
#                                                                              #
################################################################################

# --- Importations ---
import traceback

# Importations de Django REST Framework
from rest_framework.decorators import parser_classes, api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework import status

# Importations locales
from decorators.decorators import firebase_authenticated
from hairbnb.mixins.auth_mixins import FirebaseAuthMixin
from hairbnb.models import TblSalonImage, TblSalon
from hairbnb.salon.salon_serializers import TblSalonImageSerializer


class SalonImageListView(FirebaseAuthMixin, ListAPIView):
    """
    Vue basée sur une classe générique pour lister les images d'un salon.
    Gère les requêtes GET pour un salon spécifique.
    """
    # Spécifie le sérialiseur à utiliser pour convertir les objets en JSON.
    serializer_class = TblSalonImageSerializer

    def get_queryset(self):
        """
        Surcharge la méthode pour retourner uniquement les images
        du salon spécifié dans l'URL.
        """
        # Récupère l'ID du salon depuis les paramètres de l'URL.
        salon_id = self.kwargs['salon_id']
        # Filtre les images pour ne garder que celles liées à ce salon.
        return TblSalonImage.objects.filter(salon__idTblSalon=salon_id)


# Le décorateur @parser_classes indique à Django REST Framework comment interpréter
# les données de la requête. MultiPartParser est essentiel pour les envois de fichiers.
@firebase_authenticated
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def add_images_to_salon(request):
    """
    Vue basée sur une fonction pour télécharger plusieurs images
    pour un salon en une seule fois.
    """
    # Instructions de débogage laissées intentionnellement.
    print(" La vue a bien été appelée !")
    # Récupère l'ID du salon et la liste des fichiers image depuis la requête.
    salon_id = request.data.get('salon')
    images = request.FILES.getlist('image')

    print("Reçues images:", [img.name for img in images])

    # --- Validation des données d'entrée ---
    if not salon_id or not images:
        return Response({"error": "Champs requis : salon, image(s)"}, status=status.HTTP_400_BAD_REQUEST)
    if len(images) < 3:
        return Response({"error": "Veuillez télécharger au moins 3 images."}, status=status.HTTP_400_BAD_REQUEST)
    if len(images) > 12:
        return Response({"error": "Vous ne pouvez pas télécharger plus de 12 images."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie que le salon existe.
    try:
        salon = TblSalon.objects.get(idTblSalon=salon_id)
    except TblSalon.DoesNotExist:
        return Response({"error": "Salon introuvable."}, status=status.HTTP_404_NOT_FOUND)

    # --- Traitement de chaque image ---
    image_ids = []
    # Boucle sur chaque fichier image téléchargé.
    for img in images:
        print(f"-> Image: {img.name}, Taille: {img.size}")

        # Valide la taille de l'image (ne doit pas dépasser 6 Mo).
        if img.size > 6 * 1024 * 1024:
            return Response({"error": f"L'image '{img.name}' dépasse 6MB."}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # Prépare les données pour le sérialiseur.
        serializer = TblSalonImageSerializer(data={"salon": int(salon_id), "image": img})

        # Valide et sauvegarde l'image.
        if serializer.is_valid():
            instance = serializer.save()
            image_ids.append(instance.id)
        else:
            print("Serializer invalide:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Renvoie une réponse de succès avec les IDs des images créées.
    return Response({"success": True, "image_ids": image_ids}, status=status.HTTP_201_CREATED)


class SalonImageDeleteView(FirebaseAuthMixin, DestroyAPIView):
    """
    Vue basée sur une classe générique pour supprimer une image de salon.
    Gère les requêtes DELETE pour une image spécifique.
    """
    # Le queryset de base contenant tous les objets qui peuvent être supprimés.
    queryset = TblSalonImage.objects.all()
    # Le sérialiseur à utiliser.
    serializer_class = TblSalonImageSerializer
    # Le nom du champ dans l'URL qui contient la clé primaire de l'objet à supprimer.
    lookup_field = 'id'
