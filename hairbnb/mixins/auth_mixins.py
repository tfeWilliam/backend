"""
Mixins réutilisables pour l'authentification et les permissions
"""
from rest_framework.response import Response
from rest_framework import status
from hairbnb.models import TblCoiffeuse, TblCoiffeuseSalon


class FirebaseAuthMixin:
    """
    Mixin pour ajouter l'authentification Firebase aux class-based views.
    Remplace le décorateur @firebase_authenticated pour les classes.
    
    Usage:
        class MyView(FirebaseAuthMixin, APIView):
            # votre code ici
    """
    def dispatch(self, request, *args, **kwargs):
        # Vérifier l'authentification Firebase
        if not request.user or not hasattr(request.user, 'uuid'):
            return Response(
                {"detail": "Authentification requise"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Si authentifié, continuer avec la vue normale
        return super().dispatch(request, *args, **kwargs)


class OwnerMixin:
    """
    Mixin pour vérifier que l'utilisateur est propriétaire de la ressource.
    
    Usage:
        class MyView(OwnerMixin, APIView):
            owner_param = "idTblUser"  # ou le nom du paramètre à vérifier
            use_uuid = False  # True pour utiliser UUID au lieu de l'ID
    """
    owner_param = "idTblUser"
    use_uuid = False
    
    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user or not hasattr(user, "idTblUser"):
            return Response(
                {"detail": "Utilisateur non authentifié."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Récupérer le paramètre depuis l'URL, les données ou les query params
        id_param = (
            kwargs.get(self.owner_param) or
            request.data.get(self.owner_param) or
            request.query_params.get(self.owner_param)
        )

        if not id_param:
            return Response(
                {"detail": f"Paramètre '{self.owner_param}' manquant."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier la propriété
        if self.use_uuid:
            if str(user.uuid) != str(id_param):
                return Response(
                    {"detail": "Accès interdit (non propriétaire)."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            if str(user.idTblUser) != str(id_param):
                return Response(
                    {"detail": "Accès interdit (non propriétaire)."}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().dispatch(request, *args, **kwargs)


class CoiffeuseOwnerMixin:
    """
    Mixin pour vérifier que l'utilisateur est une coiffeuse propriétaire de salon.
    
    Usage:
        class MyView(CoiffeuseOwnerMixin, APIView):
            # votre code ici
    """
    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Vérification 1 : L'utilisateur est-il de type "Coiffeuse" ?
        if not hasattr(user, 'type_ref') or user.type_ref.libelle.lower() != 'coiffeuse':
            return Response(
                {'error': 'Accès non autorisé. Ce service est réservé aux coiffeuses.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Vérification 2 : La coiffeuse est-elle propriétaire ?
            coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
            is_owner = TblCoiffeuseSalon.objects.filter(
                coiffeuse=coiffeuse, 
                est_proprietaire=True
            ).exists()

            if not is_owner:
                return Response(
                    {'error': 'Cette fonctionnalité est réservée aux propriétaires de salon.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except TblCoiffeuse.DoesNotExist:
            return Response(
                {'error': 'Profil coiffeuse introuvable.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Si toutes les vérifications sont passées, on exécute la vue
        return super().dispatch(request, *args, **kwargs)


# Mixins combinés pour usage fréquent
class AuthenticatedOwnerMixin(FirebaseAuthMixin, OwnerMixin):
    """
    Mixin combiné : authentification Firebase + vérification de propriété
    """
    pass


class AuthenticatedCoiffeuseOwnerMixin(FirebaseAuthMixin, CoiffeuseOwnerMixin):
    """
    Mixin combiné : authentification Firebase + vérification coiffeuse propriétaire
    """
    pass
