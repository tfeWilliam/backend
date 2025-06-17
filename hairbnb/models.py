from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from decimal import Decimal
from hairbnb.services.validators import validate_max_images
from django.contrib.auth.models import User


# Table pour gérer les localités
class TblLocalite(models.Model):
    idTblLocalite = models.AutoField(primary_key=True)
    commune = models.CharField(max_length=40)
    code_postal = models.CharField(max_length=6)

    def __str__(self):
        return f"{self.commune} ({self.code_postal})"


# Table pour gérer les rues
class TblRue(models.Model):
    idTblRue = models.AutoField(primary_key=True)
    nom_rue = models.CharField(max_length=50)
    localite = models.ForeignKey(
        TblLocalite,
        on_delete=models.PROTECT,  # Empêche suppression si des rues l'utilisent
        related_name='rues'
    )

    class Meta:
        unique_together = ('nom_rue', 'localite')

    def __str__(self):
        return self.nom_rue

# Définition du modèle TblAdresse, représentant une adresse physique précise
class TblAdresse(models.Model):
    # Identifiant unique de l'adresse, généré automatiquement (clé primaire)
    idTblAdresse = models.AutoField(primary_key=True)

    # Champ pour le numéro de rue, augmenté à 10 caractères pour inclure les boîtes postales
    # Par exemple: "12/A", "12B/3", "12/1" etc.
    numero = models.CharField(max_length=5)

    # Clé étrangère vers le modèle TblRue, indiquant la rue à laquelle appartient cette adresse
    rue = models.ForeignKey(
        TblRue,  # Référence au modèle TblRue
        on_delete=models.PROTECT,  # Empêche suppression si des adresses l'utilisent
        related_name='adresses'  # Permet d'accéder aux adresses depuis la rue via rue.adresses.all()
    )

    # Représentation textuelle de l'adresse, utile pour l'affichage dans l'admin Django ou en debug
    def __str__(self):
        # Affiche le numéro, le nom de la rue, et la commune associée via la localité
        return f"{self.numero}, {self.rue.nom_rue}, {self.rue.localite.commune}"

################################################################################################################
########################################### Modèle représentant un utilisateur #################################
################################################################################################################
class TblUser(models.Model):
    # Identifiant unique de l'utilisateur (clé primaire auto-incrémentée)
    idTblUser = models.AutoField(primary_key=True)

    # Identifiant universel unique pour chaque utilisateur (UUID string)
    uuid = models.CharField(max_length=40, unique=True)

    # Nom de famille de l'utilisateur
    nom = models.CharField(max_length=20)

    # # Prénom de l'utilisateur
    prenom = models.CharField(max_length=20)

    # Adresse e-mail de l'utilisateur (doit être unique)
    #email = models.EmailField(unique=True)
    email = models.EmailField(max_length=150, unique=True)

    # Numéro de téléphone de l'utilisateur (format libre, max 15 chiffres)
    numero_telephone = models.CharField(max_length=20)

    # Date de naissance de l'utilisateur (optionnelle)
    date_naissance = models.DateField(null=False, blank=False)

    # Champ booléen indiquant si le compte utilisateur est actif
    is_active = models.BooleanField(default=True)

    # Lien vers l'adresse de résidence de l'utilisateur
    adresse = models.ForeignKey(
        'TblAdresse',
        on_delete=models.RESTRICT,
        null=False,
        related_name='utilisateurs'  # Accès inverse : adresse.utilisateurs.all()
    )

    # Photo de profil de l'utilisateur (champ image avec une valeur par défaut)
    photo_profil = models.ImageField(
        upload_to='photos/profils/',
        null=False,
        blank=False,
        default='assets/logo_login/avatar.png'
    )

    # Rôle attribué à l'utilisateur (clé étrangère vers la table TblRole)
    role = models.ForeignKey(
        'TblRole',
        on_delete=models.SET_DEFAULT,
        null=False,
        default=1,
        related_name='utilisateurs'
    )

    # Référence vers le sexe de l'utilisateur (clé étrangère vers TblSexe)
    sexe_ref = models.ForeignKey(
        'TblSexe',
        on_delete=models.PROTECT,
        related_name='utilisateurs',
        null=False  # Permet une migration progressive
    )

    # Référence vers le type d'utilisateur (clé étrangère vers TblType)
    type_ref = models.ForeignKey(
        'TblType',
        on_delete=models.PROTECT,
        related_name='utilisateurs',
        null=False  # Permet une migration progressive
    )

    # Représentation textuelle de l'utilisateur dans l'administration
    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.get_type()} - {self.get_sexe()} - {self.get_role()})"

    # Récupère le libellé du rôle (ex: admin, user)
    def get_role(self):
        return self.role.nom if self.role else 'user'

    # Récupère le libellé du type (ex: coiffeuse, client)
    def get_type(self):
        return self.type_ref.libelle if self.type_ref else 'Type inconnu'

    # Récupère le libellé du sexe (ex: homme, femme)
    def get_sexe(self):
        return self.sexe_ref.libelle if self.sexe_ref else 'Sexe inconnu'
################################################################################################################

class TblRole(models.Model):
    idTblRole = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=12, unique=True)  # Exemple: "admin", "user"

    def __str__(self):
        return self.nom


# Ajoutez ces nouvelles tables à votre models.py
class TblSexe(models.Model):
    idTblSexe = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.libelle


class TblType(models.Model):
    idTblType = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.libelle

################################################################################################################
########################################### Modèle représentant une coiffeuse ##################################
################################################################################################################
class TblCoiffeuse(models.Model):
    # Lien OneToOne vers le modèle TblUser (chaque coiffeuse est aussi un utilisateur)
    idTblUser = models.OneToOneField(
        'TblUser',
        on_delete=models.CASCADE,
        related_name='coiffeuse'  # Permet d’accéder à la coiffeuse via user.coiffeuse
    )

    # Nom commercial de la coiffeuse (anciennement 'denomination_sociale')
    nom_commercial = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Métadonnées pour une meilleure lisibilité dans l’admin Django
    class Meta:
        verbose_name = "Coiffeuse"
        verbose_name_plural = "Coiffeuses"

    # Représentation textuelle de la coiffeuse, affichée dans l’admin ou les interfaces
    def __str__(self):
        return f"Coiffeuse: {self.idTblUser.nom} {self.idTblUser.prenom}"
########################################################################################################################

# Table pour les clients
class TblClient(models.Model):
    idTblUser = models.ForeignKey(
        'TblUser',
        on_delete=models.CASCADE,
        related_name='clients',
        db_column='idTblUser'
    )

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"


# Table pour gérer les temps
class TblTemps(models.Model):
    idTblTemps = models.AutoField(primary_key=True, unique=True)
    minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.minutes} minutes"


# Table pour gérer les prix
class TblPrix(models.Model):
    idTblPrix = models.AutoField(primary_key=True)
    prix = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        unique=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000)]
    )

    def __str__(self):
        return f"{self.prix} €"


# Table pour gérer les services
class TblService(models.Model):
    idTblService = models.AutoField(primary_key=True)
    intitule_service = models.CharField(max_length=100)
    description = models.TextField(validators=[MaxLengthValidator(600)])

    categorie = models.ForeignKey('TblCategorie', on_delete=models.PROTECT, null=True, blank=True)


    def __str__(self):
        return f"{self.intitule_service, self.description} €"

################################################################################################################
#################             Modèle représentant les catégires des services            ########################
################################################################################################################

class TblCategorie(models.Model):
    idTblCategorie = models.AutoField(primary_key=True)
    intitule_categorie = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.intitule_categorie

################################################################################################################
################################################################################################################
#################               Modèle représentant un salon de coiffure               #########################
################################################################################################################
class TblSalon(models.Model):
    # Identifiant unique du salon (clé primaire auto-incrémentée)
    idTblSalon = models.AutoField(primary_key=True)

    # Nom du salon
    nom_salon = models.CharField(max_length=30)

    # Slogan publicitaire du salon (champ facultatif)
    slogan = models.CharField(max_length=40, blank=True, null=True)

    # Description du salon (champ facultatif, texte plus long)
    a_propos = models.TextField(max_length=700, blank=True, null=True)

    # Logo du salon, avec un emplacement de stockage personnalisé et une image par défaut
    logo_salon = models.ImageField(
        upload_to='photos/logos/',  # Dossier de destination dans MEDIA_ROOT
        null=True,
        blank=True,
        default='photos/defaults/logo_default.png'  # Image par défaut si aucun logo n'est fourni
    )

    # Numéro de tva de salon
    numero_tva = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

    # Relation ManyToMany avec les services proposés dans le salon, via une table intermédiaire
    services = models.ManyToManyField(
        'TblService',
        related_name='salons',
        through='TblSalonService'  # Table personnalisée de liaison
    )

    # Adresse du salon (relation optionnelle)
    adresse = models.ForeignKey(
        'TblAdresse',
        on_delete=models.SET_NULL,  # Si l'adresse est supprimée, on met à null
        null=True,
        related_name='salons'
    )

    # Champ pour stocker la géolocalisation du salon (latitude,longitude)
    position = models.CharField(
        max_length=50,
        default="0,0",  # Valeur par défaut
        help_text="Format: 'latitude,longitude'"
    )

    # Relation ManyToMany avec les coiffeuses travaillant dans ce salon,
    # avec une table intermédiaire personnalisée TblCoiffeuseSalon
    coiffeuses = models.ManyToManyField(
        'TblCoiffeuse',
        through='TblCoiffeuseSalon',
        related_name='salons'
    )

    def get_proprietaire(self):
        """
        Récupère la coiffeuse propriétaire du salon.
        """
        relation = self.employes.filter(est_proprietaire=True).first()
        return relation.coiffeuse if relation else None

    @property
    def coiffeuse(self):
        """
        Propriété pour maintenir la compatibilité avec l'ancien code.
        """
        return self.get_proprietaire()

    # Représentation textuelle de l'objet, utilisée notamment dans l'interface d'administration
    def __str__(self):
        # Essayer d'abord d'utiliser le propriétaire
        proprietaire = self.get_proprietaire()
        if proprietaire and hasattr(proprietaire, 'idTblUser'):
            return f"Salon de {proprietaire.idTblUser.nom} {proprietaire.idTblUser.prenom}"
        return f"Salon: {self.nom_salon}"


########################################################################################################################

################################################################################################################
########################### Modèle représentant la relation entre coiffeuse et salon ###########################
################################################################################################################
class TblCoiffeuseSalon(models.Model):
    # Identifiant unique de la relation (clé primaire auto-incrémentée)
    idCoiffeuseSalon = models.AutoField(primary_key=True)

    # Lien vers la coiffeuse employée ou collaboratrice dans le salon
    coiffeuse = models.ForeignKey(
        'TblCoiffeuse',
        on_delete=models.CASCADE,
        related_name='emplois'  # Permet d'accéder à toutes les affectations d'une coiffeuse via coiffeuse.emplois
    )

    # Lien vers le salon concerné par la relation
    salon = models.ForeignKey(
        'TblSalon',
        on_delete=models.CASCADE,
        related_name='employes'  # Permet d'accéder à toutes les coiffeuses travaillant dans un salon via salon.employes
    )

    # Indique si la coiffeuse est propriétaire ou non du salon (utile pour l'affichage ou les droits)
    est_proprietaire = models.BooleanField(default=False)

    # Contrainte d’unicité : une coiffeuse ne peut pas être liée deux fois au même salon
    class Meta:
        unique_together = ('coiffeuse', 'salon')

    # Représentation textuelle de la relation, utile pour l’admin Django et les logs
    def __str__(self):
        return f"{self.coiffeuse.idTblUser.nom} travaille chez {self.salon.nom_salon}"
########################################################################################################################


# ------------------------------------TblSalonImage---------------------------------------

class TblSalonImage(models.Model):
    salon = models.ForeignKey(
        TblSalon,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='photos/salon/',
    )

    def __str__(self):
        return f"Image du salon {self.salon.coiffeuse.idTblUser.nom} - ID {self.id}"

    def save(self, *args, **kwargs):
        try:
            validate_max_images(self.salon)
        except Exception as e:
            print("Erreur dans validate_max_images:", e)
            raise  # Pour laisser l'exception remonter si besoin
        super().save(*args, **kwargs)


# ------------------------------------TblAvis---------------------------------------

# class TblAvis(models.Model):
#     salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, related_name='avis')
#     client = models.ForeignKey('TblClient', on_delete=models.SET_NULL, null=True)
#     note = models.IntegerField(choices=[(i, f"{i}/5") for i in range(1, 6)])
#     commentaire = models.TextField()  # 🔥 Obligatoire : pas de blank=True
#
#     date = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Avis {self.note}/5 de {self.client.idTblUser.prenom if self.client else 'Anonyme'} - {self.salon}"


# 1️⃣ TABLE DES STATUTS D'AVIS
class TblAvisStatut(models.Model):
    """Table des statuts d'avis possibles"""
    idTblAvisStatut = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)  # Code technique
    libelle = models.CharField(max_length=50)  # Libellé lisible
    # description = models.TextField(blank=True, null=True)  # Description optionnelle

    class Meta:
        db_table = 'tbl_avis_statut'
        verbose_name = "Statut d'avis"
        verbose_name_plural = "Statuts d'avis"
        ordering = ['libelle']

    def __str__(self):
        return self.libelle


# 2️⃣ TABLE TBLAVIS MISE À JOUR
class TblAvis(models.Model):
    """Modèle pour les avis clients - Version finale"""

    # 🔗 Relations existantes (gardées)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, related_name='avis')
    client = models.ForeignKey('TblClient', on_delete=models.SET_NULL, null=True)

    # 🆕 NOUVEAU : Lien vers le rendez-vous (UNIQUE = 1 avis par RDV max)
    rendez_vous = models.ForeignKey(
        'TblRendezVous',
        on_delete=models.CASCADE,
        related_name='avis',
        unique=True,  # ← Garantit 1 seul avis par RDV
        null=True,  # Pour la migration des avis existants
        blank=True  # Pour la migration des avis existants
    )

    # 🆕 NOUVEAU : Statut de l'avis
    statut = models.ForeignKey(
        TblAvisStatut,
        on_delete=models.PROTECT,  # Protection contre suppression accidentelle
        related_name='avis',
        default=1  # Par défaut : "visible" (à créer en premier)
    )

    # 📊 Données d'avis (existantes, gardées)
    note = models.IntegerField(choices=[(i, f"{i}/5") for i in range(1, 6)])
    commentaire = models.TextField()  # 🔥 Obligatoire : pas de blank=True
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'TblAvis'  # Garder le même nom de table
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
        ordering = ['-date']

        # Index pour performance
        indexes = [
            models.Index(fields=['salon', 'statut']),
            models.Index(fields=['client']),
            models.Index(fields=['rendez_vous']),
            models.Index(fields=['statut']),
            models.Index(fields=['date']),
        ]

        # Contraintes
        constraints = [
            models.CheckConstraint(
                check=models.Q(note__gte=1) & models.Q(note__lte=5),
                name='tblavis_note_valide_final'
            ),
        ]

    def __str__(self):
        if self.rendez_vous:
            return f"Avis {self.note}/5 - RDV {self.rendez_vous.idRendezVous} ({self.statut.libelle})"
        else:
            # Compatibilité avec vos avis existants
            return f"Avis {self.note}/5 de {self.client.idTblUser.prenom if self.client else 'Anonyme'} - {self.salon} ({self.statut.libelle})"

    # 🆕 PROPRIÉTÉS UTILES
    @property
    def client_nom_complet(self):
        """Nom complet du client"""
        if self.client:
            return f"{self.client.idTblUser.prenom} {self.client.idTblUser.nom}"
        return "Anonyme"

    @property
    def est_visible(self):
        """Vérifie si l'avis est visible publiquement"""
        return self.statut.code == 'visible'

    @property
    def est_masque(self):
        """Vérifie si l'avis est masqué"""
        return self.statut.code == 'masque'


# Table de jonction pour relier les salons et les services
class TblSalonService(models.Model):
    idSalonService = models.AutoField(primary_key=True)
    salon = models.ForeignKey(TblSalon, on_delete=models.CASCADE, related_name="salon_service")
    service = models.ForeignKey(TblService, on_delete=models.CASCADE, related_name="salon_service")

    class Meta:
        unique_together = ('salon', 'service')  # Unicité entre un salon et un service

    def __str__(self):
        return f"Service '{self.service.intitule_service}' pour le salon '{self.salon.nom_salon}'"

class TblServiceTemps(models.Model):
    idServiceTemps = models.AutoField(primary_key=True)
    service = models.ForeignKey(
        TblService, on_delete=models.CASCADE, related_name="service_temps"
    )
    temps = models.ForeignKey(
        TblTemps, on_delete=models.CASCADE, related_name="temps_services"
    )
    # ✅ AJOUT : Salon avec null=True pour la migration
    salon = models.ForeignKey(
        TblSalon,
        on_delete=models.CASCADE,
        related_name="temps_services",
        null=True,  # ✅ Permet la migration
        blank=True  # ✅ Permet la migration
    )

    class Meta:
        # ✅ Pas de contrainte pour le moment (on l'ajoutera après)
        pass

    def __str__(self):
        salon_info = f" chez {self.salon.nom_salon}" if self.salon else " (salon non défini)"
        return f"Durée de {self.temps.minutes}min pour '{self.service.intitule_service}'{salon_info}"

class TblServicePrix(models.Model):
    idServicePrix = models.AutoField(primary_key=True)
    service = models.ForeignKey(
        TblService, on_delete=models.CASCADE, related_name="service_prix"
    )
    prix = models.ForeignKey(
        TblPrix, on_delete=models.CASCADE, related_name="prix_services"
    )
    # ✅ AJOUT : Salon avec null=True pour la migration
    salon = models.ForeignKey(
        TblSalon,
        on_delete=models.CASCADE,
        related_name="prix_services",
        null=True,  # ✅ Permet la migration
        blank=True  # ✅ Permet la migration
    )

    class Meta:
        # ✅ Pas de contrainte pour le moment (on l'ajoutera après)
        pass

    def __str__(self):
        salon_info = f" chez {self.salon.nom_salon}" if self.salon else " (salon non défini)"
        return f"Prix de {self.prix.prix}€ pour '{self.service.intitule_service}'{salon_info}"



# 📌 Modèle du panier pour chaque utilisateur
class TblCart(models.Model):
    idTblCart = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        'TblUser', on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        """ Calcule le total du panier """
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Panier de {self.user.nom} {self.user.prenom} - {self.items.count()} articles"


# 📌 Modèle pour les articles du panier
class TblCartItem(models.Model):
    idTblCartItem = models.AutoField(primary_key=True)
    cart = models.ForeignKey(
        TblCart, on_delete=models.CASCADE, related_name="items"
    )
    service = models.ForeignKey(
        TblService, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        """ Calcule le total pour cet article """
        prix_service = self.service.service_prix.first().prix.prix  # 🔥 Récupère le prix via la relation
        return self.quantity * prix_service

    def __str__(self):
        return f"{self.quantity} x {self.service.intitule_service} (Total: {self.total_price()}€)"

    class Meta:
        unique_together = ('cart', 'service')  # ✅ Un même service ne peut pas être ajouté plusieurs fois


class TblPromotion(models.Model):
    idPromotion = models.AutoField(primary_key=True)

    # ✅ AJOUT : Référence au salon (cohérence avec TblServicePrix et TblServiceTemps)
    salon = models.ForeignKey(
        'TblSalon',
        on_delete=models.CASCADE,
        related_name="promotions"
    )

    # Référence au service
    service = models.ForeignKey(
        'TblService',
        on_delete=models.CASCADE,
        related_name="promotions"
    )

    # Pourcentage de réduction
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Dates de la promotion
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField()

    # ✅ CONTRAINTE D'UNICITÉ : Un salon ne peut avoir qu'une seule promotion active par service
    class Meta:
        unique_together = ('salon', 'service', 'start_date')
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"

    def is_active(self):
        """
        Vérifie si la promotion est active en fonction de la date actuelle.
        Utilise la date uniquement, sans tenir compte des heures.
        """
        current_date = now().date()
        start_date = self.start_date.date()
        end_date = self.end_date.date()

        print(f"DEBUG is_active: today={current_date}, start={start_date}, end={end_date}")
        return start_date <= current_date <= end_date

    def get_prix_avec_promotion(self, prix_original):
        """
        Calcule le prix après application de la promotion.

        Args:
            prix_original (Decimal): Prix original du service

        Returns:
            Decimal: Prix après réduction
        """
        if not self.is_active():
            return prix_original

        reduction = (self.discount_percentage / Decimal("100")) * prix_original
        prix_final = prix_original - reduction
        return prix_final.quantize(Decimal('0.01'))  # Arrondir à 2 décimales

    def get_montant_economise(self, prix_original):
        """
        Calcule le montant économisé grâce à la promotion.

        Args:
            prix_original (Decimal): Prix original du service

        Returns:
            Decimal: Montant économisé
        """
        if not self.is_active():
            return Decimal("0.00")

        return prix_original - self.get_prix_avec_promotion(prix_original)

    def __str__(self):
        salon_nom = self.salon.nom_salon if hasattr(self.salon, 'nom_salon') else f"Salon #{self.salon.idTblSalon}"
        statut = 'Active' if self.is_active() else 'Expirée'
        return f"Promotion {self.discount_percentage}% - {self.service.intitule_service} chez {salon_nom} ({statut})"

    def save(self, *args, **kwargs):
        """
        Validation personnalisée avant sauvegarde.
        """
        # Vérifier que la date de fin est après la date de début
        if self.end_date <= self.start_date:
            raise ValueError("La date de fin doit être postérieure à la date de début")

        # Vérifier que le pourcentage est valide
        if not (0 <= self.discount_percentage <= 100):
            raise ValueError("Le pourcentage de réduction doit être entre 0 et 100")

        super().save(*args, **kwargs)


class TblRendezVous(models.Model):
    idRendezVous = models.AutoField(primary_key=True)
    client = models.ForeignKey('TblClient', on_delete=models.CASCADE, related_name='rendez_vous')
    coiffeuse = models.ForeignKey('TblCoiffeuse', on_delete=models.CASCADE, related_name='rendez_vous')
    salon = models.ForeignKey('TblSalon', on_delete=models.CASCADE, related_name='rendez_vous')
    date_heure = models.DateTimeField()
    statut = models.CharField(
        max_length=20,
        choices=[('en attente', 'En attente'), ('confirmé', 'Confirmé'), ('annulé', 'Annulé'), ('terminé', 'Terminé')],
        default='en attente'
    )
    total_prix = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duree_totale = models.PositiveIntegerField(blank=True, null=True)  # ✅ Durée totale du RDV en minutes
    est_archive = models.BooleanField(default=False)

    def calculer_total(self):
        """ Calcule le prix total et la durée totale du RDV en fonction des services choisis """
        total_prix = 0
        total_duree = 0

        for service in self.rendez_vous_services.all():
            total_prix += service.prix_applique
            total_duree += service.duree_estimee  # 🔥 Ajout de la durée estimée

        self.total_prix = total_prix
        self.duree_totale = total_duree  # 🔥 Mise à jour de la durée totale
        self.save()

    def __str__(self):
        return f"RDV {self.idRendezVous} - {self.client.idTblUser.nom} ({self.date_heure})"


class TblRendezVousService(models.Model):
    idRendezVousService = models.AutoField(primary_key=True)
    rendez_vous = models.ForeignKey(
        'TblRendezVous', on_delete=models.CASCADE, related_name='rendez_vous_services'
    )
    service = models.ForeignKey(
        'TblService', on_delete=models.CASCADE, related_name='rendez_vous_services'
    )
    prix_applique = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )  # ✅ Prix appliqué au moment de la réservation
    duree_estimee = models.PositiveIntegerField(blank=True, null=True)  # 🔥 Durée totale du service

    class Meta:
        unique_together = ('rendez_vous', 'service')  # ✅ Un même service ne peut pas être ajouté plusieurs fois

    def save(self, *args, **kwargs):
        """ Applique le prix promo au moment de la réservation """
        if self.prix_applique is None:  # ✅ Si le prix n'est pas encore défini
            # 1️⃣ Récupérer le prix standard
            prix_service = TblServicePrix.objects.filter(service=self.service).first()
            prix_final = prix_service.prix.prix if prix_service else Decimal("0.00")

            # 2️⃣ Vérifier si une promotion est active AU MOMENT DE LA RESERVATION
            promo = TblPromotion.objects.filter(
                service=self.service,
                start_date__lte=now(),
                end_date__gte=now()
            ).first()

            if promo:  # 🔥 Appliquer la réduction si une promo est trouvée
                reduction = (promo.discount_percentage / Decimal("100")) * prix_final
                prix_final -= reduction

            self.prix_applique = prix_final  # ✅ On enregistre le prix final

        # 3️⃣ Récupérer la durée estimée
        if not self.duree_estimee:
            temps_service = TblServiceTemps.objects.filter(service=self.service).first()
            self.duree_estimee = temps_service.temps.minutes if temps_service else 0

        super().save(*args, **kwargs)  # Appelle la sauvegarde originale

    def __str__(self):
        return f"{self.service.intitule_service} ({self.prix_applique} €) pour RDV {self.rendez_vous.idRendezVous}"


class TblPaiementStatut(models.Model):
    """
    Table des statuts de paiement disponibles.

    Exemples :
    - en_attente → En attente
    - payé → Payé
    - remboursé → Remboursé
    """
    idTblPaiementStatut = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)  # ex: 'payé'
    libelle = models.CharField(max_length=100)  # ex: 'Payé'

    def __str__(self):
        return self.libelle


class TblMethodePaiement(models.Model):
    """
    Table des méthodes de paiement autorisées.

    Exemples :
    - card → Carte Bancaire
    - apple_pay → Apple Pay
    """
    idTblMethodePaiement = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)  # ex: 'card'
    libelle = models.CharField(max_length=100)  # ex: 'Carte Bancaire'

    def __str__(self):
        return self.libelle


class TblPaiement(models.Model):
    """
    Paiement effectué pour un rendez-vous Hairbnb.

    Enregistre toutes les données nécessaires au suivi, à la facturation,
    et à la communication avec Stripe.
    """

    idTblPaiement = models.AutoField(primary_key=True)

    # 🔗 Lien vers le rendez-vous
    rendez_vous = models.ForeignKey('TblRendezVous', on_delete=models.CASCADE)

    # 🔗 Lien vers l'utilisateur
    utilisateur = models.ForeignKey('TblUser', on_delete=models.CASCADE, null=True, blank=True)

    # 💰 Montant payé en euros
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)

    # 🕓 Date et heure du paiement
    date_paiement = models.DateTimeField(auto_now_add=True)

    # 🔗 Statut du paiement
    statut = models.ForeignKey('TblPaiementStatut', on_delete=models.PROTECT)

    # 🔗 Méthode de paiement utilisée
    methode = models.ForeignKey('TblMethodePaiement', on_delete=models.SET_NULL, null=True, blank=True)

    # 📡 Identifiants Stripe
    stripe_payment_intent_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    stripe_charge_id = models.CharField(max_length=50, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=50, null=True, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=100, null=True, blank=True)

    # 📧 Email du client (pour factures, relances, etc.)
    email_client = models.EmailField(max_length=30, null=True, blank=True)

    # 🧾 Lien vers le reçu Stripe
    receipt_url = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Paiement de {self.montant_paye}€ pour le RDV #{self.rendez_vous.idRendezVous} — {self.statut.libelle}"


class TblTransaction(models.Model):
    """
    Modèle représentant une transaction financière liée à un paiement.

    Cette table permet de tracer de manière détaillée toutes les opérations
    financières effectuées pour un rendez-vous, que ce soit un paiement
    initial ou un remboursement partiel/total.

    Elle est utile pour gérer des cas complexes comme :
    - les paiements partiels,
    - les remboursements après annulation,
    - l’historique des opérations pour audit ou export comptable.

    Attributs :
    -----------
    paiement : ForeignKey
        Référence au paiement parent (TblPaiement) auquel la transaction est rattachée.
        Cela permet d'associer plusieurs transactions (paiement et remboursement)
        à un même rendez-vous payé.

    type : CharField
        Indique le type de transaction :
        - 'paiement' : transaction créditrice (argent entrant).
        - 'remboursement' : transaction débitrice (argent sortant).
        Champ limité à 10 caractères.

    montant : DecimalField
        Le montant de la transaction, en euros (€).
        Format : maximum 10 chiffres, dont 2 après la virgule.
        Ce champ permet une traçabilité financière précise.

    date_transaction : DateTimeField
        Date et heure de la transaction, enregistrée automatiquement à la création.

    statut : CharField
        Statut de la transaction, utile si elle est en cours ou à confirmer :
        - 'effectué' : la transaction a bien été réalisée.
        - 'en attente' : la transaction est prévue mais pas encore complétée.

    Exemple d'usage :
    -----------------
        - Enregistrer un paiement partiel :
            TblTransaction.objects.create(
                paiement=p,
                type='paiement',
                montant=30.00,
                statut='effectué'
            )

        - Ajouter un remboursement :
            TblTransaction.objects.create(
                paiement=p,
                type='remboursement',
                montant=15.00,
                statut='effectué'
            )
    """
    paiement = models.ForeignKey('TblPaiement', on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=13, choices=[('paiement', 'Paiement'), ('remboursement', 'Remboursement')])
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_transaction = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=[('effectué', 'Effectué'), ('en attente', 'En attente')])

    def __str__(self):
        return f"{self.get_type_display()} de {self.montant}€ - {self.get_statut_display()}"


class TblHoraireCoiffeuse(models.Model):
    coiffeuse = models.ForeignKey('TblCoiffeuse', on_delete=models.CASCADE, related_name='horaires')
    jour = models.IntegerField(
        choices=[(i, ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][i]) for i in range(7)])
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    class Meta:
        unique_together = ('coiffeuse', 'jour')

    def __str__(self):
        return f"{self.coiffeuse.idTblUser.nom} - {self.get_jour_display()} : {self.heure_debut} - {self.heure_fin}"


# ✅ Indisponibilités exceptionnelles (vacances, congés, absences, etc.)
class TblIndisponibilite(models.Model):
    coiffeuse = models.ForeignKey('TblCoiffeuse', on_delete=models.CASCADE, related_name='indisponibilites')
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    motif = models.CharField(max_length=60, blank=False, null=False)

    def __str__(self):
        return f"{self.date} de {self.heure_debut} à {self.heure_fin} (motif: {self.motif})"


class TblFavorite(models.Model):
    idTblFavorite = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'TblUser',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    salon = models.ForeignKey(
        TblSalon,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'salon')  # Un même utilisateur ne peut pas aimer deux fois le même salon
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"

    def __str__(self):
        return f"{self.user.nom} ♥ {self.salon.nom_salon if hasattr(self.salon, 'nom_salon') else self.salon.idTblSalon}"


class TblEmailType(models.Model):
    """Table des types d'emails de notification."""
    idTblEmailType = models.AutoField(primary_key=True)
    code = models.CharField(max_length=30, unique=True)  # Code technique (ex: 'confirmation_rdv')
    libelle = models.CharField(max_length=50)  # Libellé lisible (ex: 'Confirmation de rendez-vous')

    def __str__(self):
        return self.libelle


class TblEmailStatus(models.Model):
    """Table des statuts d'envoi d'emails."""
    idTblEmailStatus = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)  # Code technique (ex: 'en_attente')
    libelle = models.CharField(max_length=30)  # Libellé lisible (ex: 'En attente d'envoi')

    def __str__(self):
        return self.libelle


class TblEmailNotification(models.Model):
    """Table des notifications par email envoyées aux utilisateurs."""
    idTblEmailNotification = models.AutoField(primary_key=True)

    # Relations avec les autres tables
    destinataire = models.ForeignKey(
        'TblUser',
        on_delete=models.CASCADE,
        related_name='emails_recus'
    )
    salon = models.ForeignKey(
        'TblSalon',
        on_delete=models.CASCADE,
        related_name='emails_envoyes',
        null=True,
        blank=True
    )
    rendez_vous = models.ForeignKey(
        'TblRendezVous',
        on_delete=models.CASCADE,
        related_name='emails_notification',
        null=True,
        blank=True
    )
    type_email = models.ForeignKey(
        TblEmailType,
        on_delete=models.PROTECT,  # Protection contre la suppression accidentelle
        related_name='notifications'
    )
    statut = models.ForeignKey(
        TblEmailStatus,
        on_delete=models.PROTECT,  # Protection contre la suppression accidentelle
        related_name='notifications'
    )

    # Contenu de l'email
    sujet = models.CharField(max_length=100)
    contenu = models.TextField()

    # Métadonnées de l'email
    date_creation = models.DateTimeField(default=timezone.now)
    date_envoi = models.DateTimeField(null=True, blank=True)
    tentatives = models.PositiveSmallIntegerField(default=0)  # Limité à 32767, amplement suffisant

    # Traçabilité technique
    email_id = models.CharField(max_length=100, null=True,
                                blank=True)  # ID unique du message chez le prestataire d'envoi

    class Meta:
        db_table = 'TblEmailNotification'
        ordering = ['-date_creation']
        verbose_name = "Notification par email"
        verbose_name_plural = "Notifications par email"

    def __str__(self):
        return f"{self.type_email} à {self.destinataire.email} ({self.statut})"


# Modèles optimisés pour l'agent IA Claude (économie de tokens)
class AIConversation(models.Model):
    user = models.ForeignKey('TblUser', on_delete=models.CASCADE, related_name='ai_conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    # Champ pour stocker le contexte de la conversation (métadonnées, préférences)
    # Stocké au format JSON pour éviter de le recalculer à chaque message
    context_cache = models.JSONField(null=True, blank=True)

    # Nombre total de tokens utilisés pour cette conversation (pour le suivi des coûts)
    tokens_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Conversation #{self.id} - {self.user.prenom}"

    class Meta:
        ordering = ['-created_at']


class AIMessage(models.Model):
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Champs pour suivre l'utilisation des tokens
    tokens_in = models.PositiveIntegerField(default=0)  # Tokens en entrée
    tokens_out = models.PositiveIntegerField(default=0)  # Tokens en sortie

    # Champ optionnel pour stocker des données spécifiques (like entités reconnues)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']