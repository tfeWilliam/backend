from django.contrib import admin
from hairbnb.models import (
    TblLocalite, TblRue, TblAdresse, TblCoiffeuse, TblClient,
    TblSalon, TblService, TblPrix, TblTemps, TblSalonService,
    TblServicePrix, TblServiceTemps, TblCart, TblCartItem,
    TblPromotion, TblRendezVous, TblPaiement, TblRendezVousService,
    TblIndisponibilite, TblHoraireCoiffeuse, TblSalonImage, TblAvis, TblFavorite, TblTransaction, TblPaiementStatut,
    TblMethodePaiement, TblEmailNotification, TblEmailType, TblEmailStatus, TblUser, TblRole, AIConversation, AIMessage,
    TblSexe, TblType, TblCoiffeuseSalon, TblCategorie, TblAvisStatut
)

admin.site.register(TblLocalite)
admin.site.register(TblRue)
admin.site.register(TblAdresse)
admin.site.register(TblUser)
admin.site.register(TblRole)
admin.site.register(TblCoiffeuse)
admin.site.register(TblClient)
admin.site.register(TblSalon)
admin.site.register(TblSalonImage)
admin.site.register(TblAvis)
admin.site.register(TblService)
admin.site.register(TblPrix)
admin.site.register(TblTemps)
admin.site.register(TblSalonService)
admin.site.register(TblServicePrix)
admin.site.register(TblServiceTemps)
admin.site.register(TblCart)
admin.site.register(TblCartItem)
admin.site.register(TblPromotion)
admin.site.register(TblRendezVous)
admin.site.register(TblPaiement)
admin.site.register(TblRendezVousService)
admin.site.register(TblHoraireCoiffeuse)
admin.site.register(TblIndisponibilite)
admin.site.register(TblFavorite)
admin.site.register(TblTransaction)
admin.site.register(TblPaiementStatut)
admin.site.register(TblMethodePaiement)
admin.site.register(TblEmailNotification)
admin.site.register(TblEmailType)
admin.site.register(TblEmailStatus)
admin.site.register(AIConversation)
admin.site.register(AIMessage)
admin.site.register(TblSexe)
admin.site.register(TblType)
admin.site.register(TblCoiffeuseSalon)
admin.site.register(TblCategorie)
admin.site.register(TblAvisStatut)

