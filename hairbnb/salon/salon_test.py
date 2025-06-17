# hairbnb/salon/tests/test_salon.py

import io
from PIL import Image
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# =======================================================================
# 1. MOCK MODELS
# NOTE : Ces modèles sont des simulations pour permettre aux tests de
# fonctionner sans avoir le code complet du projet.
# =======================================================================
from django.db import models


class TblUser(models.Model):
    idTblUser = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, default='User')


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblAdresse(models.Model):
    idTblAdresse = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=10)
    # autres champs simulés
    rue = MagicMock()


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)
    slogan = models.CharField(max_length=255, blank=True)
    a_propos = models.TextField(blank=True)
    logo_salon = models.ImageField(upload_to='test_logos/', null=True, blank=True)
    numero_tva = models.CharField(max_length=50, blank=True, null=True, unique=True)
    adresse = models.ForeignKey(TblAdresse, on_delete=models.SET_NULL, null=True)
    position = models.CharField(max_length=255, blank=True)

    def get_proprietaire(self):
        relation = TblCoiffeuseSalon.objects.filter(salon=self, est_proprietaire=True).first()
        return relation.coiffeuse if relation else None


class TblCoiffeuseSalon(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    est_proprietaire = models.BooleanField(default=False)


# Simuler l'existence des autres serializers pour éviter les erreurs d'import
from hairbnb.serializers import salon_services_serializers

salon_services_serializers.ServiceSerializer = MagicMock()


# =======================================================================
# 2. HELPER FUNCTION
# =======================================================================
def create_dummy_image(name='logo.png'):
    """Crée un faux fichier image en mémoire pour les tests."""
    file_io = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'blue')
    image.save(file_io, 'PNG')
    file_io.seek(0)
    return SimpleUploadedFile(name, file_io.read(), content_type='image/png')


# =======================================================================
# 3. TESTS DE L'API SALON
# =======================================================================

class SalonAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée des données de base pour les tests."""
        # Coiffeuse propriétaire d'un salon
        cls.user_owner = TblUser.objects.create(nom="Proprio")
        cls.coiffeuse_owner = TblCoiffeuse.objects.create(idTblUser=cls.user_owner)

        # Coiffeuse qui n'a pas encore de salon
        cls.user_no_salon = TblUser.objects.create(nom="SansSalon")
        cls.coiffeuse_no_salon = TblCoiffeuse.objects.create(idTblUser=cls.user_no_salon)

        # Salon existant
        cls.salon = TblSalon.objects.create(nom_salon="Le Salon Existant")

        # Relation de propriété
        TblCoiffeuseSalon.objects.create(
            coiffeuse=cls.coiffeuse_owner,
            salon=cls.salon,
            est_proprietaire=True
        )

    def test_get_salon_by_coiffeuse_success(self):
        """Vérifie la récupération du salon pour une coiffeuse propriétaire."""
        url = reverse('get-salon-by-coiffeuse', kwargs={'coiffeuse_id': self.coiffeuse_owner.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La vue utilise JsonResponse, donc les données sont dans response.json()
        data = response.json()
        self.assertTrue(data['exists'])
        self.assertEqual(data['salon']['nom_salon'], self.salon.nom_salon)

    def test_get_salon_by_coiffeuse_not_owner(self):
        """Vérifie la réponse pour une coiffeuse qui n'est propriétaire d'aucun salon."""
        url = reverse('get-salon-by-coiffeuse', kwargs={'coiffeuse_id': self.coiffeuse_no_salon.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertFalse(data['exists'])
        self.assertIn("n'est propriétaire d'aucun salon", data['message'])

    def test_get_salon_by_coiffeuse_not_found(self):
        """Vérifie la réponse pour une coiffeuse qui n'existe pas."""
        url = reverse('get-salon-by-coiffeuse', kwargs={'coiffeuse_id': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.json()['exists'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_ajout_salon_success(self):
        """Teste la création réussie d'un nouveau salon."""
        self.client.force_authenticate(user=self.coiffeuse_no_salon.idTblUser)

        url = reverse('ajout-salon')
        data = {
            'idTblUser': self.coiffeuse_no_salon.pk,
            'nom_salon': 'Le Nouveau Salon',
            'slogan': 'Un style nouveau',
            'logo_salon': create_dummy_image('new_logo.png')
        }

        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')

        # Vérifier que le salon a été créé
        self.assertTrue(TblSalon.objects.filter(nom_salon='Le Nouveau Salon').exists())
        new_salon = TblSalon.objects.get(nom_salon='Le Nouveau Salon')

        # Vérifier que la relation propriétaire a bien été créée
        self.assertTrue(
            TblCoiffeuseSalon.objects.filter(
                salon=new_salon,
                coiffeuse=self.coiffeuse_no_salon,
                est_proprietaire=True
            ).exists()
        )
        self.assertIn('new_logo.png', new_salon.logo_salon.name)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_ajout_salon_missing_data(self):
        """Teste l'échec de la création si des données sont manquantes."""
        self.client.force_authenticate(user=self.coiffeuse_no_salon.idTblUser)

        url = reverse('ajout-salon')
        # 'nom_salon' est manquant, ce qui est requis par le serializer
        data = {
            'idTblUser': self.coiffeuse_no_salon.pk,
            'slogan': 'Un slogan sans nom'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('nom_salon', response.data['errors'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_ajout_salon_invalid_coiffeuse(self):
        """Teste l'échec de la création avec un ID de coiffeuse invalide."""
        # Nul besoin de s'authentifier si l'ID est invalide
        url = reverse('ajout-salon')
        data = {
            'idTblUser': 999,  # ID qui n'existe pas
            'nom_salon': 'Salon Fantôme',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('coiffeuse_id', response.data['errors'])