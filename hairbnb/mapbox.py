import requests

class MapboxAPI:
    BASE_URL = "https://api.mapbox.com"
    API_KEY = "pk.eyJ1IjoiZmFjZW9mZjIwMDMiLCJhIjoiY200bjdiZmlrMDQ2ZTJpczVsOG83b2NhOCJ9.huZ7C4_mmhYkyhtyonHF4Q"  # Remplacez par votre clé API

    @staticmethod
    def geocode_address(address):
        """Obtenir les coordonnées géographiques d'une adresse."""
        url = f"{MapboxAPI.BASE_URL}/geocoding/v5/mapbox.places/{address}.json"
        params = {"access_token": MapboxAPI.API_KEY}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                location = data["features"][0]["geometry"]["coordinates"]
                return {
                    "longitude": location[0],
                    "latitude": location[1],
                }
            else:
                raise ValueError("Adresse introuvable")
        else:
            raise ConnectionError("Erreur avec l'API Mapbox")

    @staticmethod
    def get_nearby_points_of_interest(longitude, latitude, radius=1000):
        """Obtenir des points d'intérêt autour d'une position."""
        url = f"{MapboxAPI.BASE_URL}/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
        params = {"access_token": MapboxAPI.API_KEY, "proximity": f"{longitude},{latitude}"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise ConnectionError("Erreur avec l'API Mapbox")
