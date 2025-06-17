import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MapboxAPI:
    """
    Service sécurisé pour l'API Mapbox
    Les clés API sont maintenant chargées depuis les variables d'environnement
    """
    BASE_URL = "https://api.mapbox.com"
    
    def __init__(self):
        # Récupérer la clé API depuis les settings (qui la prend depuis .env)
        self.api_key = getattr(settings, 'MAPBOX_API_KEY', None)
        
        if not self.api_key:
            raise ValueError("❌ MAPBOX_API_KEY manquante dans les variables d'environnement")
        
        logger.info("✅ MapboxAPI initialisé avec succès")
        
    def geocode_address(self, address):
        """Obtenir les coordonnées géographiques d'une adresse."""
        if not address:
            raise ValueError("Adresse requise")
            
        url = f"{self.BASE_URL}/geocoding/v5/mapbox.places/{address}.json"
        params = {"access_token": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
            
            data = response.json()
            if data.get("features"):
                location = data["features"][0]["geometry"]["coordinates"]
                return {
                    "longitude": location[0],
                    "latitude": location[1],
                }
            else:
                raise ValueError("Adresse introuvable")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête Mapbox: {str(e)}")
            raise ConnectionError(f"Erreur avec l'API Mapbox: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Erreur de format de réponse Mapbox: {str(e)}")
            raise ValueError("Format de réponse inattendu de l'API Mapbox")

    def get_nearby_points_of_interest(self, longitude, latitude, radius=1000):
        """Obtenir des points d'intérêt autour d'une position."""
        if not isinstance(longitude, (int, float)) or not isinstance(latitude, (int, float)):
            raise ValueError("Longitude et latitude doivent être des nombres")
            
        url = f"{self.BASE_URL}/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
        params = {
            "access_token": self.api_key, 
            "proximity": f"{longitude},{latitude}"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête Mapbox POI: {str(e)}")
            raise ConnectionError(f"Erreur avec l'API Mapbox: {str(e)}")

# Instance globale réutilisable (pattern singleton)
_mapbox_instance = None

def get_mapbox_api():
    """Retourne une instance unique de MapboxAPI"""
    global _mapbox_instance
    if _mapbox_instance is None:
        _mapbox_instance = MapboxAPI()
    return _mapbox_instance
