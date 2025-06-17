# hairbnb/validators.py

from django.core.exceptions import ValidationError

def validate_max_images(salon):
    """
    Valide que le salon n'a pas plus de 25 images.

    Si le salon a déjà 25 images, on bloque l'ajout d'une nouvelle.
    """
    # ✅ Import local pour éviter l'import circulaire
    from hairbnb.models import TblSalonImage

    if TblSalonImage.objects.filter(salon=salon).count() >= 25:
        raise ValidationError("Maximum 25 images autorisées par salon.")
