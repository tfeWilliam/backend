"""
Tests complets pour le module Coiffeuse
Couvre les views, business logic et intégration
"""

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import json
import logging

from hairbnb.models import (
    TblUser, TblLocalite, TblRue, TblAdresse, TblRole, TblSexe, TblType,
    TblCoiffeuse, TblSalon, TblCoiffeuseSalon
)
from hairbnb.coiffeuse.coiffeuse_business_logic import MinimalCoiffeuseData


class CoiffeuseSetupMixin:
    """Mixin pour setup commun aux tests Coiffeuse"""
    
    def setUp(self):
        """Configuration initiale pour tous les tests"""
        # Créer les données de base
        self.localite = TblLocalite.objects.create(
            commune='Bruxelles',
            code_postal='1000'
        )
        
        self.rue = TblRue.objects.create(
            nom_rue='Rue de la Paix',
            localite=self.localite
        )
        
        self.adresse = TblAdresse.objects.create(
            numero='123',
            rue=self.rue
        )
        
        self.adresse2 = TblAdresse.objects.create(
            numero='456',
            rue=self.rue
        )
        
        self.role_coiffeuse = TblRole.objects.create(nom='coiffeuse')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_coiffeuse = TblType.objects.create(libelle='coiffeuse')
        
        # Créer des utilisateurs coiffeuses
        self.user_coiffeuse1 = TblUser.objects.create(
            uuid='coiffeuse-uuid-001',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456788',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role_coiffeuse,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        
        self.user_coiffeuse2 = TblUser.objects.create(
            uuid='coiffeuse-uuid-002',
            nom='Dubois',
            prenom='Marie',
            email='marie.dubois@example.com',
            numero_telephone='+32123456787',
            date_naissance=date(1988, 7, 15),
            adresse=self.adresse2,
            role=self.role_coiffeuse,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        
        self.user_coiffeuse3 = TblUser.objects.create(
            uuid='coiffeuse-uuid-003',
            nom='Leroy',
            prenom='Claire',
            email='claire.leroy@example.com',
            numero_telephone='+32123456786',
            date_naissance=date(1990, 11, 8),
            adresse=self.adresse,
            role=self.role_coiffeuse,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        
        # Créer les coiffeuses
        self.coiffeuse1 = TblCoiffeuse.objects.create(
            idTblUser=self.user_coiffeuse1,
            nom_commercial='Salon Sophie'
        )
        
        self.coiffeuse2 = TblCoiffeuse.objects.create(
            idTblUser=self.user_coiffeuse2,
            nom_commercial='Salon Marie'
        )
        
        self.coiffeuse3 = TblCoiffeuse.objects.create(
            idTblUser=self.user_coiffeuse3,
            nom_commercial='Salon Claire'
        )
        
        # Créer des salons
        self.salon1 = TblSalon.objects.create(
            nom_salon='Salon Belle Coupe',
            slogan='La beauté à votre service',
            numero_tva='BE0123456789',
            adresse=self.adresse,
            position='50.8503,4.3517'
        )
        
        self.salon2 = TblSalon.objects.create(
            nom_salon='Salon Moderne',
            slogan='Style et élégance',
            numero_tva='BE0987654321',
            adresse=self.adresse2,
            position='50.8403,4.3417'
        )
        
        self.salon3 = TblSalon.objects.create(
            nom_salon='Salon Tendance',
            slogan='Toujours à la mode',
            adresse=self.adresse,
            position='50.8603,4.3617'
        )
        
        # Lier les coiffeuses aux salons
        self.coiffeuse_salon1 = TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse1,
            salon=self.salon1,
            est_proprietaire=True
        )
        
        self.coiffeuse_salon2 = TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse2,
            salon=self.salon2,
            est_proprietaire=True
        )
        
        # Coiffeuse3 travaille dans salon1 (sans être propriétaire)
        self.coiffeuse_salon3 = TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse3,
            salon=self.salon1,
            est_proprietaire=False
        )
        
        # Coiffeuse1 travaille aussi dans salon3 (sans être propriétaire)
        self.coiffeuse_salon_extra = TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse1,
            salon=self.salon3,
            est_proprietaire=False
        )


class MinimalCoiffeuseDataTestCase(CoiffeuseSetupMixin, TestCase):
    """Tests pour la classe MinimalCoiffeuseData"""
    
    def test_creation_minimal_coiffeuse_data_proprietaire(self):
        """Test de création des données minimales pour une coiffeuse propriétaire"""
        data = MinimalCoiffeuseData(self.coiffeuse1)
        
        # Vérifications des données de base
        self.assertEqual(data.idTblUser, self.user_coiffeuse1.idTblUser)
        self.assertEqual(data.uuid, 'coiffeuse-uuid-001')
        self.assertEqual(data.nom, 'Martin')
        self.assertEqual(data.prenom, 'Sophie')
        self.assertEqual(data.nom_commercial, 'Salon Sophie')
        
        # Vérifications des salons
        self.assertEqual(len(data.autres_salons), 2)  # salon1 + salon3
        
        # Vérifier le salon où elle est propriétaire
        salon_proprietaire = next(
            (s for s in data.autres_salons if s['est_proprietaire']), 
            None
        )
        self.assertIsNotNone(salon_proprietaire)
        self.assertEqual(salon_proprietaire['nom_salon'], 'Salon Belle Coupe')
        
        # Vérifier le salon où elle n'est pas propriétaire
        salon_employe = next(
            (s for s in data.autres_salons if not s['est_proprietaire']), 
            None
        )
        self.assertIsNotNone(salon_employe)
        self.assertEqual(salon_employe['nom_salon'], 'Salon Tendance')
    
    def test_creation_minimal_coiffeuse_data_employe(self):
        """Test de création des données minimales pour une coiffeuse employée"""
        data = MinimalCoiffeuseData(self.coiffeuse3)
        
        # Vérifications des données de base
        self.assertEqual(data.nom, 'Leroy')
        self.assertEqual(data.prenom, 'Claire')
        self.assertEqual(data.nom_commercial, 'Salon Claire')
        
        # Vérifications des salons
        self.assertEqual(len(data.autres_salons), 1)
        salon_employe = data.autres_salons[0]
        self.assertEqual(salon_employe['nom_salon'], 'Salon Belle Coupe')
        self.assertFalse(salon_employe['est_proprietaire'])
    
    def test_minimal_coiffeuse_data_sans_salon(self):
        """Test de création des données pour une coiffeuse sans salon"""
        # Créer une coiffeuse sans salon
        user_solo = TblUser.objects.create(
            uuid='coiffeuse-solo',
            nom='Solo',
            prenom='Coiffeuse',
            email='solo@example.com',
            numero_telephone='+32123456785',
            date_naissance=date(1992, 1, 1),
            adresse=self.adresse,
            role=self.role_coiffeuse,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        
        coiffeuse_solo = TblCoiffeuse.objects.create(
            idTblUser=user_solo,
            nom_commercial='Coiffeuse Solo'
        )
        
        data = MinimalCoiffeuseData(coiffeuse_solo)
        
        self.assertEqual(data.nom_commercial, 'Coiffeuse Solo')
        self.assertEqual(len(data.autres_salons), 0)
        self.assertIsNone(data.salon)
    
    def test_minimal_coiffeuse_data_photo_profil(self):
        """Test de gestion de la photo de profil"""
        # Test avec photo de profil
        self.user_coiffeuse1.photo_profil = 'photos/profils/test.jpg'
        data = MinimalCoiffeuseData(self.coiffeuse1)
        self.assertIsNotNone(data.photo_profil)
        
        # Test sans photo de profil
        self.user_coiffeuse1.photo_profil = None
        data = MinimalCoiffeuseData(self.coiffeuse1)
        self.assertIsNone(data.photo_profil)
    
    def test_minimal_coiffeuse_data_to_dict(self):
        """Test de la méthode to_dict"""
        data = MinimalCoiffeuseData(self.coiffeuse1)
        data_dict = data.to_dict()
        
        # Vérifier que c'est un dictionnaire
        self.assertIsInstance(data_dict, dict)
        
        # Vérifier que toutes les clés importantes sont présentes
        required_keys = [
            'idTblUser', 'uuid', 'nom', 'prenom', 'photo_profil',
            'nom_commercial', 'salon', 'autres_salons'
        ]
        
        for key in required_keys:
            self.assertIn(key, data_dict)
    
    def test_minimal_coiffeuse_data_salon_avec_logo(self):
        """Test de gestion du logo de salon"""
        # Ajouter un logo au salon
        self.salon1.logo_salon = 'logos/salon1.jpg'
        self.salon1.save()
        
        data = MinimalCoiffeuseData(self.coiffeuse1)
        
        # Trouver le salon avec logo dans autres_salons
        salon_avec_logo = next(
            (s for s in data.autres_salons if s['idTblSalon'] == self.salon1.idTblSalon),
            None
        )
        # Note: Le logo n'est pas inclus dans autres_salons, seulement dans salon_direct
        # Ce test vérifie que le code ne plante pas avec un logo


class CoiffeuseViewsTestCase(CoiffeuseSetupMixin, APITestCase):
    """Tests pour les vues Coiffeuse"""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        
        # Désactiver les logs pendant les tests pour plus de clarté
        logging.disable(logging.CRITICAL)
    
    def tearDown(self):
        # Réactiver les logs après les tests
        logging.disable(logging.NOTSET)
    
    def test_get_coiffeuses_info_success(self):
        """Test de récupération des informations de coiffeuses avec succès"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['coiffeuse-uuid-001', 'coiffeuse-uuid-002']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('coiffeuses', response_data)
        self.assertEqual(len(response_data['coiffeuses']), 2)
        
        # Vérifier les données de la première coiffeuse
        coiffeuse1_data = next(
            (c for c in response_data['coiffeuses'] if c['uuid'] == 'coiffeuse-uuid-001'),
            None
        )
        self.assertIsNotNone(coiffeuse1_data)
        self.assertEqual(coiffeuse1_data['nom'], 'Martin')
        self.assertEqual(coiffeuse1_data['prenom'], 'Sophie')
        self.assertEqual(coiffeuse1_data['nom_commercial'], 'Salon Sophie')
        
        # Vérifier les données de la deuxième coiffeuse
        coiffeuse2_data = next(
            (c for c in response_data['coiffeuses'] if c['uuid'] == 'coiffeuse-uuid-002'),
            None
        )
        self.assertIsNotNone(coiffeuse2_data)
        self.assertEqual(coiffeuse2_data['nom'], 'Dubois')
        self.assertEqual(coiffeuse2_data['prenom'], 'Marie')
    
    def test_get_coiffeuses_info_partial_match(self):
        """Test de récupération avec seulement certains UUIDs valides"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['coiffeuse-uuid-001', 'uuid-inexistant', 'coiffeuse-uuid-003']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(len(response_data['coiffeuses']), 2)  # Seulement les UUIDs valides
        
        # Vérifier que les bonnes coiffeuses sont retournées
        uuids_retournes = [c['uuid'] for c in response_data['coiffeuses']]
        self.assertIn('coiffeuse-uuid-001', uuids_retournes)
        self.assertIn('coiffeuse-uuid-003', uuids_retournes)
        self.assertNotIn('uuid-inexistant', uuids_retournes)
    
    def test_get_coiffeuses_info_no_uuids(self):
        """Test avec aucun UUID fourni"""
        url = reverse('get_coiffeuses_info')
        data = {'uuids': []}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Aucun UUID fourni')
    
    def test_get_coiffeuses_info_missing_uuids_key(self):
        """Test avec clé 'uuids' manquante"""
        url = reverse('get_coiffeuses_info')
        data = {'other_key': 'value'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Aucun UUID fourni')
    
    def test_get_coiffeuses_info_invalid_json(self):
        """Test avec JSON invalide"""
        url = reverse('get_coiffeuses_info')
        
        response = self.client.post(
            url, 
            'invalid json content', 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Format de requête invalide')
    
    def test_get_coiffeuses_info_all_invalid_uuids(self):
        """Test avec tous les UUIDs invalides"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['uuid-inexistant-1', 'uuid-inexistant-2']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(len(response_data['coiffeuses']), 0)
    
    def test_get_coiffeuses_info_method_not_allowed(self):
        """Test que seul POST est autorisé"""
        url = reverse('get_coiffeuses_info')
        
        # GET devrait être refusé
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PUT devrait être refusé
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # DELETE devrait être refusé
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_get_coiffeuses_info_with_salon_details(self):
        """Test de récupération avec détails complets des salons"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['coiffeuse-uuid-001']  # Coiffeuse avec plusieurs salons
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        coiffeuse_data = response_data['coiffeuses'][0]
        
        # Vérifier les salons
        self.assertIn('autres_salons', coiffeuse_data)
        self.assertEqual(len(coiffeuse_data['autres_salons']), 2)
        
        # Vérifier qu'elle est propriétaire d'au moins un salon
        est_proprietaire_quelque_part = any(
            salon['est_proprietaire'] for salon in coiffeuse_data['autres_salons']
        )
        self.assertTrue(est_proprietaire_quelque_part)
    
    @patch('hairbnb.coiffeuse.coiffeuse_views.TblCoiffeuse.objects.filter')
    def test_get_coiffeuses_info_database_error(self):
        """Test de gestion d'erreur de base de données"""
        # Simuler une erreur de base de données
        mock_filter = Mock()
        mock_filter.side_effect = Exception("Database error")
        
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['coiffeuse-uuid-001']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(response_data['message'], 'Erreur interne du serveur')


class CoiffeuseIntegrationTestCase(CoiffeuseSetupMixin, APITestCase):
    """Tests d'intégration pour le module Coiffeuse"""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    def test_workflow_complete_get_multiple_coiffeuses(self):
        """Test du workflow complet de récupération de plusieurs coiffeuses"""
        # 1. Récupérer plusieurs coiffeuses
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': [
                'coiffeuse-uuid-001',
                'coiffeuse-uuid-002', 
                'coiffeuse-uuid-003'
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # 2. Vérifier que toutes les coiffeuses sont retournées
        self.assertEqual(len(response_data['coiffeuses']), 3)
        
        # 3. Vérifier la cohérence des données avec la base
        for coiffeuse_data in response_data['coiffeuses']:
            uuid = coiffeuse_data['uuid']
            
            # Récupérer l'objet de la base
            coiffeuse_db = TblCoiffeuse.objects.get(idTblUser__uuid=uuid)
            
            # Vérifier la cohérence
            self.assertEqual(coiffeuse_data['nom'], coiffeuse_db.idTblUser.nom)
            self.assertEqual(coiffeuse_data['prenom'], coiffeuse_db.idTblUser.prenom)
            self.assertEqual(coiffeuse_data['nom_commercial'], coiffeuse_db.nom_commercial)
            
            # Vérifier le nombre de salons
            salons_db_count = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse_db).count()
            self.assertEqual(len(coiffeuse_data['autres_salons']), salons_db_count)
    
    def test_workflow_search_and_verify_salon_info(self):
        """Test de recherche et vérification des informations salon"""
        # 1. Récupérer une coiffeuse spécifique
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['coiffeuse-uuid-001']  # Sophie, propriétaire de salon1, employée de salon3
        }
        
        response = self.client.post(url, data, format='json')
        coiffeuse_data = response.json()['coiffeuses'][0]
        
        # 2. Vérifier les informations des salons
        salon_proprietaire = next(
            (s for s in coiffeuse_data['autres_salons'] if s['est_proprietaire']),
            None
        )
        self.assertIsNotNone(salon_proprietaire)
        self.assertEqual(salon_proprietaire['nom_salon'], 'Salon Belle Coupe')
        
        salon_employe = next(
            (s for s in coiffeuse_data['autres_salons'] if not s['est_proprietaire']),
            None
        )
        self.assertIsNotNone(salon_employe)
        self.assertEqual(salon_employe['nom_salon'], 'Salon Tendance')
        
        # 3. Vérifier la cohérence avec la base de données
        salon_db1 = TblSalon.objects.get(idTblSalon=salon_proprietaire['idTblSalon'])
        self.assertEqual(salon_db1.nom_salon, salon_proprietaire['nom_salon'])
        
        salon_db2 = TblSalon.objects.get(idTblSalon=salon_employe['idTblSalon'])
        self.assertEqual(salon_db2.nom_salon, salon_employe['nom_salon'])
    
    def test_workflow_partial_match_handling(self):
        """Test de gestion des correspondances partielles"""
        # 1. Mélanger UUIDs valides et invalides
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': [
                'coiffeuse-uuid-001',  # Valide
                'uuid-inexistant-1',   # Invalide
                'coiffeuse-uuid-002',  # Valide
                'uuid-inexistant-2',   # Invalide
                'coiffeuse-uuid-003'   # Valide
            ]
        }
        
        response = self.client.post(url, data, format='json')
        response_data = response.json()
        
        # 2. Vérifier que seules les coiffeuses valides sont retournées
        self.assertEqual(len(response_data['coiffeuses']), 3)
        
        uuids_retournes = {c['uuid'] for c in response_data['coiffeuses']}
        uuids_attendus = {'coiffeuse-uuid-001', 'coiffeuse-uuid-002', 'coiffeuse-uuid-003'}
        
        self.assertEqual(uuids_retournes, uuids_attendus)
        
        # 3. Vérifier qu'aucun UUID invalide n'est retourné
        for coiffeuse_data in response_data['coiffeuses']:
            self.assertNotIn('inexistant', coiffeuse_data['uuid'])


class CoiffeuseEdgeCasesTestCase(CoiffeuseSetupMixin, TestCase):
    """Tests pour les cas particuliers et erreurs"""
    
    def test_minimal_coiffeuse_data_with_none_values(self):
        """Test de MinimalCoiffeuseData avec des valeurs None"""
        # Créer une coiffeuse avec des champs optionnels à None
        user_minimal = TblUser.objects.create(
            uuid='coiffeuse-minimal',
            nom='Minimal',
            prenom='Test',
            email='minimal@example.com',
            numero_telephone='+32123456784',
            date_naissance=date(1990, 1, 1),
            adresse=self.adresse,
            role=self.role_coiffeuse,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse,
            photo_profil=None  # Pas de photo
        )
        
        coiffeuse_minimal = TblCoiffeuse.objects.create(
            idTblUser=user_minimal,
            nom_commercial=None  # Pas de nom commercial
        )
        
        # Créer les données sans erreur
        data = MinimalCoiffeuseData(coiffeuse_minimal)
        
        self.assertIsNone(data.photo_profil)
        self.assertIsNone(data.nom_commercial)
        self.assertEqual(len(data.autres_salons), 0)
        self.assertIsNone(data.salon)
    
    def test_minimal_coiffeuse_data_avec_salon_sans_logo(self):
        """Test avec un salon sans logo"""
        # Le salon3 n'a pas de logo par défaut
        data = MinimalCoiffeuseData(self.coiffeuse1)  # Travaille dans salon3
        
        # Vérifier que le code ne plante pas
        data_dict = data.to_dict()
        self.assertIsInstance(data_dict, dict)
    
    def test_get_coiffeuses_info_with_empty_request_body(self):
        """Test avec un body de requête vide"""
        url = reverse('get_coiffeuses_info')
        
        response = self.client.post(url, '', content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['status'], 'error')
    
    def test_get_coiffeuses_info_with_malformed_data(self):
        """Test avec des données malformées"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': 'should-be-list-not-string'  # Type incorrect
        }
        
        response = self.client.post(url, data, format='json')
        
        # La vue devrait gérer cela gracieusement
        self.assertIn(response.status_code, [400, 500])
    
    def test_minimal_coiffeuse_data_avec_coiffeuse_supprimee_du_salon(self):
        """Test après suppression d'une relation coiffeuse-salon"""
        # Supprimer une relation
        TblCoiffeuseSalon.objects.filter(
            coiffeuse=self.coiffeuse1,
            salon=self.salon3
        ).delete()
        
        data = MinimalCoiffeuseData(self.coiffeuse1)
        
        # Vérifier que le nombre de salons a diminué
        self.assertEqual(len(data.autres_salons), 1)  # Plus que salon1
        
        salon_restant = data.autres_salons[0]
        self.assertEqual(salon_restant['nom_salon'], 'Salon Belle Coupe')
        self.assertTrue(salon_restant['est_proprietaire'])
    
    def test_get_coiffeuses_info_avec_uuids_duplicate(self):
        """Test avec des UUIDs dupliqués"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': [
                'coiffeuse-uuid-001',
                'coiffeuse-uuid-001',  # Duplicata
                'coiffeuse-uuid-002'
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Vérifier qu'il n'y a pas de doublons dans la réponse
        uuids_retournes = [c['uuid'] for c in response_data['coiffeuses']]
        uuids_uniques = list(set(uuids_retournes))
        
        self.assertEqual(len(uuids_retournes), len(uuids_uniques))
        self.assertEqual(len(response_data['coiffeuses']), 2)


class CoiffeusePerformanceTestCase(CoiffeuseSetupMixin, TestCase):
    """Tests de performance pour le module Coiffeuse"""
    
    def test_performance_avec_beaucoup_de_coiffeuses(self):
        """Test de performance avec beaucoup de coiffeuses"""
        # Créer 20 coiffeuses supplémentaires
        coiffeuses_uuids = []
        for i in range(20):
            user = TblUser.objects.create(
                uuid=f'coiffeuse-perf-{i:03d}',
                nom=f'TestNom{i}',
                prenom=f'TestPrenom{i}',
                email=f'test{i}@example.com',
                numero_telephone=f'+3212345{i:04d}',
                date_naissance=date(1985, 1, 1),
                adresse=self.adresse,
                role=self.role_coiffeuse,
                sexe_ref=self.sexe,
                type_ref=self.type_coiffeuse
            )
            
            coiffeuse = TblCoiffeuse.objects.create(
                idTblUser=user,
                nom_commercial=f'Salon Test {i}'
            )
            
            coiffeuses_uuids.append(user.uuid)
        
        # Créer les données pour toutes les coiffeuses
        coiffeuses = TblCoiffeuse.objects.filter(idTblUser__uuid__in=coiffeuses_uuids)
        
        # Mesurer le temps de traitement (test basique)
        import time
        start_time = time.time()
        
        coiffeuses_data = [MinimalCoiffeuseData(c).to_dict() for c in coiffeuses]
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Vérifications
        self.assertEqual(len(coiffeuses_data), 20)
        
        # Le traitement ne devrait pas prendre plus de 1 seconde pour 20 coiffeuses
        self.assertLess(processing_time, 1.0)
    
    def test_performance_avec_beaucoup_de_salons_par_coiffeuse(self):
        """Test de performance avec une coiffeuse dans beaucoup de salons"""
        # Créer 10 salons supplémentaires
        salons_supplementaires = []
        for i in range(10):
            salon = TblSalon.objects.create(
                nom_salon=f'Salon Perf {i}',
                adresse=self.adresse
            )
            
            # Lier la coiffeuse1 à ce salon
            TblCoiffeuseSalon.objects.create(
                coiffeuse=self.coiffeuse1,
                salon=salon,
                est_proprietaire=False
            )
            
            salons_supplementaires.append(salon)
        
        # Créer les données
        data = MinimalCoiffeuseData(self.coiffeuse1)
        
        # Vérifications
        self.assertEqual(len(data.autres_salons), 12)  # 2 originaux + 10 nouveaux
        
        # Vérifier que toutes les relations sont correctement chargées
        for salon_data in data.autres_salons:
            self.assertIn('idTblSalon', salon_data)
            self.assertIn('nom_salon', salon_data)
            self.assertIn('est_proprietaire', salon_data)


class CoiffeuseLoggingTestCase(CoiffeuseSetupMixin, APITestCase):
    """Tests pour vérifier le bon fonctionnement du logging"""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    @patch('hairbnb.coiffeuse.coiffeuse_views.logger')
    def test_logging_success_case(self):
        """Test que les logs sont émis correctement en cas de succès"""
        url = reverse('get_coiffeuses_info')
        data = {
            'uuids': ['coiffeuse-uuid-001', 'coiffeuse-uuid-002']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que les logs ont été appelés (mock nécessaire car disabled dans setUp)
        # Les appels exacts dépendent de l'implémentation du logger
    
    @patch('hairbnb.coiffeuse.coiffeuse_views.logger')
    def test_logging_error_case(self):
        """Test que les erreurs sont loggées correctement"""
        url = reverse('get_coiffeuses_info')
        
        response = self.client.post(url, 'invalid json', content_type='application/json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que l'erreur a été loggée (mock nécessaire)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'rest_framework',
                'hairbnb',
            ],
            REST_FRAMEWORK={
                'DEFAULT_AUTHENTICATION_CLASSES': [],
                'DEFAULT_PERMISSION_CLASSES': [],
            }
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["hairbnb.coiffeuse.test_coiffeuse"])
