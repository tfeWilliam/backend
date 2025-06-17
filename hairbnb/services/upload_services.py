import os


def salon_image_upload_to(instance, filename):
    """
    Génère dynamiquement le chemin d’enregistrement des images.
    Les images sont enregistrées dans : photos/salons/<nomCoiffeuse_sans_espaces>/<filename>
    """
    # Récupérer le nom de la coiffeuse et retirer les espaces
    nom_coiffeuse = instance.coiffeuse.idTblUser.nom.replace(" ", "_")

    # Construire le chemin
    return os.path.join(f'photos/salons/{nom_coiffeuse}', filename)
