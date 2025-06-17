# # middleware/country_restriction.py

from django.http import HttpResponseForbidden
import geoip2.database
import os
import logging

# # 📍 Liste des IP autorisées
ALLOWED_IPS = ['127.0.0.1', 'localhost', '::1', '91.86.53.160']

# 📍 Logger personnalisé
logger = logging.getLogger('geoip_blocker')

# 📍 Chemin absolu vers la base GeoLite2
GEOIP_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'geoip', 'GeoLite2-Country.mmdb'
)

class CountryRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.reader = geoip2.database.Reader(GEOIP_DB_PATH)

    def __call__(self, request):
        # ✅ Récupération correcte de l'IP client même derrière Nginx
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            ip = ip.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')

        # ✅ Autorisation des IP locales
        if ip in ALLOWED_IPS:
            return self.get_response(request)

        try:
            response = self.reader.country(ip)
            country = response.country.iso_code
        except Exception as e:
            logger.info(f"GEOIP ERROR: {e}", extra={'ip': ip})
            print(f"[GEOIP ERROR] {e}")
            print(f"📍 IP = {ip} | Country = ??")
            return HttpResponseForbidden("Access Denied.")

        print(f"📍 IP = {ip} | Country = {country}")

        # ✅ Autorise uniquement la Belgique
        if country != 'BE':
            logger.info(f"Blocked country: {country}", extra={'ip': ip})
            return HttpResponseForbidden("Access Denied.")

        return self.get_response(request)








# from django.http import HttpResponseForbidden
# import geoip2.database
# import os
#
# # 📍 Chemin absolu vers ta base GeoLite2
# GEOIP_DB_PATH = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)), '..', 'geoip', 'GeoLite2-Country.mmdb'
# )
#
# class CountryRestrictionMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#         self.reader = geoip2.database.Reader(GEOIP_DB_PATH)
#
#     def __call__(self, request):
#         # ✅ Récupération correcte de l'IP client, même derrière Nginx
#         ip = request.META.get('HTTP_X_FORWARDED_FOR')
#         if ip:
#             ip = ip.split(',')[0].strip()
#         else:
#             ip = request.META.get('REMOTE_ADDR', '')
#
#         try:
#             response = self.reader.country(ip)
#             country = response.country.iso_code
#         except Exception as e:
#             print(f"[GEOIP ERROR] {e}")
#             print(f"📍 IP = {ip} | Country = ??")
#             return HttpResponseForbidden("Access Denied.")
#
#         print(f"📍 IP = {ip} | Country = {country}")
#
#         # ✅ Exemple : on n'autorise que la Belgique
#         if country != 'BE':
#             return HttpResponseForbidden("Access Denied.")
#
#         return self.get_response(request)
