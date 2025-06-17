# firebase_auth_middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

from firebase_auth_services.firebase import verify_firebase_token
from hairbnb.models import TblUser


class FirebaseAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Ne pas appliquer la logique Firebase pour l'admin ou création de profil
        if request.path.startswith('/ghost/') or request.path.startswith('/api/create-profile/'):
            return

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            request.user = None
            return

        id_token = auth_header.split(' ')[1]
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return JsonResponse({'detail': 'Token Firebase invalide'}, status=401)

        uid = decoded_token.get('uid')

        try:
            user = TblUser.objects.get(uuid=uid)
        except TblUser.DoesNotExist:
            return JsonResponse({'detail': 'Utilisateur non trouvé dans la base'}, status=404)

        request.user = user



# class FirebaseAuthMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#
#         # 🔒 Ne pas appliquer la logique Firebase pour l'admin
#         if request.path.startswith('/ghost/'):
#             return
#         auth_header = request.headers.get('Authorization')
#         #print("🧪 [Middleware] Authorization header:", auth_header)
#
#         if not auth_header or not auth_header.startswith('Bearer '):
#             #print("⛔ Aucun token ou mauvais format")
#             request.user = None
#             return
#
#         id_token = auth_header.split(' ')[1]
#         decoded_token = verify_firebase_token(id_token)
#         if not decoded_token:
#             return JsonResponse({'detail': 'Token Firebase invalide'}, status=401)
#
#         uid = decoded_token.get('uid')
#
#         try:
#             user = TblUser.objects.get(uuid=uid)
#         except TblUser.DoesNotExist:
#             #print("📥 UID Firebase reçu :", uid)
#             return JsonResponse({'detail': 'Utilisateur non trouvé dans la base'}, status=404)
#
#
#         request.user = user  # ✅ Utilisateur existant
