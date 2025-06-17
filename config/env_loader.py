import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class EnvironmentLoader:
    """Chargeur d'environnement sécurisé et intelligent"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.environment = None
        self.env_loaded = False
        
    def load_environment(self):
        """Charge l'environnement approprié selon le contexte"""
        if self.env_loaded:
            return
            
        # Détecter l'environnement
        self.environment = self._detect_environment()
        
        # Charger le fichier .env approprié
        env_file = self._get_env_file()
        
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"✅ Fichier d'environnement chargé: {env_file}")
        else:
            logger.warning(f"⚠️ Fichier d'environnement non trouvé: {env_file}")
            
        # Validation des variables critiques
        self._validate_critical_vars()
        
        self.env_loaded = True
        
    def _detect_environment(self) -> str:
        """Détecte automatiquement l'environnement"""
        # 1. Variable d'environnement explicite
        if os.getenv('ENVIRONMENT'):
            return os.getenv('ENVIRONMENT')
            
        # 2. Arguments de ligne de commande
        if '--production' in sys.argv:
            return 'production'
        elif '--testing' in sys.argv:
            return 'testing'
            
        # 3. Détection automatique basée sur le serveur
        if os.getenv('RENDER') or os.getenv('HEROKU'):
            return 'production'
        elif 'pytest' in sys.modules:
            return 'testing'
        elif os.getenv('DEBUG', '').lower() == 'false':
            return 'production'
            
        # 4. Par défaut: développement
        return 'development'
        
    def _get_env_file(self) -> Path:
        """Retourne le fichier .env approprié"""
        env_files = {
            'production': self.base_dir / '.env.production',
            'testing': self.base_dir / '.env.test',
            'development': self.base_dir / '.env'
        }
        
        # Vérifier si le fichier spécifique existe
        env_file = env_files.get(self.environment, self.base_dir / '.env')
        
        # Fallback vers .env si le fichier spécifique n'existe pas
        if not env_file.exists() and self.environment != 'development':
            logger.warning(f"Fichier {env_file} non trouvé, utilisation de .env")
            env_file = self.base_dir / '.env'
            
        return env_file
        
    def _validate_critical_vars(self):
        """Valide que les variables critiques sont présentes"""
        critical_vars = [
            'SECRET_KEY',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD'
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            raise ValueError(
                f"❌ Variables d'environnement critiques manquantes: {', '.join(missing_vars)}"
            )
            
    def get_env(self, key: str, default=None, required: bool = False):
        """Récupère une variable d'environnement avec validation"""
        if not self.env_loaded:
            self.load_environment()
            
        value = os.getenv(key, default)
        
        if required and not value:
            raise ValueError(f"❌ Variable d'environnement requise manquante: {key}")
            
        return value
        
    def get_boolean(self, key: str, default: bool = False) -> bool:
        """Récupère une variable booléenne"""
        value = self.get_env(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')
        
    def get_list(self, key: str, separator: str = ',', default: list = None) -> list:
        """Récupère une liste depuis une variable d'environnement"""
        value = self.get_env(key, '')
        if not value:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]
