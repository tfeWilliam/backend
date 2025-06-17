from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from hairbnb.models import TblCoiffeuse, TblCoiffeuseSalon

"""
********************************************************************************
Un décorateur en Python est une fonction qui permet de modifier ou d'étendre 
le comportement d'autres fonctions ou méthodes sans changer leur code source. 
Il s'agit d'un outil puissant pour la programmation modulaire et réutilisable.
********************************************************************************
"""


def firebase_authenticated(view_func):
    """
    Décorateur qui vérifie si l'utilisateur est authentifié via Firebase.
    Si l'utilisateur n'est pas authentifié, renvoie une réponse 401.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user or not hasattr(request.user, 'uuid'):
            return Response({"detail": "Authentification requise"}, status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def is_owner(param_name="idTblUser", use_uuid=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user or not hasattr(user, "idTblUser"):
                return Response({"detail": "Utilisateur non authentifié."}, status=status.HTTP_401_UNAUTHORIZED)

            id_param = (
                    kwargs.get(param_name) or
                    request.data.get(param_name) or
                    request.query_params.get(param_name)
            )

            if not id_param:
                return Response({"detail": f"Paramètre '{param_name}' manquant."}, status=status.HTTP_400_BAD_REQUEST)

            if use_uuid:
                if str(user.uuid) != str(id_param):
                    return Response({"detail": "Accès interdit (non propriétaire)."}, status=status.HTTP_403_FORBIDDEN)
            else:
                if str(user.idTblUser) != str(id_param):
                    return Response({"detail": "Accès interdit (non propriétaire)."}, status=status.HTTP_403_FORBIDDEN)

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator

def is_owner_coiffeuse(view_func):
    """
    Décorateur qui vérifie si l'utilisateur connecté est bien une coiffeuse
    ET si elle est marquée comme propriétaire d'un salon.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Vérification 1 : L'utilisateur est-il de type "Coiffeuse" ?
        # La comparaison est en minuscules pour accepter "coiffeuse" ou "Coiffeuse".
        if not hasattr(user, 'type_ref') or user.type_ref.libelle.lower() != 'coiffeuse':
            return Response(
                {'error': 'Accès non autorisé. Ce service est réservé aux coiffeuses.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Vérification 2 : La coiffeuse est-elle propriétaire ?
            coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
            is_owner = TblCoiffeuseSalon.objects.filter(coiffeuse=coiffeuse, est_proprietaire=True).exists()

            if not is_owner:
                return Response(
                    {'error': 'Cette fonctionnalité est réservée aux propriétaires de salon.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except TblCoiffeuse.DoesNotExist:
            return Response({'error': 'Profil coiffeuse introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        # Si toutes les vérifications sont passées, on exécute la vue
        return view_func(request, *args, **kwargs)

    return _wrapped_view
