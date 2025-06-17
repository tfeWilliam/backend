import requests


class GeolocationService:
    @staticmethod
    def geocode_address(adresse_complete):
        """
        Méthode pour récupérer les coordonnées géographiques (latitude, longitude)
        à partir d'une adresse complète en utilisant l'API Nominatim.

        Arguments :
        - adresse_complete (str) : L'adresse complète à géocoder.

        Retour :
        - tuple (latitude, longitude) : Les coordonnées géographiques si disponibles.
        - (None, None) : Si l'adresse n'a pas pu être géocodée ou si une erreur s'est produite.

        Étapes :
        1. Construire l'URL pour l'API Nominatim avec l'adresse complète.
        2. Envoyer une requête GET au serveur Nominatim avec un en-tête "User-Agent".
        3. Récupérer et analyser la réponse JSON.
        4. Extraire les coordonnées si elles existent, sinon retourner (None, None).
        """
        try:
            # Construire l'URL avec l'adresse complète
            url = f"https://nominatim.openstreetmap.org/search?q={adresse_complete}&format=json&limit=1"

            # En-têtes pour la requête HTTP, le "User-Agent" est obligatoire pour l'API Nominatim
            headers = {'User-Agent': 'Hairbnb/1.0'}

            # Envoyer une requête GET au serveur Nominatim
            response = requests.get(url, headers=headers)

            # Convertir la réponse en JSON
            data = response.json()

            # Vérifier si des résultats sont retournés
            if data:
                # Extraire latitude et longitude depuis le premier résultat
                latitude = data[0]['lat']
                longitude = data[0]['lon']
                return latitude, longitude

            # Si aucun résultat, retourner (None, None)
            return None, None
        except Exception as e:
            # En cas d'erreur, afficher l'erreur et retourner (None, None)
            print(f"Erreur de géocodage : {e}")
            return None, None
