# hairbnb/ai_service/ai_service.py
import anthropic
import json
import tiktoken
from django.conf import settings
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        # Initialiser le client Claude avec la clé API
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
        )
        # Encoder pour compter les tokens - CORRECTION
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Compte le nombre de tokens dans un texte"""
        return len(self.encoder.encode(text))

    def get_response(self,
                     query: str,
                     context: Optional[Dict[str, Any]] = None,
                     message_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Obtient une réponse de Claude basée sur la requête et le contexte.

        Args:
            query: La question posée par l'utilisateur
            context: Contexte de la base de données (statistiques, etc.)
            message_history: Historique des messages précédents (facultatif)

        Returns:
            Un dictionnaire contenant la réponse et les statistiques de tokens
        """
        try:
            # Système prompt optimisé pour économiser des tokens
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

            # Optimisation du contexte - ne garder que les données pertinentes
            filtered_context = {}
            if context:
                # Mots-clés dans la requête pour filtrer le contexte
                query_lower = query.lower()

                # Mappings entre mots-clés et sections du contexte
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

                # Déterminer les sections pertinentes
                relevant_sections = set()
                for keyword, sections in keywords_mapping.items():
                    if keyword in query_lower:
                        relevant_sections.update(sections)

                # Si aucune section pertinente n'est trouvée, inclure les statistiques générales
                if not relevant_sections:
                    relevant_sections.add("statistiques_generales")

                # Filtrer le contexte pour n'inclure que les sections pertinentes
                for section in relevant_sections:
                    if section in context:
                        filtered_context[section] = context[section]

            # Formater le contexte de manière compacte pour économiser des tokens
            context_str = ""
            if filtered_context:
                try:
                    # Convertir en JSON compact
                    context_str = json.dumps(filtered_context, ensure_ascii=False, separators=(',', ':'))

                    # Si le contexte est trop long, ne garder que les parties les plus importantes
                    if len(context_str) > 4000:
                        logger.warning("Contexte trop long, réduction...")
                        # Gardez seulement les statistiques essentielles
                        compact_context = {}
                        for section, data in filtered_context.items():
                            if isinstance(data, dict):
                                # Ne conserver que les premiers niveaux
                                compact_context[section] = {k: v for k, v in data.items()
                                                            if not isinstance(v, (dict, list)) or k == "total"}
                            else:
                                compact_context[section] = data

                        context_str = json.dumps(compact_context, ensure_ascii=False, separators=(',', ':'))
                except Exception as e:
                    logger.error(f"Erreur lors du formatage du contexte: {str(e)}")
                    context_str = str(filtered_context)

            # Construire les messages pour l'API de manière économe
            messages = []

            # Si l'historique existe, ne garder que les 2 derniers messages pour économiser
            if message_history and len(message_history) > 2:
                messages.extend(message_history[-2:])  # Seulement les 2 derniers messages
            elif message_history:
                messages.extend(message_history)

            # Ajouter le message actuel de manière compacte
            user_content = f"Q:{query}"
            if context_str:
                user_content += f"\nDonnées:{context_str}"

            messages.append({"role": "user", "content": user_content})

            # Compter les tokens en entrée
            input_tokens = self.count_tokens(system_prompt + user_content)

            # Appeler l'API Claude avec des paramètres optimisés
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Plus économique que Opus
                max_tokens=300,  # Réduit à 300 pour forcer la concision
                system=system_prompt,
                messages=messages,
                temperature=0.3  # Température plus basse pour des réponses précises et concises

            )

            # Extraire la réponse
            ai_response = response.content[0].text

            # Compter les tokens en sortie
            output_tokens = self.count_tokens(ai_response)

            # Retourner la réponse et les statistiques
            return {
                "response": ai_response,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens
                }
            }

        except Exception as e:
            logger.error(f"Erreur dans AIService.get_response: {str(e)}")
            # Message d'erreur minimal pour économiser les tokens
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
# import tiktoken  # Pour compter les tokens
# from django.conf import settings
# from typing import Dict, Any, Optional, List
#
#
# class AIService:
#     def __init__(self):
#         # Initialiser le client Claude avec la clé API
#         self.client = anthropic.Anthropic(
#             api_key=settings.ANTHROPIC_API_KEY,
#         )
#         # Encoder pour compter les tokens - CORRECTION ICI
#         # AVANT: self.encoder = tiktoken.encoding_for_model("cl100k_base")
#         # APRÈS:
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
#             # Préparer le système prompt
#             system_prompt = """
#             Tu es un assistant spécialisé qui analyse les données de l'application Hairbnb,
#             une plateforme qui met en relation des coiffeuses et des clients.
#             Tu as accès aux statistiques et aux données de l'application
#             que tu peux utiliser pour répondre aux questions de l'utilisateur.
#             Évite les formules de politesse inutiles, les répétitions et les informations non demandées.
#             Sois précis, informatif et utile. Fournis des insights pertinents basés
#             sur les données disponibles.
#             Utilise des phrases courtes et va droit au but.
#             Économise les tokens en étant concis tout en restant complet.
#             """
#
#             # Préparer le contenu du message
#             context_str = ""
#             if context:
#                 context_str = json.dumps(context, ensure_ascii=False, indent=2)
#
#             # Construire les messages pour l'API
#             messages = []
#
#             # Ajouter l'historique des messages si disponible
#             if message_history:
#                 messages.extend(message_history)
#
#             # Ajouter le message actuel
#             user_content = f"Voici les données de mon application Hairbnb:\n\n{context_str}\n\nMa question: {query}"
#             messages.append({"role": "user", "content": user_content})
#
#             # Compter les tokens en entrée
#             input_tokens = self.count_tokens(system_prompt + user_content)
#
#             # Appeler l'API Claude
#             response = self.client.messages.create(
#                 model="claude-3-opus-20240229",  # Version alternative
#                 max_tokens=500,
#                 system=system_prompt,
#                 messages=messages
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
#             # En cas d'erreur, retourner un message d'erreur
#             error_message = f"Je suis désolé, je rencontre des difficultés techniques. Erreur: {str(e)}"
#             return {
#                 "response": error_message,
#                 "error": str(e),
#                 "tokens": {
#                     "input": self.count_tokens(query),
#                     "output": self.count_tokens(error_message),
#                     "total": self.count_tokens(query) + self.count_tokens(error_message)
#                 }
#             }