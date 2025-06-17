# hairbnb/promotion/tests/test_promotions.py

from datetime import date, timedelta
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


class TblService(models.Model):
    idTblService = models.AutoField(primary_key=True)
    intitule_service = models.CharField(max_length=100)


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)


class TblUser(models.Model):
    idTblUser = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblCoiffeuseSalon(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)


class TblPromotion(models.Model):
    idPromotion = models.AutoField(primary_key=True)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE, related_name='promotions')
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def is_active(self): return self.start_date <= timezone.now() <= self.end_date


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.promotion.business_logique import PromotionManager
# Simuler l'import manquant pour la vue create_promotion
from hairbnb.salon_services import salon_services_business_logic

salon_services_business_logic.ServiceData = lambda service: {"id": service.idTblService,
                                                             "nom": service.intitule_service}


# =======================================================================
# 3. TESTS DE LA LOGIQUE MÉTIER (PromotionManager)
# =======================================================================
class PromotionManagerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = TblService.objects.create(intitule_service="Test Service")
        now = timezone.now()

        # 1 promotion active
        TblPromotion.objects.create(service=cls.service, discount_percentage=10, start_date=now - timedelta(days=1),
                                    end_date=now + timedelta(days=1))
        # 2 promotions à venir
        TblPromotion.objects.create(service=cls.service, discount_percentage=15, start_date=now + timedelta(days=2),
                                    end_date=now + timedelta(days=4))
        TblPromotion.objects.create(service=cls.service, discount_percentage=20, start_date=now + timedelta(days=5),
                                    end_date=now + timedelta(days=7))
        # 6 promotions expirées (pour tester la pagination)
        for i in range(6):
            TblPromotion.objects.create(service=cls.service, discount_percentage=5,
                                        start_date=now - timedelta(days=10 + i), end_date=now - timedelta(days=8 + i))

    def test_promotion_categorization_and_counts(self):
        """Vérifie que le manager catégorise et compte correctement les promotions."""
        manager = PromotionManager(self.service)
        counts = manager.get_counts()

        self.assertEqual(counts['active'], 1)
        self.assertEqual(counts['upcoming'], 2)
        self.assertEqual(counts['expired'], 6)

    def test_get_active_promotion(self):
        """Vérifie la récupération de la promotion active."""
        manager = PromotionManager(self.service)
        active_promo = manager.get_active()
        self.assertIsNotNone(active_promo)
        self.assertEqual(active_promo['status'], 'active')

    def test_get_expired_pagination(self):
        """Vérifie que la pagination des promotions expirées fonctionne."""
        manager = PromotionManager(self.service)

        # Première page
        expired_page1 = manager.get_expired(page=1, page_size=5)
        self.assertEqual(len(expired_page1['results']), 5)
        self.assertEqual(expired_page1['page'], 1)
        self.assertEqual(expired_page1['total_pages'], 2)
        self.assertEqual(expired_page1['total_items'], 6)

        # Deuxième page
        expired_page2 = manager.get_expired(page=2, page_size=5)
        self.assertEqual(len(expired_page2['results']), 1)
        self.assertEqual(expired_page2['page'], 2)


# =======================================================================
# 4. TESTS DE L'API PROMOTIONS
# =======================================================================
class PromotionAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = TblUser.objects.create(nom="Coiffeuse", prenom="Test")
        cls.coiffeuse = TblCoiffeuse.objects.create(idTblUser=cls.user)
        cls.salon = TblSalon.objects.create(nom_salon="Le Salon")
        cls.service = TblService.objects.create(intitule_service="Coupe Dame")
        TblCoiffeuseSalon.objects.create(coiffeuse=cls.coiffeuse, salon=cls.salon)

        # Promotion existante pour les tests de MAJ, suppression et chevauchement
        cls.existing_promo = TblPromotion.objects.create(
            service=cls.service, salon=cls.salon, discount_percentage=20,
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=20)
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_create_promotion_success(self):
        """Teste la création réussie d'une promotion."""
        url = reverse('create-promotion',
                      kwargs={'salon_id': self.salon.idTblSalon, 'service_id': self.service.idTblService})
        data = {
            "discount_percentage": 15.0,
            "start_date": (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "end_date": (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Promotion créée avec succès", response.data['message'])
        self.assertTrue(TblPromotion.objects.filter(discount_percentage=15.0).exists())

    def test_create_promotion_overlap_fails(self):
        """Vérifie que la création échoue si les dates chevauchent une promotion existante."""
        url = reverse('create-promotion',
                      kwargs={'salon_id': self.salon.idTblSalon, 'service_id': self.service.idTblService})
        # Dates qui chevauchent self.existing_promo
        data = {
            "discount_percentage": 25.0,
            "start_date": (timezone.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            "end_date": (timezone.now() + timedelta(days=25)).strftime('%Y-%m-%d')
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("chevauchent", response.data['error'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_promotion_success(self):
        """Teste la mise à jour réussie d'une promotion."""
        url = reverse('update-promotion',
                      kwargs={'salon_id': self.salon.idTblSalon, 'service_id': self.service.idTblService,
                              'promotion_id': self.existing_promo.idPromotion})
        data = {
            "discount_percentage": 22.0,
            "start_date": self.existing_promo.start_date.strftime('%Y-%m-%d'),
            "end_date": self.existing_promo.end_date.strftime('%Y-%m-%d')
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['promotion']['discount_percentage']), 22.0)

        self.existing_promo.refresh_from_db()
        self.assertEqual(self.existing_promo.discount_percentage, 22.0)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_promotion_unauthorized(self):
        """Vérifie que la mise à jour échoue si l'utilisateur n'a pas accès au salon."""
        # Créer un autre utilisateur qui n'est pas lié au salon
        other_user = TblUser.objects.create(nom="Autre", prenom="User")
        TblCoiffeuse.objects.create(idTblUser=other_user)
        self.client.force_authenticate(user=other_user)  # S'authentifier en tant que cet autre utilisateur

        url = reverse('update-promotion',
                      kwargs={'salon_id': self.salon.idTblSalon, 'service_id': self.service.idTblService,
                              'promotion_id': self.existing_promo.idPromotion})
        data = {"discount_percentage": 50.0}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Accès interdit", response.data['detail'])

    def test_delete_promotion(self):
        """Teste la suppression réussie d'une promotion."""
        promo_to_delete = TblPromotion.objects.create(
            service=self.service, salon=self.salon, discount_percentage=99,
            start_date=timezone.now(), end_date=timezone.now() + timedelta(days=1)
        )
        initial_count = TblPromotion.objects.count()

        url = reverse('delete-promotion', kwargs={'promotion_id': promo_to_delete.idPromotion})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TblPromotion.objects.count(), initial_count - 1)