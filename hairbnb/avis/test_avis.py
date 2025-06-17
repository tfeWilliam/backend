# avis/tests/test_serializers.py

import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework import serializers, status

# Importez vos modèles (nous allons les simuler ici pour l'exemple)
# Dans un projet réel, vous importeriez directement depuis hairbnb.models
from django.db import models
from django.contrib.auth.models import AbstractUser

# --- Création de modèles factices pour les tests ---
# NOTE : Dans votre projet, vous devriez importer vos vrais modèles.
# Ces modèles sont des simulations basées sur votre code.

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    photo_profil = models.CharField(max_length=255, null=True, blank=True)
    # on enlève l'email pour éviter les conflits avec le parent
    email = None
    USERNAME_FIELD = 'username'


class TblSalon(models.Model):
    idTblSalon = models.AutoField(primary_key=True)
    nom_salon = models.CharField(max_length=100)
    logo_salon = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nom_salon

class TblClient(models.Model):
    idTblUser = models.OneToOneField(User, on_delete=models.CASCADE)

class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    client = models.ForeignKey(TblClient, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, default='terminé')
    date_heure = models.DateTimeField()
    duree_totale = models.IntegerField(default=60)

    @property
    def avis(self):
        return TblAvis.objects.filter(rendez_vous=self)

class TblAvisStatut(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)

class TblAvis(models.Model):
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(TblClient, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    rendez_vous = models.OneToOneField(TblRendezVous, on_delete=models.CASCADE, related_name='avis_relation')
    note = models.IntegerField()
    commentaire = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    statut = models.ForeignKey(TblAvisStatut, on_delete=models.PROTECT)


# Importez vos serializers
from hairbnb.avis.avis_serializers import AvisCreateSerializer, RdvEligibleAvisSerializer

class AvisSerializersTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée les données initiales pour tous les tests de cette classe."""
        cls.user1 = User.objects.create_user(username='client1', password='password123', prenom='Jean', nom='Valjean')
        cls.client1 = TblClient.objects.create(idTblUser=cls.user1)

        cls.user2 = User.objects.create_user(username='client2', password='password123')
        cls.client2 = TblClient.objects.create(idTblUser=cls.user2)

        cls.salon = TblSalon.objects.create(nom_salon="Le Coiffeur Chic")
        TblAvisStatut.objects.create(code='visible', libelle='Visible')

        # RDV terminé il y a 3 jours, éligible pour un avis
        cls.rdv_eligible = TblRendezVous.objects.create(
            client=cls.client1,
            salon=cls.salon,
            statut='terminé',
            date_heure=timezone.now() - timedelta(days=3)
        )

        # RDV terminé mais déjà noté
        cls.rdv_deja_note = TblRendezVous.objects.create(
            client=cls.client1,
            salon=cls.salon,
            statut='terminé',
            date_heure=timezone.now() - timedelta(days=4)
        )
        TblAvis.objects.create(
            client=cls.client1,
            salon=cls.salon,
            rendez_vous=cls.rdv_deja_note,
            note=5,
            commentaire="C'était parfait !",
            statut=TblAvisStatut.objects.get(code='visible')
        )

        # RDV en attente (pas terminé)
        cls.rdv_en_attente = TblRendezVous.objects.create(
            client=cls.client1,
            salon=cls.salon,
            statut='en_attente',
            date_heure=timezone.now() + timedelta(days=1)
        )

        # RDV appartenant à un autre client
        cls.rdv_autre_client = TblRendezVous.objects.create(
            client=cls.client2,
            salon=cls.salon,
            statut='terminé',
            date_heure=timezone.now() - timedelta(days=2)
        )

    def _get_mock_request(self, user):
        """Crée une requête mock avec un utilisateur authentifié."""
        request = MagicMock()
        request.user = user
        return {'request': request}

    def test_create_avis_serializer_valide(self):
        """Teste la création d'un avis avec des données valides."""
        data = {
            'idRendezVous': self.rdv_eligible.idRendezVous,
            'note': 4,
            'commentaire': 'Un service de très bonne qualité.'
        }
        context = self._get_mock_request(self.user1)
        serializer = AvisCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        avis = serializer.save()
        self.assertEqual(avis.note, 4)
        self.assertEqual(avis.client, self.client1)
        self.assertEqual(avis.salon, self.salon)
        self.assertEqual(TblAvis.objects.count(), 2) # 1 de setUp, 1 créé ici

    def test_create_avis_note_invalide(self):
        """Teste la validation pour une note hors des bornes."""
        data = {'idRendezVous': self.rdv_eligible.idRendezVous, 'note': 6, 'commentaire': 'Commentaire valide.'}
        context = self._get_mock_request(self.user1)
        serializer = AvisCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('note', serializer.errors)

    def test_create_avis_commentaire_trop_court(self):
        """Teste la validation pour un commentaire trop court."""
        data = {'idRendezVous': self.rdv_eligible.idRendezVous, 'note': 5, 'commentaire': 'Court'}
        context = self._get_mock_request(self.user1)
        serializer = AvisCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('commentaire', serializer.errors)

    def test_create_avis_rdv_deja_note(self):
        """Teste qu'on ne peut pas noter un RDV qui a déjà un avis."""
        data = {'idRendezVous': self.rdv_deja_note.idRendezVous, 'note': 3, 'commentaire': 'Je re-note ce RDV'}
        context = self._get_mock_request(self.user1)
        serializer = AvisCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('idRendezVous', serializer.errors)
        self.assertEqual(serializer.errors['idRendezVous'][0], "Un avis a déjà été donné pour ce rendez-vous.")

    def test_create_avis_rdv_non_termine(self):
        """Teste qu'on ne peut pas noter un RDV non terminé."""
        data = {'idRendezVous': self.rdv_en_attente.idRendezVous, 'note': 5, 'commentaire': 'Un commentaire pour le futur.'}
        context = self._get_mock_request(self.user1)
        serializer = AvisCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('idRendezVous', serializer.errors)
        self.assertEqual(serializer.errors['idRendezVous'][0], "Seuls les rendez-vous terminés peuvent recevoir un avis.")

    def test_create_avis_rdv_autre_client(self):
        """Teste qu'un client ne peut pas noter le RDV d'un autre."""
        data = {'idRendezVous': self.rdv_autre_client.idRendezVous, 'note': 1, 'commentaire': "Je n'étais pas là !"}
        context = self._get_mock_request(self.user1)
        serializer = AvisCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('idRendezVous', serializer.errors)
        self.assertEqual(serializer.errors['idRendezVous'][0], "Rendez-vous non trouvé ou non autorisé.")

    def test_rdv_eligible_serializer(self):
        """Teste le serializer pour les RDV éligibles."""
        # Un RDV terminé il y a 2h pile n'est pas encore éligible
        rdv_trop_recent = TblRendezVous.objects.create(
            client=self.client1, salon=self.salon, statut='terminé',
            date_heure=timezone.now() - timedelta(hours=2, minutes=59) # Moins de 2h depuis la fin (60min de durée)
        )

        serializer_eligible = RdvEligibleAvisSerializer(instance=self.rdv_eligible)
        serializer_trop_recent = RdvEligibleAvisSerializer(instance=rdv_trop_recent)
        serializer_deja_note = RdvEligibleAvisSerializer(instance=self.rdv_deja_note)

        # Le RDV de plus de 2h est éligible
        self.assertTrue(serializer_eligible.data['est_eligible'])
        # Le RDV de moins de 2h n'est pas éligible
        self.assertFalse(serializer_trop_recent.data['est_eligible'])
        # Le RDV déjà noté n'est pas éligible
        self.assertFalse(serializer_deja_note.data['est_eligible'])
        self.assertEqual(serializer_eligible.data['salon_nom'], "Le Coiffeur Chic")


class AvisViewsTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée les données pour les tests de vues."""
        # Utilisateur et client pour les tests
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.client = TblClient.objects.create(idTblUser=cls.user)

        # Un autre utilisateur pour tester les permissions
        cls.other_user = User.objects.create_user(username='otheruser', password='password')
        cls.other_client = TblClient.objects.create(idTblUser=cls.other_user)

        # Salon
        cls.salon = TblSalon.objects.create(idTblSalon=1, nom_salon="Salon Test")

        # Statut d'avis
        cls.statut_visible = TblAvisStatut.objects.create(code='visible', libelle='Visible')

        # RDV terminé il y a 3 heures (éligible pour un avis)
        cls.rdv1 = TblRendezVous.objects.create(
            client=cls.client, salon=cls.salon, statut='terminé',
            date_heure=timezone.now() - timedelta(hours=5)  # 5h avant - (1h de rdv) - 2h d'attente = éligible
        )
        # RDV terminé mais trop récent
        cls.rdv2 = TblRendezVous.objects.create(
            client=cls.client, salon=cls.salon, statut='terminé',
            date_heure=timezone.now() - timedelta(hours=1)
        )
        # Avis existant pour notre utilisateur
        cls.rdv3 = TblRendezVous.objects.create(
            client=cls.client, salon=cls.salon, statut='terminé',
            date_heure=timezone.now() - timedelta(days=2)
        )
        cls.avis1 = TblAvis.objects.create(
            client=cls.client, salon=cls.salon, rendez_vous=cls.rdv3,
            note=5, commentaire="Super expérience client !", statut=cls.statut_visible
        )
        # Avis d'un autre utilisateur
        cls.rdv4 = TblRendezVous.objects.create(
            client=cls.other_client, salon=cls.salon, statut='terminé',
            date_heure=timezone.now() - timedelta(days=3)
        )
        cls.avis2 = TblAvis.objects.create(
            client=cls.other_client, salon=cls.salon, rendez_vous=cls.rdv4,
            note=3, commentaire="Moyen.", statut=cls.statut_visible
        )

    def setUp(self):
        """Authentifie le client pour chaque test."""
        # self.client est le client de test de DRF, ne pas confondre avec notre modèle TblClient
        self.client.force_authenticate(user=self.user)

    # Patch des décorateurs pour ne pas dépendre de Firebase/logique externe
    @patch('hairbnb.avis.views.firebase_authenticated', lambda f: f)
    def test_mes_rdv_avis_en_attente(self):
        """Vérifie que la vue retourne uniquement les RDV éligibles."""
        url = reverse('mes-rdv-avis-en-attente')  # Assurez-vous d'avoir nommé votre URL
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['rdv_eligibles'][0]['idRendezVous'], self.rdv1.idRendezVous)

    @patch('hairbnb.avis.views.firebase_authenticated', lambda f: f)
    @patch('hairbnb.avis.views.is_owner', lambda **kwargs: lambda f: f)
    def test_creer_avis(self):
        """Teste la création d'un nouvel avis."""
        url = reverse('creer-avis')
        data = {'idRendezVous': self.rdv1.idRendezVous, 'note': 4, 'commentaire': 'Très bon service, je recommande.'}

        # Simuler request.user.uuid
        self.user.uuid = self.client.idTblUser.uuid  # Assurez-vous que le mock user a un uuid
        self.client.force_authenticate(user=self.user)  # Ré-authentifier avec le user modifié

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['avis']['note'], 4)
        self.assertTrue(TblAvis.objects.filter(rendez_vous=self.rdv1).exists())

    def test_avis_salon_public(self):
        """Teste la vue publique des avis d'un salon."""
        self.client.force_authenticate(user=None)  # Déconnexion pour tester l'accès public
        url = reverse('avis-salon-public', kwargs={'salon_id': self.salon.idTblSalon})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['statistiques']['total_avis'], 2)
        self.assertEqual(response.data['statistiques']['moyenne_notes'], 4.0)  # (5+3)/2
        self.assertEqual(len(response.data['avis']), 2)

    @patch('hairbnb.avis.views.firebase_authenticated', lambda f: f)
    @patch('hairbnb.avis.views.is_owner', lambda **kwargs: lambda f: f)
    def test_modifier_avis(self):
        """Teste la modification d'un avis par son propriétaire."""
        url = reverse('modifier-avis', kwargs={'avis_id': self.avis1.id})
        data = {'note': 4, 'commentaire': 'Finalement, je mets 4 étoiles.'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.avis1.refresh_from_db()
        self.assertEqual(self.avis1.note, 4)
        self.assertEqual(self.avis1.commentaire, 'Finalement, je mets 4 étoiles.')

    @patch('hairbnb.avis.views.firebase_authenticated', lambda f: f)
    @patch('hairbnb.avis.views.is_owner', lambda **kwargs: lambda f: f)
    def test_modifier_avis_non_proprietaire(self):
        """Teste qu'un utilisateur ne peut pas modifier l'avis d'un autre."""
        # On simule un échec de la requête get_object_or_404
        # car la vue filtre par client=client_connecté
        url = reverse('modifier-avis', kwargs={'avis_id': self.avis2.id})
        data = {'note': 1}
        response = self.client.patch(url, data, format='json')

        # La vue retournera 404 car l'avis n'est pas trouvé pour le client connecté
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "Avis non trouvé ou non autorisé")

    @patch('hairbnb.avis.views.firebase_authenticated', lambda f: f)
    @patch('hairbnb.avis.views.is_owner', lambda **kwargs: lambda f: f)
    def test_supprimer_avis(self):
        """Teste la suppression d'un avis par son propriétaire."""
        avis_a_supprimer = TblAvis.objects.create(
            client=self.client, salon=self.salon,
            rendez_vous=TblRendezVous.objects.create(
                client=self.client, salon=self.salon, statut='terminé', date_heure=timezone.now() - timedelta(days=10)
            ),
            note=1, commentaire="À supprimer", statut=self.statut_visible
        )
        avis_count_before = TblAvis.objects.count()
        url = reverse('supprimer-avis', kwargs={'avis_id': avis_a_supprimer.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TblAvis.objects.count(), avis_count_before - 1)