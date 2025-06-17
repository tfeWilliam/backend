# hairbnb/gallery/tests/test_gallery.py

import io
from PIL import Image
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# =======================================================================
# 1. MOCK MODELS
# NOTE : Ces modèles sont des simulations pour permettre aux tests de
# fonctionner sans avoir le code complet du projet.
# =======================================================================
from django.db import models


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)


class TblSalonImage(models.Model):
    id = models.AutoField(primary_key=True)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, related_name='images')
    # ImageField est utilisé pour simuler le stockage de fichiers
    image = models.ImageField(upload_to='test_salon_images/')


# =======================================================================
# 2. HELPER FUNCTION
# =======================================================================
def create_dummy_image(name='test.png', size_kb=100):
    """Crée un faux fichier image en mémoire pour les tests."""
    file_io = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'white')
    image.save(file_io, 'PNG')
    # Simuler la taille du fichier si nécessaire
    file_io.seek(0, io.SEEK_END)
    actual_size = file_io.tell()
    if size_kb * 1024 > actual_size:
        file_io.write(b'\0' * (size_kb * 1024 - actual_size))

    file_io.seek(0)
    return SimpleUploadedFile(name, file_io.read(), content_type='image/png')


# =======================================================================
# 3. TESTS DE L'API GALLERY
# =======================================================================

class GalleryAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée un salon et quelques images pour les tests."""
        cls.salon = TblSalon.objects.create(nom_salon="Salon de Test")

        # Créer 2 images initiales pour le salon
        cls.image1 = TblSalonImage.objects.create(salon=cls.salon, image=create_dummy_image('img1.png'))
        cls.image2 = TblSalonImage.objects.create(salon=cls.salon, image=create_dummy_image('img2.png'))

    def test_list_salon_images(self):
        """Vérifie que la liste des images d'un salon est correctement retournée."""
        url = reverse('salon-image-list', kwargs={'salon_id': self.salon.idTblSalon})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Vérifie que l'ID de l'image est bien dans la réponse
        self.assertEqual(response.data[0]['id'], self.image1.id)

    def test_add_images_to_salon_success(self):
        """Teste l'ajout réussi de plusieurs images à un salon."""
        url = reverse('add-images-to-salon')
        images_to_upload = [
            create_dummy_image('new1.png'),
            create_dummy_image('new2.png'),
            create_dummy_image('new3.png'),
        ]
        data = {
            'salon': self.salon.idTblSalon,
            'image': images_to_upload
        }

        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['image_ids']), 3)
        self.assertEqual(TblSalonImage.objects.filter(salon=self.salon).count(), 5)  # 2 initiales + 3 nouvelles

    def test_add_images_too_few(self):
        """Teste l'échec si moins de 3 images sont envoyées."""
        url = reverse('add-images-to-salon')
        data = {
            'salon': self.salon.idTblSalon,
            'image': [create_dummy_image('one.png'), create_dummy_image('two.png')]
        }
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Veuillez télécharger au moins 3 images.")

    def test_add_images_too_many(self):
        """Teste l'échec si plus de 12 images sont envoyées."""
        url = reverse('add-images-to-salon')
        images_to_upload = [create_dummy_image(f'img{i}.png') for i in range(13)]
        data = {'salon': self.salon.idTblSalon, 'image': images_to_upload}

        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Vous ne pouvez pas télécharger plus de 12 images.")

    def test_add_images_file_too_large(self):
        """Teste l'échec si une image dépasse la taille maximale de 6MB."""
        url = reverse('add-images-to-salon')
        images_to_upload = [
            create_dummy_image('small.png', size_kb=100),
            create_dummy_image('large.png', size_kb=7 * 1024),  # 7MB
            create_dummy_image('another_small.png', size_kb=100),
        ]
        data = {'salon': self.salon.idTblSalon, 'image': images_to_upload}

        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertIn("dépasse 6MB", response.data['error'])

    def test_add_images_salon_not_found(self):
        """Teste l'échec si l'ID du salon n'existe pas."""
        url = reverse('add-images-to-salon')
        data = {
            'salon': 999,  # ID inexistant
            'image': [create_dummy_image(f'img{i}.png') for i in range(3)]
        }
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Salon introuvable.")

    def test_delete_salon_image(self):
        """Teste la suppression réussie d'une image de salon."""
        image_to_delete_id = self.image1.id
        initial_count = TblSalonImage.objects.count()

        url = reverse('salon-image-delete', kwargs={'id': image_to_delete_id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TblSalonImage.objects.count(), initial_count - 1)
        # Vérifie que l'image spécifique a bien été supprimée
        with self.assertRaises(TblSalonImage.DoesNotExist):
            TblSalonImage.objects.get(id=image_to_delete_id)

    def test_delete_nonexistent_image(self):
        """Teste la suppression d'une image qui n'existe pas (doit retourner 404)."""
        url = reverse('salon-image-delete', kwargs={'id': 999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)