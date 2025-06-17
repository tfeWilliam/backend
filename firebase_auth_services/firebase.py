################################################################################
#                                                                              #
#                            MODULE DE GESTION FIREBASE                          #
#                                                                              #
#  Ce script gère l'interaction avec le SDK Admin de Firebase pour Python.     #
#  Il initialise la connexion à l'aide des identifiants locaux et fournit      #
#  une fonction pour vérifier les jetons d'identification (ID Tokens)          #
#  envoyés par les applications clientes.                                      #
#                                                                              #
################################################################################

# Importation des bibliothèques nécessaires
import firebase_admin  # SDK principal de Firebase Admin
from firebase_admin import credentials, auth # Modules pour les identifiants et l'authentification
import os # Module pour interagir avec le système d'exploitation (chemins de fichiers)

# Construction dynamique du chemin vers le fichier de clés de service Firebase.
# Cela garantit que le chemin est correct, peu importe d'où le script est exécuté.
FIREBASE_CREDENTIAL_PATH = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')

# Initialisation de l'application Firebase Admin.
# Le bloc 'if not firebase_admin._apps:' est une sécurité pour éviter de
# ré-initialiser l'application si ce module est importé plusieurs fois.
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token):
    """
    Vérifie la validité d'un jeton d'identification Firebase (ID Token).

    Args:
        id_token (str): Le jeton JWT fourni par le client après sa connexion.

    Returns:
        dict: Un dictionnaire contenant les informations décodées de l'utilisateur
              (comme 'uid', 'email', etc.) si le jeton est valide.
        None: Retourne None si la vérification échoue (jeton invalide, expiré, etc.).
    """
    try:
        # Tente de vérifier et décoder le jeton en utilisant le SDK Firebase.
        # Si le jeton est invalide, cette fonction lèvera une exception.
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        # Capture toute exception durant la vérification pour éviter un crash.
        print(f"Erreur lors de la vérification du jeton Firebase: {e}")
        return None





# # firebase.py
#
# import firebase_admin
# from firebase_admin import credentials, auth
# import os
#
# # 👇 Utilise ton fichier .json téléchargé depuis Firebase Console
# FIREBASE_CREDENTIAL_PATH = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
#
# if not firebase_admin._apps:
#     cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
#     firebase_admin.initialize_app(cred)
#
#
# # firebase.py (suite)
#
# def verify_firebase_token(id_token):
#     try:
#         decoded_token = auth.verify_id_token(id_token)
#         return decoded_token  # contient 'uid', 'email', etc.
#     except Exception as e:
#         print(f"❌ Erreur de vérification Firebase: {e}")
#         return None
