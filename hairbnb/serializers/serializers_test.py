# hairbnb/tests/test_multiple_serializers.py

from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import serializers

# =======================================================================
# 1. MOCK MODELS
# NOTE : Ces modèles sont des simulations pour permettre aux tests de
# fonctionner sans avoir le code complet du projet.
# =======================================================================
from django.db import models

from hairbnb.promotion.promotion_serializers import PromotionUpdateSerializer
from hairbnb.serializers.horaire_coiffeuse_serializers import HoraireCoiffeuseSerializer
from hairbnb.serializers.rdvs_serializers import RendezVousSerializer


# --- Modèles pour les Horaires ---
class TblUser(models.Model):
    nom = models.CharField(max_length=100, default='User')
    prenom = models.CharField(max_length=100, default='Test')


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblHoraireCoiffeuse(models.Model):
    id = models.AutoField(primary_key=True)
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    jour = models.IntegerField(choices=[(0, 'Lundi'), (1, 'Mardi')])
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    def get_jour_display(self):
        return dict(self._meta.get_field('jour').choices).get(self.jour)


class TblIndisponibilite(models.Model):
    id = models.AutoField(primary_key=True)
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    motif = models.CharField(max_length=255, blank=True)


# --- Modèles pour les Promotions ---
class TblService(models.Model):
    idTblService = models.AutoField(primary_key=True)
    intitule_service = models.CharField(max_length=100)


class TblPromotion(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


# --- Modèles pour les Rendez-vous ---
class TblClient(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblSalon(models.Model):
    nom_salon = models.CharField(max_length=100)
    # Simuler les dépendances pour le SalonSerializer
    adresse = None

    def get_proprietaire(self): return None


class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    client = models.ForeignKey(TblClient, on_delete=models.CASCADE)
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    statut = models.CharField(max_length=50)
    total_prix = models.DecimalField(max_digits=10, decimal_places=2)
    duree_totale = models.IntegerField()


class TblRendezVousService(models.Model):
    idRendezVousService = models.AutoField(primary_key=True)
    rendez_vous = models.ForeignKey(TblRendezVous, on_delete=models.CASCADE, related_name='rendez_vous_services')
    service = models.ForeignKey(TblService, on_delete=models.CASCADE)
    prix_applique = models.DecimalField(max_digits=10, decimal_places=2)
    duree_estimee = models.IntegerField()


class TblPaiement(models.Model):
    idPaiement = models.AutoField(primary_key=True)
    rendez_vous = models.ForeignKey(TblRendezVous, on_delete=models.CASCADE)
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField()
    methode = models.CharField(max_length=50)
    statut = models.CharField(max_length=50)


# =======================================================================
# 2. IMPORT DES SÉRIALISEURS À TESTER
# =======================================================================



# =======================================================================
# 3. TESTS
# =======================================================================

class HoraireSerializersTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = TblUser.objects.create()
        cls.coiffeuse = TblCoiffeuse.objects.create(idTblUser=user)
        cls.horaire = TblHoraireCoiffeuse.objects.create(
            coiffeuse=cls.coiffeuse, jour=0,  # Lundi
            heure_debut=datetime.strptime("09:00", "%H:%M").time(),
            heure_fin=datetime.strptime("17:00", "%H:%M").time()
        )

    def test_horaire_coiffeuse_serializer(self):
        """Vérifie que le champ 'jour_label' est correctement sérialisé."""
        serializer = HoraireCoiffeuseSerializer(instance=self.horaire)
        data = serializer.data
        self.assertEqual(data['jour'], 0)
        self.assertEqual(data['jour_label'], 'Lundi')


class RendezVousSerializersTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Créer tous les objets liés nécessaires pour un RendezVous
        user_client = TblUser.objects.create(nom="Client", prenom="Test")
        client = TblClient.objects.create(idTblUser=user_client)
        user_coiffeuse = TblUser.objects.create(nom="Coiffeuse", prenom="Test")
        coiffeuse = TblCoiffeuse.objects.create(idTblUser=user_coiffeuse)
        salon = TblSalon.objects.create(nom_salon="Le Salon Test")
        service = TblService.objects.create(intitule_service="Coupe simple")

        cls.rdv = TblRendezVous.objects.create(
            client=client, coiffeuse=coiffeuse, salon=salon,
            date_heure=timezone.now(), statut="confirmé",
            total_prix=Decimal("25.00"), duree_totale=30
        )
        TblRendezVousService.objects.create(
            rendez_vous=cls.rdv, service=service,
            prix_applique=Decimal("25.00"), duree_estimee=30
        )

    @patch('hairbnb.profil.profil_serializers.UserSerializer')  # Mock pour simplifier
    def test_rendezvous_serializer_nested_structure(self, mock_user_serializer):
        """Vérifie que le RendezVousSerializer inclut bien les données imbriquées."""
        # Simuler un retour simple pour le serializer mocké
        mock_user_serializer.return_value.data = {"nom": "Mocked"}

        serializer = RendezVousSerializer(instance=self.rdv)
        data = serializer.data

        self.assertEqual(data['idRendezVous'], self.rdv.idRendezVous)
        self.assertIn('client', data)
        self.assertIn('coiffeuse', data)
        self.assertIn('salon', data)
        self.assertIn('services', data)
        self.assertEqual(len(data['services']), 1)
        self.assertEqual(data['services'][0]['prix_applique'], "25.00")


class PromotionUpdateSerializerTest(TestCase):

    def test_promotion_update_valid_data(self):
        """Vérifie que des données valides passent la validation."""
        data = {
            "discount_percentage": 25.0,
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        }
        serializer = PromotionUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Vérifie la conversion des dates
        validated_data = serializer.validated_data
        self.assertIsInstance(validated_data['start_date'], datetime)
        self.assertEqual(validated_data['start_date'].day, 1)

    def test_promotion_update_invalid_date_format(self):
        """Vérifie que le serializer échoue avec un mauvais format de date."""
        data = {
            "discount_percentage": 20.0,
            "start_date": "01/01/2025",  # Format incorrect
            "end_date": "31-01-2025"
        }
        serializer = PromotionUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('start_date', serializer.errors)

    def test_promotion_update_end_date_before_start_date(self):
        """Vérifie que la date de fin ne peut pas être avant la date de début."""
        data = {
            "discount_percentage": 10.0,
            "start_date": "2025-02-10",
            "end_date": "2025-02-01"  # Date de fin antérieure
        }
        serializer = PromotionUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # C'est une erreur non liée à un champ spécifique
        self.assertIn('end_date', serializer.errors)

    def test_promotion_update_discount_out_of_bounds(self):
        """Vérifie que le pourcentage de réduction est dans les bornes (0-100)."""
        data = {
            "discount_percentage": 110.0,  # Pourcentage invalide
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        }
        serializer = PromotionUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('discount_percentage', serializer.errors)