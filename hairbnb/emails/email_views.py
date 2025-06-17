################################################################################
#                                                                              #
#                 VUE DE L'API POUR LE SERVICE D'EMAILS                          #
#                                                                              #
#  Ce fichier définit la vue `EmailNotificationAPIView`, un point d'accès      #
#  (endpoint) centralisé pour déclencher l'envoi d'emails transactionnels     #
#  depuis une application cliente (ex: une application mobile Flutter).        #
#                                                                              #
#  Le processus est le suivant :                                               #
#    1. Recevoir une requête POST avec les détails de l'email à envoyer.       #
#    2. Valider les données de la requête.                                     #
#    3. Utiliser `EmailService` pour d'abord créer un enregistrement de        #
#       la notification en base de données pour le suivi.                      #
#    4. Utiliser `EmailService` pour ensuite envoyer l'email.                  #
#    5. Retourner une réponse détaillée sur le succès ou l'échec de l'opération.#
#                                                                              #
################################################################################

# --- Importations ---
import logging
import traceback

# Importations de Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Importations des modules personnalisés de l'application
from hairbnb.emails.email_services import EmailService
from hairbnb.emails.emails_serializers import EmailNotificationCreateSerializer, EmailNotificationSerializer
from hairbnb.models import TblUser, TblRendezVous

# Initialisation du logger pour ce module
logger = logging.getLogger(__name__)

class EmailNotificationAPIView(APIView):
    """
    Vue basée sur une classe pour gérer les requêtes d'envoi de notifications par email.
    """

    # Le décorateur de permissions est actuellement désactivé, rendant la vue publiquement accessible.
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Gère les requêtes POST pour créer et envoyer une notification par email.
        """
        # Log de la réception de la requête pour le suivi.
        logger.info(f"Requête de notification email reçue: {request.data}")

        # --- Étape 1 : Validation des données d'entrée ---
        # Utilise un sérialiseur pour valider la structure et les types de données de la requête.
        serializer = EmailNotificationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Données invalides: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # --- Étape 2 : Récupération des données et des objets liés ---
            data = serializer.validated_data
            to_email = data['toEmail']
            template_id = data['templateId']
            rendez_vous_id = data.get('rendezVousId')
            logger.info(f"Données validées: email={to_email}, template={template_id}, rdv_id={rendez_vous_id}")

            # Récupère l'utilisateur destinataire depuis la base de données.
            try:
                destinataire = TblUser.objects.get(email=to_email)
                logger.info(f"Destinataire trouvé: {destinataire.idTblUser}")
            except TblUser.DoesNotExist:
                logger.error(f"Utilisateur avec email {to_email} non trouvé")
                return Response({"error": f"Utilisateur avec email {to_email} non trouvé"},
                                status=status.HTTP_404_NOT_FOUND)

            # Si un ID de rendez-vous est fourni, récupère les objets RDV et Salon.
            rendez_vous = None
            salon = None
            if rendez_vous_id:
                try:
                    rendez_vous = TblRendezVous.objects.get(idRendezVous=rendez_vous_id)
                    salon = rendez_vous.salon
                    logger.info(
                        f"Rendez-vous trouvé: {rendez_vous.idRendezVous}, Salon: {salon.nom_salon if salon else 'None'}")
                except TblRendezVous.DoesNotExist:
                    logger.error(f"Rendez-vous avec ID {rendez_vous_id} non trouvé")
                    return Response({"error": f"Rendez-vous avec ID {rendez_vous_id} non trouvé"},
                                    status=status.HTTP_404_NOT_FOUND)

            # --- Étape 3 : Création de la notification en base de données ---
            # Délègue la création de l'enregistrement à EmailService.
            logger.info("Tentative de création de la notification...")
            try:
                notification = EmailService.create_notification(destinataire=destinataire, type_email_code=template_id,
                                                                salon=salon, rendez_vous=rendez_vous)
                logger.info(f"Notification créée avec succès: {notification.idTblEmailNotification}")
            except Exception as create_error:
                logger.error(f"Erreur lors de la création de la notification: {str(create_error)}")
                logger.error(traceback.format_exc())
                return Response({"error": f"Erreur lors de la création de la notification: {str(create_error)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # --- Étape 4 : Envoi de l'email ---
            # Délègue l'envoi effectif de l'email à EmailService.
            logger.info("Tentative d'envoi de l'email...")
            try:
                success = EmailService.send_notification(notification.idTblEmailNotification)
                logger.info(f"Résultat de l'envoi: {success}")
            except Exception as send_error:
                logger.error(f"Erreur lors de l'envoi de l'email: {str(send_error)}")
                logger.error(traceback.format_exc())
                return Response({"error": f"Erreur lors de l'envoi de l'email: {str(send_error)}",
                                 "notification": EmailNotificationSerializer(notification).data},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # --- Étape 5 : Construction de la réponse finale ---
            # Formate l'objet notification pour l'inclure dans la réponse.
            response_serializer = EmailNotificationSerializer(notification)
            if success:
                logger.info("Email envoyé avec succès")
                return Response({"message": "Email envoyé avec succès", "notification": response_serializer.data},
                                status=status.HTTP_200_OK)
            else:
                logger.error("Échec de l'envoi de l'email")
                return Response(
                    {"error": "Erreur lors de l'envoi de l'email", "notification": response_serializer.data},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Gestion des erreurs imprévues ---
        except Exception as e:
            logger.error(f"Exception non gérée: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# # Fichier: views.py (modifié avec des logs détaillés)
# import logging
# import traceback
#
# from rest_framework.decorators import permission_classes
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from hairbnb.emails.email_services import EmailService
# from hairbnb.emails.emails_serializers import EmailNotificationCreateSerializer, EmailNotificationSerializer
# from hairbnb.models import TblUser, TblRendezVous
#
# # Configurer le logger
# logger = logging.getLogger(__name__)
#
# class EmailNotificationAPIView(APIView):
#     """API pour envoyer des emails de notification depuis l'application mobile."""
#     #permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         """Traite les demandes d'envoi d'email."""
#         logger.info(f"Requête de notification email reçue: {request.data}")
#
#         # Validation des données d'entrée avec le serializer
#         serializer = EmailNotificationCreateSerializer(data=request.data)
#         if not serializer.is_valid():
#             logger.error(f"Données invalides: {serializer.errors}")
#             return Response(
#                 serializer.errors,
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             # Récupération des données validées
#             data = serializer.validated_data
#             to_email = data['toEmail']
#             template_id = data['templateId']
#             rendez_vous_id = data.get('rendezVousId')
#             logger.info(f"Données validées: email={to_email}, template={template_id}, rdv_id={rendez_vous_id}")
#
#             # Récupération du destinataire
#             try:
#                 destinataire = TblUser.objects.get(email=to_email)
#                 logger.info(f"Destinataire trouvé: {destinataire.idTblUser}")
#             except TblUser.DoesNotExist:
#                 logger.error(f"Utilisateur avec email {to_email} non trouvé")
#                 return Response(
#                     {"error": f"Utilisateur avec email {to_email} non trouvé"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
#
#             # Récupération du rendez-vous et du salon si applicable
#             rendez_vous = None
#             salon = None
#             if rendez_vous_id:
#                 try:
#                     rendez_vous = TblRendezVous.objects.get(idRendezVous=rendez_vous_id)
#                     salon = rendez_vous.salon
#                     logger.info(
#                         f"Rendez-vous trouvé: {rendez_vous.idRendezVous}, Salon: {salon.nom_salon if salon else 'None'}")
#                 except TblRendezVous.DoesNotExist:
#                     logger.error(f"Rendez-vous avec ID {rendez_vous_id} non trouvé")
#                     return Response(
#                         {"error": f"Rendez-vous avec ID {rendez_vous_id} non trouvé"},
#                         status=status.HTTP_404_NOT_FOUND
#                     )
#
#             # Création de la notification
#             logger.info("Tentative de création de la notification...")
#             try:
#                 notification = EmailService.create_notification(
#                     destinataire=destinataire,
#                     type_email_code=template_id,
#                     salon=salon,
#                     rendez_vous=rendez_vous
#                 )
#                 logger.info(f"Notification créée avec succès: {notification.idTblEmailNotification}")
#             except Exception as create_error:
#                 logger.error(f"Erreur lors de la création de la notification: {str(create_error)}")
#                 logger.error(traceback.format_exc())
#                 return Response(
#                     {"error": f"Erreur lors de la création de la notification: {str(create_error)}"},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
#
#             # Envoi de l'email
#             logger.info("Tentative d'envoi de l'email...")
#             try:
#                 success = EmailService.send_notification(notification.idTblEmailNotification)
#                 logger.info(f"Résultat de l'envoi: {success}")
#             except Exception as send_error:
#                 logger.error(f"Erreur lors de l'envoi de l'email: {str(send_error)}")
#                 logger.error(traceback.format_exc())
#                 return Response(
#                     {
#                         "error": f"Erreur lors de l'envoi de l'email: {str(send_error)}",
#                         "notification": EmailNotificationSerializer(notification).data
#                     },
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
#
#             # Sérialisation de la réponse
#             response_serializer = EmailNotificationSerializer(notification)
#             if success:
#                 logger.info("Email envoyé avec succès")
#                 return Response(
#                     {
#                         "message": "Email envoyé avec succès",
#                         "notification": response_serializer.data
#                     },
#                     status=status.HTTP_200_OK
#                 )
#             else:
#                 logger.error("Échec de l'envoi de l'email")
#                 return Response(
#                     {
#                         "error": "Erreur lors de l'envoi de l'email",
#                         "notification": response_serializer.data
#                     },
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )
#         except Exception as e:
#             logger.error(f"Exception non gérée: {str(e)}")
#             logger.error(traceback.format_exc())
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )