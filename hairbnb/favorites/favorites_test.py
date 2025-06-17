# hairbnb/favorites/tests/test_favorites.py

import uuid
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
    # Utilisation d'un AutoField simple pour la facilité des tests.
    idTblUser = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, default='User')


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)
    logo_salon = models.URLField(blank=True, null=True)
    # Simuler d'autres champs pour le TblSalonSerializer
    slogan = models.CharField(max_length=255, default='')


class TblFavorite(models.Model):
    idTblFavorite = models.AutoField(primary_key=True)
    user = models.ForeignKey(TblUser, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Assure qu'un utilisateur ne peut ajouter un salon en favori qu'une seule fois
        unique_together = ('user', 'salon')


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
# Note : Pour que cela fonctionne, vous devrez ajuster les chemins d'import
# en fonction de la structure de votre projet.
from hairbnb.favorites.favorites_serializer import TblFavoriteSerializer, FavoriteCheckSerializer
from hairbnb.salon.salon_serializers import TblSalonSerializer  # Supposé exister


# =======================================================================
# 3. TESTS DE L'API FAVORIS
# =======================================================================

class FavoritesAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée les données initiales pour tous les tests de cette classe."""
        # Création de deux utilisateurs
        cls.user1 = TblUser.objects.create(nom="Alice")
        cls.user2 = TblUser.objects.create(nom="Bob")

        # Création de deux salons
        cls.salon1 = TblSalon.objects.create(nom_salon="Salon Chic")
        cls.salon2 = TblSalon.objects.create(nom_salon="Coiffure Moderne")

        # Alice a mis le "Salon Chic" en favori
        cls.favorite1 = TblFavorite.objects.create(user=cls.user1, salon=cls.salon1)

    def test_get_user_favorites(self):
        """Vérifie que la liste des favoris d'un utilisateur est bien retournée."""
        # On suppose que l'URL est nommée 'get-user-favorites' dans votre urls.py
        url = reverse('get-user-favorites') + f'?user={self.user1.idTblUser}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['salon']['nom_salon'], self.salon1.nom_salon)
        self.assertEqual(response.data[0]['user'], self.user1.idTblUser)

    def test_get_favorites_no_user_param(self):
        """Vérifie qu'une erreur 400 est retournée si le paramètre 'user' est manquant."""
        url = reverse('get-user-favorites')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Paramètre 'user' requis")

    def test_add_new_favorite(self):
        """Teste l'ajout d'un nouveau salon aux favoris."""
        url = reverse('add-favorite')
        data = {'user': self.user1.idTblUser, 'salon': self.salon2.idTblSalon}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TblFavorite.objects.count(), 2)
        # Vérifie que le nouveau favori existe bien pour l'utilisateur 1 et le salon 2
        self.assertTrue(TblFavorite.objects.filter(user=self.user1, salon=self.salon2).exists())

    def test_add_existing_favorite(self):
        """Teste l'ajout d'un favori qui existe déjà (doit retourner 200 OK)."""
        initial_count = TblFavorite.objects.count()
        url = reverse('add-favorite')
        data = {'user': self.user1.idTblUser, 'salon': self.salon1.idTblSalon}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TblFavorite.objects.count(), initial_count)  # Le nombre ne doit pas changer

    def test_remove_favorite(self):
        """Teste la suppression d'un favori existant."""
        initial_count = TblFavorite.objects.count()
        url = reverse('remove-favorite')
        data = {'id': self.favorite1.idTblFavorite}

        response = self.client.delete(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TblFavorite.objects.count(), initial_count - 1)

    def test_remove_nonexistent_favorite(self):
        """Teste la suppression d'un favori qui n'existe pas (doit retourner 404)."""
        url = reverse('remove-favorite')
        data = {'id': 999}  # ID qui n'existe pas

        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_check_favorite_exists(self):
        """Vérifie un favori existant avec l'endpoint dédié."""
        url = reverse('check-favorite') + f'?user={self.user1.idTblUser}&salon={self.salon1.idTblSalon}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifie que le serializer 'FavoriteCheckSerializer' est bien utilisé
        self.assertEqual(response.data['salon'], self.salon1.idTblSalon)
        self.assertIsInstance(response.data['salon'], int)  # Le salon doit être un entier
        self.assertEqual(response.data['user'], self.user1.idTblUser)

    def test_check_favorite_does_not_exist(self):
        """Vérifie un favori non-existante avec l'endpoint dédié (doit retourner 404)."""
        url = reverse('check-favorite') + f'?user={self.user1.idTblUser}&salon={self.salon2.idTblSalon}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)