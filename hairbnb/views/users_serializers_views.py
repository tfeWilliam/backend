import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import TblCoiffeuse, TblClient, TblUser, TblSalon
from ..profil.profil_serializers import CoiffeuseSerializer, ClientSerializer


#*****************************************Afficher la coiffeuse****************************************
@api_view(['GET'])
def get_coiffeuse_by_uuid(request, uuid):
    try:
        user = TblUser.objects.get(uuid=uuid, type='coiffeuse')
        coiffeuse = TblCoiffeuse.objects.get(idTblUser=user)
        serializer = CoiffeuseSerializer(coiffeuse)

        return Response({"status": "success", "data": serializer.data}, status=200)

    except TblUser.DoesNotExist:
        return Response({"status": "error", "message": "Utilisateur introuvable ou non une coiffeuse."}, status=404)

    except TblCoiffeuse.DoesNotExist:
        return Response({"status": "error", "message": "Coiffeuse introuvable."}, status=404)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)
#**************************************************************************************************************************

#*************************************************Afficher le client*******************************************************

@api_view(['GET'])
def get_client_by_uuid(request, uuid):
    try:
        user = TblUser.objects.get(uuid=uuid, type='client')
        client = TblClient.objects.get(idTblUser=user)
        serializer = ClientSerializer(client)

        return Response({"status": "success", "data": serializer.data}, status=200)

    except TblUser.DoesNotExist:
        return Response({"status": "error", "message": "Utilisateur introuvable ou non un client."}, status=404)

    except TblClient.DoesNotExist:
        return Response({"status": "error", "message": "Client introuvable."}, status=404)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

# **************************************************************************************************************************

# ********************************************update_coiffeuse**********************************************************
@api_view(['PUT'])
def update_coiffeuse(request, uuid):
    try:
        coiffeuse = TblCoiffeuse.objects.get(uuid=uuid)
    except TblCoiffeuse.DoesNotExist:
        return Response({'error': 'Coiffeuse not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CoiffeuseSerializer(coiffeuse, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# **************************************************************************************************************************

# ********************************************update_client**********************************************************
@api_view(['PUT'])
def update_client(request, uuid):
    try:
        client = TblClient.objects.get(uuid=uuid)
    except TblClient.DoesNotExist:
        return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ClientSerializer(client, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# **************************************************************************************************************************
