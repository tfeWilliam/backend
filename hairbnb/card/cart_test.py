# hairbnb/card/tests/test_cart.py

import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

# =======================================================================
# 1. MOCK MODELS
# NOTE : Ces modèles sont des simulations pour permettre aux tests de
# fonctionner sans avoir le code complet du projet. Dans votre
# projet réel, vous importeriez vos vrais modèles.
# =======================================================================

from django.db import models


class TblUser(models.Model):
    idTblUser = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    # Simule la relation inverse pour CurrentUserData
    tblclient = None

    def __str__(self):
        return self.nom


class TblPrix(models.Model):
    prix = models.DecimalField(max_digits=10, decimal_places=2)


class TblTemps(models.Model):
    minutes = models.IntegerField()


class TblService(models.Model):
    idTblService = models.AutoField(primary_key=True)
    intitule_service = models.CharField(max_length=100)
    description = models.TextField()
    # Simuler la relation many-to-many ou one-to-many
    service_prix = models.ManyToManyField(TblPrix)
    service_temps = models.ManyToManyField(TblTemps)
    # Pour la logique de get_cart
    salon_service = models.ManyToManyField('TblSalonService', related_name='services')


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblSalon(models.Model):
    coiffeuse = models.OneToOneField(TblCoiffeuse, on_delete=models.CASCADE)


class TblSalonService(models.Model):
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)


class TblPromotion(models.Model):
    idPromotion = models.AutoField(primary_key=True)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def is_active(self):
        return self.start_date <= timezone.now() <= self.end_date


class TblCart(models.Model):
    idTblCart = models.AutoField(primary_key=True)
    user = models.OneToOneField(TblUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        # Simulation simplifiée du calcul du prix total
        total = Decimal("0.00")
        for item in self.items.all():
            item_data = CartItemData(item)
            total += Decimal(str(item_data.service['prix_final'])) * item.quantity
        return float(total)


class TblCartItem(models.Model):
    idTblCartItem = models.AutoField(primary_key=True)
    cart = models.ForeignKey(TblCart, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.card.card_business_logic import CartItemData, CartData
from hairbnb.card.card_serializers import CartSerializer, CartItemSerializer
# Simule l'import manquant pour que CartData fonctionne
from hairbnb.currentUser import currentUser_business_logic

currentUser_business_logic.CurrentUserData = lambda user: {"user_id": str(user.idTblUser), "nom": user.nom}


# =======================================================================
# 3. TESTS DE LA LOGIQUE MÉTIER (Business Logic)
# =======================================================================
class CartBusinessLogicTests(TestCase):

    def setUp(self):
        # Service SANS promotion
        self.service1 = TblService.objects.create(intitule_service="Coupe Simple", description="Rapide et efficace")
        prix1 = TblPrix.objects.create(prix=Decimal("25.00"))
        self.service1.service_prix.add(prix1)

        # Service AVEC promotion
        self.service2 = TblService.objects.create(intitule_service="Couleur & Brushing",
                                                  description="Transformation complète")
        prix2 = TblPrix.objects.create(prix=Decimal("100.00"))
        self.service2.service_prix.add(prix2)

        self.promo = TblPromotion.objects.create(
            service=self.service2,
            discount_percentage=Decimal("20.00"),  # 20% de réduction
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1)
        )
        self.cart_item_promo = type('TblCartItem', (object,),
                                    {'idTblCartItem': 1, 'service': self.service2, 'quantity': 1})()

    def test_cart_item_data_sans_promotion(self):
        """Vérifie que le prix final est le prix standard s'il n'y a pas de promotion active."""
        cart_item_mock = type('TblCartItem', (object,), {'idTblCartItem': 2, 'service': self.service1, 'quantity': 1})()

        item_data = CartItemData(cart_item_mock)
        data_dict = item_data.to_dict()

        self.assertIsNone(data_dict['service']['promotion'])
        self.assertEqual(data_dict['service']['prix'], 25.00)
        self.assertEqual(data_dict['service']['prix_final'], 25.00)

    def test_cart_item_data_avec_promotion(self):
        """Vérifie que la réduction est correctement appliquée lorsqu'une promotion est active."""
        item_data = CartItemData(self.cart_item_promo)
        data_dict = item_data.to_dict()

        self.assertIsNotNone(data_dict['service']['promotion'])
        self.assertEqual(data_dict['service']['prix'], 100.00)
        self.assertEqual(data_dict['service']['prix_final'], 80.00)  # 100 - (20% de 100)
        self.assertTrue(data_dict['service']['promotion']['is_active'])


# =======================================================================
# 4. TESTS DES VUES (API Endpoints)
# =======================================================================
class CartViewsTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée les données initiales pour tous les tests de vues."""
        # Utilisateurs
        cls.user1 = TblUser.objects.create(nom="Alice")
        cls.user2 = TblUser.objects.create(nom="Bob")

        # Services
        cls.service1 = TblService.objects.create(intitule_service="Service A")
        cls.service1.service_prix.add(TblPrix.objects.create(prix=Decimal("10.00")))
        cls.service2 = TblService.objects.create(intitule_service="Service B")
        cls.service2.service_prix.add(TblPrix.objects.create(prix=Decimal("20.00")))

        # Structure pour get_cart (Coiffeuse -> Salon -> SalonService)
        coiffeuse_user = TblUser.objects.create(nom="Coiffeuse Carla")
        coiffeuse = TblCoiffeuse.objects.create(idTblUser=coiffeuse_user)
        salon = TblSalon.objects.create(coiffeuse=coiffeuse)
        salon_service = TblSalonService.objects.create(salon=salon, service=cls.service1)

        # Panier pour user1
        cls.cart1 = TblCart.objects.create(user=cls.user1)
        cls.cart_item1 = TblCartItem.objects.create(cart=cls.cart1, service=cls.service1, quantity=2)

    def setUp(self):
        """Authentifie le client pour chaque test."""
        self.client.force_authenticate(user=self.user1)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('decorators.decorators.is_owner', lambda *args, **kwargs: lambda f: f)
    def test_get_cart_existant(self):
        """Teste la récupération d'un panier existant."""
        url = reverse('get-cart', kwargs={'user_id': self.user1.idTblUser})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['service']['idTblService'], self.service1.idTblService)
        self.assertIsNotNone(response.data['coiffeuse_id'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('decorators.decorators.is_owner', lambda *args, **kwargs: lambda f: f)
    def test_get_cart_vide(self):
        """Teste la récupération d'un panier vide pour un utilisateur qui n'en a pas encore."""
        url = reverse('get-cart', kwargs={'user_id': self.user2.idTblUser})
        self.client.force_authenticate(user=self.user2)  # Authentifier comme user2
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'], [])
        self.assertIsNone(response.data['coiffeuse_id'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('decorators.decorators.is_owner', lambda *args, **kwargs: lambda f: f)
    def test_add_to_cart_nouveau_service(self):
        """Teste l'ajout d'un nouveau service au panier."""
        url = reverse('add-to-cart')
        data = {'user_id': str(self.user1.idTblUser), 'service_id': self.service2.idTblService}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart1.items.count(), 2)
        self.assertTrue(self.cart1.items.filter(service=self.service2).exists())

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('decorators.decorators.is_owner', lambda *args, **kwargs: lambda f: f)
    def test_add_to_cart_service_existant(self):
        """Teste l'incrémentation de la quantité si le service est déjà dans le panier."""
        url = reverse('add-to-cart')
        data = {'user_id': str(self.user1.idTblUser), 'service_id': self.service1.idTblService, 'quantity': 1}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cart_item1.refresh_from_db()
        self.assertEqual(self.cart_item1.quantity, 3)  # 2 (initial) + 1 (ajouté)
        self.assertEqual(self.cart1.items.count(), 1)  # Pas de nouvel item créé

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('decorators.decorators.is_owner', lambda *args, **kwargs: lambda f: f)
    def test_remove_from_cart(self):
        """Teste la suppression d'un article du panier."""
        url = reverse('remove-from-cart')
        data = {'user_id': str(self.user1.idTblUser), 'service_id': self.service1.idTblService}

        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart1.items.count(), 0)
        self.assertFalse(TblCartItem.objects.filter(idTblCartItem=self.cart_item1.idTblCartItem).exists())

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('decorators.decorators.is_owner', lambda *args, **kwargs: lambda f: f)
    def test_clear_cart(self):
        """Teste la suppression de tous les articles du panier."""
        # Ajoutons un deuxième article pour s'assurer que tout est supprimé
        TblCartItem.objects.create(cart=self.cart1, service=self.service2, quantity=1)
        self.assertEqual(self.cart1.items.count(), 2)

        url = reverse('clear-cart')
        data = {'user_id': str(self.user1.idTblUser)}

        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.cart1.items.count(), 0)