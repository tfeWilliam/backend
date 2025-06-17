# À remplacer dans settings_test.py

# ❌ AVANT (DANGEREUX)
STRIPE_SECRET_KEY = "sk_test_51QxTcwPLEsfXjeyf4PAmUsqK9XGI6G1WG5a7sf..."
ANTHROPIC_API_KEY = "sk-ant-api03-ebchyQKh3n-AB4aMxgxsY1ZaEEINH2L6GI57Uy..."
EMAIL_HOST_PASSWORD = '**Time1990**'

# ✅ APRÈS (SÉCURISÉ)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY") 
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# Et assure-toi d'avoir ça en haut du fichier :
from dotenv import load_dotenv
load_dotenv()
