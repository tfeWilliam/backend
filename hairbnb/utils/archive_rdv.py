from django.utils.timezone import now
from hairbnb.models import TblRendezVous

def archive_rendezvous_if_needed():
    """
    Archive tous les rendez-vous dans le passé, peu importe leur statut
    """
    now_time = now()

    rdvs_a_archiver = TblRendezVous.objects.filter(
        date_heure__lt=now_time,
        est_archive=False
    )

    count = rdvs_a_archiver.update(est_archive=True)

    return count  # Utile pour logs/debug









# from django.utils.timezone import now
# from hairbnb.models import TblRendezVous
#
# def archive_rendezvous_if_needed():
#     """
#     🔄 Archive les rendez-vous dans le passé avec statut terminé ou confirmé
#     """
#     now_time = now()
#
#     rdvs_a_archiver = TblRendezVous.objects.filter(
#         date_heure__lt=now_time,
#         est_archive=False,
#         statut__in=["confirmé", "terminé"]
#     )
#
#     count = rdvs_a_archiver.update(est_archive=True)
#
#     return count  # Optionnel, utile pour debug/log
