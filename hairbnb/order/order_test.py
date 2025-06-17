# hairbnb/order/tests/test_orders.py

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

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
    idTblUser = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, default='User')
    prenom = models.CharField(max_length=100, default='Test')
    email = models.EmailField(unique=True, null=True)
    numero_telephone = models.CharField(max_length=20, default='')


class TblClient(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblSalon(models.Model):
    nom_salon = models.CharField(max_length=100)


class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    client = models.ForeignKey(TblClient, on_delete=models.CASCADE)
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    statut = models.CharField(max_length=50)
    total_prix = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    duree_totale = models.IntegerField(default=60)
    est_archive = models.BooleanField(default=False)
    rendez_vous_services = None  # Simulé par le setup de test si besoin


class TblPaiementStatut(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100, default='')


class TblPaiementMethode(models.Model):
    libelle = models.CharField(max_length=100)


class TblPaiement(models.Model):
    rendez_vous = models.ForeignKey(TblRendezVous, on_delete=models.CASCADE)
    statut = models.ForeignKey(TblPaiementStatut, on_delete=models.PROTECT)
    methode = models.ForeignKey(TblPaiementMethode, on_delete=models.PROTECT, null=True)
    date_paiement = models.DateTimeField()
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_url = models.URLField(blank=True, null=True)


# =======================================================================
# 2. TESTS DE L'API COMMANDES
# =======================================================================

class OrderAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée les données initiales pour tous les tests."""
        # Utilisateurs et profils
        cls.client_user = TblUser.objects.create(nom="Client", prenom="Alice", email="alice@client.com")
        cls.client_profile = TblClient.objects.create(idTblUser=cls.client_user)
        cls.coiffeuse_user = TblUser.objects.create(nom="Coiffeuse", prenom="Carla", email="carla@coiffeuse.com")
        cls.coiffeuse_profile = TblCoiffeuse.objects.create(idTblUser=cls.coiffeuse_user)

        # Salon
        cls.salon = TblSalon.objects.create(nom_salon="Le Grand Salon")

        # Statut et méthode de paiement
        statut_paye = TblPaiementStatut.objects.create(code="payé", libelle="Payé")
        methode_carte = TblPaiementMethode.objects.create(libelle="Carte de crédit")

        # Commande 1: Payée et terminée (pour la vue client)
        cls.rdv_paye = TblRendezVous.objects.create(
            client=cls.client_profile, coiffeuse=cls.coiffeuse_profile, salon=cls.salon,
            date_heure=timezone.now() - timedelta(days=5), statut="terminé"
        )
        cls.paiement = TblPaiement.objects.create(
            rendez_vous=cls.rdv_paye, statut=statut_paye, methode=methode_carte,
            date_paiement=timezone.now() - timedelta(days=5), montant_paye=50.00
        )

        # Commande 2: En attente (pour la vue coiffeuse)
        cls.rdv_en_attente = TblRendezVous.objects.create(
            client=cls.client_profile, coiffeuse=cls.coiffeuse_profile, salon=cls.salon,
            date_heure=timezone.now() + timedelta(days=2), statut="en attente"
        )

        # Commande 3: Confirmée (pour les tests de mise à jour)
        cls.rdv_a_modifier = TblRendezVous.objects.create(
            client=cls.client_profile, coiffeuse=cls.coiffeuse_profile, salon=cls.salon,
            date_heure=timezone.now() + timedelta(days=3), statut="confirmé"
        )

    def test_mes_commandes_client_view(self):
        """Vérifie que le client voit uniquement ses commandes payées."""
        url = reverse('mes-commandes', kwargs={'idUser': self.client_user.idTblUser})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['idRendezVous'], self.rdv_paye.idRendezVous)
        self.assertEqual(float(response.data[0]['montant_paye']), 50.00)

    def test_commandes_coiffeuse_view_default(self):
        """Vérifie que la coiffeuse voit les commandes 'en attente' par défaut."""
        url = reverse('commandes-coiffeuse', kwargs={'idUser': self.coiffeuse_user.idTblUser})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['idRendezVous'], self.rdv_en_attente.idRendezVous)
        self.assertEqual(response.data[0]['statut'], 'en attente')

    def test_commandes_coiffeuse_view_filtered(self):
        """Vérifie que la coiffeuse peut filtrer les commandes par statut."""
        url = reverse('commandes-coiffeuse', kwargs={'idUser': self.coiffeuse_user.idTblUser}) + '?statut=terminé'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['idRendezVous'], self.rdv_paye.idRendezVous)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_statut_commande_success(self):
        """Teste la mise à jour réussie du statut d'une commande par la coiffeuse."""
        self.client.force_authenticate(user=self.coiffeuse_user)
        url = reverse('update-statut-commande', kwargs={'idRendezVous': self.rdv_a_modifier.idRendezVous})
        data = {'statut': 'terminé'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['statut'], 'terminé')

        self.rdv_a_modifier.refresh_from_db()
        self.assertEqual(self.rdv_a_modifier.statut, 'terminé')

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_statut_commande_unauthorized(self):
        """Teste qu'un utilisateur non autorisé (le client) ne peut pas modifier le statut."""
        # Authentification en tant que client
        self.client.force_authenticate(user=self.client_user)

        url = reverse('update-statut-commande', kwargs={'idRendezVous': self.rdv_a_modifier.idRendezVous})
        data = {'statut': 'terminé'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_date_heure_commande_success(self):
        """Teste la mise à jour réussie de la date/heure d'une commande."""
        self.client.force_authenticate(user=self.coiffeuse_user)
        url = reverse('update-date-heure-commande', kwargs={'idRendezVous': self.rdv_a_modifier.idRendezVous})

        new_datetime_str = (timezone.now() + timedelta(days=10)).isoformat()
        data = {'date_heure': new_datetime_str}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.rdv_a_modifier.refresh_from_db()
        # Compare les chaînes formatées pour éviter les problèmes de fuseau horaire et de microsecondes
        self.assertEqual(self.rdv_a_modifier.date_heure.isoformat().split('+')[0], new_datetime_str.split('+')[0])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_update_date_heure_rdv_termine(self):
        """Teste l'échec de la modification d'un rdv déjà terminé."""
        self.client.force_authenticate(user=self.coiffeuse_user)
        url = reverse('update-date-heure-commande', kwargs={'idRendezVous': self.rdv_paye.idRendezVous})
        data = {'date_heure': (timezone.now() + timedelta(days=1)).isoformat()}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Impossible de modifier un rendez-vous avec le statut 'terminé'", response.data['detail'])