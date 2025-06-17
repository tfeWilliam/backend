# hairbnb/emails/tests/test_emails.py

import uuid
import smtplib
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
    nom = models.CharField(max_length=100, default='User')
    prenom = models.CharField(max_length=100, default='Test')


class TblClient(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)


class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    client = models.ForeignKey(TblClient, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    date_heure = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, default='confirmé')
    # Simuler le related manager pour les services
    rendez_vous_services = MagicMock()


class TblEmailType(models.Model):
    idTblEmailType = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)


class TblEmailStatus(models.Model):
    idTblEmailStatus = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)


class TblEmailNotification(models.Model):
    idTblEmailNotification = models.AutoField(primary_key=True)
    destinataire = models.ForeignKey(TblUser, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, null=True, blank=True, on_delete=models.SET_NULL)
    rendez_vous = models.ForeignKey(TblRendezVous, null=True, blank=True, on_delete=models.SET_NULL)
    type_email = models.ForeignKey(TblEmailType, on_delete=models.PROTECT)
    statut = models.ForeignKey(TblEmailStatus, on_delete=models.PROTECT)
    sujet = models.CharField(max_length=255)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_envoi = models.DateTimeField(null=True, blank=True)
    tentatives = models.PositiveIntegerField(default=0)


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.emails.email_services import EmailService
from hairbnb.emails.emails_serializers import EmailNotificationCreateSerializer


# =======================================================================
# 3. TESTS DU SERVICE EMAIL (Logique métier)
# =======================================================================
@override_settings(DEFAULT_FROM_EMAIL='test@example.com')
class EmailServiceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Création des données de base
        cls.user = TblUser.objects.create(email='destinataire@test.com', prenom="John", nom="Doe")
        cls.client = TblClient.objects.create(idTblUser=cls.user)
        cls.salon = TblSalon.objects.create(nom_salon="Le Salon Test")
        cls.rdv = TblRendezVous.objects.create(client=cls.client, salon=cls.salon)

        # Création des types et statuts d'email
        TblEmailType.objects.create(code='confirmation_rdv', libelle='Confirmation RDV')
        TblEmailStatus.objects.create(code='en_attente', libelle='En attente')
        TblEmailStatus.objects.create(code='envoye', libelle='Envoyé')
        TblEmailStatus.objects.create(code='echec', libelle='Échec')

    @patch('hairbnb.emails.email_services.render_to_string', return_value='Sujet de Test')
    def test_create_notification(self, mock_render_to_string):
        """Vérifie qu'une notification est correctement créée en base de données."""
        notification = EmailService.create_notification(
            destinataire=self.user,
            type_email_code='confirmation_rdv',
            salon=self.salon,
            rendez_vous=self.rdv
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.destinataire, self.user)
        self.assertEqual(notification.statut.code, 'en_attente')
        self.assertEqual(notification.sujet, 'Sujet de Test')
        mock_render_to_string.assert_called_once()

    @patch('hairbnb.emails.email_services.render_to_string')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_send_notification_succes(self, mock_send, mock_render):
        """Teste l'envoi réussi d'une notification."""
        mock_render.side_effect = ['Sujet de Test', '<html>Contenu HTML</html>']

        # 1. Créer la notification
        notification = EmailService.create_notification(
            destinataire=self.user, type_email_code='confirmation_rdv', rendez_vous=self.rdv
        )

        # 2. Envoyer la notification
        success = EmailService.send_notification(notification.idTblEmailNotification)

        # 3. Vérifier les assertions
        self.assertTrue(success)
        mock_send.assert_called_once()

        notification.refresh_from_db()
        self.assertEqual(notification.statut.code, 'envoye')
        self.assertIsNotNone(notification.date_envoi)
        self.assertIn('<html>Contenu HTML</html>', notification.contenu)

    @patch('hairbnb.emails.email_services.render_to_string', return_value='Sujet')
    @patch('django.core.mail.EmailMultiAlternatives.send', side_effect=smtplib.SMTPException("Erreur de connexion"))
    def test_send_notification_echec(self, mock_send, mock_render):
        """Teste la gestion d'un échec lors de l'envoi."""
        notification = EmailService.create_notification(
            destinataire=self.user, type_email_code='confirmation_rdv'
        )

        success = EmailService.send_notification(notification.idTblEmailNotification)

        self.assertFalse(success)
        mock_send.assert_called_once()

        notification.refresh_from_db()
        self.assertEqual(notification.statut.code, 'echec')
        self.assertEqual(notification.tentatives, 1)


# =======================================================================
# 4. TESTS DE LA VUE API
# =======================================================================
class EmailViewsTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = TblUser.objects.create(email='api-user@test.com')
        cls.client = TblClient.objects.create(idTblUser=cls.user)
        cls.salon = TblSalon.objects.create(nom_salon="Salon API")
        cls.rdv = TblRendezVous.objects.create(client=cls.client, salon=cls.salon)
        TblEmailType.objects.create(code='test_template', libelle='Template de test')
        TblEmailStatus.objects.create(code='en_attente', libelle='En attente')

    # On mock les méthodes du service pour isoler le test de la vue
    @patch('hairbnb.emails.email_views.EmailService.send_notification', return_value=True)
    @patch('hairbnb.emails.email_views.EmailService.create_notification')
    def test_api_send_email_succes(self, mock_create, mock_send):
        """Teste un appel réussi à l'API pour envoyer un email."""
        # Configurer le mock pour retourner une notification valide
        mock_notification = MagicMock(spec=TblEmailNotification)
        mock_notification.idTblEmailNotification = 1
        mock_create.return_value = mock_notification

        url = reverse('email-notification')  # Assurez-vous que votre URL est nommée 'email-notification'
        data = {
            "toEmail": self.user.email,
            "templateId": "test_template",
            "rendezVousId": self.rdv.idRendezVous
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Email envoyé avec succès")
        mock_create.assert_called_once()
        mock_send.assert_called_once_with(mock_notification.idTblEmailNotification)

    def test_api_donnees_invalides(self):
        """Teste l'API avec des données manquantes ou invalides."""
        url = reverse('email-notification')

        # Cas 1: 'toEmail' manquant
        data = {"templateId": "test_template"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('toEmail', response.data)

        # Cas 2: 'templateId' invalide
        data = {"toEmail": self.user.email, "templateId": "template_inexistant"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('templateId', response.data)

    def test_api_utilisateur_non_trouve(self):
        """Teste le cas où l'email du destinataire n'est pas en base de données."""
        url = reverse('email-notification')
        data = {
            "toEmail": "inconnu@test.com",
            "templateId": "test_template"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("non trouvé", response.data['error'])