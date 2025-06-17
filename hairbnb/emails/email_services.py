################################################################################
#                                                                              #
#                 SERVICE DE GESTION D'EMAILS (HAIRBNB)                        #
#                                                                              #
#  Ce fichier définit la classe `EmailService`, qui centralise toute la        #
#  logique de création, de stockage et d'envoi des emails transactionnels      #
#  de l'application (confirmation de RDV, annulation, etc.).                   #
#                                                                              #
#  Principales responsabilités :                                               #
#    - Créer des notifications d'email et les sauvegarder en base de données   #
#      pour le suivi.                                                          #
#    - Utiliser le moteur de templates de Django pour générer le contenu       #
#      HTML et le sujet des emails.                                            #
#    - Gérer l'envoi effectif des emails.                                      #
#    - Mettre à jour le statut des notifications (en attente, envoyé, échec).  #
#    - Fournir des méthodes de haut niveau pour les cas d'usage courants.      #
#                                                                              #
################################################################################

# --- Importations ---
import logging
import traceback
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.db import transaction

# Importation des modèles de la base de données
from ..models import TblEmailNotification, TblEmailType, TblEmailStatus

# Initialisation du logger pour ce module
logger = logging.getLogger(__name__)


class EmailService:
    """
    Classe de service encapsulant toute la logique d'envoi d'emails.
    """

    @classmethod
    def get_email_type(cls, code):
        """
        Récupère une instance de TblEmailType par son code.
        Si le type n'existe pas, il est créé automatiquement.
        """
        logger.info(f"Recherche du type d'email avec code: {code}")
        try:
            email_type = TblEmailType.objects.get(code=code)
            logger.info(f"Type d'email trouvé: {email_type.idTblEmailType}")
            return email_type
        except TblEmailType.DoesNotExist:
            logger.error(f"Type d'email avec code '{code}' non trouvé dans la base de données")
            # Crée dynamiquement le type s'il manque, pour la robustesse.
            email_type = TblEmailType.objects.create(code=code, libelle=code.replace('_', ' ').title())
            logger.info(f"Type d'email créé automatiquement: {email_type.idTblEmailType}")
            return email_type
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du type d'email: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @classmethod
    def get_email_status(cls, code):
        """
        Récupère une instance de TblEmailStatus par son code.
        Si le statut n'existe pas, il est créé automatiquement.
        """
        logger.info(f"Recherche du statut d'email avec code: {code}")
        try:
            email_status = TblEmailStatus.objects.get(code=code)
            logger.info(f"Statut d'email trouvé: {email_status.idTblEmailStatus}")
            return email_status
        except TblEmailStatus.DoesNotExist:
            logger.error(f"Statut d'email avec code '{code}' non trouvé dans la base de données")
            # Crée dynamiquement le statut s'il manque.
            email_status = TblEmailStatus.objects.create(code=code, libelle=code.replace('_', ' ').title())
            logger.info(f"Statut d'email créé automatiquement: {email_status.idTblEmailStatus}")
            return email_status
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut d'email: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @classmethod
    @transaction.atomic
    def create_notification(cls, destinataire, type_email_code, salon=None, rendez_vous=None):
        """
        Crée une nouvelle entrée de notification d'email dans la base de données,
        prête à être envoyée. L'opération est atomique.
        """
        logger.info(
            f"Création d'une notification email: type={type_email_code}, destinataire={destinataire.email if destinataire else 'None'}")
        try:
            # Récupère les objets Type et Statut nécessaires.
            type_email = cls.get_email_type(type_email_code)
            statut_en_attente = cls.get_email_status('en_attente')

            if not destinataire:
                logger.error("Destinataire non fourni pour la création de notification")
                raise ValueError("Destinataire non fourni")

            logger.info(
                f"Contexte de création - Destinataire: {destinataire.prenom} {destinataire.nom}, Email: {destinataire.email}")
            if salon: logger.info(f"Salon: {salon.nom_salon}")
            if rendez_vous: logger.info(f"Rendez-vous: {rendez_vous.idRendezVous}, statut: {rendez_vous.statut}")

            # --- Génération du sujet de l'email à partir d'un template ---
            template_prefix = f"emails/{type_email_code}"
            template_subject_path = f"{template_prefix}_subject.txt"
            logger.info(f"Vérification du template: {template_subject_path}")
            from django.template.loader import get_template
            try:
                # Vérifie si le template de sujet existe.
                template = get_template(template_subject_path)
                logger.info(f"Template sujet trouvé: {template.origin.name}")

                # Prépare le contexte avec les variables pour le template.
                context = {'prenom': destinataire.prenom, 'nom': destinataire.nom}
                if salon: context['salon_nom'] = salon.nom_salon
                if rendez_vous:
                    context['date_heure'] = rendez_vous.date_heure
                    context['statut'] = rendez_vous.statut

                # Génère le sujet final.
                sujet = render_to_string(template_subject_path, context).strip()
                logger.info(f"Sujet généré: {sujet}")

            except Exception as template_error:
                # Si le template n'est pas trouvé ou qu'une erreur survient, utilise un sujet par défaut.
                logger.error(f"Template sujet non trouvé ou erreur: {template_subject_path} - {str(template_error)}")
                sujet = f"Notification {type_email_code.replace('_', ' ')}"
                logger.info(f"Utilisation d'un sujet par défaut: {sujet}")

            # Crée l'enregistrement en base de données.
            notification = TblEmailNotification.objects.create(
                destinataire=destinataire, salon=salon, rendez_vous=rendez_vous,
                type_email=type_email, statut=statut_en_attente, sujet=sujet,
                contenu=""
            )
            logger.info(f"Notification créée avec succès: ID={notification.idTblEmailNotification}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @classmethod
    def send_notification(cls, notification_id):
        """
        Envoie une notification email qui a déjà été créée dans la base de données.
        Gère la génération du contenu HTML, l'envoi effectif et la mise à jour des statuts.
        """
        logger.info(f"====== DÉBUT D'ENVOI D'EMAIL (ID: {notification_id}) ======")
        notification, statut_envoye, statut_echec = None, None, None
        try:
            # Récupère la notification à envoyer et les statuts possibles.
            logger.info(f"Récupération de la notification: {notification_id}")
            notification = TblEmailNotification.objects.get(idTblEmailNotification=notification_id)
            logger.info(f"Notification récupérée: destinataire={notification.destinataire.email}")
            statut_envoye = cls.get_email_status('envoye')
            statut_echec = cls.get_email_status('echec')

            # Log des informations de configuration pour le débogage.
            logger.info(
                f"Configuration email: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}")
            logger.info(f"FROM_EMAIL={settings.DEFAULT_FROM_EMAIL}")

            # --- Préparation du contexte pour le template HTML ---
            logger.info("Préparation du contexte pour le template")
            context = {'prenom': notification.destinataire.prenom, 'nom': notification.destinataire.nom}
            if notification.salon:
                context['salon_nom'] = notification.salon.nom_salon
                logger.info(f"Salon ajouté au contexte: {notification.salon.nom_salon}")
            if notification.rendez_vous:
                context['date_heure'] = notification.rendez_vous.date_heure
                context['statut'] = notification.rendez_vous.statut
                logger.info(
                    f"Rendez-vous ajouté au contexte: date={notification.rendez_vous.date_heure}, statut={notification.rendez_vous.statut}")

                # Ajoute les détails des services du rendez-vous au contexte.
                try:
                    services = [{'nom': rdv_service.service.intitule_service, 'prix': rdv_service.prix_applique,
                                 'duree': rdv_service.duree_estimee} for rdv_service in
                                notification.rendez_vous.rendez_vous_services.all()]
                    if services:
                        context['services'], context['total_prix'], context[
                            'duree_totale'] = services, notification.rendez_vous.total_prix, notification.rendez_vous.duree_totale
                        logger.info(f"Services ajoutés au contexte: {len(services)} services")
                except Exception as services_error:
                    logger.error(f"Erreur lors de la récupération des services: {str(services_error)}")

            # --- Génération du contenu HTML de l'email ---
            template_prefix = f"emails/{notification.type_email.code}"
            template_body_path = f"{template_prefix}_body.html"
            logger.info(f"Vérification du template HTML: {template_body_path}")
            from django.template.loader import get_template
            try:
                template = get_template(template_body_path)
                logger.info(f"Template HTML trouvé: {template.origin.name}")
                contenu_html = render_to_string(template_body_path, context)
                logger.info(f"Contenu HTML généré, taille: {len(contenu_html)} caractères")
            except Exception as template_error:
                # Si le template n'est pas trouvé, un contenu par défaut est généré.
                logger.error(f"Template HTML non trouvé ou erreur: {template_body_path} - {str(template_error)}")
                contenu_html = f"<html><body><h1>Notification</h1><p>Bonjour {context.get('prenom', '')} {context.get('nom', '')},</p><p>Ceci est une notification automatique.</p></body></html>"
                logger.info("Utilisation d'un contenu HTML par défaut")

            # Sauvegarde le contenu HTML généré dans la base de données.
            try:
                notification.contenu = contenu_html
                notification.save(update_fields=['contenu'])
                logger.info("Contenu HTML sauvegardé dans la base de données")
            except Exception as save_error:
                logger.error(f"Erreur lors de la sauvegarde du contenu: {str(save_error)}")

            # --- Préparation et envoi de l'email ---
            logger.info(f"Préparation de l'email à: {notification.destinataire.email}")
            email = EmailMultiAlternatives(subject=notification.sujet, body="", from_email=settings.DEFAULT_FROM_EMAIL,
                                           to=[notification.destinataire.email])
            email.attach_alternative(contenu_html, "text/html")
            logger.info("Contenu HTML attaché à l'email")

            logger.info("Tentative d'envoi de l'email...")
            try:
                email.send(fail_silently=False)
                logger.info("Email envoyé avec succès!")
            except Exception as send_error:
                logger.error(f"Erreur lors de l'envoi de l'email: {str(send_error)}")
                logger.error(traceback.format_exc())
                raise

            # --- Mise à jour du statut après envoi réussi ---
            try:
                notification.statut, notification.date_envoi = statut_envoye, timezone.now()
                notification.save(update_fields=['statut', 'date_envoi'])
                logger.info("Statut et date d'envoi mis à jour dans la base de données")
            except Exception as update_error:
                logger.error(f"Erreur lors de la mise à jour du statut: {str(update_error)}")

            logger.info(f"====== FIN D'ENVOI D'EMAIL (ID: {notification_id}) - SUCCÈS ======")
            return True
        except Exception as e:
            logger.error(f"====== ERREUR GLOBALE LORS DE L'ENVOI DE L'EMAIL {notification_id}: {str(e)} ======")
            logger.error(traceback.format_exc())

            # --- Mise à jour du statut en cas d'échec global ---
            if notification and statut_echec:
                try:
                    notification.tentatives = notification.tentatives + 1 if notification.tentatives else 1
                    notification.statut = statut_echec
                    notification.save(update_fields=['statut', 'tentatives'])
                    logger.info(f"Statut mis à jour en 'échec', tentatives: {notification.tentatives}")
                except Exception as inner_e:
                    logger.error(f"Erreur lors de la mise à jour du statut en échec: {str(inner_e)}")
            return False

    # --- Méthodes de haut niveau pour les cas d'usage courants ---
    @classmethod
    def send_rdv_confirmation(cls, rendez_vous):
        """
        Méthode de commodité pour créer et envoyer un email de confirmation de RDV.
        """
        logger.info(f"Demande d'envoi d'email de confirmation pour RDV ID: {rendez_vous.idRendezVous}")
        client, salon = rendez_vous.client.idTblUser, rendez_vous.salon
        logger.info(f"Client: {client.prenom} {client.nom}, Salon: {salon.nom_salon}")
        try:
            notification = cls.create_notification(destinataire=client, type_email_code='confirmation_rdv', salon=salon,
                                                   rendez_vous=rendez_vous)
            logger.info(f"Notification de confirmation créée: {notification.idTblEmailNotification}")
            success = cls.send_notification(notification.idTblEmailNotification)
            logger.info(f"Résultat de l'envoi de confirmation: {'Succès' if success else 'Échec'}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors du processus de confirmation de RDV: {str(e)}")
            raise

    @classmethod
    def send_rdv_modification(cls, rendez_vous):
        """
        Méthode de commodité pour créer et envoyer un email de modification de RDV.
        """
        logger.info(f"Demande d'envoi d'email de modification pour RDV ID: {rendez_vous.idRendezVous}")
        client, salon = rendez_vous.client.idTblUser, rendez_vous.salon
        logger.info(f"Client: {client.prenom} {client.nom}, Salon: {salon.nom_salon}")
        try:
            notification = cls.create_notification(destinataire=client, type_email_code='modification_rdv', salon=salon,
                                                   rendez_vous=rendez_vous)
            logger.info(f"Notification de modification créée: {notification.idTblEmailNotification}")
            success = cls.send_notification(notification.idTblEmailNotification)
            logger.info(f"Résultat de l'envoi de modification: {'Succès' if success else 'Échec'}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors du processus de modification de RDV: {str(e)}")
            raise

    @classmethod
    def send_rdv_annulation(cls, rendez_vous):
        """
        Méthode de commodité pour créer et envoyer un email d'annulation de RDV.
        """
        logger.info(f"Demande d'envoi d'email d'annulation pour RDV ID: {rendez_vous.idRendezVous}")
        client, salon = rendez_vous.client.idTblUser, rendez_vous.salon
        logger.info(f"Client: {client.prenom} {client.nom}, Salon: {salon.nom_salon}")
        try:
            notification = cls.create_notification(destinataire=client, type_email_code='annulation_rdv', salon=salon,
                                                   rendez_vous=rendez_vous)
            logger.info(f"Notification d'annulation créée: {notification.idTblEmailNotification}")
            success = cls.send_notification(notification.idTblEmailNotification)
            logger.info(f"Résultat de l'envoi d'annulation: {'Succès' if success else 'Échec'}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors du processus d'annulation de RDV: {str(e)}")
            raise







# # Fichier: services/email_service.py
#
# import logging
# import traceback
# from django.core.mail import EmailMultiAlternatives
# from django.template.loader import render_to_string
# from django.utils import timezone
# from django.conf import settings
# from django.db import transaction
#
# from ..models import TblEmailNotification, TblEmailType, TblEmailStatus
#
# # Configuration du logger
# logger = logging.getLogger(__name__)
#
#
# class EmailService:
#     """
#     Service responsable de la création et de l'envoi d'emails de notification.
#     Gère le stockage des emails envoyés dans la base de données.
#     """
#
#     @classmethod
#     def get_email_type(cls, code):
#         """Récupère un type d'email à partir de son code."""
#         logger.info(f"Recherche du type d'email avec code: {code}")
#         try:
#             email_type = TblEmailType.objects.get(code=code)
#             logger.info(f"Type d'email trouvé: {email_type.idTblEmailType}")
#             return email_type
#         except TblEmailType.DoesNotExist:
#             logger.error(f"Type d'email avec code '{code}' non trouvé dans la base de données")
#             # Créer le type d'email si non existant (solution de contournement)
#             email_type = TblEmailType.objects.create(
#                 code=code,
#                 libelle=code.replace('_', ' ').title()
#             )
#             logger.info(f"Type d'email créé automatiquement: {email_type.idTblEmailType}")
#             return email_type
#         except Exception as e:
#             logger.error(f"Erreur lors de la récupération du type d'email: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise
#
#     @classmethod
#     def get_email_status(cls, code):
#         """Récupère un statut d'email à partir de son code."""
#         logger.info(f"Recherche du statut d'email avec code: {code}")
#         try:
#             email_status = TblEmailStatus.objects.get(code=code)
#             logger.info(f"Statut d'email trouvé: {email_status.idTblEmailStatus}")
#             return email_status
#         except TblEmailStatus.DoesNotExist:
#             logger.error(f"Statut d'email avec code '{code}' non trouvé dans la base de données")
#             # Créer le statut d'email si non existant (solution de contournement)
#             email_status = TblEmailStatus.objects.create(
#                 code=code,
#                 libelle=code.replace('_', ' ').title()
#             )
#             logger.info(f"Statut d'email créé automatiquement: {email_status.idTblEmailStatus}")
#             return email_status
#         except Exception as e:
#             logger.error(f"Erreur lors de la récupération du statut d'email: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise
#
#     @classmethod
#     @transaction.atomic
#     def create_notification(cls, destinataire, type_email_code, salon=None, rendez_vous=None):
#         """
#         Crée une nouvelle notification email dans la base de données.
#
#         Args:
#             destinataire: Instance de TblUser (le destinataire)
#             type_email_code: Code du type d'email (ex: 'confirmation_rdv')
#             salon: Instance de TblSalon (optionnel)
#             rendez_vous: Instance de TblRendezVous (optionnel)
#
#         Returns:
#             TblEmailNotification: L'instance créée
#         """
#         logger.info(
#             f"Création d'une notification email: type={type_email_code}, destinataire={destinataire.email if destinataire else 'None'}")
#
#         try:
#             # Récupération des objets pour les clés étrangères
#             type_email = cls.get_email_type(type_email_code)
#             statut_en_attente = cls.get_email_status('en_attente')
#
#             # Vérification des données requises
#             if not destinataire:
#                 logger.error("Destinataire non fourni pour la création de notification")
#                 raise ValueError("Destinataire non fourni")
#
#             # Informations sur le contexte
#             logger.info(
#                 f"Contexte de création - Destinataire: {destinataire.prenom} {destinataire.nom}, Email: {destinataire.email}")
#             if salon:
#                 logger.info(f"Salon: {salon.nom_salon}")
#             if rendez_vous:
#                 logger.info(f"Rendez-vous: {rendez_vous.idRendezVous}, statut: {rendez_vous.statut}")
#
#             # Génération du sujet à partir du template
#             template_prefix = f"emails/{type_email_code}"
#             template_subject_path = f"{template_prefix}_subject.txt"
#
#             # Vérification de l'existence du template
#             logger.info(f"Vérification du template: {template_subject_path}")
#             from django.template.loader import get_template
#             try:
#                 template = get_template(template_subject_path)
#                 logger.info(f"Template sujet trouvé: {template.origin.name}")
#             except Exception as template_error:
#                 logger.error(f"Template sujet non trouvé: {template_subject_path}")
#                 logger.error(str(template_error))
#                 # Utiliser un sujet par défaut si le template n'existe pas
#                 sujet = f"Notification {type_email_code.replace('_', ' ')}"
#                 logger.info(f"Utilisation d'un sujet par défaut: {sujet}")
#             else:
#                 # Préparation du contexte pour le template
#                 context = {
#                     'prenom': destinataire.prenom,
#                     'nom': destinataire.nom,
#                 }
#
#                 if salon:
#                     context['salon_nom'] = salon.nom_salon
#
#                 if rendez_vous:
#                     context['date_heure'] = rendez_vous.date_heure
#                     context['statut'] = rendez_vous.statut
#
#                 # Génération du sujet
#                 try:
#                     sujet = render_to_string(template_subject_path, context).strip()
#                     logger.info(f"Sujet généré: {sujet}")
#                 except Exception as render_error:
#                     logger.error(f"Erreur lors de la génération du sujet: {str(render_error)}")
#                     sujet = f"Notification {type_email_code.replace('_', ' ')}"
#                     logger.info(f"Utilisation d'un sujet par défaut: {sujet}")
#
#             # Création de l'entrée dans la base de données
#             notification = TblEmailNotification.objects.create(
#                 destinataire=destinataire,
#                 salon=salon,
#                 rendez_vous=rendez_vous,
#                 type_email=type_email,
#                 statut=statut_en_attente,
#                 sujet=sujet,
#                 contenu="",  # Le contenu sera généré lors de l'envoi
#             )
#
#             logger.info(f"Notification créée avec succès: ID={notification.idTblEmailNotification}")
#             return notification
#
#         except Exception as e:
#             logger.error(f"Erreur lors de la création de la notification: {str(e)}")
#             logger.error(traceback.format_exc())
#             raise
#
#     @classmethod
#     def send_notification(cls, notification_id):
#         """
#         Envoie une notification email préalablement créée.
#
#         Args:
#             notification_id: ID de la notification à envoyer
#
#         Returns:
#             bool: True si l'envoi a réussi, False sinon
#         """
#         logger.info(f"====== DÉBUT D'ENVOI D'EMAIL (ID: {notification_id}) ======")
#
#         # Définir les variables au niveau de la fonction pour éviter les variables globales
#         notification = None
#         statut_envoye = None
#         statut_echec = None
#
#         try:
#             # Récupération de la notification
#             logger.info(f"Récupération de la notification: {notification_id}")
#             notification = TblEmailNotification.objects.get(idTblEmailNotification=notification_id)
#             logger.info(f"Notification récupérée: destinataire={notification.destinataire.email}")
#
#             # Récupération des statuts
#             statut_envoye = cls.get_email_status('envoye')
#             statut_echec = cls.get_email_status('echec')
#
#             # Vérification des configurations d'email
#             logger.info(
#                 f"Configuration email: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}, USER={settings.EMAIL_HOST_USER}")
#             logger.info(f"FROM_EMAIL={settings.DEFAULT_FROM_EMAIL}")
#
#             # Test simple d'envoi d'email
#             # logger.info("Test simple d'envoi d'email...")
#             # try:
#             #     test_email = EmailMultiAlternatives(
#             #         subject="Test d'envoi simple",
#             #         body="Ceci est un test simple",
#             #         from_email=settings.DEFAULT_FROM_EMAIL,
#             #         to=[notification.destinataire.email]
#             #     )
#             #     test_result = test_email.send(fail_silently=True)
#             #     logger.info(f"Résultat du test d'envoi simple: {test_result}")
#             # except Exception as test_error:
#             #     logger.warning(f"Test d'envoi simple échoué: {str(test_error)}")
#             #     # On continue malgré l'échec du test
#
#             # Préparation du contexte pour le template
#             logger.info("Préparation du contexte pour le template")
#             context = {
#                 'prenom': notification.destinataire.prenom,
#                 'nom': notification.destinataire.nom,
#             }
#
#             if notification.salon:
#                 context['salon_nom'] = notification.salon.nom_salon
#                 logger.info(f"Salon ajouté au contexte: {notification.salon.nom_salon}")
#
#             if notification.rendez_vous:
#                 context['date_heure'] = notification.rendez_vous.date_heure
#                 context['statut'] = notification.rendez_vous.statut
#                 logger.info(
#                     f"Rendez-vous ajouté au contexte: date={notification.rendez_vous.date_heure}, statut={notification.rendez_vous.statut}")
#
#                 # Ajout des services du rendez-vous si disponibles
#                 services = []
#                 try:
#                     for rdv_service in notification.rendez_vous.rendez_vous_services.all():
#                         services.append({
#                             'nom': rdv_service.service.intitule_service,
#                             'prix': rdv_service.prix_applique,
#                             'duree': rdv_service.duree_estimee
#                         })
#
#                     if services:
#                         context['services'] = services
#                         context['total_prix'] = notification.rendez_vous.total_prix
#                         context['duree_totale'] = notification.rendez_vous.duree_totale
#                         logger.info(f"Services ajoutés au contexte: {len(services)} services")
#                 except Exception as services_error:
#                     logger.error(f"Erreur lors de la récupération des services: {str(services_error)}")
#
#             # Génération du contenu HTML
#             template_prefix = f"emails/{notification.type_email.code}"
#             template_body_path = f"{template_prefix}_body.html"
#
#             # Vérification de l'existence du template
#             logger.info(f"Vérification du template HTML: {template_body_path}")
#             from django.template.loader import get_template
#             try:
#                 template = get_template(template_body_path)
#                 logger.info(f"Template HTML trouvé: {template.origin.name}")
#             except Exception as template_error:
#                 logger.error(f"Template HTML non trouvé: {template_body_path}")
#                 logger.error(str(template_error))
#                 # Créer un contenu HTML par défaut
#                 contenu_html = f"""
#                 <html>
#                 <body>
#                     <h1>Notification</h1>
#                     <p>Bonjour {context.get('prenom', '')} {context.get('nom', '')},</p>
#                     <p>Ceci est une notification automatique concernant votre rendez-vous.</p>
#                 </body>
#                 </html>
#                 """
#                 logger.info("Utilisation d'un contenu HTML par défaut")
#             else:
#                 # Génération du contenu HTML
#                 try:
#                     contenu_html = render_to_string(template_body_path, context)
#                     logger.info(f"Contenu HTML généré, taille: {len(contenu_html)} caractères")
#                 except Exception as render_error:
#                     logger.error(f"Erreur lors de la génération du contenu HTML: {str(render_error)}")
#                     # Créer un contenu HTML par défaut
#                     contenu_html = f"""
#                     <html>
#                     <body>
#                         <h1>Notification</h1>
#                         <p>Bonjour {context.get('prenom', '')} {context.get('nom', '')},</p>
#                         <p>Ceci est une notification automatique concernant votre rendez-vous.</p>
#                     </body>
#                     </html>
#                     """
#                     logger.info("Utilisation d'un contenu HTML par défaut après erreur")
#
#             # Mise à jour du contenu dans la base
#             try:
#                 notification.contenu = contenu_html
#                 notification.save(update_fields=['contenu'])
#                 logger.info("Contenu HTML sauvegardé dans la base de données")
#             except Exception as save_error:
#                 logger.error(f"Erreur lors de la sauvegarde du contenu: {str(save_error)}")
#
#             # Préparation de l'email
#             logger.info(f"Préparation de l'email à: {notification.destinataire.email}")
#             email = EmailMultiAlternatives(
#                 subject=notification.sujet,
#                 body="",  # Corps texte vide, on utilise uniquement le HTML
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[notification.destinataire.email]
#             )
#
#             # Ajout du contenu HTML
#             email.attach_alternative(contenu_html, "text/html")
#             logger.info("Contenu HTML attaché à l'email")
#
#             # Envoi de l'email
#             logger.info("Tentative d'envoi de l'email...")
#             try:
#                 email.send(fail_silently=False)
#                 logger.info("Email envoyé avec succès!")
#             except Exception as send_error:
#                 logger.error(f"Erreur lors de l'envoi de l'email: {str(send_error)}")
#                 logger.error(traceback.format_exc())
#                 raise
#
#             # Mise à jour du statut et de la date d'envoi
#             try:
#                 notification.statut = statut_envoye
#                 notification.date_envoi = timezone.now()
#                 notification.save(update_fields=['statut', 'date_envoi'])
#                 logger.info("Statut et date d'envoi mis à jour dans la base de données")
#             except Exception as update_error:
#                 logger.error(f"Erreur lors de la mise à jour du statut: {str(update_error)}")
#
#             logger.info(f"====== FIN D'ENVOI D'EMAIL (ID: {notification_id}) - SUCCÈS ======")
#             return True
#
#         except Exception as e:
#             logger.error(f"====== ERREUR GLOBALE LORS DE L'ENVOI DE L'EMAIL {notification_id}: {str(e)} ======")
#             logger.error(traceback.format_exc())
#
#             # Mise à jour du statut en échec et incrément des tentatives
#             if notification and statut_echec:
#                 try:
#                     notification.tentatives = notification.tentatives + 1 if notification.tentatives else 1
#                     notification.statut = statut_echec
#                     notification.save(update_fields=['statut', 'tentatives'])
#                     logger.info(f"Statut mis à jour en 'échec', tentatives: {notification.tentatives}")
#                 except Exception as inner_e:
#                     logger.error(f"Erreur lors de la mise à jour du statut en échec: {str(inner_e)}")
#
#             return False
#
#     @classmethod
#     def send_rdv_confirmation(cls, rendez_vous):
#         """
#         Envoie un email de confirmation de rendez-vous.
#
#         Args:
#             rendez_vous: Instance de TblRendezVous
#
#         Returns:
#             TblEmailNotification: L'instance de notification créée et envoyée
#         """
#         logger.info(f"Demande d'envoi d'email de confirmation pour RDV ID: {rendez_vous.idRendezVous}")
#
#         # Récupération des informations nécessaires
#         client = rendez_vous.client.idTblUser
#         salon = rendez_vous.salon
#
#         logger.info(f"Client: {client.prenom} {client.nom}, Salon: {salon.nom_salon}")
#
#         # Création de la notification
#         try:
#             notification = cls.create_notification(
#                 destinataire=client,
#                 type_email_code='confirmation_rdv',
#                 salon=salon,
#                 rendez_vous=rendez_vous
#             )
#             logger.info(f"Notification de confirmation créée: {notification.idTblEmailNotification}")
#         except Exception as e:
#             logger.error(f"Erreur lors de la création de la notification de confirmation: {str(e)}")
#             raise
#
#         # Envoi de la notification
#         try:
#             success = cls.send_notification(notification.idTblEmailNotification)
#             logger.info(f"Résultat de l'envoi de confirmation: {'Succès' if success else 'Échec'}")
#         except Exception as e:
#             logger.error(f"Erreur lors de l'envoi de la notification de confirmation: {str(e)}")
#             success = False
#
#         return notification
#
#     @classmethod
#     def send_rdv_modification(cls, rendez_vous):
#         """
#         Envoie un email de modification de rendez-vous.
#
#         Args:
#             rendez_vous: Instance de TblRendezVous
#
#         Returns:
#             TblEmailNotification: L'instance de notification créée et envoyée
#         """
#         logger.info(f"Demande d'envoi d'email de modification pour RDV ID: {rendez_vous.idRendezVous}")
#
#         client = rendez_vous.client.idTblUser
#         salon = rendez_vous.salon
#
#         logger.info(f"Client: {client.prenom} {client.nom}, Salon: {salon.nom_salon}")
#
#         try:
#             notification = cls.create_notification(
#                 destinataire=client,
#                 type_email_code='modification_rdv',
#                 salon=salon,
#                 rendez_vous=rendez_vous
#             )
#             logger.info(f"Notification de modification créée: {notification.idTblEmailNotification}")
#         except Exception as e:
#             logger.error(f"Erreur lors de la création de la notification de modification: {str(e)}")
#             raise
#
#         try:
#             success = cls.send_notification(notification.idTblEmailNotification)
#             logger.info(f"Résultat de l'envoi de modification: {'Succès' if success else 'Échec'}")
#         except Exception as e:
#             logger.error(f"Erreur lors de l'envoi de la notification de modification: {str(e)}")
#             success = False
#
#         return notification
#
#     @classmethod
#     def send_rdv_annulation(cls, rendez_vous):
#         """
#         Envoie un email d'annulation de rendez-vous.
#
#         Args:
#             rendez_vous: Instance de TblRendezVous
#
#         Returns:
#             TblEmailNotification: L'instance de notification créée et envoyée
#         """
#         logger.info(f"Demande d'envoi d'email d'annulation pour RDV ID: {rendez_vous.idRendezVous}")
#
#         client = rendez_vous.client.idTblUser
#         salon = rendez_vous.salon
#
#         logger.info(f"Client: {client.prenom} {client.nom}, Salon: {salon.nom_salon}")
#
#         try:
#             notification = cls.create_notification(
#                 destinataire=client,
#                 type_email_code='annulation_rdv',
#                 salon=salon,
#                 rendez_vous=rendez_vous
#             )
#             logger.info(f"Notification d'annulation créée: {notification.idTblEmailNotification}")
#         except Exception as e:
#             logger.error(f"Erreur lors de la création de la notification d'annulation: {str(e)}")
#             raise
#
#         try:
#             success = cls.send_notification(notification.idTblEmailNotification)
#             logger.info(f"Résultat de l'envoi d'annulation: {'Succès' if success else 'Échec'}")
#         except Exception as e:
#             logger.error(f"Erreur lors de l'envoi de la notification d'annulation: {str(e)}")
#             success = False
#
#         return notification