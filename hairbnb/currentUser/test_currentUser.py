"""
Tests pour le module CurrentUser
Couvre les views, serializers et la logique métier
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import Mock, patch
from datetime import date
from decimal import Decimal
import json

from hairbnb.models import (
    TblUser, TblLocalite, TblRue, TblAdresse, TblRole, TblSexe, TblType,
    TblCoiffeuse, TblClient, TblSalon, TblCoiffeuseSalon
)
from hairbnb.currentUser.CurrentUser_serializer import (
    CurrentUserSerializer, TblLocaliteSerializer, TblRueSerializer,
    TblAdresseSerializer, TblCoiffeuseSerializer, LocaliteSerializer,
    RueSerializer, AdresseSerializer, UserSerializer
)
from hairbnb.currentUser.currentUser_business_logic import CurrentUserData


class CurrentUserSetupMixin:
    """Mixin pour setup commun aux tests CurrentUser"""
    
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
        
        self.role_user = TblRole.objects.create(nom='user')
        self.role_coiffeuse = TblRole.objects.create(nom='coiffeuse')
        
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_client = TblType.objects.create(libelle='client')
        self.type_coiffeuse = TblType.objects.create(libelle='coiffeuse')
        
        # Créer un utilisateur client
        self.user_client = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role_user,
            sexe_ref=self.sexe,
            type_ref=self.type_client
        )
        
        # Créer un utilisateur coiffeuse
        self.user_coiffeuse = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
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
        
        # Créer la coiffeuse
        self.coiffeuse = TblCoiffeuse.objects.create(
            idTblUser=self.user_coiffeuse,
            nom_commercial='Salon Sophie'
        )
        
        # Créer un salon
        self.salon = TblSalon.objects.create(
            nom_salon='Salon Belle Coupe',
            slogan='La beauté à votre service',
            numero_tva='BE0123456789',
            adresse=self.adresse,
            position='50.8503,4.3517'
        )
        
        # Lier la coiffeuse au salon comme propriétaire
        self.coiffeuse_salon = TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse,
            salon=self.salon,
            est_proprietaire=True
        )
        
        # Créer un client
        self.client_obj = TblClient.objects.create(idTblUser=self.user_client)


class CurrentUserSerializerTestCase(CurrentUserSetupMixin, TestCase):
    """Tests pour les serializers CurrentUser"""
    
    def test_localite_serializer(self):
        """Test du LocaliteSerializer"""
        serializer = LocaliteSerializer(self.localite)
        data = serializer.data
        
        self.assertEqual(data['commune'], 'Bruxelles')
        self.assertEqual(data['code_postal'], '1000')
        self.assertIn('idTblLocalite', data)
    
    def test_tbl_localite_serializer(self):
        """Test du TblLocaliteSerializer"""
        serializer = TblLocaliteSerializer(self.localite)
        data = serializer.data
        
        self.assertEqual(data['commune'], 'Bruxelles')
        self.assertEqual(data['code_postal'], '1000')
        self.assertNotIn('idTblLocalite', data)
    
    def test_rue_serializer(self):
        """Test du RueSerializer"""
        serializer = RueSerializer(self.rue)
        data = serializer.data
        
        self.assertEqual(data['nom_rue'], 'Rue de la Paix')
        self.assertIn('localite', data)
        self.assertEqual(data['localite']['commune'], 'Bruxelles')
    
    def test_tbl_rue_serializer(self):
        """Test du TblRueSerializer"""
        serializer = TblRueSerializer(self.rue)
        data = serializer.data
        
        self.assertEqual(data['nom_rue'], 'Rue de la Paix')
        self.assertIn('localite', data)
        self.assertEqual(data['localite']['commune'], 'Bruxelles')
    
    def test_adresse_serializer(self):
        """Test du AdresseSerializer"""
        serializer = AdresseSerializer(self.adresse)
        data = serializer.data
        
        self.assertEqual(data['numero'], '123')
        self.assertIn('rue', data)
        self.assertEqual(data['rue']['nom_rue'], 'Rue de la Paix')
    
    def test_tbl_adresse_serializer(self):
        """Test du TblAdresseSerializer"""
        serializer = TblAdresseSerializer(self.adresse)
        data = serializer.data
        
        self.assertEqual(data['numero'], '123')
        self.assertIn('rue', data)
        self.assertEqual(data['rue']['nom_rue'], 'Rue de la Paix')
    
    def test_tbl_coiffeuse_serializer(self):
        """Test du TblCoiffeuseSerializer"""
        serializer = TblCoiffeuseSerializer(self.coiffeuse)
        data = serializer.data
        
        self.assertEqual(data['nom_commercial'], 'Salon Sophie')
        self.assertIn('salons', data)
        self.assertIn('salon_principal', data)
        self.assertIn('est_proprietaire', data)
        
        # Vérifier les salons
        self.assertEqual(len(data['salons']), 1)
        self.assertEqual(data['salons'][0]['nom_salon'], 'Salon Belle Coupe')
        self.assertTrue(data['salons'][0]['est_proprietaire'])
        
        # Vérifier le salon principal
        self.assertIsNotNone(data['salon_principal'])
        self.assertEqual(data['salon_principal']['nom_salon'], 'Salon Belle Coupe')
        
        # Vérifier est_proprietaire
        self.assertTrue(data['est_proprietaire'])
    
    def test_current_user_serializer_client(self):
        """Test du CurrentUserSerializer pour un client"""
        request = Mock()
        request.build_absolute_uri = Mock(return_value='http://testserver/media/test.jpg')
        
        serializer = CurrentUserSerializer(
            self.user_client,
            context={'request': request}
        )
        data = serializer.data
        
        # Vérifications de base
        self.assertEqual(data['nom'], 'Dupont')
        self.assertEqual(data['prenom'], 'Marie')
        self.assertEqual(data['email'], 'marie.dupont@example.com')
        self.assertEqual(data['type'], 'client')
        self.assertEqual(data['sexe'], 'Femme')
        self.assertEqual(data['role'], 'user')
        
        # Vérifier l'adresse
        self.assertIn('adresse', data)
        self.assertEqual(data['adresse']['numero'], '123')
        
        # Le client ne devrait pas avoir de données coiffeuse
        self.assertIsNone(data['coiffeuse'])
    
    def test_current_user_serializer_coiffeuse(self):
        """Test du CurrentUserSerializer pour une coiffeuse"""
        request = Mock()
        request.build_absolute_uri = Mock(return_value='http://testserver/media/test.jpg')
        
        serializer = CurrentUserSerializer(
            self.user_coiffeuse,
            context={'request': request}
        )
        data = serializer.data
        
        # Vérifications de base
        self.assertEqual(data['nom'], 'Martin')
        self.assertEqual(data['prenom'], 'Sophie')
        self.assertEqual(data['type'], 'coiffeuse')
        
        # Vérifier les données coiffeuse
        self.assertIsNotNone(data['coiffeuse'])
        self.assertEqual(data['coiffeuse']['nom_commercial'], 'Salon Sophie')
        self.assertTrue(data['coiffeuse']['est_proprietaire'])
    
    def test_current_user_serializer_photo_profil_url(self):
        """Test de la conversion URL de la photo de profil"""
        request = Mock()
        request.build_absolute_uri = Mock(return_value='http://testserver/media/test.jpg')
        
        # Simuler une photo de profil
        self.user_client.photo_profil = 'test.jpg'
        
        serializer = CurrentUserSerializer(
            self.user_client,
            context={'request': request}
        )
        data = serializer.data
        
        self.assertEqual(data['photo_profil'], 'http://testserver/media/test.jpg')
        request.build_absolute_uri.assert_called_once()


class CurrentUserViewsTestCase(CurrentUserSetupMixin, APITestCase):
    """Tests pour les vues CurrentUser"""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    def test_get_current_user_authenticated(self):
        """Test get_current_user avec utilisateur authentifié"""
        # Simuler un utilisateur authentifié
        self.client.force_authenticate(user=self.user_client)
        
        # Mock de la request pour avoir le bon user
        with patch('hairbnb.currentUser.currentUser_views.request') as mock_request:
            mock_request.user = self.user_client
            
            url = reverse('get_current_user')
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('user', data)
        self.assertEqual(data['user']['nom'], 'Dupont')
    
    def test_get_current_user_no_user(self):
        """Test get_current_user sans utilisateur"""
        # Mock d'un utilisateur sans uuid
        mock_user = Mock()
        mock_user.uuid = None
        
        with patch('hairbnb.currentUser.currentUser_views.request') as mock_request:
            mock_request.user = mock_user
            
            url = reverse('get_current_user')
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Utilisateur non trouvé')
    
    def test_get_current_user_anonymous(self):
        """Test get_current_user avec utilisateur anonyme"""
        with patch('hairbnb.currentUser.currentUser_views.request') as mock_request:
            mock_request.user = None
            
            url = reverse('get_current_user')
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_user_by_id_existing_user(self):
        """Test get_user_by_id avec utilisateur existant"""
        url = reverse('get_user_by_id', kwargs={'id': self.user_client.idTblUser})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('user', data)
        self.assertEqual(data['user']['nom'], 'Dupont')
        self.assertEqual(data['user']['email'], 'marie.dupont@example.com')
    
    def test_get_user_by_id_coiffeuse_with_salon_info(self):
        """Test get_user_by_id pour une coiffeuse avec infos salon enrichies"""
        url = reverse('get_user_by_id', kwargs={'id': self.user_coiffeuse.idTblUser})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        user_data = data['user']
        
        # Vérifier les données de base
        self.assertEqual(user_data['nom'], 'Martin')
        self.assertEqual(user_data['type'], 'coiffeuse')
        
        # Vérifier les données enrichies de coiffeuse
        self.assertIn('coiffeuse', user_data)
        coiffeuse_data = user_data['coiffeuse']
        
        # Vérifier tous_salons
        self.assertIn('tous_salons', coiffeuse_data)
        self.assertEqual(len(coiffeuse_data['tous_salons']), 1)
        salon_info = coiffeuse_data['tous_salons'][0]
        self.assertEqual(salon_info['nom_salon'], 'Salon Belle Coupe')
        self.assertTrue(salon_info['est_proprietaire'])
        
        # Vérifier salon_principal
        self.assertIn('salon_principal', coiffeuse_data)
        salon_principal = coiffeuse_data['salon_principal']
        self.assertIsNotNone(salon_principal)
        self.assertEqual(salon_principal['nom_salon'], 'Salon Belle Coupe')
        self.assertEqual(salon_principal['numero_tva'], 'BE0123456789')
        
        # Vérifier l'adresse du salon principal
        self.assertIn('adresse', salon_principal)
        adresse_salon = salon_principal['adresse']
        self.assertEqual(adresse_salon['numero'], '123')
        self.assertEqual(adresse_salon['rue'], 'Rue de la Paix')
        self.assertEqual(adresse_salon['commune'], 'Bruxelles')
    
    def test_get_user_by_id_nonexistent_user(self):
        """Test get_user_by_id avec utilisateur inexistant"""
        url = reverse('get_user_by_id', kwargs={'id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Utilisateur introuvable')
    
    def test_get_user_by_id_methods_allowed(self):
        """Test que seul GET est autorisé pour get_user_by_id"""
        url = reverse('get_user_by_id', kwargs={'id': self.user_client.idTblUser})
        
        # POST devrait être refusé
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PUT devrait être refusé
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # DELETE devrait être refusé
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CurrentUserBusinessLogicTestCase(CurrentUserSetupMixin, TestCase):
    """Tests pour la logique métier CurrentUser"""
    
    def test_current_user_data_client(self):
        """Test CurrentUserData pour un client"""
        user_data = CurrentUserData(self.user_client)
        
        # Vérifications de base
        self.assertEqual(user_data.nom, 'Dupont')
        self.assertEqual(user_data.prenom, 'Marie')
        self.assertEqual(user_data.email, 'marie.dupont@example.com')
        self.assertEqual(user_data.type, 'client')
        self.assertEqual(user_data.sexe, 'Femme')
        
        # Vérifier l'adresse
        self.assertIsNotNone(user_data.adresse)
        self.assertEqual(user_data.adresse['numero'], '123')
        self.assertEqual(user_data.adresse['rue'], 'Rue de la Paix')
        self.assertEqual(user_data.adresse['commune'], 'Bruxelles')
        self.assertEqual(user_data.adresse['code_postal'], '1000')
        
        # Le client ne devrait pas avoir d'extra_data spécifique
        self.assertIsNone(user_data.extra_data)
    
    def test_current_user_data_coiffeuse(self):
        """Test CurrentUserData pour une coiffeuse"""
        user_data = CurrentUserData(self.user_coiffeuse)
        
        # Vérifications de base
        self.assertEqual(user_data.nom, 'Martin')
        self.assertEqual(user_data.prenom, 'Sophie')
        self.assertEqual(user_data.type, 'coiffeuse')
        
        # Vérifier les extra_data de coiffeuse
        self.assertIsNotNone(user_data.extra_data)
        extra_data = user_data.extra_data
        
        self.assertEqual(extra_data['nom_commercial'], 'Salon Sophie')
        
        # Vérifier salon_principal
        self.assertIn('salon_principal', extra_data)
        salon_principal = extra_data['salon_principal']
        self.assertIsNotNone(salon_principal)
        self.assertEqual(salon_principal['nom_salon'], 'Salon Belle Coupe')
        self.assertEqual(salon_principal['numero_tva'], 'BE0123456789')
        
        # Vérifier tous_salons
        self.assertIn('tous_salons', extra_data)
        self.assertEqual(len(extra_data['tous_salons']), 1)
        salon_info = extra_data['tous_salons'][0]
        self.assertEqual(salon_info['nom_salon'], 'Salon Belle Coupe')
        self.assertTrue(salon_info['est_proprietaire'])
    
    def test_current_user_data_coiffeuse_multiple_salons(self):
        """Test CurrentUserData pour une coiffeuse avec plusieurs salons"""
        # Créer un deuxième salon
        salon2 = TblSalon.objects.create(
            nom_salon='Salon Secondaire',
            slogan='Autre salon',
            adresse=self.adresse
        )
        
        # Lier la coiffeuse au deuxième salon (sans être propriétaire)
        TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse,
            salon=salon2,
            est_proprietaire=False
        )
        
        user_data = CurrentUserData(self.user_coiffeuse)
        extra_data = user_data.extra_data
        
        # Vérifier tous_salons
        self.assertEqual(len(extra_data['tous_salons']), 2)
        
        # Vérifier que le salon principal reste correct
        salon_principal = extra_data['salon_principal']
        self.assertEqual(salon_principal['nom_salon'], 'Salon Belle Coupe')
    
    def test_current_user_data_sans_adresse(self):
        """Test CurrentUserData pour un utilisateur sans adresse"""
        # Créer un utilisateur sans adresse
        user_sans_adresse = TblUser.objects.create(
            uuid='user-sans-adresse',
            nom='Test',
            prenom='User',
            email='test@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 1, 1),
            adresse=None,
            role=self.role_user,
            sexe_ref=self.sexe,
            type_ref=self.type_client
        )
        
        user_data = CurrentUserData(user_sans_adresse)
        
        self.assertIsNone(user_data.adresse)
    
    def test_current_user_data_to_dict(self):
        """Test de la méthode to_dict"""
        user_data = CurrentUserData(self.user_client)
        data_dict = user_data.to_dict()
        
        # Vérifier que c'est un dictionnaire
        self.assertIsInstance(data_dict, dict)
        
        # Vérifier que toutes les clés importantes sont présentes
        required_keys = [
            'idTblUser', 'uuid', 'nom', 'prenom', 'email',
            'numero_telephone', 'date_naissance', 'sexe',
            'is_active', 'type', 'adresse', 'extra_data'
        ]
        
        for key in required_keys:
            self.assertIn(key, data_dict)
    
    def test_current_user_data_coiffeuse_sans_salon(self):
        """Test CurrentUserData pour une coiffeuse sans salon"""
        # Créer une coiffeuse sans salon
        user_coiffeuse_solo = TblUser.objects.create(
            uuid='coiffeuse-solo',
            nom='Solo',
            prenom='Coiffeuse',
            email='solo@example.com',
            numero_telephone='+32123456787',
            date_naissance=date(1985, 1, 1),
            adresse=self.adresse,
            role=self.role_coiffeuse,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        
        coiffeuse_solo = TblCoiffeuse.objects.create(
            idTblUser=user_coiffeuse_solo,
            nom_commercial='Coiffeuse Solo'
        )
        
        user_data = CurrentUserData(user_coiffeuse_solo)
        extra_data = user_data.extra_data
        
        self.assertEqual(extra_data['nom_commercial'], 'Coiffeuse Solo')
        self.assertIsNone(extra_data['salon_principal'])
        self.assertEqual(len(extra_data['tous_salons']), 0)


class CurrentUserIntegrationTestCase(CurrentUserSetupMixin, APITestCase):
    """Tests d'intégration pour CurrentUser"""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    def test_workflow_complete_coiffeuse(self):
        """Test du workflow complet pour une coiffeuse"""
        # 1. Récupérer l'utilisateur par ID
        url = reverse('get_user_by_id', kwargs={'id': self.user_coiffeuse.idTblUser})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # 2. Vérifier que toutes les données sont cohérentes
        user_data = data['user']
        
        # Données utilisateur de base
        self.assertEqual(user_data['nom'], 'Martin')
        self.assertEqual(user_data['type'], 'coiffeuse')
        
        # Données coiffeuse
        coiffeuse_data = user_data['coiffeuse']
        self.assertEqual(coiffeuse_data['nom_commercial'], 'Salon Sophie')
        
        # Données salon
        salon_principal = coiffeuse_data['salon_principal']
        self.assertEqual(salon_principal['nom_salon'], 'Salon Belle Coupe')
        
        # 3. Vérifier la cohérence avec la base de données
        coiffeuse_db = TblCoiffeuse.objects.get(idTblUser=self.user_coiffeuse)
        salon_db = TblSalon.objects.get(idTblSalon=salon_principal['idTblSalon'])
        
        self.assertEqual(salon_db.nom_salon, salon_principal['nom_salon'])
        self.assertEqual(salon_db.numero_tva, salon_principal['numero_tva'])
    
    def test_workflow_complete_client(self):
        """Test du workflow complet pour un client"""
        # Simuler l'authentification
        self.client.force_authenticate(user=self.user_client)
        
        with patch('hairbnb.currentUser.currentUser_views.request') as mock_request:
            mock_request.user = self.user_client
            
            # 1. Récupérer l'utilisateur actuel
            url = reverse('get_current_user')
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # 2. Vérifier que les données sont cohérentes
        user_data = data['user']
        
        self.assertEqual(user_data['nom'], 'Dupont')
        self.assertEqual(user_data['type'], 'client')
        self.assertIsNone(user_data['coiffeuse'])  # Client n'a pas de données coiffeuse
        
        # 3. Récupérer le même utilisateur par ID
        url2 = reverse('get_user_by_id', kwargs={'id': self.user_client.idTblUser})
        response2 = self.client.get(url2)
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data2 = response2.json()
        
        # 4. Vérifier que les données sont identiques
        user_data2 = data2['user']
        
        self.assertEqual(user_data['nom'], user_data2['nom'])
        self.assertEqual(user_data['email'], user_data2['email'])
        self.assertEqual(user_data['type'], user_data2['type'])


class CurrentUserEdgeCasesTestCase(CurrentUserSetupMixin, TestCase):
    """Tests pour les cas particuliers et erreurs"""
    
    def test_serializer_with_none_context(self):
        """Test du serializer sans contexte request"""
        serializer = CurrentUserSerializer(self.user_client)
        data = serializer.data
        
        # Devrait fonctionner même sans contexte
        self.assertEqual(data['nom'], 'Dupont')
        # La photo de profil ne sera pas convertie en URL absolue
    
    def test_serializer_coiffeuse_avec_erreur_salon(self):
        """Test du serializer coiffeuse quand il y a une erreur avec le salon"""
        # Supprimer la relation salon pour créer une erreur
        TblCoiffeuseSalon.objects.filter(coiffeuse=self.coiffeuse).delete()
        
        serializer = TblCoiffeuseSerializer(self.coiffeuse)
        data = serializer.data
        
        # Devrait gérer l'absence de salon gracieusement
        self.assertEqual(data['nom_commercial'], 'Salon Sophie')
        self.assertEqual(len(data['salons']), 0)
        self.assertIsNone(data['salon_principal'])
        self.assertFalse(data['est_proprietaire'])
    
    def test_current_user_data_with_coiffeuse_does_not_exist(self):
        """Test CurrentUserData quand l'objet coiffeuse n'existe pas"""
        # Supprimer l'objet coiffeuse mais garder le type
        TblCoiffeuse.objects.filter(idTblUser=self.user_coiffeuse).delete()
        
        user_data = CurrentUserData(self.user_coiffeuse)
        
        # Devrait gérer l'absence de coiffeuse gracieusement
        self.assertEqual(user_data.type, 'coiffeuse')
        self.assertIsNone(user_data.extra_data)
    
    def test_current_user_data_with_client_does_not_exist(self):
        """Test CurrentUserData quand l'objet client n'existe pas"""
        # Supprimer l'objet client mais garder le type
        TblClient.objects.filter(idTblUser=self.user_client).delete()
        
        user_data = CurrentUserData(self.user_client)
        
        # Devrait gérer l'absence de client gracieusement
        self.assertEqual(user_data.type, 'client')
        self.assertIsNone(user_data.extra_data)
    
    def test_current_user_data_type_inconnu(self):
        """Test CurrentUserData avec un type d'utilisateur inconnu"""
        type_inconnu = TblType.objects.create(libelle='admin')
        
        user_admin = TblUser.objects.create(
            uuid='admin-uuid',
            nom='Admin',
            prenom='User',
            email='admin@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 1, 1),
            adresse=self.adresse,
            role=self.role_user,
            sexe_ref=self.sexe,
            type_ref=type_inconnu
        )
        
        user_data = CurrentUserData(user_admin)
        
        self.assertEqual(user_data.type, 'admin')
        self.assertIsNone(user_data.extra_data)
    
    def test_view_get_user_by_id_with_invalid_id(self):
        """Test get_user_by_id avec un ID invalide"""
        url = reverse('get_user_by_id', kwargs={'id': 'invalid'})
        
        # Django devrait retourner 404 pour un ID invalide
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# Tests de performance (optionnels)
class CurrentUserPerformanceTestCase(CurrentUserSetupMixin, TestCase):
    """Tests de performance pour CurrentUser"""
    
    def test_serializer_performance_avec_beaucoup_de_salons(self):
        """Test de performance du serializer avec beaucoup de salons"""
        # Créer 10 salons supplémentaires
        for i in range(10):
            salon = TblSalon.objects.create(
                nom_salon=f'Salon {i}',
                adresse=self.adresse
            )
            TblCoiffeuseSalon.objects.create(
                coiffeuse=self.coiffeuse,
                salon=salon,
                est_proprietaire=False
            )
        
        # Le serializer devrait gérer cela efficacement
        with self.assertNumQueries(3):  # Optimiser selon les requêtes réelles
            serializer = TblCoiffeuseSerializer(self.coiffeuse)
            data = serializer.data
            
            # Vérifier que tous les salons sont inclus
            self.assertEqual(len(data['salons']), 11)  # 10 + le salon principal


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
    failures = test_runner.run_tests(["hairbnb.currentUser.test_currentUser"])
