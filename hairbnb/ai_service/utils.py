################################################################################
#                                                                              #
#                   UTILITAIRES POUR LE SERVICE IA (HAIRBNB)                   #
#                                                                              #
#  Ce fichier contient la fonction centrale `get_database_context_for_query`.  #
#  Son rôle est essentiel : analyser une question en langage naturel posée par #
#  un utilisateur, et en fonction des mots-clés détectés, interroger la base  #
#  de données pour extraire des informations pertinentes et agrégées.          #
#                                                                              #
#  Le dictionnaire "contexte" ainsi généré est ensuite fourni à l'IA pour lui  #
#  permettre de formuler des réponses factuelles et basées sur les données     #
#  en temps réel de l'application.                                             #
#                                                                              #
################################################################################

# Importation des modules Django et Python nécessaires
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
import logging

# Initialisation du logger pour ce module, pour enregistrer les erreurs
logger = logging.getLogger(__name__)


def get_database_context_for_query(query, user=None):
    """
    Analyse la requête de l'utilisateur pour extraire dynamiquement des données
    pertinentes de la base de données et les formater dans un dictionnaire de contexte.

    Args:
        query (str): La question en langage naturel posée par l'utilisateur.
        user (TblUser, optional): L'objet utilisateur authentifié, utilisé pour
                                  extraire des informations personnelles. Defaults to None.

    Returns:
        dict: Un dictionnaire contenant les données extraites, structurées par sujet,
              prêt à être envoyé à l'IA.
    """
    # Convertit la requête en minuscules pour une analyse insensible à la casse.
    query_lower = query.lower()
    # Initialise le dictionnaire qui contiendra le contexte final.
    context = {}

    # Un bloc try...except global pour capturer toute erreur imprévue durant l'extraction.
    try:
        # Les importations de modèles sont faites ici pour éviter les dépendances circulaires
        # qui peuvent survenir si ce fichier utilitaire est importé par les modèles eux-mêmes.
        from hairbnb.models import (
            TblUser, TblClient, TblCoiffeuse, TblRole,
            TblLocalite, TblRue, TblAdresse,
            TblSalon, TblService, TblSalonService, TblServicePrix, TblServiceTemps,
            TblTemps, TblPrix, TblSalonImage, TblAvis,
            TblRendezVous, TblRendezVousService, TblIndisponibilite, TblHoraireCoiffeuse,
            TblPaiement, TblPaiementStatut, TblMethodePaiement, TblTransaction,
            TblPromotion, TblFavorite, TblEmailNotification, TblEmailType, TblEmailStatus,
            TblCart, TblCartItem
        )

        # --- Détection des sujets dans la requête de l'utilisateur ---
        subjects = []

        # Dictionnaire mappant des sujets à une liste de mots-clés associés.
        subject_keywords = {
            "statistiques": ["stat", "chiffre", "nombre", "total", "combien", "global"],
            "utilisateurs": ["utilisateur", "user", "client", "membre", "compte"],
            "coiffeuses": ["coiffeuse", "coiffeur", "professionnel", "styliste"],
            "salons": ["salon", "établissement", "local"],
            "services": ["service", "prestation", "coiffure", "coupe", "coloration", "soin"],
            "rendez_vous": ["rendez-vous", "rdv", "réservation", "booking", "planning", "agenda", "calendrier"],
            "paiements": ["paiement", "argent", "tarif", "prix", "facture", "revenu", "chiffre d'affaire"],
            "avis": ["avis", "commentaire", "feedback", "note", "évaluation", "rating"],
            "localisation": ["adresse", "lieu", "localisation", "ville", "commune", "code postal"],
            "promotions": ["promo", "promotion", "réduction", "discount", "offre", "solde"],
            "favoris": ["favori", "préféré", "save", "aime"],
            "emails": ["email", "mail", "notification", "message"],
            "horaires": ["horaire", "planning", "disponibilité", "heure", "jour"],
        }

        # Itération pour trouver les sujets pertinents en fonction des mots-clés.
        for subject, keywords in subject_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                subjects.append(subject)

        # Si aucun sujet n'est explicitement détecté, on fournit les statistiques générales par défaut.
        if not subjects:
            subjects.append("statistiques")

        # Détecte si la requête concerne des informations personnelles ("mes rdv", "mon profil", etc.).
        if user and any(term in query_lower for term in ["mon", "ma", "mes", "je", "j'ai", "moi"]):
            subjects.append("personnel")

        # --- Extraction des données en fonction des sujets détectés ---

        # --- Contexte : Statistiques Générales ---
        if "statistiques" in subjects:
            context["statistiques_generales"] = {
                "utilisateurs": {
                    "total": TblUser.objects.count(),
                    "coiffeuses": TblCoiffeuse.objects.count(),
                    "clients": TblClient.objects.count(),
                    "actifs": TblUser.objects.filter(is_active=True).count(),
                },
                "salons": {
                    "total": TblSalon.objects.count()
                },
                "services": {
                    "total": TblService.objects.count(),
                    "prix_moyen": float(TblServicePrix.objects.annotate(
                        prix_service=Sum('prix__prix')
                    ).aggregate(Avg('prix_service'))['prix_service__avg'] or 0)
                },
                "rendez_vous": {
                    "total": TblRendezVous.objects.count(),
                    "en_attente": TblRendezVous.objects.filter(statut='en attente').count(),
                    "confirmés": TblRendezVous.objects.filter(statut='confirmé').count(),
                    "annulés": TblRendezVous.objects.filter(statut='annulé').count(),
                    "terminés": TblRendezVous.objects.filter(statut='terminé').count(),
                },
                "avis": {
                    "total": TblAvis.objects.count(),
                    "note_moyenne": float(TblAvis.objects.aggregate(Avg('note'))['note__avg'] or 0),
                }
            }

        # --- Contexte : Utilisateurs ---
        if "utilisateurs" in subjects:
            context["utilisateurs"] = {
                "total": TblUser.objects.count(),
                "par_type": {
                    "coiffeuses": TblUser.objects.filter(type='coiffeuse').count(),
                    "clients": TblUser.objects.filter(type='client').count(),
                },
                "par_genre": {
                    "hommes": TblUser.objects.filter(sexe='homme').count(),
                    "femmes": TblUser.objects.filter(sexe='femme').count(),
                    "autres": TblUser.objects.filter(sexe='autre').count(),
                },
                "actifs": TblUser.objects.filter(is_active=True).count(),
                "inactifs": TblUser.objects.filter(is_active=False).count(),
                "nouveaux_30_jours": TblUser.objects.filter(
                    date_naissance__gte=datetime.now() - timedelta(days=30)
                ).count(),
            }

            clients_avec_rdv = TblClient.objects.annotate(
                nb_rdv=Count('rendez_vous')
            ).filter(nb_rdv__gt=0).count()

            context["utilisateurs"]["clients_details"] = {
                "avec_rdv": clients_avec_rdv,
                "sans_rdv": TblClient.objects.count() - clients_avec_rdv,
                "avec_favoris": TblClient.objects.filter(
                    idTblUser__favorites__isnull=False
                ).distinct().count()
            }

        # --- Contexte : Coiffeuses ---
        if "coiffeuses" in subjects:
            coiffeuses_avec_salon = TblCoiffeuse.objects.filter(salon__isnull=False).count()

            context["coiffeuses"] = {
                "total": TblCoiffeuse.objects.count(),
                "avec_salon": coiffeuses_avec_salon,
                "sans_salon": TblCoiffeuse.objects.count() - coiffeuses_avec_salon,
                "top_coiffeuses": []
            }

            top_coiffeuses = TblCoiffeuse.objects.annotate(
                nb_rdv=Count('rendez_vous')
            ).order_by('-nb_rdv')[:5]

            for coiffeuse in top_coiffeuses:
                try:
                    salon = TblSalon.objects.filter(coiffeuse=coiffeuse).first()
                    note_moyenne = 0
                    if salon:
                        note_moyenne = TblAvis.objects.filter(salon=salon).aggregate(Avg('note'))['note__avg'] or 0

                    context["coiffeuses"]["top_coiffeuses"].append({
                        "nom": f"{coiffeuse.idTblUser.prenom} {coiffeuse.idTblUser.nom}",
                        "nombre_rdv": coiffeuse.nb_rdv,
                        "salon": salon.nom_salon if salon else "Pas de salon",
                        "note": float(note_moyenne)
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des données coiffeuse: {str(e)}")

        # --- Contexte : Salons ---
        if "salons" in subjects:
            top_salons = TblSalon.objects.annotate(
                note_moyenne=Avg('avis__note'),
                nb_avis=Count('avis')
            ).order_by('-note_moyenne')[:5]

            salons_data = []
            for salon in top_salons:
                if not salon.note_moyenne:
                    continue

                try:
                    nb_services = salon.services.count()
                    salons_data.append({
                        "nom": salon.nom_salon,
                        "coiffeuse": f"{salon.coiffeuse.idTblUser.prenom} {salon.coiffeuse.idTblUser.nom}",
                        "note": float(salon.note_moyenne),
                        "nombre_avis": salon.nb_avis,
                        "nombre_services": nb_services
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des données salon: {str(e)}")

            context["salons"] = {
                "total": TblSalon.objects.count(),
                "avec_avis": TblSalon.objects.annotate(nb_avis=Count('avis')).filter(nb_avis__gt=0).count(),
                "top_salons": salons_data
            }

        # --- Contexte : Services ---
        if "services" in subjects:
            top_services = TblService.objects.annotate(
                nb_rdv=Count('rendez_vous_services')
            ).order_by('-nb_rdv')[:10]

            services_data = []
            for service in top_services:
                try:
                    prix_obj = TblServicePrix.objects.filter(service=service).first()
                    prix = prix_obj.prix.prix if prix_obj and hasattr(prix_obj, 'prix') else 0

                    temps_obj = TblServiceTemps.objects.filter(service=service).first()
                    duree = temps_obj.temps.minutes if temps_obj and hasattr(temps_obj, 'temps') else 0

                    services_data.append({
                        "nom": service.intitule_service,
                        "description": service.description[:50] + "..." if len(
                            service.description) > 50 else service.description,
                        "prix": float(prix),
                        "duree_minutes": duree,
                        "utilisations": service.nb_rdv
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des données service: {str(e)}")

            context["services"] = {
                "total": TblService.objects.count(),
                "prix_moyen": float(TblPrix.objects.aggregate(Avg('prix'))['prix__avg'] or 0),
                "top_services": services_data
            }

        # --- Contexte : Rendez-vous ---
        if "rendez_vous" in subjects:
            context["rendez_vous"] = {
                "total": TblRendezVous.objects.count(),
                "par_statut": {
                    "en_attente": TblRendezVous.objects.filter(statut='en attente').count(),
                    "confirmés": TblRendezVous.objects.filter(statut='confirmé').count(),
                    "annulés": TblRendezVous.objects.filter(statut='annulé').count(),
                    "terminés": TblRendezVous.objects.filter(statut='terminé').count()
                },
                "prix_moyen": float(TblRendezVous.objects.filter(
                    total_prix__isnull=False
                ).aggregate(Avg('total_prix'))['total_prix__avg'] or 0),
                "duree_moyenne": TblRendezVous.objects.filter(
                    duree_totale__isnull=False
                ).aggregate(Avg('duree_totale'))['duree_totale__avg'] or 0,
                "recents": {
                    "30_jours": TblRendezVous.objects.filter(
                        date_heure__gte=datetime.now() - timedelta(days=30)
                    ).count(),
                    "7_jours": TblRendezVous.objects.filter(
                        date_heure__gte=datetime.now() - timedelta(days=7)
                    ).count()
                },
                "a_venir": TblRendezVous.objects.filter(
                    date_heure__gt=datetime.now()
                ).count()
            }

        # --- Contexte : Paiements ---
        if "paiements" in subjects:
            paiements = TblPaiement.objects.all()

            context["paiements"] = {
                "total": paiements.count(),
                "montant_total": float(paiements.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0),
                "montant_moyen": float(paiements.aggregate(Avg('montant_paye'))['montant_paye__avg'] or 0),
                "par_methode": {}
            }

            methodes = TblMethodePaiement.objects.all()
            for methode in methodes:
                count = paiements.filter(methode=methode).count()
                if count > 0:
                    context["paiements"]["par_methode"][methode.libelle] = count

        # --- Contexte : Avis ---
        if "avis" in subjects:
            avis = TblAvis.objects.all()

            context["avis"] = {
                "total": avis.count(),
                "note_moyenne": float(avis.aggregate(Avg('note'))['note__avg'] or 0),
                "repartition": {
                    "5_etoiles": avis.filter(note=5).count(),
                    "4_etoiles": avis.filter(note=4).count(),
                    "3_etoiles": avis.filter(note=3).count(),
                    "2_etoiles": avis.filter(note=2).count(),
                    "1_etoile": avis.filter(note=1).count()
                }
            }

        # --- Contexte : Promotions ---
        if "promotions" in subjects:
            promos = TblPromotion.objects.all()
            now_date = datetime.now()

            context["promotions"] = {
                "total": promos.count(),
                "actives": promos.filter(start_date__lte=now_date, end_date__gte=now_date).count(),
                "futures": promos.filter(start_date__gt=now_date).count(),
                "expirees": promos.filter(end_date__lt=now_date).count(),
                "reduction_moyenne": float(
                    promos.aggregate(Avg('discount_percentage'))['discount_percentage__avg'] or 0)
            }

        # --- Contexte : Localisation ---
        if "localisation" in subjects:
            context["localisation"] = {
                "communes": TblLocalite.objects.count(),
                "top_communes": []
            }

            top_communes = TblLocalite.objects.annotate(
                nb_users=Count('rues__adresses__utilisateurs')
            ).order_by('-nb_users')[:5]

            for commune in top_communes:
                if commune.nb_users > 0:
                    context["localisation"]["top_communes"].append({
                        "nom": commune.commune,
                        "code_postal": commune.code_postal,
                        "nombre_utilisateurs": commune.nb_users
                    })

        # --- Contexte : Données Personnelles de l'utilisateur connecté ---
        if "personnel" in subjects and user:
            context["personnel"] = {
                "profil": {
                    "id": user.idTblUser,
                    "nom": user.nom,
                    "prenom": user.prenom,
                    "email": user.email,
                    "type": user.type,
                    "role": user.role.nom if hasattr(user, 'role') and user.role else "Utilisateur",
                    "est_actif": user.is_active
                }
            }

            # Si l'utilisateur est un client, on récupère ses données spécifiques.
            if user.type == 'client':
                try:
                    client = TblClient.objects.filter(idTblUser=user).first()
                    if client:
                        rdvs = TblRendezVous.objects.filter(client=client)

                        context["personnel"]["rendez_vous"] = {
                            "total": rdvs.count(),
                            "en_attente": rdvs.filter(statut='en attente').count(),
                            "confirmes": rdvs.filter(statut='confirmé').count(),
                            "annules": rdvs.filter(statut='annulé').count(),
                            "termines": rdvs.filter(statut='terminé').count(),
                            "a_venir": rdvs.filter(date_heure__gt=datetime.now()).count()
                        }

                        favoris = TblFavorite.objects.filter(user=user)
                        if favoris.exists():
                            context["personnel"]["favoris"] = []
                            for fav in favoris:
                                context["personnel"]["favoris"].append({
                                    "salon": fav.salon.nom_salon,
                                    "coiffeuse": f"{fav.salon.coiffeuse.idTblUser.prenom} {fav.salon.coiffeuse.idTblUser.nom}"
                                })

                        try:
                            panier = TblCart.objects.filter(user=user).first()
                            if panier:
                                items = TblCartItem.objects.filter(cart=panier)
                                if items.exists():
                                    context["personnel"]["panier"] = {
                                        "nombre_articles": items.count(),
                                        "total": float(panier.total_price()),
                                        "articles": []
                                    }

                                    for item in items:
                                        context["personnel"]["panier"]["articles"].append({
                                            "service": item.service.intitule_service,
                                            "quantite": item.quantity,
                                            "prix_unitaire": float(item.service.service_prix.first().prix.prix),
                                            "total": float(item.total_price())
                                        })
                        except Exception as e:
                            logger.error(f"Erreur lors de la récupération du panier: {str(e)}")
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des données client: {str(e)}")

            # Si l'utilisateur est une coiffeuse, on récupère ses données spécifiques.
            elif user.type == 'coiffeuse':
                try:
                    coiffeuse = TblCoiffeuse.objects.filter(idTblUser=user).first()
                    if coiffeuse:
                        salon = TblSalon.objects.filter(coiffeuse=coiffeuse).first()
                        if salon:
                            context["personnel"]["salon"] = {
                                "id": salon.idTblSalon,
                                "nom": salon.nom_salon,
                                "slogan": salon.slogan,
                                "description": salon.a_propos,
                                "nombre_services": salon.services.count(),
                                "nombre_images": TblSalonImage.objects.filter(salon=salon).count(),
                                "evaluation": {
                                    "nombre_avis": TblAvis.objects.filter(salon=salon).count(),
                                    "note_moyenne": float(
                                        TblAvis.objects.filter(salon=salon).aggregate(Avg('note'))['note__avg'] or 0)
                                }
                            }

                            services = salon.services.all()
                            if services.exists():
                                context["personnel"]["salon"]["services"] = []
                                for service in services:
                                    prix_obj = TblServicePrix.objects.filter(service=service).first()
                                    prix = prix_obj.prix.prix if prix_obj and hasattr(prix_obj, 'prix') else 0

                                    context["personnel"]["salon"]["services"].append({
                                        "nom": service.intitule_service,
                                        "prix": float(prix),
                                        "utilisations": TblRendezVousService.objects.filter(
                                            service=service,
                                            rendez_vous__coiffeuse=coiffeuse
                                        ).count()
                                    })

                        rdvs = TblRendezVous.objects.filter(coiffeuse=coiffeuse)
                        if rdvs.exists():
                            context["personnel"]["rendez_vous"] = {
                                "total": rdvs.count(),
                                "en_attente": rdvs.filter(statut='en attente').count(),
                                "confirmes": rdvs.filter(statut='confirmé').count(),
                                "annules": rdvs.filter(statut='annulé').count(),
                                "termines": rdvs.filter(statut='terminé').count(),
                                "a_venir": rdvs.filter(date_heure__gt=datetime.now()).count(),
                                "recents": rdvs.filter(date_heure__gte=datetime.now() - timedelta(days=30)).count()
                            }

                        horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=coiffeuse)
                        if horaires.exists():
                            context["personnel"]["horaires"] = []
                            jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                            for horaire in horaires:
                                context["personnel"]["horaires"].append({
                                    "jour": jours[horaire.jour],
                                    "debut": str(horaire.heure_debut),
                                    "fin": str(horaire.heure_fin)
                                })

                        indispos = TblIndisponibilite.objects.filter(
                            coiffeuse=coiffeuse,
                            date__gte=datetime.now().date()
                        )
                        if indispos.exists():
                            context["personnel"]["indisponibilites"] = []
                            for indispo in indispos:
                                context["personnel"]["indisponibilites"].append({
                                    "date": str(indispo.date),
                                    "debut": str(indispo.heure_debut),
                                    "fin": str(indispo.heure_fin),
                                    "motif": indispo.motif
                                })
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des données coiffeuse: {str(e)}")

    except Exception as e:
        # En cas d'erreur majeure, on log l'erreur et on l'ajoute au contexte
        # pour informer l'utilisateur ou le développeur.
        logger.error(f"Erreur globale dans get_database_context_for_query: {str(e)}")
        context['error'] = f"Erreur lors de l'extraction des données: {str(e)}"

    # Retourne le dictionnaire de contexte final.
    return context





# # hairbnb/ai_service/utils.py
# from django.db.models import Count, Sum, Avg
# from datetime import datetime, timedelta
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# def get_database_context_for_query(query, user=None):
#     """
#     Fonction pour extraire les informations pertinentes de la base de données
#     en fonction de la requête de l'utilisateur.
#     """
#     query_lower = query.lower()
#     context = {}
#
#     try:
#         # Importation de tous les modèles de données
#         from hairbnb.models import (
#             # Utilisateurs et profils
#             TblUser, TblClient, TblCoiffeuse, TblRole,
#
#             # Localisation
#             TblLocalite, TblRue, TblAdresse,
#
#             # Salon et services
#             TblSalon, TblService, TblSalonService, TblServicePrix, TblServiceTemps,
#             TblTemps, TblPrix, TblSalonImage, TblAvis,
#
#             # Rendez-vous
#             TblRendezVous, TblRendezVousService, TblIndisponibilite, TblHoraireCoiffeuse,
#
#             # Paiements
#             TblPaiement, TblPaiementStatut, TblMethodePaiement, TblTransaction,
#
#             # Marketing
#             TblPromotion, TblFavorite, TblEmailNotification, TblEmailType, TblEmailStatus,
#
#             # Panier
#             TblCart, TblCartItem
#         )
#
#         # Détection intelligente des sujets de la requête
#         subjects = []
#
#         # Liste de tous les sujets possibles avec leurs mots-clés associés
#         subject_keywords = {
#             "statistiques": ["stat", "chiffre", "nombre", "total", "combien", "global"],
#             "utilisateurs": ["utilisateur", "user", "client", "membre", "compte"],
#             "coiffeuses": ["coiffeuse", "coiffeur", "professionnel", "styliste"],
#             "salons": ["salon", "établissement", "local"],
#             "services": ["service", "prestation", "coiffure", "coupe", "coloration", "soin"],
#             "rendez_vous": ["rendez-vous", "rdv", "réservation", "booking", "planning", "agenda", "calendrier"],
#             "paiements": ["paiement", "argent", "tarif", "prix", "facture", "revenu", "chiffre d'affaire"],
#             "avis": ["avis", "commentaire", "feedback", "note", "évaluation", "rating"],
#             "localisation": ["adresse", "lieu", "localisation", "ville", "commune", "code postal"],
#             "promotions": ["promo", "promotion", "réduction", "discount", "offre", "solde"],
#             "favoris": ["favori", "préféré", "save", "aime"],
#             "emails": ["email", "mail", "notification", "message"],
#             "horaires": ["horaire", "planning", "disponibilité", "heure", "jour"],
#         }
#
#         # Détection des sujets dans la requête
#         for subject, keywords in subject_keywords.items():
#             if any(keyword in query_lower for keyword in keywords):
#                 subjects.append(subject)
#
#         # Si aucun sujet n'est détecté, on ajoute les statistiques par défaut
#         if not subjects:
#             subjects.append("statistiques")
#
#         # Si l'utilisateur demande des informations personnelles
#         if user and any(term in query_lower for term in ["mon", "ma", "mes", "je", "j'ai", "moi"]):
#             subjects.append("personnel")
#
#         # Statistiques générales
#         if "statistiques" in subjects:
#             context["statistiques_generales"] = {
#                 "utilisateurs": {
#                     "total": TblUser.objects.count(),
#                     "coiffeuses": TblCoiffeuse.objects.count(),
#                     "clients": TblClient.objects.count(),
#                     "actifs": TblUser.objects.filter(is_active=True).count(),
#                 },
#                 "salons": {
#                     "total": TblSalon.objects.count()
#                 },
#                 "services": {
#                     "total": TblService.objects.count(),
#                     "prix_moyen": float(TblServicePrix.objects.annotate(
#                         prix_service=Sum('prix__prix')
#                     ).aggregate(Avg('prix_service'))['prix_service__avg'] or 0)
#                 },
#                 "rendez_vous": {
#                     "total": TblRendezVous.objects.count(),
#                     "en_attente": TblRendezVous.objects.filter(statut='en attente').count(),
#                     "confirmés": TblRendezVous.objects.filter(statut='confirmé').count(),
#                     "annulés": TblRendezVous.objects.filter(statut='annulé').count(),
#                     "terminés": TblRendezVous.objects.filter(statut='terminé').count(),
#                 },
#                 "avis": {
#                     "total": TblAvis.objects.count(),
#                     "note_moyenne": float(TblAvis.objects.aggregate(Avg('note'))['note__avg'] or 0),
#                 }
#             }
#
#         # Informations sur les utilisateurs
#         if "utilisateurs" in subjects:
#             # Répartition par type
#             context["utilisateurs"] = {
#                 "total": TblUser.objects.count(),
#                 "par_type": {
#                     "coiffeuses": TblUser.objects.filter(type='coiffeuse').count(),
#                     "clients": TblUser.objects.filter(type='client').count(),
#                 },
#                 "par_genre": {
#                     "hommes": TblUser.objects.filter(sexe='homme').count(),
#                     "femmes": TblUser.objects.filter(sexe='femme').count(),
#                     "autres": TblUser.objects.filter(sexe='autre').count(),
#                 },
#                 "actifs": TblUser.objects.filter(is_active=True).count(),
#                 "inactifs": TblUser.objects.filter(is_active=False).count(),
#                 "nouveaux_30_jours": TblUser.objects.filter(
#                     date_naissance__gte=datetime.now() - timedelta(days=30)
#                 ).count(),
#             }
#
#             # Informations sur les clients
#             clients_avec_rdv = TblClient.objects.annotate(
#                 nb_rdv=Count('rendez_vous')
#             ).filter(nb_rdv__gt=0).count()
#
#             context["utilisateurs"]["clients_details"] = {
#                 "avec_rdv": clients_avec_rdv,
#                 "sans_rdv": TblClient.objects.count() - clients_avec_rdv,
#                 "avec_favoris": TblClient.objects.filter(
#                     idTblUser__favorites__isnull=False
#                 ).distinct().count()
#             }
#
#         # Informations sur les coiffeuses
#         if "coiffeuses" in subjects:
#             coiffeuses_avec_salon = TblCoiffeuse.objects.filter(salon__isnull=False).count()
#
#             context["coiffeuses"] = {
#                 "total": TblCoiffeuse.objects.count(),
#                 "avec_salon": coiffeuses_avec_salon,
#                 "sans_salon": TblCoiffeuse.objects.count() - coiffeuses_avec_salon,
#                 "top_coiffeuses": []
#             }
#
#             # Top coiffeuses (par nombre de rendez-vous)
#             top_coiffeuses = TblCoiffeuse.objects.annotate(
#                 nb_rdv=Count('rendez_vous')
#             ).order_by('-nb_rdv')[:5]
#
#             for coiffeuse in top_coiffeuses:
#                 try:
#                     salon = TblSalon.objects.filter(coiffeuse=coiffeuse).first()
#                     note_moyenne = 0
#                     if salon:
#                         note_moyenne = TblAvis.objects.filter(salon=salon).aggregate(Avg('note'))['note__avg'] or 0
#
#                     context["coiffeuses"]["top_coiffeuses"].append({
#                         "nom": f"{coiffeuse.idTblUser.prenom} {coiffeuse.idTblUser.nom}",
#                         "nombre_rdv": coiffeuse.nb_rdv,
#                         "salon": salon.nom_salon if salon else "Pas de salon",
#                         "note": float(note_moyenne)
#                     })
#                 except Exception as e:
#                     logger.error(f"Erreur lors de la récupération des données coiffeuse: {str(e)}")
#
#         # Informations sur les salons
#         if "salons" in subjects:
#             # Top des salons par note moyenne
#             top_salons = TblSalon.objects.annotate(
#                 note_moyenne=Avg('avis__note'),
#                 nb_avis=Count('avis')
#             ).order_by('-note_moyenne')[:5]
#
#             salons_data = []
#             for salon in top_salons:
#                 if not salon.note_moyenne:
#                     continue
#
#                 try:
#                     nb_services = salon.services.count()
#                     salons_data.append({
#                         "nom": salon.nom_salon,
#                         "coiffeuse": f"{salon.coiffeuse.idTblUser.prenom} {salon.coiffeuse.idTblUser.nom}",
#                         "note": float(salon.note_moyenne),
#                         "nombre_avis": salon.nb_avis,
#                         "nombre_services": nb_services
#                     })
#                 except Exception as e:
#                     logger.error(f"Erreur lors de la récupération des données salon: {str(e)}")
#
#             context["salons"] = {
#                 "total": TblSalon.objects.count(),
#                 "avec_avis": TblSalon.objects.annotate(nb_avis=Count('avis')).filter(nb_avis__gt=0).count(),
#                 "top_salons": salons_data
#             }
#
#         # Informations sur les services
#         if "services" in subjects:
#             # Services les plus populaires (par nombre de rendez-vous)
#             top_services = TblService.objects.annotate(
#                 nb_rdv=Count('rendez_vous_services')
#             ).order_by('-nb_rdv')[:10]
#
#             services_data = []
#             for service in top_services:
#                 try:
#                     prix_obj = TblServicePrix.objects.filter(service=service).first()
#                     prix = prix_obj.prix.prix if prix_obj and hasattr(prix_obj, 'prix') else 0
#
#                     # Durée moyenne du service
#                     temps_obj = TblServiceTemps.objects.filter(service=service).first()
#                     duree = temps_obj.temps.minutes if temps_obj and hasattr(temps_obj, 'temps') else 0
#
#                     services_data.append({
#                         "nom": service.intitule_service,
#                         "description": service.description[:50] + "..." if len(
#                             service.description) > 50 else service.description,
#                         "prix": float(prix),
#                         "duree_minutes": duree,
#                         "utilisations": service.nb_rdv
#                     })
#                 except Exception as e:
#                     logger.error(f"Erreur lors de la récupération des données service: {str(e)}")
#
#             context["services"] = {
#                 "total": TblService.objects.count(),
#                 "prix_moyen": float(TblPrix.objects.aggregate(Avg('prix'))['prix__avg'] or 0),
#                 "top_services": services_data
#             }
#
#         # Informations sur les rendez-vous
#         if "rendez_vous" in subjects:
#             # Statistiques générales
#             context["rendez_vous"] = {
#                 "total": TblRendezVous.objects.count(),
#                 "par_statut": {
#                     "en_attente": TblRendezVous.objects.filter(statut='en attente').count(),
#                     "confirmés": TblRendezVous.objects.filter(statut='confirmé').count(),
#                     "annulés": TblRendezVous.objects.filter(statut='annulé').count(),
#                     "terminés": TblRendezVous.objects.filter(statut='terminé').count()
#                 },
#                 "prix_moyen": float(TblRendezVous.objects.filter(
#                     total_prix__isnull=False
#                 ).aggregate(Avg('total_prix'))['total_prix__avg'] or 0),
#                 "duree_moyenne": TblRendezVous.objects.filter(
#                     duree_totale__isnull=False
#                 ).aggregate(Avg('duree_totale'))['duree_totale__avg'] or 0,
#                 "recents": {
#                     "30_jours": TblRendezVous.objects.filter(
#                         date_heure__gte=datetime.now() - timedelta(days=30)
#                     ).count(),
#                     "7_jours": TblRendezVous.objects.filter(
#                         date_heure__gte=datetime.now() - timedelta(days=7)
#                     ).count()
#                 },
#                 "a_venir": TblRendezVous.objects.filter(
#                     date_heure__gt=datetime.now()
#                 ).count()
#             }
#
#         # Informations sur les paiements
#         if "paiements" in subjects:
#             paiements = TblPaiement.objects.all()
#
#             context["paiements"] = {
#                 "total": paiements.count(),
#                 "montant_total": float(paiements.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0),
#                 "montant_moyen": float(paiements.aggregate(Avg('montant_paye'))['montant_paye__avg'] or 0),
#                 "par_methode": {}
#             }
#
#             # Répartition par méthode de paiement
#             methodes = TblMethodePaiement.objects.all()
#             for methode in methodes:
#                 count = paiements.filter(methode=methode).count()
#                 if count > 0:
#                     context["paiements"]["par_methode"][methode.libelle] = count
#
#         # Informations sur les avis
#         if "avis" in subjects:
#             avis = TblAvis.objects.all()
#
#             context["avis"] = {
#                 "total": avis.count(),
#                 "note_moyenne": float(avis.aggregate(Avg('note'))['note__avg'] or 0),
#                 "repartition": {
#                     "5_etoiles": avis.filter(note=5).count(),
#                     "4_etoiles": avis.filter(note=4).count(),
#                     "3_etoiles": avis.filter(note=3).count(),
#                     "2_etoiles": avis.filter(note=2).count(),
#                     "1_etoile": avis.filter(note=1).count()
#                 }
#             }
#
#         # Informations sur les promotions
#         if "promotions" in subjects:
#             promos = TblPromotion.objects.all()
#             now_date = datetime.now()
#
#             context["promotions"] = {
#                 "total": promos.count(),
#                 "actives": promos.filter(start_date__lte=now_date, end_date__gte=now_date).count(),
#                 "futures": promos.filter(start_date__gt=now_date).count(),
#                 "expirees": promos.filter(end_date__lt=now_date).count(),
#                 "reduction_moyenne": float(
#                     promos.aggregate(Avg('discount_percentage'))['discount_percentage__avg'] or 0)
#             }
#
#         # Informations de localisation
#         if "localisation" in subjects:
#             context["localisation"] = {
#                 "communes": TblLocalite.objects.count(),
#                 "top_communes": []
#             }
#
#             # Top communes par nombre d'utilisateurs
#             top_communes = TblLocalite.objects.annotate(
#                 nb_users=Count('rues__adresses__utilisateurs')
#             ).order_by('-nb_users')[:5]
#
#             for commune in top_communes:
#                 if commune.nb_users > 0:
#                     context["localisation"]["top_communes"].append({
#                         "nom": commune.commune,
#                         "code_postal": commune.code_postal,
#                         "nombre_utilisateurs": commune.nb_users
#                     })
#
#         # Informations personnelles de l'utilisateur
#         if "personnel" in subjects and user:
#             context["personnel"] = {
#                 "profil": {
#                     "id": user.idTblUser,
#                     "nom": user.nom,
#                     "prenom": user.prenom,
#                     "email": user.email,
#                     "type": user.type,
#                     "role": user.role.nom if hasattr(user, 'role') and user.role else "Utilisateur",
#                     "est_actif": user.is_active
#                 }
#             }
#
#             # Informations spécifiques au client
#             if user.type == 'client':
#                 try:
#                     client = TblClient.objects.filter(idTblUser=user).first()
#                     if client:
#                         rdvs = TblRendezVous.objects.filter(client=client)
#
#                         context["personnel"]["rendez_vous"] = {
#                             "total": rdvs.count(),
#                             "en_attente": rdvs.filter(statut='en attente').count(),
#                             "confirmes": rdvs.filter(statut='confirmé').count(),
#                             "annules": rdvs.filter(statut='annulé').count(),
#                             "termines": rdvs.filter(statut='terminé').count(),
#                             "a_venir": rdvs.filter(date_heure__gt=datetime.now()).count()
#                         }
#
#                         # Favoris
#                         favoris = TblFavorite.objects.filter(user=user)
#                         if favoris.exists():
#                             context["personnel"]["favoris"] = []
#                             for fav in favoris:
#                                 context["personnel"]["favoris"].append({
#                                     "salon": fav.salon.nom_salon,
#                                     "coiffeuse": f"{fav.salon.coiffeuse.idTblUser.prenom} {fav.salon.coiffeuse.idTblUser.nom}"
#                                 })
#
#                         # Panier
#                         try:
#                             panier = TblCart.objects.filter(user=user).first()
#                             if panier:
#                                 items = TblCartItem.objects.filter(cart=panier)
#                                 if items.exists():
#                                     context["personnel"]["panier"] = {
#                                         "nombre_articles": items.count(),
#                                         "total": float(panier.total_price()),
#                                         "articles": []
#                                     }
#
#                                     for item in items:
#                                         context["personnel"]["panier"]["articles"].append({
#                                             "service": item.service.intitule_service,
#                                             "quantite": item.quantity,
#                                             "prix_unitaire": float(item.service.service_prix.first().prix.prix),
#                                             "total": float(item.total_price())
#                                         })
#                         except Exception as e:
#                             logger.error(f"Erreur lors de la récupération du panier: {str(e)}")
#                 except Exception as e:
#                     logger.error(f"Erreur lors de la récupération des données client: {str(e)}")
#
#             # Informations spécifiques à la coiffeuse
#             elif user.type == 'coiffeuse':
#                 try:
#                     coiffeuse = TblCoiffeuse.objects.filter(idTblUser=user).first()
#                     if coiffeuse:
#                         # Salon
#                         salon = TblSalon.objects.filter(coiffeuse=coiffeuse).first()
#                         if salon:
#                             context["personnel"]["salon"] = {
#                                 "id": salon.idTblSalon,
#                                 "nom": salon.nom_salon,
#                                 "slogan": salon.slogan,
#                                 "description": salon.a_propos,
#                                 "nombre_services": salon.services.count(),
#                                 "nombre_images": TblSalonImage.objects.filter(salon=salon).count(),
#                                 "evaluation": {
#                                     "nombre_avis": TblAvis.objects.filter(salon=salon).count(),
#                                     "note_moyenne": float(
#                                         TblAvis.objects.filter(salon=salon).aggregate(Avg('note'))['note__avg'] or 0)
#                                 }
#                             }
#
#                             # Services du salon
#                             services = salon.services.all()
#                             if services.exists():
#                                 context["personnel"]["salon"]["services"] = []
#                                 for service in services:
#                                     prix_obj = TblServicePrix.objects.filter(service=service).first()
#                                     prix = prix_obj.prix.prix if prix_obj and hasattr(prix_obj, 'prix') else 0
#
#                                     context["personnel"]["salon"]["services"].append({
#                                         "nom": service.intitule_service,
#                                         "prix": float(prix),
#                                         "utilisations": TblRendezVousService.objects.filter(
#                                             service=service,
#                                             rendez_vous__coiffeuse=coiffeuse
#                                         ).count()
#                                     })
#
#                         # Rendez-vous
#                         rdvs = TblRendezVous.objects.filter(coiffeuse=coiffeuse)
#                         if rdvs.exists():
#                             context["personnel"]["rendez_vous"] = {
#                                 "total": rdvs.count(),
#                                 "en_attente": rdvs.filter(statut='en attente').count(),
#                                 "confirmes": rdvs.filter(statut='confirmé').count(),
#                                 "annules": rdvs.filter(statut='annulé').count(),
#                                 "termines": rdvs.filter(statut='terminé').count(),
#                                 "a_venir": rdvs.filter(date_heure__gt=datetime.now()).count(),
#                                 "recents": rdvs.filter(date_heure__gte=datetime.now() - timedelta(days=30)).count()
#                             }
#
#                         # Horaires
#                         horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse=coiffeuse)
#                         if horaires.exists():
#                             context["personnel"]["horaires"] = []
#                             jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
#                             for horaire in horaires:
#                                 context["personnel"]["horaires"].append({
#                                     "jour": jours[horaire.jour],
#                                     "debut": str(horaire.heure_debut),
#                                     "fin": str(horaire.heure_fin)
#                                 })
#
#                         # Indisponibilités
#                         indispos = TblIndisponibilite.objects.filter(
#                             coiffeuse=coiffeuse,
#                             date__gte=datetime.now().date()
#                         )
#                         if indispos.exists():
#                             context["personnel"]["indisponibilites"] = []
#                             for indispo in indispos:
#                                 context["personnel"]["indisponibilites"].append({
#                                     "date": str(indispo.date),
#                                     "debut": str(indispo.heure_debut),
#                                     "fin": str(indispo.heure_fin),
#                                     "motif": indispo.motif
#                                 })
#                 except Exception as e:
#                     logger.error(f"Erreur lors de la récupération des données coiffeuse: {str(e)}")
#
#     except Exception as e:
#         logger.error(f"Erreur globale dans get_database_context_for_query: {str(e)}")
#         context['error'] = f"Erreur lors de l'extraction des données: {str(e)}"
#
#     return context