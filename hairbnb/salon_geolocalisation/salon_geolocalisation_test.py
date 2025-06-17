# hairbnb/salon_geolocalisation/tests/test_salon_geolocalisation.py

import uuid
from unittest.mock import patch, MagicMock

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


class TblUser(models.Model):
    idTblUser = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=40, unique=True, default=uuid.uuid4)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    photo_profil = models.URLField(null=True, blank=True)

    def get_role(self): return "user"

    def get_type(self): return "client"


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)
    nom_commercial = models.CharField(max_length=100, null=True, blank=True)


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)
    slogan = models.CharField(max_length=255, null=True, blank=True)
    logo_salon = models.URLField(null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)


class TblCoiffeuseSalon(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    est_proprietaire = models.BooleanField(default=False)


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.salon_geolocalisation.salon_geolocalisation_views import haversine


# =======================================================================
# 3. TESTS DE LA LOGIQUE MÉTIER (Haversine)
# =======================================================================
class HaversineTests(TestCase):
    def test_haversine_calculation(self):
        """Vérifie que la formule de Haversine calcule une distance correcte."""
        # Coordonnées approximatives de Bruxelles et Paris
        lat1, lon1 = 50.8503, 4.3517  # Bruxelles
        lat2, lon2 = 48.8566, 2.3522  # Paris

        distance = haversine(lat1, lon1, lat2, lon2)

        # La distance est d'environ 264 km. On vérifie qu'elle est dans une plage raisonnable.
        self.assertAlmostEqual(distance, 264, delta=5)


# =======================================================================
# 4. TESTS DES VUES API
# =======================================================================
class SalonGeolocalisationAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée des salons à différentes positions pour les tests."""
        user1 = TblUser.objects.create(nom="Coiffeuse", prenom="A")
        coiffeuse1 = TblCoiffeuse.objects.create(idTblUser=user1)

        # Un salon proche de Bruxelles (Grand-Place)
        cls.salon_proche = TblSalon.objects.create(
            nom_salon="Salon du Centre",
            position="50.8467,4.3525"  # Proche de la Grand-Place
        )
        TblCoiffeuseSalon.objects.create(coiffeuse=coiffeuse1, salon=cls.salon_proche, est_proprietaire=True)

        # Un salon plus éloigné à Anvers
        cls.salon_loin = TblSalon.objects.create(
            nom_salon="Salon d'Anvers",
            position="51.2194,4.4025"
        )

        # Un salon sans position
        cls.salon_sans_position = TblSalon.objects.create(
            nom_salon="Salon non géolocalisé",
            position=None
        )

        # Point de référence du client pour les tests (près de la Grand-Place)
        cls.client_lat = 50.8503
        cls.client_lon = 4.3517

    def setUp(self):
        """Authentifie un utilisateur pour les tests qui le nécessitent."""
        user = TblUser.objects.create(nom="Test", prenom="User")
        self.client.force_authenticate(user=user)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_salons_proches_success(self):
        """Vérifie que seuls les salons dans le rayon spécifié sont retournés."""
        url = reverse('salons-proches')
        # On demande les salons dans un rayon de 5 km
        params = {'lat': self.client_lat, 'lon': self.client_lon, 'distance': 5}

        response = self.client.get(url, params)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['salons'][0]['nom'], 'Salon du Centre')
        self.assertIn('distance', data['salons'][0])
        self.assertLess(data['salons'][0]['distance'], 5)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_salons_proches_large_rayon(self):
        """Vérifie qu'un rayon plus large inclut plus de salons."""
        url = reverse('salons-proches')
        # On demande les salons dans un rayon de 100 km
        params = {'lat': self.client_lat, 'lon': self.client_lon, 'distance': 100}

        response = self.client.get(url, params)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 2)  # Doit inclure Bruxelles et Anvers

        # Vérifie que les salons sont triés par distance
        self.assertEqual(data['salons'][0]['nom'], 'Salon du Centre')
        self.assertEqual(data['salons'][1]['nom'], "Salon d'Anvers")

    def test_get_all_salons(self):
        """Vérifie la récupération de la liste de tous les salons."""
        url = reverse('get-all-salons')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 3)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_get_salon_details_success(self):
        """Vérifie la récupération des détails d'un salon spécifique."""
        url = reverse('get-salon-details', kwargs={'salon_id': self.salon_proche.idTblSalon})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['salon']['nom'], 'Salon du Centre')

        # Vérifie que la géolocalisation est correctement parsée
        self.assertAlmostEqual(data['salon']['latitude'], 50.8467, delta=0.001)
        self.assertAlmostEqual(data['salon']['longitude'], 4.3525, delta=0.001)

        # Vérifie que les détails de la coiffeuse sont inclus
        self.assertEqual(len(data['salon']['coiffeuses_details']), 1)
        self.assertEqual(data['salon']['coiffeuses_details'][0]['nom'], 'Coiffeuse')

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_get_salon_details_not_found(self):
        """Vérifie la réponse pour un salon qui n'existe pas."""
        url = reverse('get-salon-details', kwargs={'salon_id': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['status'], 'error')