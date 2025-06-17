# hairbnb/profil/tests/test_profil.py

import uuid
import io
from PIL import Image
from unittest.mock import patch, MagicMock

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


# Modèles de base pour l'adresse
class TblLocalite(models.Model):
    commune = models.CharField(max_length=40)
    code_postal = models.CharField(max_length=6)


class TblRue(models.Model):
    nom_rue = models.CharField(max_length=100)
    localite = models.ForeignKey(TblLocalite, on_delete=models.CASCADE)


class TblAdresse(models.Model):
    numero = models.CharField(max_length=15)
    rue = models.ForeignKey(TblRue, on_delete=models.CASCADE)


# Modèles de référence pour l'utilisateur
class TblRole(models.Model):
    nom = models.CharField(max_length=50, unique=True)


class TblSexe(models.Model):
    libelle = models.CharField(max_length=10, unique=True)


class TblType(models.Model):
    libelle = models.CharField(max_length=15, unique=True)


# Modèle Utilisateur principal
class TblUser(models.Model):
    idTblUser = models.AutoField(primary_key=True)  # Utiliser AutoField pour simplifier les tests
    uuid = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    numero_telephone = models.CharField(max_length=20)
    date_naissance = models.DateField()
    photo_profil = models.ImageField(upload_to='test_photos/', null=True, blank=True)
    adresse = models.ForeignKey(TblAdresse, on_delete=models.SET_NULL, null=True)
    role = models.ForeignKey(TblRole, on_delete=models.PROTECT)
    sexe_ref = models.ForeignKey(TblSexe, on_delete=models.PROTECT)
    type_ref = models.ForeignKey(TblType, on_delete=models.PROTECT)

    def get_type(self): return self.type_ref.libelle

    def get_role(self): return self.role.nom


# Modèles spécifiques Client et Coiffeuse
class TblClient(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)
    nom_commercial = models.CharField(max_length=50, blank=True)


# Dépendances pour les tests de suppression
class TblSalon(models.Model): id = models.AutoField(primary_key=True)


class TblRendezVous(models.Model):
    client = models.ForeignKey(TblClient, on_delete=models.CASCADE, null=True)
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE, null=True)


class TblFavorite(models.Model): user = models.ForeignKey(TblUser, on_delete=models.CASCADE)


class TblAvis(models.Model): client = models.ForeignKey(TblClient, on_delete=models.SET_NULL, null=True)


class TblCart(models.Model): user = models.OneToOneField(TblUser, on_delete=models.CASCADE)


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.profil.profil_serializers import UserCreationSerializer, DeleteProfileUserSerializer


# =======================================================================
# 3. HELPER FUNCTION
# =======================================================================
def create_dummy_image(name='test.png'):
    file_io = io.BytesIO()
    image = Image.new('RGB', (100, 100), 'white')
    image.save(file_io, 'PNG')
    file_io.seek(0)
    return SimpleUploadedFile(name, file_io.read(), content_type='image/png')


# =======================================================================
# 4. TESTS DES SERIALIZERS
# =======================================================================

class UserCreationSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        TblRole.objects.create(nom='user')
        TblSexe.objects.create(libelle='Homme')
        TblSexe.objects.create(libelle='Femme')
        TblType.objects.create(libelle='Client')
        TblType.objects.create(libelle='Coiffeuse')

    def test_create_client_profile_success(self):
        """Teste la création réussie d'un profil Client."""
        data = {
            "userUuid": str(uuid.uuid4()),
            "email": "client@test.com",
            "type": "Client",
            "nom": "Doe",
            "prenom": "John",
            "sexe": "Homme",
            "telephone": "123456789",
            "date_naissance": "01-01-1990",
            "code_postal": "1000",
            "commune": "Bruxelles",
            "rue": "Rue Neuve",
            "numero": "1",
            "photo_profil": create_dummy_image()
        }

        serializer = UserCreationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()

        self.assertIsNotNone(user)
        self.assertEqual(TblUser.objects.count(), 1)
        self.assertEqual(TblClient.objects.count(), 1)
        self.assertEqual(TblCoiffeuse.objects.count(), 0)
        self.assertTrue(TblUser.objects.first().photo_profil.name.endswith('.png'))

    def test_create_coiffeuse_profile_success(self):
        """Teste la création réussie d'un profil Coiffeuse."""
        data = {
            "userUuid": str(uuid.uuid4()), "email": "coiffeuse@test.com", "type": "Coiffeuse",
            "nom": "Smith", "prenom": "Jane", "sexe": "Femme", "telephone": "987654321",
            "date_naissance": "01-01-1992", "code_postal": "1050", "commune": "Ixelles",
            "rue": "Avenue Louise", "numero": "100", "nom_commercial": "Jane's Hair"
        }
        serializer = UserCreationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertIsNotNone(user)
        self.assertEqual(TblCoiffeuse.objects.count(), 1)
        self.assertEqual(TblClient.objects.count(), 0)
        self.assertEqual(TblCoiffeuse.objects.first().nom_commercial, "Jane's Hair")

    def test_validation_fails_duplicate_email(self):
        """Vérifie que le serializer échoue si l'email existe déjà."""
        TblUser.objects.create(
            uuid=str(uuid.uuid4()), email="client@test.com", nom="Test", prenom="User",
            date_naissance="1990-01-01", role=TblRole.objects.first(),
            sexe_ref=TblSexe.objects.first(), type_ref=TblType.objects.first()
        )
        data = {"userUuid": str(uuid.uuid4()), "email": "client@test.com", "type": "Client",
                "nom": "Doe", "prenom": "John", "sexe": "Homme", "telephone": "123456789",
                "date_naissance": "01-01-1990", "code_postal": "1000", "commune": "Bruxelles",
                "rue": "Rue Neuve", "numero": "1"}
        serializer = UserCreationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class DeleteProfileSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée un utilisateur avec de nombreuses données liées."""
        role = TblRole.objects.create(nom='user')
        sexe = TblSexe.objects.create(libelle='Femme')
        type_cli = TblType.objects.create(libelle='Client')

        cls.user_to_delete = TblUser.objects.create(
            uuid=str(uuid.uuid4()), email="delete@me.com", nom="ToDelete", prenom="User",
            date_naissance="1990-01-01", role=role, sexe_ref=sexe, type_ref=type_cli
        )
        cls.client = TblClient.objects.create(idTblUser=cls.user_to_delete)

        # Créer des données liées
        cls.rdv = TblRendezVous.objects.create(client=cls.client)
        cls.fav = TblFavorite.objects.create(user=cls.user_to_delete)
        cls.avis = TblAvis.objects.create(client=cls.client)
        cls.cart = TblCart.objects.create(user=cls.user_to_delete)

    def test_delete_profile_logic(self):
        """Vérifie que la logique de suppression supprime bien toutes les données associées."""
        self.assertEqual(TblRendezVous.objects.count(), 1)
        self.assertEqual(TblFavorite.objects.count(), 1)
        self.assertEqual(TblAvis.objects.count(), 1)
        self.assertEqual(TblCart.objects.count(), 1)

        serializer = DeleteProfileUserSerializer(
            data={'anonymize_reviews': False},  # On supprime les avis pour ce test
            context={'id_cible': self.user_to_delete.idTblUser}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        summary = serializer.save()

        # Vérifier que les données ont été supprimées
        self.assertEqual(summary['deleted_items']['rdv_as_client'], 1)
        self.assertEqual(summary['deleted_items']['favoris_user'], 1)
        self.assertEqual(summary['deleted_items']['avis_deleted'], 1)
        self.assertEqual(summary['deleted_items']['cart'], 1)

        # Vérifier que les tables sont vides
        self.assertEqual(TblUser.objects.count(), 0)
        self.assertEqual(TblRendezVous.objects.count(), 0)
        self.assertEqual(TblFavorite.objects.count(), 0)
        self.assertEqual(TblAvis.objects.count(), 0)
        self.assertEqual(TblCart.objects.count(), 0)


# =======================================================================
# 5. TESTS DES VUES API
# =======================================================================
class ProfileAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        role = TblRole.objects.create(nom='user')
        sexe = TblSexe.objects.create(libelle='Homme')
        type_ref = TblType.objects.create(libelle='Client')

        cls.user = TblUser.objects.create(
            uuid="test-uuid-123", email="get@me.com", nom="GetUser", prenom="Test",
            date_naissance="1995-05-05", role=role, sexe_ref=sexe, type_ref=type_ref
        )

    def test_get_user_profile(self):
        """Teste la récupération réussie d'un profil utilisateur."""
        url = reverse('get-user-profile', kwargs={'userUuid': self.user.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['nom'], 'GetUser')

    # Mock de la logique de suppression pour ne tester que la vue
    @patch('hairbnb.profil.profil_serializers.DeleteProfileUserSerializer.save')
    @patch('firebase_admin.auth.get_user_by_email')
    @patch('firebase_admin.auth.delete_user')
    @patch('decorators.decorators.firebase_authenticated')
    def test_delete_my_profile_firebase(self, mock_auth_deco, mock_delete_firebase, mock_get_firebase, mock_save):
        """Teste la suppression de son propre profil via le point de terminaison sécurisé."""

        # Simuler un utilisateur authentifié via le décorateur
        mock_auth_deco.return_value = lambda f: f
        self.client.force_authenticate(user=self.user)

        # Attacher l'uuid au mock de l'utilisateur de la requête
        self.user.uuid = "test-uuid-123"

        # Simuler le retour de la logique de suppression
        mock_save.return_value = {"deleted_items": {"user_account": 1}}

        url = reverse('delete-my-profile-firebase')
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_save.assert_called_once()
        mock_delete_firebase.assert_called_once()