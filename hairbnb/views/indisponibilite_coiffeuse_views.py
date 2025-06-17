from rest_framework.decorators import api_view

from hairbnb.business.business_logic import IndisponibiliteData
from hairbnb.models import TblIndisponibilite, TblCoiffeuse
from rest_framework.response import Response

@api_view(['GET'])
def get_indisponibilites(request, coiffeuse_id):
    try:
        indispos = TblIndisponibilite.objects.filter(coiffeuse__idTblUser=coiffeuse_id).order_by('-date')
        data = [IndisponibiliteData(i).to_dict() for i in indispos]
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


from rest_framework import status

@api_view(['POST'])
def add_indisponibilite(request):
    try:
        print("📥 Données reçues :", request.data)

        data = request.data
        coiffeuse_user_id = data["coiffeuse"]

        # 🔍 Récupérer la coiffeuse à partir de son user ID
        coiffeuse = TblCoiffeuse.objects.filter(idTblUser__idTblUser=coiffeuse_user_id).first()
        if not coiffeuse:
            return Response({"error": "Coiffeuse non trouvée pour cet ID utilisateur"}, status=404)

        indispo = TblIndisponibilite.objects.create(
            coiffeuse=coiffeuse,
            date=data["date"],
            heure_debut=data["heure_debut"],
            heure_fin=data["heure_fin"],
            motif=data.get("motif", "")
        )

        return Response({
            "message": "Indisponibilité enregistrée ✅",
            "indisponibilite": IndisponibiliteData(indispo).to_dict()
        })

    except Exception as e:
        import traceback
        print("⛔ ERREUR:", e)
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)



@api_view(['PUT'])
def update_indisponibilite(request, indispo_id):
    """
    Format attendu :
    {
        "date": "2025-05-02",
        "heure_debut": "09:00",
        "heure_fin": "12:00",
        "motif": "RDV médical"
    }
    """
    try:
        indispo = TblIndisponibilite.objects.filter(id=indispo_id).first()
        if not indispo:
            return Response({"error": "Indisponibilité introuvable"}, status=404)

        # Mise à jour des champs
        data = request.data
        indispo.date = data.get("date", indispo.date)
        indispo.heure_debut = data.get("heure_debut", indispo.heure_debut)
        indispo.heure_fin = data.get("heure_fin", indispo.heure_fin)
        indispo.motif = data.get("motif", indispo.motif)
        indispo.save()

        return Response({
            "message": "Indisponibilité mise à jour ✅",
            "indisponibilite": IndisponibiliteData(indispo).to_dict()
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)



@api_view(['DELETE'])
def delete_indisponibilite(request, indispo_id):
    try:
        indispo = TblIndisponibilite.objects.filter(id=indispo_id).first()
        if not indispo:
            return Response({"error": "Indisponibilité introuvable"}, status=404)

        indispo.delete()
        return Response({"message": "Indisponibilité supprimée 🗑️"})

    except Exception as e:
        return Response({"error": str(e)}, status=500)



