# hairbnb/payment/tests/test_paiement.py

import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
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
    idTblUser = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)


class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    # Autres champs non nécessaires pour ces tests


class TblRendezVousService(models.Model):
    rendez_vous = models.ForeignKey(TblRendezVous, on_delete=models.CASCADE)
    prix_applique = models.DecimalField(max_digits=10, decimal_places=2)


class TblPaiementStatut(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100, default='')


class TblMethodePaiement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100, default='')


class TblPaiement(models.Model):
    idTblPaiement = models.AutoField(primary_key=True)
    rendez_vous = models.ForeignKey(TblRendezVous, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(TblUser, on_delete=models.CASCADE)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)
    statut = models.ForeignKey(TblPaiementStatut, on_delete=models.PROTECT)
    methode = models.ForeignKey(TblMethodePaiement, on_delete=models.PROTECT, null=True)
    stripe_checkout_session_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_charge_id = models.CharField(max_length=255, null=True, blank=True)
    receipt_url = models.URLField(blank=True, null=True)
    email_client = models.EmailField(null=True, blank=True)


class TblTransaction(models.Model):
    paiement = models.ForeignKey(TblPaiement, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)  # 'remboursement'
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=50)  # 'effectué'


# =======================================================================
# 2. TESTS DE L'API DE PAIEMENT
# =======================================================================

@override_settings(STRIPE_SECRET_KEY='sk_test_123', STRIPE_WEBHOOK_SECRET='whsec_test_123')
class PaiementAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée les données initiales pour tous les tests."""
        cls.user = TblUser.objects.create(email="testuser@example.com")
        cls.rdv = TblRendezVous.objects.create()
        TblRendezVousService.objects.create(rendez_vous=cls.rdv, prix_applique=Decimal("50.00"))
        TblRendezVousService.objects.create(rendez_vous=cls.rdv, prix_applique=Decimal("25.00"))

        # Statuts et méthodes de paiement
        cls.statut_en_attente = TblPaiementStatut.objects.create(code='en_attente', libelle='En attente')
        cls.statut_paye = TblPaiementStatut.objects.create(code='payé', libelle='Payé')
        cls.statut_rembourse = TblPaiementStatut.objects.create(code='remboursé', libelle='Remboursé')
        cls.methode_carte = TblMethodePaiement.objects.create(code='card', libelle='Carte')

    def setUp(self):
        """Authentifie un utilisateur pour les tests qui le nécessitent."""
        self.client.force_authenticate(user=self.user)

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_stripe_session_create):
        """Vérifie la création réussie d'une session de paiement Stripe."""
        # Configuration du mock pour simuler la réponse de Stripe
        mock_stripe_session_create.return_value = MagicMock(
            id='cs_test_12345',
            url='https://checkout.stripe.com/pay/cs_test_12345'
        )

        url = reverse('create-checkout-session')
        data = {'rendez_vous_id': self.rdv.idRendezVous}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], 'cs_test_12345')
        self.assertEqual(response.data['checkout_url'], 'https://checkout.stripe.com/pay/cs_test_12345')

        # Vérifie que l'objet TblPaiement a été créé en base de données
        paiement = TblPaiement.objects.get(stripe_checkout_session_id='cs_test_12345')
        self.assertEqual(paiement.montant_paye, Decimal("75.00"))
        self.assertEqual(paiement.statut, self.statut_en_attente)

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_session_completed(self, mock_construct_event):
        """Teste la mise à jour du statut du paiement après un webhook Stripe."""
        # 1. Créer un paiement 'en attente' comme si une session venait d'être créée
        paiement = TblPaiement.objects.create(
            rendez_vous=self.rdv,
            utilisateur=self.user,
            montant_paye=Decimal("75.00"),
            statut=self.statut_en_attente,
            stripe_checkout_session_id='cs_test_webhook'
        )

        # 2. Créer un faux événement Stripe
        fake_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_webhook',
                    'payment_intent': 'pi_test_123'
                }
            }
        }
        mock_construct_event.return_value = fake_event

        # 3. Appeler le webhook
        url = reverse('stripe-webhook')
        response = self.client.post(url, data={}, content_type='application/json')

        # 4. Vérifier les résultats
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        paiement.refresh_from_db()
        self.assertEqual(paiement.statut, self.statut_paye)
        self.assertEqual(paiement.stripe_payment_intent_id, 'pi_test_123')

    def test_check_payment_status(self):
        """Vérifie la vue qui contrôle le statut d'un paiement."""
        # Cas 1: Le paiement n'existe pas ou n'est pas payé
        url = reverse('check-payment-status', kwargs={'rendez_vous_id': self.rdv.idRendezVous})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'non payé')

        # Cas 2: Le paiement est marqué comme payé
        TblPaiement.objects.create(
            rendez_vous=self.rdv, utilisateur=self.user, montant_paye=75.00, statut=self.statut_paye
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'payé')

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('stripe.Refund.create')
    def test_rembourser_paiement(self, mock_stripe_refund):
        """Vérifie la logique de remboursement d'un paiement."""
        # Créer un paiement payé avec un ID de charge Stripe
        paiement_a_rembourser = TblPaiement.objects.create(
            rendez_vous=self.rdv,
            utilisateur=self.user,
            montant_paye=Decimal("75.00"),
            statut=self.statut_paye,
            stripe_charge_id='ch_test_123'
        )

        mock_stripe_refund.return_value = MagicMock(id='re_test_123')

        url = reverse('rembourser-paiement')
        data = {'id_paiement': paiement_a_rembourser.idTblPaiement, 'montant': '50.00'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Remboursement effectué avec succès")

        # Vérifier que la transaction de remboursement a été créée
        self.assertTrue(TblTransaction.objects.filter(paiement=paiement_a_rembourser, type='remboursement').exists())

        # Vérifier que le statut du paiement a été mis à jour
        paiement_a_rembourser.refresh_from_db()
        self.assertEqual(paiement_a_rembourser.statut, self.statut_rembourse)