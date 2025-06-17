# hairbnb/disponibilites/tests/test_disponibilites.py

import uuid
from datetime import date, time, datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# =======================================================================
# 1. MOCK MODELS
# NOTE : Ces modèles sont des simulations pour permettre aux tests de
# fonctionner. Dans votre projet, vous importeriez vos vrais modèles.
# =======================================================================
from django.db import models


class TblUserTypeRef(models.Model):
    libelle = models.CharField(max_length=50)


class TblUser(models.Model):
    idTblUser = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, default='')
    prenom = models.CharField(max_length=100, default='')
    is_active = models.BooleanField(default=True)
    type_ref = models.ForeignKey(TblUserTypeRef, on_delete=models.SET_NULL, null=True)


class TblCoiffeuse(models.Model):
    idTblUser = models.OneToOneField(TblUser, on_delete=models.CASCADE, primary_key=True)


class TblHoraireCoiffeuse(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    jour = models.IntegerField()  # 0=Lundi, ..., 6=Dimanche
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()


class TblIndisponibilite(models.Model):
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()


class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    coiffeuse = models.ForeignKey(TblCoiffeuse, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    duree_totale = models.IntegerField(default=60)
    statut = models.CharField(max_length=50, default='confirmé')


# =======================================================================
# 2. IMPORT DES MODULES À TESTER
# =======================================================================
from hairbnb.dispinibilites.disponibilities_serializers import DisponibilitesClientSerializer


# =======================================================================
# 3. TESTS DU SERIALIZER (Logique de Calcul)
# =======================================================================
class DisponibilitesSerializerTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée une coiffeuse avec un horaire, un rdv et une indisponibilité."""
        type_coiffeuse = TblUserTypeRef.objects.create(libelle='coiffeuse')
        user_coiffeuse = TblUser.objects.create(nom="Test", prenom="Carla", type_ref=type_coiffeuse)
        cls.coiffeuse = TblCoiffeuse.objects.create(idTblUser=user_coiffeuse)

        # Le jour de test sera un mardi
        cls.test_date = date.today() + timedelta(days=(1 - date.today().weekday() + 7) % 7)  # Prochain mardi
        if cls.test_date == date.today():
            cls.test_date += timedelta(days=7)  # S'assurer que ce n'est pas aujourd'hui pour simplifier

        # Horaire pour le mardi : 9h-12h et 13h-18h (non implémenté, on simule 9h-18h)
        TblHoraireCoiffeuse.objects.create(
            coiffeuse=cls.coiffeuse,
            jour=1,  # Mardi
            heure_debut=time(9, 0),
            heure_fin=time(18, 0)
        )

        # Un rendez-vous le matin
        TblRendezVous.objects.create(
            coiffeuse=cls.coiffeuse,
            date_heure=datetime.combine(cls.test_date, time(10, 0)),
            duree_totale=60  # 10h00 - 11h00
        )

        # Une indisponibilité l'après-midi
        TblIndisponibilite.objects.create(
            coiffeuse=cls.coiffeuse,
            date=cls.test_date,
            heure_debut=time(14, 0),
            heure_fin=time(15, 30)
        )
        cls.serializer = DisponibilitesClientSerializer()

    def test_calcul_disponibilites_jour_normal(self):
        """Vérifie que les créneaux sont correctement générés en évitant les obstacles."""
        duree = 60  # 1 heure
        dispos = self.serializer.calculate_disponibilites(self.coiffeuse.pk, self.test_date, duree)

        # Créneaux attendus :
        # - Avant le RDV : 9h-10h
        # - Après le RDV et avant l'indispo : 11h-12h, 12h-13h, 13h-14h
        # - Après l'indispo : 15h30-16h30, 16h30-17h30
        creneaux_debut = {d['debut'].strftime('%H:%M') for d in dispos}

        self.assertIn('09:00', creneaux_debut)
        self.assertNotIn('10:00', creneaux_debut)  # Bloqué par le RDV
        self.assertIn('11:00', creneaux_debut)
        self.assertIn('11:30', creneaux_debut)
        self.assertIn('13:30', creneaux_debut)
        self.assertNotIn('14:00', creneaux_debut)  # Bloqué par l'indispo
        self.assertIn('15:30', creneaux_debut)
        self.assertIn('17:00', creneaux_debut)

        # Le dernier créneau possible est 17:00 pour un service de 60 min (fin 18:00)
        self.assertNotIn('17:30', creneaux_debut)

    def test_jour_ferme_retourne_liste_vide(self):
        """Vérifie qu'aucun créneau n'est retourné pour un jour sans horaire."""
        jour_ferme = self.test_date + timedelta(days=1)  # Mercredi (pas d'horaire défini)
        duree = 30
        dispos = self.serializer.calculate_disponibilites(self.coiffeuse.pk, jour_ferme, duree)
        self.assertEqual(dispos, [])

    def test_validation_date_passee(self):
        """Vérifie que le serializer rejette une date dans le passé."""
        data = {
            'coiffeuse_id': self.coiffeuse.pk,
            'date': date.today() - timedelta(days=1),
            'duree': 30
        }
        serializer = DisponibilitesClientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('date', serializer.errors)

    def test_validation_coiffeuse_inexistante(self):
        """Vérifie que le serializer rejette un ID de coiffeuse invalide."""
        data = {
            'coiffeuse_id': 999,  # ID qui n'existe pas
            'date': date.today(),
            'duree': 30
        }
        serializer = DisponibilitesClientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coiffeuse_id', serializer.errors)


# =======================================================================
# 4. TESTS DES VUES (API Endpoints)
# =======================================================================
class DisponibilitesViewsTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        """Crée un utilisateur et une coiffeuse pour les tests de vues."""
        type_coiffeuse = TblUserTypeRef.objects.create(libelle='coiffeuse')
        cls.user = TblUser.objects.create(nom="Client", prenom="Test")
        user_coiffeuse = TblUser.objects.create(
            nom="Test", prenom="Carla", is_active=True, type_ref=type_coiffeuse
        )
        cls.coiffeuse = TblCoiffeuse.objects.create(idTblUser=user_coiffeuse)
        # On mock le calcul pour ne pas dépendre de la logique complexe ici
        cls.mock_dispos = [{'debut': '09:00', 'fin': '10:00'}]

    def setUp(self):
        """Authentifie le client pour chaque test."""
        self.client.force_authenticate(user=self.user)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('hairbnb.dispinibilites.disponibilities_serializers.DisponibilitesClientSerializer.is_valid',
           return_value=True)
    @patch('hairbnb.dispinibilites.disponibilities_serializers.DisponibilitesClientSerializer.calculate_disponibilites')
    def test_get_disponibilites_client_succes(self, mock_calculate, mock_is_valid):
        """Teste l'appel réussi à la vue get_disponibilites_client."""
        mock_calculate.return_value = self.mock_dispos

        test_date = date.today().strftime('%Y-%m-%d')
        url = reverse('get-disponibilites-client', kwargs={'coiffeuse_id': self.coiffeuse.pk})
        response = self.client.get(url, {'date': test_date, 'duree': '60'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['nb_creneaux'], 1)
        self.assertEqual(response.data['disponibilites'], self.mock_dispos)
        self.assertIn('coiffeuse_nom', response.data)

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_get_disponibilites_parametre_date_manquant(self):
        """Teste l'échec de la requête s'il manque le paramètre 'date'."""
        url = reverse('get-disponibilites-client', kwargs={'coiffeuse_id': self.coiffeuse.pk})
        response = self.client.get(url, {'duree': '60'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data['error'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_get_disponibilites_parametre_duree_manquant(self):
        """Teste l'échec de la requête s'il manque le paramètre 'duree'."""
        url = reverse('get-disponibilites-client', kwargs={'coiffeuse_id': self.coiffeuse.pk})
        response = self.client.get(url, {'date': date.today().strftime('%Y-%m-%d')})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duree', response.data['error'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    def test_get_disponibilites_format_date_invalide(self):
        """Teste l'échec de la requête avec un format de date incorrect."""
        url = reverse('get-disponibilites-client', kwargs={'coiffeuse_id': self.coiffeuse.pk})
        response = self.client.get(url, {'date': '10-06-2025', 'duree': '60'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Format invalide', response.data['error'])

    @patch('decorators.decorators.firebase_authenticated', lambda f: f)
    @patch('hairbnb.dispinibilites.disponibilities_serializers.DisponibilitesClientSerializer.is_valid',
           return_value=True)
    @patch('hairbnb.dispinibilites.disponibilities_serializers.DisponibilitesClientSerializer.calculate_disponibilites')
    def test_get_creneaux_jour_succes(self, mock_calculate, mock_is_valid):
        """Teste l'appel réussi à la vue get_creneaux_jour pour Flutter."""
        mock_calculate.return_value = self.mock_dispos

        test_date_str = date.today().strftime('%Y-%m-%d')
        url = reverse('get-creneaux-jour', kwargs={'coiffeuse_id': self.coiffeuse.pk})
        response = self.client.get(url, {'date': test_date_str, 'duree': '30'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['creneaux'], self.mock_dispos)
        self.assertEqual(response.data['date'], test_date_str)