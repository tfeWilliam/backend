# 🚀 Guide de Migration Rapide - HairBnB Sécurisé

## ✅ Étapes de migration (15 minutes)

### 1. Vérification initiale
```bash
# Vérifier que la nouvelle structure est en place
python scripts/check_env.py
```

### 2. Tester la nouvelle configuration
```bash
# Tester le chargement des variables
python manage.py check
```

### 3. Migrer les vues pour utiliser les nouvelles variables

#### A. Remplacer mapbox.py
Remplacez `hairbnb/mapbox.py` par `hairbnb/mapbox_secure.py` :
```bash
mv hairbnb/mapbox.py hairbnb/mapbox_old.py
mv hairbnb/mapbox_secure.py hairbnb/mapbox.py
```

#### B. Modifier les imports dans vos vues
Dans tous les fichiers qui utilisent MapboxAPI :
```python
# ANCIEN
from hairbnb.mapbox import MapboxAPI
api = MapboxAPI()

# NOUVEAU  
from hairbnb.mapbox import get_mapbox_api
api = get_mapbox_api()
```

### 4. Modifier le settings principal

#### A. Sauvegarder l'ancienne configuration
```bash
cp hairbnb_backend/settings.py hairbnb_backend/settings_old.py
cp hairbnb_backend/settings_test.py hairbnb_backend/settings_test_old.py
```

#### B. Créer le nouveau settings.py
```python
"""
Nouveau settings.py sécurisé
"""
import os
from pathlib import Path
from config.env_loader import EnvironmentLoader

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger l'environnement sécurisé
env = EnvironmentLoader(BASE_DIR)
env.load_environment()

# Récupérer la configuration depuis les variables d'environnement
SECRET_KEY = env.get_env('SECRET_KEY', required=True)
DEBUG = env.get_boolean('DEBUG', False)
ALLOWED_HOSTS = env.get_list('ALLOWED_HOSTS', default=['localhost'])

# Base de données sécurisée
DATABASES = {
    'default': {
        'ENGINE': env.get_env('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': env.get_env('DB_NAME', required=True),
        'USER': env.get_env('DB_USER', required=True), 
        'PASSWORD': env.get_env('DB_PASSWORD', required=True),
        'HOST': env.get_env('DB_HOST', 'localhost'),
        'PORT': env.get_env('DB_PORT', '5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}

# APIs sécurisées
STRIPE_SECRET_KEY = env.get_env('STRIPE_SECRET_KEY', required=True)
STRIPE_PUBLISHABLE_KEY = env.get_env('STRIPE_PUBLISHABLE_KEY', required=True) 
STRIPE_WEBHOOK_SECRET = env.get_env('STRIPE_WEBHOOK_SECRET', required=True)
ANTHROPIC_API_KEY = env.get_env('ANTHROPIC_API_KEY', required=True)
MAPBOX_API_KEY = env.get_env('MAPBOX_API_KEY', required=True)

# Email sécurisé
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.get_env('EMAIL_HOST', 'mail.hairbnb.site')
EMAIL_PORT = int(env.get_env('EMAIL_PORT', '465'))
EMAIL_USE_SSL = env.get_boolean('EMAIL_USE_SSL', True)
EMAIL_HOST_USER = env.get_env('EMAIL_HOST_USER', required=True)
EMAIL_HOST_PASSWORD = env.get_env('EMAIL_HOST_PASSWORD', required=True)
DEFAULT_FROM_EMAIL = env.get_env('DEFAULT_FROM_EMAIL', 'HairBnB <noreply@hairbnb.site>')

# CORS sécurisé
CORS_ALLOWED_ORIGINS = env.get_list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type", "X-CSRFToken"]

# CSRF sécurisé
CSRF_TRUSTED_ORIGINS = env.get_list('CSRF_TRUSTED_ORIGINS')

# Firebase
FIREBASE_CREDENTIALS_PATH = env.get_env('FIREBASE_CREDENTIALS_PATH', 
                                       os.path.join(BASE_DIR, 'firebase_auth_services/firebase_credentials.json'))

# ========================================
# GARDER TOUT LE RESTE DE VOTRE SETTINGS EXISTANT
# ========================================

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hairbnb.apps.HairbnbConfig',
    'corsheaders',
    'rest_framework',
]

# Middleware (copier depuis votre settings actuel)
MIDDLEWARE = [
    'hairbnb_backend.middlewares.BlockWordPressScannersMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.country_restriction.CountryRestrictionMiddleware',
    'middleware.firebase_auth_middleware.FirebaseAuthMiddleware',
    'middleware.bypass_csrf_middleware.BypassCSRFMiddleware',
    'middleware.block_malicious_requests_middleware.BlockMaliciousRequestsMiddleware',
]

# Copier tous vos autres settings (ROOT_URLCONF, TEMPLATES, etc.)
ROOT_URLCONF = 'hairbnb_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hairbnb_backend.wsgi.application'

# Tous vos autres settings (AUTH_PASSWORD_VALIDATORS, LANGUAGE_CODE, etc.)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files  
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# Logging (garder votre config existante)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'geoip': {
            'format': '[%(asctime)s] [%(levelname)s] [%(ip)s] %(message)s',
        },
    },
    'handlers': {
        'geoip_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'geoip_blocked.log'),
            'formatter': 'geoip',
        },
    },
    'loggers': {
        'geoip_blocker': {
            'handlers': ['geoip_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Sécurité pour la production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 5. Générer une nouvelle clé secrète
```bash
python scripts/generate_secret_key.py
```
Copiez la nouvelle clé dans votre fichier `.env`.

### 6. Test final
```bash
# Vérifier que tout fonctionne
python scripts/check_env.py

# Tester Django
python manage.py check
python manage.py migrate --dry-run

# Tester le serveur
python manage.py runserver
```

### 7. Déploiement
Pour déployer en production, configurez les variables d'environnement sur votre plateforme :

**Render/Heroku/Vercel :**
```
SECRET_KEY=votre-nouvelle-cle-production
DEBUG=False
ALLOWED_HOSTS=hairbnb.site,www.hairbnb.site
STRIPE_SECRET_KEY=sk_live_...
ANTHROPIC_API_KEY=...
MAPBOX_API_KEY=...
EMAIL_HOST_PASSWORD=...
ENVIRONMENT=production
```

## 🚨 Points critiques

1. **TESTEZ d'abord en local** avant de déployer
2. **Sauvegardez** vos anciens fichiers avant remplacement
3. **Vérifiez** que `.env` est bien dans `.gitignore`
4. **Utilisez des clés différentes** pour dev/test/production
5. **Ne committez JAMAIS** les fichiers `.env`

## 🆘 En cas de problème

Si quelque chose ne fonctionne pas :

1. **Revenez aux anciens settings** temporairement
2. **Vérifiez les logs** Django pour les erreurs
3. **Testez une variable à la fois** 
4. **Contactez l'équipe** si nécessaire

## ✅ Checklist finale

- [ ] .env créé avec toutes les clés
- [ ] .gitignore mis à jour
- [ ] Anciens settings sauvegardés
- [ ] Nouveau settings.py en place
- [ ] mapbox.py sécurisé
- [ ] Tests passent (`python scripts/check_env.py`)
- [ ] Application démarre (`python manage.py runserver`)
- [ ] Variables production configurées

**Durée estimée : 15-30 minutes** ⏱️
