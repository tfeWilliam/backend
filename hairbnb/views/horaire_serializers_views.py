from rest_framework.decorators import api_view
from rest_framework.response import Response
from hairbnb.models import TblHoraireCoiffeuse
from hairbnb.business.business_logic import HoraireCoiffeuseData  # <-- ✅ ton fichier personnalisé


@api_view(['GET'])
def get_horaires_coiffeuse(request, coiffeuse_id):
    try:
        horaires = TblHoraireCoiffeuse.objects.filter(coiffeuse__idTblUser=coiffeuse_id)
        data = [HoraireCoiffeuseData(h).to_dict() for h in horaires]
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from hairbnb.models import TblHoraireCoiffeuse, TblCoiffeuse
from hairbnb.business.business_logic import HoraireCoiffeuseData

@api_view(['POST'])
def set_horaire_coiffeuse(request):
    """
    Crée ou met à jour un horaire hebdomadaire pour une coiffeuse.
    Attendu :
    {
        "coiffeuse": 10,
        "jour": 0,
        "heure_debut": "08:00",
        "heure_fin": "17:00"
    }
    """
    try:
        data = request.data
        coiffeuse_id = data.get("coiffeuse")
        jour = data.get("jour")
        heure_debut_str = data.get("heure_debut")
        heure_fin_str = data.get("heure_fin")

        if not all([coiffeuse_id, jour is not None, heure_debut_str, heure_fin_str]):
            return Response({"error": "Champs requis : coiffeuse, jour, heure_debut, heure_fin"}, status=400)

        # Convertir string -> datetime.time
        heure_debut = datetime.strptime(heure_debut_str, "%H:%M").time()
        heure_fin = datetime.strptime(heure_fin_str, "%H:%M").time()

        # Récupérer l'objet coiffeuse via l'ID utilisateur
        coiffeuse = TblCoiffeuse.objects.get(idTblUser__idTblUser=coiffeuse_id)
        #print(f">> Coiffeuse trouvée: {coiffeuse.idTblUser.nom}")

        # Création ou mise à jour
        horaire, created = TblHoraireCoiffeuse.objects.update_or_create(
            coiffeuse=coiffeuse,
            jour=jour,
            defaults={
                "heure_debut": heure_debut,
                "heure_fin": heure_fin
            }
        )

        result = HoraireCoiffeuseData(horaire).to_dict()
        return Response({
            "message": "Horaire ajouté ✅" if created else "Horaire mis à jour 🔁",
            "horaire": result
        })

    except TblCoiffeuse.DoesNotExist:
        return Response({"error": "Coiffeuse introuvable"}, status=404)
    except Exception as e:
        print("⛔ ERREUR:", e)
        return Response({"error": str(e)}, status=500)






@api_view(['DELETE'])
def delete_horaire_coiffeuse(request, coiffeuse_id, jour):
    try:
        horaire = TblHoraireCoiffeuse.objects.filter(coiffeuse__idTblUser=coiffeuse_id, jour=jour).first()
        if not horaire:
            return Response({"error": "Horaire introuvable"}, status=404)

        horaire.delete()
        return Response({"message": f"Horaire supprimé pour le jour {jour}"})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
