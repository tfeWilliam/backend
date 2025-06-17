################################################################################
#                                                                              #
#               MODULE DE SERVICE IA POUR L'APPLICATION HAIRBNB                #
#                                                                              #
#  Ce script contient la logique d'interaction avec l'API de l'intelligence   #
#  artificielle d'Anthropic (Claude). Il est conçu pour recevoir une requête   #
#  utilisateur, la contextualiser avec des données de la base de données,     #
#  et retourner une réponse générée par l'IA.                                  #
#                                                                              #
#  Le fichier contient deux implémentations de la classe `AIService` :         #
#  1. Une version hautement optimisée pour économiser les "tokens" en         #
#     utilisant des stratégies de filtrage et de compactage.                   #
#  2. Une version plus ancienne (laissée en commentaire dans le code original)#
#     qui utilise une approche plus simple et un modèle d'IA différent.       #
#                                                                              #
################################################################################

# Importation des bibliothèques nécessaires
import anthropic
import json
import tiktoken
from django.conf import settings
from typing import Dict, Any, Optional, List
import logging

# Configuration du logger pour enregistrer les informations et erreurs
logger = logging.getLogger(__name__)


class AIService:
    """
    Définit le service d'interaction avec l'IA.
    Cette classe gère l'initialisation du client API, le comptage des tokens,
    et la génération des réponses.
    """

    def __init__(self):
        # Initialisation du client Anthropic pour communiquer avec l'API Claude.
        # La clé API est récupérée depuis les paramètres de configuration de Django.
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
        )
        # Initialisation de l'encodeur de tokens 'tiktoken'.
        # 'cl100k_base' est l'encodage standard utilisé par les modèles Claude 3.
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Calcule le nombre de tokens pour une chaîne de caractères donnée.
        """
        return len(self.encoder.encode(text))

    def get_response(self,
                     query: str,
                     context: Optional[Dict[str, Any]] = None,
                     message_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Fonction principale qui interroge l'IA et retourne sa réponse.
        Elle prend la question de l'utilisateur, des données de contexte optionnelles
        et un historique de conversation pour générer une réponse pertinente.
        """
        # Le bloc try-except permet de capturer les erreurs potentielles lors de l'appel à l'API.
        try:
            # Le "System Prompt" instruit l'IA sur son rôle et ses contraintes.
            # Il est spécifiquement rédigé pour forcer des réponses courtes et directes
            # afin de minimiser le coût en tokens.
            system_prompt = """
            Tu es l'assistant Hairbnb qui analyse les données de coiffure et clients.
            RÈGLES STRICTES POUR ÉCONOMISER DES TOKENS:
            1. Sois extrêmement concis - pas de formules de politesse
            2. Réponds directement à la question sans introduction
            3. Utilise des listes à puces pour présenter les chiffres
            4. Limite-toi aux données demandées uniquement
            5. Réponds en 3-4 phrases maximum quand possible
            6. Supprime tout mot superflu

            FORMAT DES RÉPONSES:
            - Réponds normalement avec du texte simple dans la plupart des cas
            - Utilise des tableaux HTML UNIQUEMENT quand on te demande explicitement un "tableau" 
                ou quand tu dois présenter une liste structurée de données comme des clients, services, etc.

            Exemple de tableau HTML à utiliser SEULEMENT quand c'est demandé:
            <table border="1">
            <tr>
                <th>Nom</th>
                <th>Adresse</th>
                <th>Date</th>
            </tr>
            <tr>
            <td>Jean Dupont</td>
            <td>10 rue de Paris</td>
            <td>15/04/1985</td>
            </tr>
            </table>
            """

            # Début de la stratégie d'optimisation : filtrage du contexte.
            filtered_context = {}
            # Le filtrage n'est appliqué que si un contexte est fourni.
            if context:
                # La requête de l'utilisateur est mise en minuscules pour une comparaison insensible à la casse.
                query_lower = query.lower()

                # Ce dictionnaire mappe des mots-clés à des sections de données.
                # Si un mot-clé est trouvé dans la question, la section de données correspondante sera envoyée à l'IA.
                keywords_mapping = {
                    "statistiques": ["statistiques_generales"],
                    "utilisateur": ["utilisateurs", "clients", "personnel"],
                    "salon": ["salons", "personnel"],
                    "service": ["services"],
                    "rendez": ["rendez_vous", "personnel"],
                    "rdv": ["rendez_vous", "personnel"],
                    "réservation": ["rendez_vous", "personnel"],
                    "avis": ["avis"],
                    "note": ["avis"],
                    "paiement": ["paiements"],
                    "mon": ["personnel"],
                    "mes": ["personnel"],
                    "ma": ["personnel"],
                    "je": ["personnel"],
                    "client": ["clients", "utilisateurs"],
                    "coiffeuse": ["coiffeuses"]
                }

                # Un 'set' est utilisé pour stocker les sections pertinentes afin d'éviter les doublons.
                relevant_sections = set()
                # Itération sur les mots-clés pour trouver ceux présents dans la requête.
                for keyword, sections in keywords_mapping.items():
                    if keyword in query_lower:
                        relevant_sections.update(sections)

                # Si aucune correspondance n'est trouvée, on inclut par défaut les statistiques générales.
                if not relevant_sections:
                    relevant_sections.add("statistiques_generales")

                # Le contexte filtré est construit en n'ajoutant que les sections jugées pertinentes.
                for section in relevant_sections:
                    if section in context:
                        filtered_context[section] = context[section]

            # Le contexte (un dictionnaire Python) est transformé en une chaîne de caractères JSON.
            context_str = ""
            if filtered_context:
                try:
                    # La conversion en JSON est faite sans espaces pour économiser un maximum de tokens.
                    context_str = json.dumps(filtered_context, ensure_ascii=False, separators=(',', ':'))

                    # Mesure de sécurité : si le contexte reste trop volumineux (plus de 4000 caractères),
                    # une réduction plus agressive est appliquée.
                    if len(context_str) > 4000:
                        logger.warning("Contexte trop long, réduction...")
                        # Une nouvelle version du contexte est créée en ne gardant que les données de premier niveau.
                        compact_context = {}
                        for section, data in filtered_context.items():
                            if isinstance(data, dict):
                                compact_context[section] = {k: v for k, v in data.items()
                                                            if not isinstance(v, (dict, list)) or k == "total"}
                            else:
                                compact_context[section] = data
                        # Le contexte ultra-compact est reconverti en JSON.
                        context_str = json.dumps(compact_context, ensure_ascii=False, separators=(',', ':'))
                except Exception as e:
                    # En cas d'erreur de conversion JSON, on utilise une représentation textuelle simple.
                    logger.error(f"Erreur lors du formatage du contexte: {str(e)}")
                    context_str = str(filtered_context)

            # Préparation de la liste des messages à envoyer à l'API.
            messages = []

            # Si un historique de conversation est fourni et contient plus de 2 messages,
            # seuls les deux derniers sont conservés pour limiter le nombre de tokens.
            if message_history and len(message_history) > 2:
                messages.extend(message_history[-2:])
            elif message_history:
                messages.extend(message_history)

            # Le message de l'utilisateur est formaté de manière compacte avec un préfixe "Q:".
            user_content = f"Q:{query}"
            # Si un contexte existe, il est ajouté, préfixé par "Données:".
            if context_str:
                user_content += f"\nDonnées:{context_str}"

            # Le message final de l'utilisateur est ajouté à la liste des messages.
            messages.append({"role": "user", "content": user_content})

            # Le nombre de tokens envoyés en entrée est calculé.
            input_tokens = self.count_tokens(system_prompt + user_content)

            # Appel effectif à l'API d'Anthropic (Claude).
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Modèle choisi pour son rapport coût/performance.
                max_tokens=300,  # Limite basse pour forcer l'IA à être concise.
                system=system_prompt,  # Les instructions pour l'IA.
                messages=messages,  # La conversation.
                temperature=0.3  # Une température basse rend les réponses plus déterministes et factuelles.
            )

            # Le texte de la réponse est extrait de l'objet retourné par l'API.
            ai_response = response.content[0].text

            # Le nombre de tokens reçus en sortie est calculé.
            output_tokens = self.count_tokens(ai_response)

            # La réponse finale est structurée dans un dictionnaire, incluant les statistiques de tokens.
            return {
                "response": ai_response,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens
                }
            }
        # Gestion des exceptions qui pourraient survenir.
        except Exception as e:
            logger.error(f"Erreur dans AIService.get_response: {str(e)}")
            # Un message d'erreur formaté est retourné à l'utilisateur.
            error_message = f"Erreur technique: {str(e)}"
            return {
                "response": error_message,
                "error": str(e),
                "tokens": {
                    "input": self.count_tokens(query),
                    "output": self.count_tokens(error_message),
                    "total": self.count_tokens(query) + self.count_tokens(error_message)
                }
            }





# # hairbnb/ai_service/ai_service.py
# import anthropic
# import json
# import tiktoken
# from django.conf import settings
# from typing import Dict, Any, Optional, List
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class AIService:
#     def __init__(self):
#         # Initialiser le client Claude avec la clé API
#         self.client = anthropic.Anthropic(
#             api_key=settings.ANTHROPIC_API_KEY,
#         )
#         # Encoder pour compter les tokens - CORRECTION
#         self.encoder = tiktoken.get_encoding("cl100k_base")
#
#     def count_tokens(self, text: str) -> int:
#         """Compte le nombre de tokens dans un texte"""
#         return len(self.encoder.encode(text))
#
#     def get_response(self,
#                      query: str,
#                      context: Optional[Dict[str, Any]] = None,
#                      message_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
#         """
#         Obtient une réponse de Claude basée sur la requête et le contexte.
#
#         Args:
#             query: La question posée par l'utilisateur
#             context: Contexte de la base de données (statistiques, etc.)
#             message_history: Historique des messages précédents (facultatif)
#
#         Returns:
#             Un dictionnaire contenant la réponse et les statistiques de tokens
#         """
#         try:
#             # Système prompt optimisé pour économiser des tokens
#             system_prompt = """
#             Tu es l'assistant Hairbnb qui analyse les données de coiffure et clients.
#             RÈGLES STRICTES POUR ÉCONOMISER DES TOKENS:
#             1. Sois extrêmement concis - pas de formules de politesse
#             2. Réponds directement à la question sans introduction
#             3. Utilise des listes à puces pour présenter les chiffres
#             4. Limite-toi aux données demandées uniquement
#             5. Réponds en 3-4 phrases maximum quand possible
#             6. Supprime tout mot superflu
#
#             FORMAT DES RÉPONSES:
#             - Réponds normalement avec du texte simple dans la plupart des cas
#             - Utilise des tableaux HTML UNIQUEMENT quand on te demande explicitement un "tableau"
#                 ou quand tu dois présenter une liste structurée de données comme des clients, services, etc.
#
#             Exemple de tableau HTML à utiliser SEULEMENT quand c'est demandé:
#             <table border="1">
#             <tr>
#                 <th>Nom</th>
#                 <th>Adresse</th>
#                 <th>Date</th>
#             </tr>
#             <tr>
#             <td>Jean Dupont</td>
#             <td>10 rue de Paris</td>
#             <td>15/04/1985</td>
#             </tr>
#             </table>
#             """
#
#             # Optimisation du contexte - ne garder que les données pertinentes
#             filtered_context = {}
#             if context:
#                 # Mots-clés dans la requête pour filtrer le contexte
#                 query_lower = query.lower()
#
#                 # Mappings entre mots-clés et sections du contexte
#                 keywords_mapping = {
#                     "statistiques": ["statistiques_generales"],
#                     "utilisateur": ["utilisateurs", "clients", "personnel"],
#                     "salon": ["salons", "personnel"],
#                     "service": ["services"],
#                     "rendez": ["rendez_vous", "personnel"],
#                     "rdv": ["rendez_vous", "personnel"],
#                     "réservation": ["rendez_vous", "personnel"],
#                     "avis": ["avis"],
#                     "note": ["avis"],
#                     "paiement": ["paiements"],
#                     "mon": ["personnel"],
#                     "mes": ["personnel"],
#                     "ma": ["personnel"],
#                     "je": ["personnel"],
#                     "client": ["clients", "utilisateurs"],
#                     "coiffeuse": ["coiffeuses"]
#                 }
#
#                 # Déterminer les sections pertinentes
#                 relevant_sections = set()
#                 for keyword, sections in keywords_mapping.items():
#                     if keyword in query_lower:
#                         relevant_sections.update(sections)
#
#                 # Si aucune section pertinente n'est trouvée, inclure les statistiques générales
#                 if not relevant_sections:
#                     relevant_sections.add("statistiques_generales")
#
#                 # Filtrer le contexte pour n'inclure que les sections pertinentes
#                 for section in relevant_sections:
#                     if section in context:
#                         filtered_context[section] = context[section]
#
#             # Formater le contexte de manière compacte pour économiser des tokens
#             context_str = ""
#             if filtered_context:
#                 try:
#                     # Convertir en JSON compact
#                     context_str = json.dumps(filtered_context, ensure_ascii=False, separators=(',', ':'))
#
#                     # Si le contexte est trop long, ne garder que les parties les plus importantes
#                     if len(context_str) > 4000:
#                         logger.warning("Contexte trop long, réduction...")
#                         # Gardez seulement les statistiques essentielles
#                         compact_context = {}
#                         for section, data in filtered_context.items():
#                             if isinstance(data, dict):
#                                 # Ne conserver que les premiers niveaux
#                                 compact_context[section] = {k: v for k, v in data.items()
#                                                             if not isinstance(v, (dict, list)) or k == "total"}
#                             else:
#                                 compact_context[section] = data
#
#                         context_str = json.dumps(compact_context, ensure_ascii=False, separators=(',', ':'))
#                 except Exception as e:
#                     logger.error(f"Erreur lors du formatage du contexte: {str(e)}")
#                     context_str = str(filtered_context)
#
#             # Construire les messages pour l'API de manière économe
#             messages = []
#
#             # Si l'historique existe, ne garder que les 2 derniers messages pour économiser
#             if message_history and len(message_history) > 2:
#                 messages.extend(message_history[-2:])  # Seulement les 2 derniers messages
#             elif message_history:
#                 messages.extend(message_history)
#
#             # Ajouter le message actuel de manière compacte
#             user_content = f"Q:{query}"
#             if context_str:
#                 user_content += f"\nDonnées:{context_str}"
#
#             messages.append({"role": "user", "content": user_content})
#
#             # Compter les tokens en entrée
#             input_tokens = self.count_tokens(system_prompt + user_content)
#
#             # Appeler l'API Claude avec des paramètres optimisés
#             response = self.client.messages.create(
#                 model="claude-3-haiku-20240307",  # Plus économique que Opus
#                 max_tokens=300,  # Réduit à 300 pour forcer la concision
#                 system=system_prompt,
#                 messages=messages,
#                 temperature=0.3  # Température plus basse pour des réponses précises et concises
#
#             )
#
#             # Extraire la réponse
#             ai_response = response.content[0].text
#
#             # Compter les tokens en sortie
#             output_tokens = self.count_tokens(ai_response)
#
#             # Retourner la réponse et les statistiques
#             return {
#                 "response": ai_response,
#                 "tokens": {
#                     "input": input_tokens,
#                     "output": output_tokens,
#                     "total": input_tokens + output_tokens
#                 }
#             }
#
#         except Exception as e:
#             logger.error(f"Erreur dans AIService.get_response: {str(e)}")
#             # Message d'erreur minimal pour économiser les tokens
#             error_message = f"Erreur technique: {str(e)}"
#             return {
#                 "response": error_message,
#                 "error": str(e),
#                 "tokens": {
#                     "input": self.count_tokens(query),
#                     "output": self.count_tokens(error_message),
#                     "total": self.count_tokens(query) + self.count_tokens(error_message)
#                 }
#             }
#
#
#
#
#
#
# # # hairbnb/ai_service/ai_service.py
# # import anthropic
# # import json
# # import tiktoken  # Pour compter les tokens
# # from django.conf import settings
# # from typing import Dict, Any, Optional, List
# #
# #
# # class AIService:
# #     def __init__(self):
# #         # Initialiser le client Claude avec la clé API
# #         self.client = anthropic.Anthropic(
# #             api_key=settings.ANTHROPIC_API_KEY,
# #         )
# #         # Encoder pour compter les tokens - CORRECTION ICI
# #         # AVANT: self.encoder = tiktoken.encoding_for_model("cl100k_base")
# #         # APRÈS:
# #         self.encoder = tiktoken.get_encoding("cl100k_base")
# #
# #     def count_tokens(self, text: str) -> int:
# #         """Compte le nombre de tokens dans un texte"""
# #         return len(self.encoder.encode(text))
# #
# #     def get_response(self,
# #                      query: str,
# #                      context: Optional[Dict[str, Any]] = None,
# #                      message_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
# #         """
# #         Obtient une réponse de Claude basée sur la requête et le contexte.
# #
# #         Args:
# #             query: La question posée par l'utilisateur
# #             context: Contexte de la base de données (statistiques, etc.)
# #             message_history: Historique des messages précédents (facultatif)
# #
# #         Returns:
# #             Un dictionnaire contenant la réponse et les statistiques de tokens
# #         """
# #         try:
# #             # Préparer le système prompt
# #             system_prompt = """
# #             Tu es un assistant spécialisé qui analyse les données de l'application Hairbnb,
# #             une plateforme qui met en relation des coiffeuses et des clients.
# #             Tu as accès aux statistiques et aux données de l'application
# #             que tu peux utiliser pour répondre aux questions de l'utilisateur.
# #             Évite les formules de politesse inutiles, les répétitions et les informations non demandées.
# #             Sois précis, informatif et utile. Fournis des insights pertinents basés
# #             sur les données disponibles.
# #             Utilise des phrases courtes et va droit au but.
# #             Économise les tokens en étant concis tout en restant complet.
# #             """
# #
# #             # Préparer le contenu du message
# #             context_str = ""
# #             if context:
# #                 context_str = json.dumps(context, ensure_ascii=False, indent=2)
# #
# #             # Construire les messages pour l'API
# #             messages = []
# #
# #             # Ajouter l'historique des messages si disponible
# #             if message_history:
# #                 messages.extend(message_history)
# #
# #             # Ajouter le message actuel
# #             user_content = f"Voici les données de mon application Hairbnb:\n\n{context_str}\n\nMa question: {query}"
# #             messages.append({"role": "user", "content": user_content})
# #
# #             # Compter les tokens en entrée
# #             input_tokens = self.count_tokens(system_prompt + user_content)
# #
# #             # Appeler l'API Claude
# #             response = self.client.messages.create(
# #                 model="claude-3-opus-20240229",  # Version alternative
# #                 max_tokens=500,
# #                 system=system_prompt,
# #                 messages=messages
# #             )
# #
# #             # Extraire la réponse
# #             ai_response = response.content[0].text
# #
# #             # Compter les tokens en sortie
# #             output_tokens = self.count_tokens(ai_response)
# #
# #             # Retourner la réponse et les statistiques
# #             return {
# #                 "response": ai_response,
# #                 "tokens": {
# #                     "input": input_tokens,
# #                     "output": output_tokens,
# #                     "total": input_tokens + output_tokens
# #                 }
# #             }
# #
# #         except Exception as e:
# #             # En cas d'erreur, retourner un message d'erreur
# #             error_message = f"Je suis désolé, je rencontre des difficultés techniques. Erreur: {str(e)}"
# #             return {
# #                 "response": error_message,
# #                 "error": str(e),
# #                 "tokens": {
# #                     "input": self.count_tokens(query),
# #                     "output": self.count_tokens(error_message),
# #                     "total": self.count_tokens(query) + self.count_tokens(error_message)
# #                 }
# #             }