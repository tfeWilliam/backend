################################################################################
#                                                                              #
#         SÉRIALISEURS POUR LE CALCUL DES DISPONIBILITÉS (HAIRBNB)               #
#                                                                              #
#  Ce fichier définit les sérialiseurs (serializers) responsables de la        #
#  logique complexe de calcul des disponibilités d'une coiffeuse.              #
#                                                                              #
#  La classe principale, `DisponibilitesClientSerializer`, a un double rôle :  #
#    1. Valider les paramètres d'entrée (ID de la coiffeuse, date, durée).     #
#    2. Orchestrer et exécuter l'algorithme qui détermine les créneaux         #
#       horaires libres en tenant compte des horaires de travail, des          #
#       rendez-vous existants et des indisponibilités exceptionnelles.         #
#                                                                              #
################################################################################

# --- Importations ---
from rest_framework import serializers
from datetime import datetime, timedelta,date

# Importation des modèles de la base de données
from hairbnb.models import TblCoiffeuse, TblHoraireCoiffeuse, TblIndisponibilite, TblRendezVous


class CreneauDisponibleSerializer(serializers.Serializer):
    """
    Sérialiseur simple non lié à un modèle, utilisé pour définir la structure
    d'un unique créneau horaire disponible dans la réponse de l'API.
    """
    # Formate l'heure de début au format "HH:MM".
    debut = serializers.TimeField(format='%H:%M')
    # Formate l'heure de fin au format "HH:MM".
    fin = serializers.TimeField(format='%H:%M')


class DisponibilitesClientSerializer(serializers.Serializer):
    """
    Gère la validation des entrées et le calcul des disponibilités pour une coiffeuse.
    """
    # --- Champs d'entrée pour la validation ---
    coiffeuse_id = serializers.IntegerField()
    date = serializers.DateField()
    # La durée doit être entre 1 minute et 480 minutes (8 heures).
    duree = serializers.IntegerField(min_value=1, max_value=480)

    # --- Champ de sortie (utilisé pour la documentation de l'API) ---
    disponibilites = CreneauDisponibleSerializer(many=True, read_only=True)

    def validate_coiffeuse_id(self, value):
        """
        Validation personnalisée : vérifie que la coiffeuse existe,
        qu'elle est active et que son type d'utilisateur est correct.
        """
        try:
            coiffeuse = TblCoiffeuse.objects.select_related('idTblUser').get(idTblUser__idTblUser=value)
            user = coiffeuse.idTblUser
            if not user.is_active:
                raise serializers.ValidationError(f"La coiffeuse (ID: {value}) n'est pas active.")
            if user.type_ref.libelle.lower() != 'coiffeuse':
                raise serializers.ValidationError(f"L'utilisateur (ID: {value}) n'est pas une coiffeuse.")
            return value
        except TblCoiffeuse.DoesNotExist:
            raise serializers.ValidationError(f"Coiffeuse avec l'ID {value} introuvable.")

    def validate_date(self, value):
        """Validation personnalisée : vérifie que la date demandée n'est pas dans le passé."""
        if value < date.today():
            raise serializers.ValidationError("Impossible de réserver dans le passé.")
        return value

    def calculate_disponibilites(self, coiffeuse_id, target_date, duree_minutes):
        """
        Méthode principale qui orchestre le calcul des créneaux disponibles.
        """
        try:
            # Étape 1 : Récupérer l'objet Coiffeuse depuis la base de données.
            coiffeuse = TblCoiffeuse.objects.select_related('idTblUser').get(idTblUser__idTblUser=coiffeuse_id)

            # Étape 2 : Récupérer l'horaire de travail normal pour le jour de la semaine demandé.
            jour_semaine = target_date.weekday()
            horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=coiffeuse, jour=jour_semaine).first()
            if not horaires:
                print(f"⚠️ Aucun horaire défini pour {coiffeuse.idTblUser.nom} le {jour_semaine}")
                return []

            # Étape 3 : Récupérer toutes les périodes d'indisponibilité exceptionnelles pour ce jour.
            indisponibilites = TblIndisponibilite.objects.filter(coiffeuse=coiffeuse, date=target_date)

            # Étape 4 : Récupérer tous les rendez-vous déjà pris qui ne sont ni annulés ni terminés.
            rdv_existants = TblRendezVous.objects.filter(coiffeuse=coiffeuse, date_heure__date=target_date, statut__in=['en attente', 'confirmé']).order_by('date_heure')

            # Étape 5 : Appeler la méthode privée qui contient l'algorithme de génération de créneaux.
            creneaux_libres = self._generer_creneaux_libres(horaires, indisponibilites, rdv_existants, target_date, duree_minutes)

            print(f"✅ {len(creneaux_libres)} créneaux trouvés pour {coiffeuse.idTblUser.nom} le {target_date}")
            return creneaux_libres

        except TblCoiffeuse.DoesNotExist:
            print(f"❌ Coiffeuse {coiffeuse_id} introuvable")
            return []
        except Exception as e:
            print(f"❌ Erreur calcul disponibilités: {e}")
            return []

    def _generer_creneaux_libres(self, horaires, indisponibilites, rdv_existants, target_date, duree_minutes):
        """
        Algorithme de génération de créneaux. Il "parcourt" la journée et identifie
        les plages horaires libres suffisamment longues pour accueillir le service.
        """
        creneaux_libres = []
        duree_service = timedelta(minutes=duree_minutes)

        # Définit les bornes de la journée de travail.
        debut_travail = datetime.combine(target_date, horaires.heure_debut)
        fin_travail = datetime.combine(target_date, horaires.heure_fin)

        # Cas particulier : si on cherche pour aujourd'hui, on ne propose pas de créneaux passés.
        maintenant = datetime.now()
        if target_date == date.today() and debut_travail < maintenant:
            # On arrondit l'heure de début de la recherche à la prochaine demi-heure.
            minutes_arrondies = ((maintenant.minute // 30) + 1) * 30
            debut_travail = maintenant.replace(minute=0, second=0, microsecond=0)
            debut_travail += timedelta(minutes=minutes_arrondies)

        # Crée une liste unique de tous les "obstacles" (périodes bloquées) de la journée.
        obstacles = []
        for indispo in indisponibilites:
            debut_obstacle = datetime.combine(target_date, indispo.heure_debut)
            fin_obstacle = datetime.combine(target_date, indispo.heure_fin)
            obstacles.append((debut_obstacle, fin_obstacle, "indisponibilité"))
        for rdv in rdv_existants:
            debut_rdv = rdv.date_heure
            fin_rdv = debut_rdv + timedelta(minutes=rdv.duree_totale or 60)
            obstacles.append((debut_rdv, fin_rdv, f"RDV#{rdv.idRendezVous}"))

        # Trie les obstacles par heure de début pour les traiter dans l'ordre chronologique.
        obstacles.sort(key=lambda x: x[0])

        # Initialise un "curseur" temporel au début de la journée de travail (ou à maintenant).
        curseur = debut_travail

        # Itère sur chaque obstacle pour trouver les créneaux libres entre eux.
        for debut_obstacle, fin_obstacle, type_obstacle in obstacles:
            # Vérifie s'il y a assez de place entre le curseur actuel et le début du prochain obstacle.
            if curseur + duree_service <= debut_obstacle:
                # Si oui, génère des créneaux par tranches de 30 minutes dans cet intervalle.
                while curseur + duree_service <= debut_obstacle:
                    fin_creneau = curseur + duree_service
                    creneaux_libres.append({'debut': curseur.time(), 'fin': fin_creneau.time()})
                    curseur += timedelta(minutes=30)
            # Déplace le curseur juste après la fin de l'obstacle actuel.
            curseur = max(curseur, fin_obstacle)

        # Après avoir traité tous les obstacles, vérifie s'il reste de la place jusqu'à la fin de la journée.
        while curseur + duree_service <= fin_travail:
            fin_creneau = curseur + duree_service
            creneaux_libres.append({'debut': curseur.time(), 'fin': fin_creneau.time()})
            curseur += timedelta(minutes=30)

        return creneaux_libres








# from rest_framework import serializers
# from datetime import datetime, timedelta,date
#
# from hairbnb.models import TblCoiffeuse, TblHoraireCoiffeuse, TblIndisponibilite, TblRendezVous
#
#
# class CreneauDisponibleSerializer(serializers.Serializer):
#     """
#     Sérialise un créneau horaire disponible.
#     """
#     debut = serializers.TimeField(format='%H:%M')
#     fin = serializers.TimeField(format='%H:%M')
#
#
# class DisponibilitesClientSerializer(serializers.Serializer):
#     """
#     Sérialise les disponibilités d'une coiffeuse pour une date donnée.
#
#     Calculé dynamiquement en fonction de :
#     - Les horaires de travail de la coiffeuse
#     - Ses indisponibilités exceptionnelles
#     - Ses rendez-vous déjà réservés
#     - La durée du service demandé
#     """
#
#     # Paramètres d'entrée (validation)
#     coiffeuse_id = serializers.IntegerField()
#     date = serializers.DateField()
#     duree = serializers.IntegerField(min_value=1, max_value=480)  # Entre 1 min et 8h
#
#     # Données de sortie
#     disponibilites = CreneauDisponibleSerializer(many=True, read_only=True)
#
#     def validate_coiffeuse_id(self, value):
#         """Vérifie que la coiffeuse existe et est active."""
#         try:
#             coiffeuse = TblCoiffeuse.objects.select_related('idTblUser').get(
#                 idTblUser__idTblUser=value
#             )
#
#             # Vérifier que l'utilisateur est actif et du bon type
#             user = coiffeuse.idTblUser
#             if not user.is_active:
#                 raise serializers.ValidationError(f"La coiffeuse (ID: {value}) n'est pas active.")
#
#             # Vérifier le type d'utilisateur
#             if user.type_ref.libelle.lower() != 'coiffeuse':
#                 raise serializers.ValidationError(f"L'utilisateur (ID: {value}) n'est pas une coiffeuse.")
#
#             return value
#
#         except TblCoiffeuse.DoesNotExist:
#             raise serializers.ValidationError(f"Coiffeuse avec l'ID {value} introuvable.")
#
#     def validate_date(self, value):
#         """Vérifie que la date n'est pas dans le passé."""
#         if value < date.today():
#             raise serializers.ValidationError("Impossible de réserver dans le passé.")
#         return value
#
#     def calculate_disponibilites(self, coiffeuse_id, target_date, duree_minutes):
#         """
#         Calcule les créneaux disponibles pour une coiffeuse à une date donnée.
#
#         Args:
#             coiffeuse_id (int): ID de la coiffeuse
#             target_date (date): Date ciblée
#             duree_minutes (int): Durée du service en minutes
#
#         Returns:
#             List[dict]: Liste des créneaux disponibles avec 'debut' et 'fin'
#         """
#         try:
#             # 1️⃣ Récupérer la coiffeuse
#             coiffeuse = TblCoiffeuse.objects.select_related('idTblUser').get(
#                 idTblUser__idTblUser=coiffeuse_id
#             )
#
#             # 2️⃣ Récupérer les horaires de travail pour ce jour de la semaine
#             jour_semaine = target_date.weekday()  # 0=Lundi, 6=Dimanche
#
#             horaires = TblHoraireCoiffeuse.objects.filter(
#                 coiffeuse=coiffeuse,
#                 jour=jour_semaine
#             ).first()
#
#             if not horaires:
#                 print(f"⚠️ Aucun horaire défini pour {coiffeuse.idTblUser.nom} le {jour_semaine}")
#                 return []
#
#             # 3️⃣ Récupérer les indisponibilités exceptionnelles
#             indisponibilites = TblIndisponibilite.objects.filter(
#                 coiffeuse=coiffeuse,
#                 date=target_date
#             )
#
#             # 4️⃣ Récupérer les rendez-vous déjà pris
#             rdv_existants = TblRendezVous.objects.filter(
#                 coiffeuse=coiffeuse,
#                 date_heure__date=target_date,
#                 statut__in=['en attente', 'confirmé']  # Exclure annulés/terminés
#             ).order_by('date_heure')
#
#             # 5️⃣ Générer les créneaux libres
#             creneaux_libres = self._generer_creneaux_libres(
#                 horaires, indisponibilites, rdv_existants,
#                 target_date, duree_minutes
#             )
#
#             print(f"✅ {len(creneaux_libres)} créneaux trouvés pour {coiffeuse.idTblUser.nom} le {target_date}")
#             return creneaux_libres
#
#         except TblCoiffeuse.DoesNotExist:
#             print(f"❌ Coiffeuse {coiffeuse_id} introuvable")
#             return []
#         except Exception as e:
#             print(f"❌ Erreur calcul disponibilités: {e}")
#             return []
#
#     def _generer_creneaux_libres(self, horaires, indisponibilites, rdv_existants, target_date, duree_minutes):
#         """
#         Génère la liste des créneaux libres en tenant compte de tous les obstacles.
#         """
#         creneaux_libres = []
#
#         # Convertir la durée en timedelta
#         duree_service = timedelta(minutes=duree_minutes)
#
#         # Heure de début et fin de travail
#         debut_travail = datetime.combine(target_date, horaires.heure_debut)
#         fin_travail = datetime.combine(target_date, horaires.heure_fin)
#
#         # Si la date est aujourd'hui, commencer à partir de maintenant
#         maintenant = datetime.now()
#         if target_date == date.today() and debut_travail < maintenant:
#             # Arrondir à la prochaine demi-heure
#             minutes_arrondies = ((maintenant.minute // 30) + 1) * 30
#             debut_travail = maintenant.replace(minute=0, second=0, microsecond=0)
#             debut_travail += timedelta(minutes=minutes_arrondies)
#
#         # Créer une liste de tous les obstacles (indispos + rdv)
#         obstacles = []
#
#         # Ajouter les indisponibilités
#         for indispo in indisponibilites:
#             debut_obstacle = datetime.combine(target_date, indispo.heure_debut)
#             fin_obstacle = datetime.combine(target_date, indispo.heure_fin)
#             obstacles.append((debut_obstacle, fin_obstacle, "indisponibilité"))
#
#         # Ajouter les rendez-vous existants
#         for rdv in rdv_existants:
#             debut_rdv = rdv.date_heure
#             fin_rdv = debut_rdv + timedelta(minutes=rdv.duree_totale or 60)  # Durée par défaut 1h
#             obstacles.append((debut_rdv, fin_rdv, f"RDV#{rdv.idRendezVous}"))
#
#         # Trier les obstacles par heure de début
#         obstacles.sort(key=lambda x: x[0])
#
#         # Générer les créneaux entre les obstacles
#         curseur = debut_travail
#
#         for debut_obstacle, fin_obstacle, type_obstacle in obstacles:
#             # Y a-t-il de la place avant cet obstacle ?
#             if curseur + duree_service <= debut_obstacle:
#                 # Créer des créneaux de 30 minutes jusqu'à l'obstacle
#                 while curseur + duree_service <= debut_obstacle:
#                     fin_creneau = curseur + duree_service
#                     creneaux_libres.append({
#                         'debut': curseur.time(),
#                         'fin': fin_creneau.time()
#                     })
#                     curseur += timedelta(minutes=30)  # Créneaux par tranches de 30 min
#
#             # Avancer le curseur après cet obstacle
#             curseur = max(curseur, fin_obstacle)
#
#         # Vérifier s'il reste de la place après le dernier obstacle
#         while curseur + duree_service <= fin_travail:
#             fin_creneau = curseur + duree_service
#             creneaux_libres.append({
#                 'debut': curseur.time(),
#                 'fin': fin_creneau.time()
#             })
#             curseur += timedelta(minutes=30)
#
#         return creneaux_libres