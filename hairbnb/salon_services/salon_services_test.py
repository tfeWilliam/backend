# hairbnb/salon_services/tests/test_salon_services.py

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
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
    # Simuler la relation type_ref
    type_ref = MagicMock()
    type_ref.libelle = 'Coiffeuse'


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)


class TblCoiffeuseSalon(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    est_proprietaire = models.BooleanField(default=False)


class TblCategorie(models.Model):
    idTblCategorie = models.AutoField(primary_key=True)
    intitule_categorie = models.CharField(max_length=100)


class TblService(models.Model):
    idTblService = models.AutoField(primary_key=True)
    intitule_service = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    categorie = models.ForeignKey(TblCategorie, on_delete=models.SET_NULL, null=True)


class TblSalonService(models.Model):
    idSalonService = models.AutoField(primary_key=True)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)


class TblPrix(models.Model): prix = models.DecimalField(max_digits=10, decimal_places=2)


class TblTemps(models.Model): minutes = models.IntegerField()


class TblServicePrix(models.Model):
    service = models.ForeignKey(TblService, on_delete=models.CASCADE, related_name='service_prix')
    prix = models.ForeignKey(TblPrix, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, null=True)


class TblServiceTemps(models.Model):
    service = models.ForeignKey(TblService, on_delete=models.CASCADE, related_name='service_temps')
    temps = models.ForeignKey(TblTemps, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, null=True)


class TblPromotion(models.Model):
    service = models.ForeignKey(TblService, on_delete=models.CASCADE, related_name='promotions')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.salon_services.salon_services_business_logic import ServiceData


# =======================================================================
# 3. TESTS DE LA LOGIQUE MÉTIER
# =======================================================================
class ServiceDataTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = TblService.objects.create(intitule_service="Test Service")
        prix = TblPrix.objects.create(prix=Decimal("100.00"))
        temps = TblTemps.objects.create(minutes=60)
        TblServicePrix.objects.create(service=cls.service, prix=prix)
        TblServiceTemps.objects.create(service=cls.service, temps=temps)

        # Promotion active
        TblPromotion.objects.create(
            service=cls.service, discount_percentage=20,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1)
        )
        # Promotion future
        TblPromotion.objects.create(
            service=cls.service, discount_percentage=30,
            start_date=timezone.now() + timezone.timedelta(days=2),
            end_date=timezone.now() + timezone.timedelta(days=4)
        )

    def test_service_data_with_active_promotion(self):
        """Vérifie que ServiceData calcule correctement le prix final avec une promotion."""
        service_data = ServiceData(self.service).to_dict()

        self.assertIsNotNone(service_data['promotion_active'])
        self.assertEqual(service_data['prix'], Decimal("100.00"))
        self.assertEqual(service_data['prix_final'], Decimal("80.00"))  # 100 - 20%
        self.assertEqual(len(service_data['promotions_a_venir']), 1)


# =======================================================================
# 4. TESTS DES VUES API
# =======================================================================
class SalonServiceAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = TblUser.objects.create()
        cls.coiffeuse = TblCoiffeuse.objects.create(idTblUser=cls.user)
        cls.salon = TblSalon.objects.create(nom_salon="Le Salon Principal")
        TblCoiffeuseSalon.objects.create(coiffeuse=cls.coiffeuse, salon=cls.salon, est_proprietaire=True)

        cls.categorie = TblCategorie.objects.create(intitule_categorie="Coupes")

        # Un service global qui n'est pas encore dans le salon
        cls.global_service = TblService.objects.create(intitule_service="Shampoing Global", categorie=cls.categorie)

        # Un service déjà dans le salon
        cls.existing_service = TblService.objects.create(intitule_service="Coupe Dame", categorie=cls.categorie)
        cls.salon_service_link = TblSalonService.objects.create(salon=cls.salon, service=cls.existing_service)
        prix = TblPrix.objects.create(prix=Decimal("50.00"))
        temps = TblTemps.objects.create(minutes=45)
        TblServicePrix.objects.create(service=cls.existing_service, prix=prix, salon=cls.salon)
        TblServiceTemps.objects.create(service=cls.existing_service, temps=temps, salon=cls.salon)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    @patch('decorators.decorators.is_owner', lambda **kwargs: lambda f: f)
    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_create_new_global_service(self):
        """Teste la création d'un nouveau service global et son ajout automatique au salon."""
        url = reverse('create-new-global-service')
        data = {
            "userId": self.user.idTblUser,
            "intitule_service": "Nouvelle Couleur",
            "description": "Une couleur éclatante.",
            "prix": 120.50,
            "temps_minutes": 90,
            "categorie_id": self.categorie.idTblCategorie
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')

        # Vérifier que le service a été créé dans la table globale ET dans le salon
        self.assertTrue(TblService.objects.filter(intitule_service="Nouvelle Couleur").exists())
        self.assertTrue(
            TblSalonService.objects.filter(salon=self.salon, service__intitule_service="Nouvelle Couleur").exists())

    @patch('decorators.decorators.is_owner', lambda **kwargs: lambda f: f)
    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_add_existing_service_to_salon(self):
        """Teste l'ajout d'un service global existant à un salon."""
        url = reverse('add-existing-service-to-salon')
        data = {
            "userId": self.user.idTblUser,
            "service_id": self.global_service.idTblService,
            "prix": 30.00,
            "temps_minutes": 20
        }

        service_count_before = TblService.objects.count()
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Le nombre de services globaux ne doit pas changer
        self.assertEqual(TblService.objects.count(), service_count_before)
        # Mais le service doit maintenant être lié au salon
        self.assertTrue(TblSalonService.objects.filter(salon=self.salon, service=self.global_service).exists())

    @patch('decorators.decorators.is_owner', lambda **kwargs: lambda f: f)
    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_remove_service_from_salon(self):
        """Teste la suppression d'un service d'un salon (sans supprimer le service global)."""
        url = reverse('remove-service-from-salon', kwargs={'salon_service_id': self.salon_service_link.idSalonService})
        data = {"userId": self.user.idTblUser}

        service_count_before = TblService.objects.count()
        salon_service_count_before = TblSalonService.objects.count()

        response = self.client.delete(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # La relation salon-service est supprimée
        self.assertEqual(TblSalonService.objects.count(), salon_service_count_before - 1)
        # Mais le service global existe toujours
        self.assertEqual(TblService.objects.count(), service_count_before)
        self.assertTrue(TblService.objects.filter(idTblService=self.existing_service.idTblService).exists())

    @patch('decorators.decorators.is_owner', lambda **kwargs: lambda f: f)
    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_service(self):
        """Teste la mise à jour du prix et du temps d'un service."""
        url = reverse('update-service', kwargs={'service_id': self.existing_service.idTblService})
        data = {
            "userId": self.user.idTblUser,
            "prix": 55.00,
            "temps_minutes": 50
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que le prix et le temps ont été mis à jour dans les tables de liaison
        new_prix = TblServicePrix.objects.get(service=self.existing_service).prix.prix
        new_temps = TblServiceTemps.objects.get(service=self.existing_service).temps.minutes

        self.assertEqual(new_prix, Decimal("55.00"))
        self.assertEqual(new_temps, 50)