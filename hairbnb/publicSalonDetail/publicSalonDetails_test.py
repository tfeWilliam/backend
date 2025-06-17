# hairbnb/salon/tests/test_salon_details.py

from unittest.mock import MagicMock
from decimal import Decimal

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
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    photo_profil = models.URLField(null=True, blank=True)
    numero_telephone = models.CharField(max_length=20, null=True, blank=True)


class TblClient(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)
    nom_commercial = models.CharField(max_length=100, null=True, blank=True)


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)
    slogan = models.CharField(max_length=255, null=True, blank=True)
    a_propos = models.TextField(null=True, blank=True)
    logo_salon = models.URLField(null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)  # Simuler comme un CharField
    adresse = models.ForeignKey('TblAdresse', on_delete=models.SET_NULL, null=True)

    def get_proprietaire(self):
        relation = TblCoiffeuseSalon.objects.filter(salon=self, est_proprietaire=True).first()
        return relation.coiffeuse if relation else None


class TblCoiffeuseSalon(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    est_proprietaire = models.BooleanField(default=False)


class TblAvis(models.Model):
    salon = models.ForeignKey(TblSalon, related_name='avis', on_delete=models.CASCADE)
    client = models.ForeignKey(TblClient, on_delete=models.SET_NULL, null=True)
    note = models.IntegerField()
    commentaire = models.TextField()


# On a besoin de ces modèles pour que le serializer ne lève pas d'erreurs d'import,
# même si on ne les utilise pas directement dans les assertions.
class TblSalonImage(models.Model): salon = models.ForeignKey(TblSalon, related_name='images', on_delete=models.CASCADE)


class TblService(models.Model): pass


class TblSalonService(models.Model):
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)


class TblHoraireCoiffeuse(models.Model): pass


class TblPromotion(models.Model): pass


class TblAdresse(models.Model): pass


# =======================================================================
# 2. TESTS DE L'API DES DÉTAILS DU SALON
# =======================================================================

class SalonDetailsAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée une configuration de test avec plusieurs coiffeuses et salons."""
        # Utilisateurs et profils coiffeuses
        user1 = TblUser.objects.create(nom="Dupont", prenom="Alice")
        cls.coiffeuse1 = TblCoiffeuse.objects.create(idTblUser=user1)

        user2 = TblUser.objects.create(nom="Martin", prenom="Bob")
        cls.coiffeuse2 = TblCoiffeuse.objects.create(idTblUser=user2)

        # Utilisateur et profil client pour les avis
        user_client = TblUser.objects.create(nom="Client", prenom="Test")
        cls.client_profile = TblClient.objects.create(idTblUser=user_client)

        # Salons
        cls.salon1 = TblSalon.objects.create(nom_salon="Salon d'Alice")
        cls.salon2 = TblSalon.objects.create(nom_salon="Salon Élégance")
        cls.salon3 = TblSalon.objects.create(nom_salon="Le Salon de Bob")

        # Relations Coiffeuse-Salon
        # Alice est propriétaire du salon 1
        TblCoiffeuseSalon.objects.create(coiffeuse=cls.coiffeuse1, salon=cls.salon1, est_proprietaire=True)
        # Alice est employée au salon 2
        TblCoiffeuseSalon.objects.create(coiffeuse=cls.coiffeuse1, salon=cls.salon2, est_proprietaire=False)
        # Bob est propriétaire du salon 3
        TblCoiffeuseSalon.objects.create(coiffeuse=cls.coiffeuse2, salon=cls.salon3, est_proprietaire=True)

        # Avis pour le salon 1
        TblAvis.objects.create(salon=cls.salon1, client=cls.client_profile, note=5, commentaire="Excellent !")
        TblAvis.objects.create(salon=cls.salon1, client=cls.client_profile, note=3, commentaire="Moyen.")

    def test_get_single_salon_details(self):
        """Vérifie la récupération des détails pour un salon spécifique."""
        url = reverse('salon-detail', kwargs={'salon_id': self.salon1.idTblSalon})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nom_salon'], "Salon d'Alice")
        # Vérifie que les champs calculés du serializer fonctionnent
        self.assertEqual(response.data['nombre_avis'], 2)
        self.assertEqual(response.data['note_moyenne'], 4.0)  # (5+3)/2
        self.assertEqual(response.data['coiffeuse']['idTblUser']['nom'], 'Dupont')  # Vérifie le propriétaire

    def test_get_salon_not_found(self):
        """Vérifie qu'une erreur 404 est retournée pour un salon inexistant."""
        url = reverse('salon-detail', kwargs={'salon_id': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_salons_no_filter(self):
        """Vérifie la récupération de la liste de tous les salons sans filtre."""
        url = reverse('salon-list')  # On suppose que votre URL de liste n'a pas de nom spécifique
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

    def test_salon_list_pagination(self):
        """Vérifie que la pagination de la liste des salons fonctionne."""
        url = reverse('salon-list') + '?limit=2&offset=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 2)
        # L'offset est de 1, donc le premier résultat doit être le salon2
        self.assertEqual(response.data['results'][0]['nom_salon'], 'Salon Élégance')

    def test_salon_list_filter_by_coiffeuse(self):
        """Vérifie le filtre pour lister les salons d'une coiffeuse."""
        url = reverse('salon-list') + f'?coiffeuse_id={self.coiffeuse1.idTblUser_id}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Alice travaille dans 2 salons
        salon_names = {item['nom_salon'] for item in response.data['results']}
        self.assertIn("Salon d'Alice", salon_names)
        self.assertIn("Salon Élégance", salon_names)

    def test_salon_list_filter_by_coiffeuse_and_proprietaire(self):
        """Vérifie le filtre pour lister les salons où une coiffeuse est propriétaire."""
        url = reverse('salon-list') + f'?coiffeuse_id={self.coiffeuse1.idTblUser_id}&est_proprietaire=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Alice est propriétaire d'un seul salon
        self.assertEqual(response.data['results'][0]['nom_salon'], "Salon d'Alice")