from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from hairbnb.models import (
    TblLocalite, TblRue, TblAdresse, TblUser, TblRole, TblSexe, TblType,
    TblCoiffeuse, TblClient, TblSalon, TblCoiffeuseSalon, TblSalonImage,
    TblService, TblCategorie, TblTemps, TblPrix, TblSalonService,
    TblServiceTemps, TblServicePrix, TblRendezVous, TblRendezVousService,
    TblPromotion, TblAvis, TblAvisStatut, TblPaiement, TblPaiementStatut,
    TblMethodePaiement, TblTransaction, TblHoraireCoiffeuse,
    TblIndisponibilite, TblFavorite, TblEmailType, TblEmailStatus,
    TblEmailNotification, TblCart, TblCartItem, AIConversation, AIMessage
)


class TblLocaliteTestCase(TestCase):
    """Tests pour le modèle TblLocalite"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.localite_data = {
            'commune': 'Bruxelles',
            'code_postal': '1000'
        }
    
    def test_creation_localite(self):
        """Test de création d'une localité"""
        localite = TblLocalite.objects.create(**self.localite_data)
        self.assertEqual(localite.commune, 'Bruxelles')
        self.assertEqual(localite.code_postal, '1000')
    
    def test_str_representation(self):
        """Test de la représentation string"""
        localite = TblLocalite.objects.create(**self.localite_data)
        self.assertEqual(str(localite), "Bruxelles (1000)")
    
    def test_commune_max_length(self):
        """Test de la longueur maximale du champ commune"""
        long_commune = "x" * 41  # Plus que 40 caractères
        with self.assertRaises(ValidationError):
            localite = TblLocalite(commune=long_commune, code_postal='1000')
            localite.full_clean()


class TblRueTestCase(TestCase):
    """Tests pour le modèle TblRue"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.localite = TblLocalite.objects.create(
            commune='Bruxelles',
            code_postal='1000'
        )
        self.rue_data = {
            'nom_rue': 'Rue de la Paix',
            'localite': self.localite
        }
    
    def test_creation_rue(self):
        """Test de création d'une rue"""
        rue = TblRue.objects.create(**self.rue_data)
        self.assertEqual(rue.nom_rue, 'Rue de la Paix')
        self.assertEqual(rue.localite, self.localite)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        rue = TblRue.objects.create(**self.rue_data)
        self.assertEqual(str(rue), "Rue de la Paix")
    
    def test_unique_together_constraint(self):
        """Test de la contrainte d'unicité nom_rue + localite"""
        TblRue.objects.create(**self.rue_data)
        with self.assertRaises(IntegrityError):
            TblRue.objects.create(**self.rue_data)
    
    def test_relation_avec_localite(self):
        """Test de la relation avec TblLocalite"""
        rue = TblRue.objects.create(**self.rue_data)
        self.assertEqual(self.localite.rues.first(), rue)


class TblAdresseTestCase(TestCase):
    """Tests pour le modèle TblAdresse"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.localite = TblLocalite.objects.create(
            commune='Bruxelles',
            code_postal='1000'
        )
        self.rue = TblRue.objects.create(
            nom_rue='Rue de la Paix',
            localite=self.localite
        )
        self.adresse_data = {
            'numero': '123',
            'rue': self.rue
        }
    
    def test_creation_adresse(self):
        """Test de création d'une adresse"""
        adresse = TblAdresse.objects.create(**self.adresse_data)
        self.assertEqual(adresse.numero, '123')
        self.assertEqual(adresse.rue, self.rue)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        adresse = TblAdresse.objects.create(**self.adresse_data)
        expected = "123, Rue de la Paix, Bruxelles"
        self.assertEqual(str(adresse), expected)


class TblRoleTestCase(TestCase):
    """Tests pour le modèle TblRole"""
    
    def test_creation_role(self):
        """Test de création d'un rôle"""
        role = TblRole.objects.create(nom='admin')
        self.assertEqual(role.nom, 'admin')
        self.assertEqual(str(role), 'admin')
    
    def test_unique_nom(self):
        """Test de l'unicité du nom de rôle"""
        TblRole.objects.create(nom='admin')
        with self.assertRaises(IntegrityError):
            TblRole.objects.create(nom='admin')


class TblSexeTestCase(TestCase):
    """Tests pour le modèle TblSexe"""
    
    def test_creation_sexe(self):
        """Test de création d'un sexe"""
        sexe = TblSexe.objects.create(libelle='Homme')
        self.assertEqual(sexe.libelle, 'Homme')
        self.assertEqual(str(sexe), 'Homme')


class TblTypeTestCase(TestCase):
    """Tests pour le modèle TblType"""
    
    def test_creation_type(self):
        """Test de création d'un type"""
        type_obj = TblType.objects.create(libelle='Coiffeuse')
        self.assertEqual(type_obj.libelle, 'Coiffeuse')
        self.assertEqual(str(type_obj), 'Coiffeuse')


class TblUserTestCase(TestCase):
    """Tests pour le modèle TblUser"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer les objets de référence
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
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Client')
        
        self.user_data = {
            'uuid': 'test-uuid-123',
            'nom': 'Dupont',
            'prenom': 'Marie',
            'email': 'marie.dupont@example.com',
            'numero_telephone': '+32123456789',
            'date_naissance': date(1990, 5, 15),
            'adresse': self.adresse,
            'role': self.role,
            'sexe_ref': self.sexe,
            'type_ref': self.type_user
        }
    
    def test_creation_user(self):
        """Test de création d'un utilisateur"""
        user = TblUser.objects.create(**self.user_data)
        self.assertEqual(user.nom, 'Dupont')
        self.assertEqual(user.prenom, 'Marie')
        self.assertEqual(user.email, 'marie.dupont@example.com')
        self.assertTrue(user.is_active)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        user = TblUser.objects.create(**self.user_data)
        expected = "Dupont Marie (Client - Femme - user)"
        self.assertEqual(str(user), expected)
    
    def test_unique_email(self):
        """Test de l'unicité de l'email"""
        TblUser.objects.create(**self.user_data)
        user_data_2 = self.user_data.copy()
        user_data_2['uuid'] = 'test-uuid-456'
        with self.assertRaises(IntegrityError):
            TblUser.objects.create(**user_data_2)
    
    def test_unique_uuid(self):
        """Test de l'unicité de l'UUID"""
        TblUser.objects.create(**self.user_data)
        user_data_2 = self.user_data.copy()
        user_data_2['email'] = 'autre@example.com'
        with self.assertRaises(IntegrityError):
            TblUser.objects.create(**user_data_2)
    
    def test_methods_get_role_type_sexe(self):
        """Test des méthodes get_role, get_type, get_sexe"""
        user = TblUser.objects.create(**self.user_data)
        self.assertEqual(user.get_role(), 'user')
        self.assertEqual(user.get_type(), 'Client')
        self.assertEqual(user.get_sexe(), 'Femme')


class TblCoiffeuseTestCase(TestCase):
    """Tests pour le modèle TblCoiffeuse"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer un utilisateur de base
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='coiffeuse')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Coiffeuse')
        
        self.user = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
    
    def test_creation_coiffeuse(self):
        """Test de création d'une coiffeuse"""
        coiffeuse = TblCoiffeuse.objects.create(
            idTblUser=self.user,
            nom_commercial='Salon Sophie'
        )
        self.assertEqual(coiffeuse.idTblUser, self.user)
        self.assertEqual(coiffeuse.nom_commercial, 'Salon Sophie')
    
    def test_str_representation(self):
        """Test de la représentation string"""
        coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user)
        expected = "Coiffeuse: Martin Sophie"
        self.assertEqual(str(coiffeuse), expected)
    
    def test_relation_onetoone_avec_user(self):
        """Test de la relation OneToOne avec TblUser"""
        coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user)
        self.assertEqual(self.user.coiffeuse, coiffeuse)


class TblServiceTestCase(TestCase):
    """Tests pour le modèle TblService"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.categorie = TblCategorie.objects.create(
            intitule_categorie='Coupe'
        )
        self.service_data = {
            'intitule_service': 'Coupe femme',
            'description': 'Coupe de cheveux pour femme avec brushing',
            'categorie': self.categorie
        }
    
    def test_creation_service(self):
        """Test de création d'un service"""
        service = TblService.objects.create(**self.service_data)
        self.assertEqual(service.intitule_service, 'Coupe femme')
        self.assertEqual(service.description, 'Coupe de cheveux pour femme avec brushing')
        self.assertEqual(service.categorie, self.categorie)


class TblSalonTestCase(TestCase):
    """Tests pour le modèle TblSalon"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer une coiffeuse
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='coiffeuse')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Coiffeuse')
        
        self.user = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
        
        self.coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user)
        
        self.salon_data = {
            'nom_salon': 'Salon Belle Coupe',
            'slogan': 'La beauté à votre service',
            'a_propos': 'Un salon moderne et accueillant',
            'numero_tva': 'BE0123456789',
            'adresse': self.adresse,
            'position': '50.8503,4.3517'
        }
    
    def test_creation_salon(self):
        """Test de création d'un salon"""
        salon = TblSalon.objects.create(**self.salon_data)
        self.assertEqual(salon.nom_salon, 'Salon Belle Coupe')
        self.assertEqual(salon.slogan, 'La beauté à votre service')
        self.assertEqual(salon.numero_tva, 'BE0123456789')
    
    def test_str_representation_avec_proprietaire(self):
        """Test de la représentation string avec propriétaire"""
        salon = TblSalon.objects.create(**self.salon_data)
        # Ajouter la coiffeuse comme propriétaire
        TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse,
            salon=salon,
            est_proprietaire=True
        )
        expected = "Salon de Martin Sophie"
        self.assertEqual(str(salon), expected)
    
    def test_str_representation_sans_proprietaire(self):
        """Test de la représentation string sans propriétaire"""
        salon = TblSalon.objects.create(**self.salon_data)
        expected = "Salon: Salon Belle Coupe"
        self.assertEqual(str(salon), expected)
    
    def test_get_proprietaire(self):
        """Test de la méthode get_proprietaire"""
        salon = TblSalon.objects.create(**self.salon_data)
        
        # Sans propriétaire
        self.assertIsNone(salon.get_proprietaire())
        
        # Avec propriétaire
        TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse,
            salon=salon,
            est_proprietaire=True
        )
        self.assertEqual(salon.get_proprietaire(), self.coiffeuse)


class TblCoiffeuseSalonTestCase(TestCase):
    """Tests pour le modèle TblCoiffeuseSalon"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer les objets nécessaires
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='coiffeuse')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Coiffeuse')
        
        self.user = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
        
        self.coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user)
        self.salon = TblSalon.objects.create(nom_salon='Test Salon', adresse=self.adresse)
    
    def test_creation_relation_coiffeuse_salon(self):
        """Test de création d'une relation coiffeuse-salon"""
        relation = TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse,
            salon=self.salon,
            est_proprietaire=True
        )
        self.assertEqual(relation.coiffeuse, self.coiffeuse)
        self.assertEqual(relation.salon, self.salon)
        self.assertTrue(relation.est_proprietaire)
    
    def test_unique_together_constraint(self):
        """Test de la contrainte d'unicité coiffeuse + salon"""
        TblCoiffeuseSalon.objects.create(
            coiffeuse=self.coiffeuse,
            salon=self.salon
        )
        with self.assertRaises(IntegrityError):
            TblCoiffeuseSalon.objects.create(
                coiffeuse=self.coiffeuse,
                salon=self.salon
            )


class TblPromotionTestCase(TestCase):
    """Tests pour le modèle TblPromotion"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer les objets nécessaires
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        
        self.salon = TblSalon.objects.create(nom_salon='Test Salon', adresse=self.adresse)
        self.categorie = TblCategorie.objects.create(intitule_categorie='Coupe')
        self.service = TblService.objects.create(
            intitule_service='Coupe femme',
            description='Coupe de cheveux',
            categorie=self.categorie
        )
        
        self.promo_data = {
            'salon': self.salon,
            'service': self.service,
            'discount_percentage': Decimal('20.00'),
            'start_date': timezone.now() - timedelta(days=1),
            'end_date': timezone.now() + timedelta(days=7)
        }
    
    def test_creation_promotion(self):
        """Test de création d'une promotion"""
        promo = TblPromotion.objects.create(**self.promo_data)
        self.assertEqual(promo.salon, self.salon)
        self.assertEqual(promo.service, self.service)
        self.assertEqual(promo.discount_percentage, Decimal('20.00'))
    
    def test_is_active_method(self):
        """Test de la méthode is_active"""
        # Promotion active
        promo_active = TblPromotion.objects.create(**self.promo_data)
        self.assertTrue(promo_active.is_active())
        
        # Promotion expirée
        promo_expiree = TblPromotion.objects.create(
            salon=self.salon,
            service=self.service,
            discount_percentage=Decimal('15.00'),
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(promo_expiree.is_active())
    
    def test_get_prix_avec_promotion(self):
        """Test du calcul du prix avec promotion"""
        promo = TblPromotion.objects.create(**self.promo_data)
        prix_original = Decimal('50.00')
        prix_attendu = Decimal('40.00')  # 50 - 20% = 40
        
        prix_calcule = promo.get_prix_avec_promotion(prix_original)
        self.assertEqual(prix_calcule, prix_attendu)
    
    def test_validation_dates(self):
        """Test de validation des dates"""
        with self.assertRaises(ValueError):
            promo = TblPromotion(
                salon=self.salon,
                service=self.service,
                discount_percentage=Decimal('20.00'),
                start_date=timezone.now() + timedelta(days=7),
                end_date=timezone.now() + timedelta(days=1)  # Date de fin avant début
            )
            promo.save()


class TblRendezVousTestCase(TestCase):
    """Tests pour le modèle TblRendezVous"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer les objets nécessaires
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_client = TblType.objects.create(libelle='Client')
        self.type_coiffeuse = TblType.objects.create(libelle='Coiffeuse')
        
        # Créer un client
        self.user_client = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_client
        )
        self.client = TblClient.objects.create(idTblUser=self.user_client)
        
        # Créer une coiffeuse
        self.user_coiffeuse = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456788',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        self.coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user_coiffeuse)
        
        # Créer un salon
        self.salon = TblSalon.objects.create(nom_salon='Test Salon', adresse=self.adresse)
        
        self.rdv_data = {
            'client': self.client,
            'coiffeuse': self.coiffeuse,
            'salon': self.salon,
            'date_heure': timezone.now() + timedelta(days=1),
            'statut': 'confirmé'
        }
    
    def test_creation_rendez_vous(self):
        """Test de création d'un rendez-vous"""
        rdv = TblRendezVous.objects.create(**self.rdv_data)
        self.assertEqual(rdv.client, self.client)
        self.assertEqual(rdv.coiffeuse, self.coiffeuse)
        self.assertEqual(rdv.salon, self.salon)
        self.assertEqual(rdv.statut, 'confirmé')
        self.assertFalse(rdv.est_archive)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        rdv = TblRendezVous.objects.create(**self.rdv_data)
        expected_start = f"RDV {rdv.idRendezVous} - Dupont"
        self.assertTrue(str(rdv).startswith(expected_start))
    
    def test_calculer_total(self):
        """Test de la méthode calculer_total"""
        rdv = TblRendezVous.objects.create(**self.rdv_data)
        
        # Créer un service avec prix et temps
        categorie = TblCategorie.objects.create(intitule_categorie='Coupe')
        service = TblService.objects.create(
            intitule_service='Coupe femme',
            description='Coupe de cheveux',
            categorie=categorie
        )
        
        # Ajouter le service au rendez-vous
        TblRendezVousService.objects.create(
            rendez_vous=rdv,
            service=service,
            prix_applique=Decimal('50.00'),
            duree_estimee=60
        )
        
        rdv.calculer_total()
        rdv.refresh_from_db()
        
        self.assertEqual(rdv.total_prix, Decimal('50.00'))
        self.assertEqual(rdv.duree_totale, 60)


class TblAvisTestCase(TestCase):
    """Tests pour le modèle TblAvis"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer les objets nécessaires
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_client = TblType.objects.create(libelle='Client')
        
        # Créer un client
        self.user_client = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_client
        )
        self.client = TblClient.objects.create(idTblUser=self.user_client)
        
        # Créer un salon
        self.salon = TblSalon.objects.create(nom_salon='Test Salon', adresse=self.adresse)
        
        # Créer un statut d'avis
        self.statut_avis = TblAvisStatut.objects.create(
            code='visible',
            libelle='Visible'
        )
        
        self.avis_data = {
            'salon': self.salon,
            'client': self.client,
            'note': 5,
            'commentaire': 'Excellent service!',
            'statut': self.statut_avis
        }
    
    def test_creation_avis(self):
        """Test de création d'un avis"""
        avis = TblAvis.objects.create(**self.avis_data)
        self.assertEqual(avis.salon, self.salon)
        self.assertEqual(avis.client, self.client)
        self.assertEqual(avis.note, 5)
        self.assertEqual(avis.commentaire, 'Excellent service!')
    
    def test_client_nom_complet_property(self):
        """Test de la propriété client_nom_complet"""
        avis = TblAvis.objects.create(**self.avis_data)
        self.assertEqual(avis.client_nom_complet, 'Marie Dupont')
    
    def test_est_visible_property(self):
        """Test de la propriété est_visible"""
        avis = TblAvis.objects.create(**self.avis_data)
        self.assertTrue(avis.est_visible)


class TblPaiementTestCase(TestCase):
    """Tests pour le modèle TblPaiement"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer les objets nécessaires
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_client = TblType.objects.create(libelle='Client')
        self.type_coiffeuse = TblType.objects.create(libelle='Coiffeuse')
        
        # Créer un client
        self.user_client = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_client
        )
        self.client = TblClient.objects.create(idTblUser=self.user_client)
        
        # Créer une coiffeuse
        self.user_coiffeuse = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456788',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_coiffeuse
        )
        self.coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user_coiffeuse)
        
        # Créer un salon et un rendez-vous
        self.salon = TblSalon.objects.create(nom_salon='Test Salon', adresse=self.adresse)
        self.rdv = TblRendezVous.objects.create(
            client=self.client,
            coiffeuse=self.coiffeuse,
            salon=self.salon,
            date_heure=timezone.now() + timedelta(days=1)
        )
        
        # Créer des statuts et méthodes de paiement
        self.statut_paiement = TblPaiementStatut.objects.create(
            code='payé',
            libelle='Payé'
        )
        self.methode_paiement = TblMethodePaiement.objects.create(
            code='card',
            libelle='Carte Bancaire'
        )
        
        self.paiement_data = {
            'rendez_vous': self.rdv,
            'utilisateur': self.user_client,
            'montant_paye': Decimal('50.00'),
            'statut': self.statut_paiement,
            'methode': self.methode_paiement,
            'email_client': 'marie.dupont@example.com'
        }
    
    def test_creation_paiement(self):
        """Test de création d'un paiement"""
        paiement = TblPaiement.objects.create(**self.paiement_data)
        self.assertEqual(paiement.rendez_vous, self.rdv)
        self.assertEqual(paiement.montant_paye, Decimal('50.00'))
        self.assertEqual(paiement.statut, self.statut_paiement)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        paiement = TblPaiement.objects.create(**self.paiement_data)
        expected = f"Paiement de 50.00€ pour le RDV #{self.rdv.idRendezVous} — Payé"
        self.assertEqual(str(paiement), expected)


class TblHoraireCoiffeuseTestCase(TestCase):
    """Tests pour le modèle TblHoraireCoiffeuse"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer une coiffeuse
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='coiffeuse')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Coiffeuse')
        
        self.user = TblUser.objects.create(
            uuid='coiffeuse-uuid-123',
            nom='Martin',
            prenom='Sophie',
            email='sophie.martin@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1985, 3, 20),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
        self.coiffeuse = TblCoiffeuse.objects.create(idTblUser=self.user)
        
        self.horaire_data = {
            'coiffeuse': self.coiffeuse,
            'jour': 0,  # Lundi
            'heure_debut': time(9, 0),
            'heure_fin': time(17, 0)
        }
    
    def test_creation_horaire(self):
        """Test de création d'un horaire"""
        horaire = TblHoraireCoiffeuse.objects.create(**self.horaire_data)
        self.assertEqual(horaire.coiffeuse, self.coiffeuse)
        self.assertEqual(horaire.jour, 0)
        self.assertEqual(horaire.heure_debut, time(9, 0))
        self.assertEqual(horaire.heure_fin, time(17, 0))
    
    def test_unique_together_constraint(self):
        """Test de la contrainte d'unicité coiffeuse + jour"""
        TblHoraireCoiffeuse.objects.create(**self.horaire_data)
        with self.assertRaises(IntegrityError):
            TblHoraireCoiffeuse.objects.create(**self.horaire_data)


class TblCartTestCase(TestCase):
    """Tests pour le modèle TblCart"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer un utilisateur
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Client')
        
        self.user = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
    
    def test_creation_cart(self):
        """Test de création d'un panier"""
        cart = TblCart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.total_price(), 0)  # Panier vide
    
    def test_str_representation(self):
        """Test de la représentation string"""
        cart = TblCart.objects.create(user=self.user)
        expected = "Panier de Dupont Marie - 0 articles"
        self.assertEqual(str(cart), expected)
    
    def test_total_price_avec_items(self):
        """Test du calcul du prix total avec des articles"""
        cart = TblCart.objects.create(user=self.user)
        
        # Créer un service avec prix
        categorie = TblCategorie.objects.create(intitule_categorie='Coupe')
        service = TblService.objects.create(
            intitule_service='Coupe femme',
            description='Coupe de cheveux',
            categorie=categorie
        )
        prix = TblPrix.objects.create(prix=Decimal('50.00'))
        TblServicePrix.objects.create(service=service, prix=prix)
        
        # Ajouter l'article au panier
        TblCartItem.objects.create(
            cart=cart,
            service=service,
            quantity=2
        )
        
        self.assertEqual(cart.total_price(), 100)  # 2 * 50


class AIConversationTestCase(TestCase):
    """Tests pour le modèle AIConversation"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer un utilisateur
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Client')
        
        self.user = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
    
    def test_creation_ai_conversation(self):
        """Test de création d'une conversation IA"""
        conversation = AIConversation.objects.create(
            user=self.user,
            tokens_used=100
        )
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.tokens_used, 100)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        conversation = AIConversation.objects.create(user=self.user)
        expected = f"Conversation #{conversation.id} - Marie"
        self.assertEqual(str(conversation), expected)


class AIMessageTestCase(TestCase):
    """Tests pour le modèle AIMessage"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer un utilisateur et une conversation
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Client')
        
        self.user = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
        
        self.conversation = AIConversation.objects.create(user=self.user)
    
    def test_creation_ai_message(self):
        """Test de création d'un message IA"""
        message = AIMessage.objects.create(
            conversation=self.conversation,
            content="Bonjour, comment puis-je vous aider?",
            is_user=False,
            tokens_in=10,
            tokens_out=15
        )
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.content, "Bonjour, comment puis-je vous aider?")
        self.assertFalse(message.is_user)
        self.assertEqual(message.tokens_in, 10)
        self.assertEqual(message.tokens_out, 15)


# Tests pour les modèles de validation et contraintes
class ValidationTestCase(TestCase):
    """Tests pour les validations et contraintes des modèles"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.localite = TblLocalite.objects.create(commune='Bruxelles', code_postal='1000')
        self.rue = TblRue.objects.create(nom_rue='Rue Test', localite=self.localite)
        self.adresse = TblAdresse.objects.create(numero='1', rue=self.rue)
        self.role = TblRole.objects.create(nom='user')
        self.sexe = TblSexe.objects.create(libelle='Femme')
        self.type_user = TblType.objects.create(libelle='Client')
        
        self.user = TblUser.objects.create(
            uuid='client-uuid-123',
            nom='Dupont',
            prenom='Marie',
            email='marie.dupont@example.com',
            numero_telephone='+32123456789',
            date_naissance=date(1990, 5, 15),
            adresse=self.adresse,
            role=self.role,
            sexe_ref=self.sexe,
            type_ref=self.type_user
        )
    
    def test_tbl_prix_validation(self):
        """Test de validation des prix"""
        # Prix valide
        prix_valide = TblPrix(prix=Decimal('50.00'))
        prix_valide.full_clean()  # Ne devrait pas lever d'exception
        
        # Prix négatif (invalide)
        with self.assertRaises(ValidationError):
            prix_negatif = TblPrix(prix=Decimal('-10.00'))
            prix_negatif.full_clean()
        
        # Prix trop élevé (invalide)
        with self.assertRaises(ValidationError):
            prix_trop_eleve = TblPrix(prix=Decimal('1500.00'))
            prix_trop_eleve.full_clean()
    
    def test_tbl_avis_note_validation(self):
        """Test de validation des notes d'avis"""
        salon = TblSalon.objects.create(nom_salon='Test Salon', adresse=self.adresse)
        client = TblClient.objects.create(idTblUser=self.user)
        statut = TblAvisStatut.objects.create(code='visible', libelle='Visible')
        
        # Note valide
        avis_valide = TblAvis(
            salon=salon,
            client=client,
            note=4,
            commentaire='Très bien',
            statut=statut
        )
        avis_valide.full_clean()
        
        # Note invalide (trop basse)
        with self.assertRaises(ValidationError):
            avis_invalide = TblAvis(
                salon=salon,
                client=client,
                note=0,
                commentaire='Mauvais',
                statut=statut
            )
            avis_invalide.full_clean()
        
        # Note invalide (trop haute)
        with self.assertRaises(ValidationError):
            avis_invalide = TblAvis(
                salon=salon,
                client=client,
                note=6,
                commentaire='Excellent',
                statut=statut
            )
            avis_invalide.full_clean()


# Test runner pour exécuter tous les tests
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
                'hairbnb',
            ],
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["hairbnb.tests"])
