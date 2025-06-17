# urls.py - URLs pour le système d'avis

from django.urls import path

from hairbnb.avis.avis_views import avis_salon_public, supprimer_avis, modifier_avis, mes_avis, creer_avis, \
    mes_rdv_avis_en_attente

urlpatterns = [
    # 🔐 APIs PROTÉGÉES (avec authentification Firebase)

    # Récupérer les RDV éligibles aux avis pour le client connecté
    path('mes-rdv-avis-en-attente/', mes_rdv_avis_en_attente, name='mes_rdv_avis_en_attente'),

    # Créer un nouvel avis (+ vérification propriétaire)
    path('avis/creer/', creer_avis, name='creer_avis'),

    # Lister ses propres avis (+ vérification propriétaire)
    path('mes-avis/', mes_avis, name='mes_avis'),

    # Modifier un avis existant (+ vérification propriétaire)
    path('avis/<int:avis_id>/modifier/', modifier_avis, name='modifier_avis'),

    # Supprimer un avis existant (+ vérification propriétaire)
    path('avis/<int:avis_id>/supprimer/', supprimer_avis, name='supprimer_avis'),

    # 🌐 APIs PUBLIQUES (sans authentification)

    # Voir les avis publics d'un salon
    path('salon/<int:salon_id>/avis/', avis_salon_public, name='avis_salon_public'),
]

# 📋 RÉSUMÉ DES ENDPOINTS DISPONIBLES :

"""
🔐 ENDPOINTS PROTÉGÉS (nécessitent authentification Firebase) :

GET    /api/mes-rdv-avis-en-attente/
       → Récupère les RDV terminés sans avis du client connecté
       → Utilisé pour afficher "X avis en attente" sur la home page

POST   /api/avis/creer/
       → Crée un nouvel avis
       → Body: {"idRendezVous": 123, "note": 5, "commentaire": "Excellent !"}
       → Vérifie que le RDV appartient au client connecté

GET    /api/mes-avis/?client_uuid=xxx
       → Liste tous les avis donnés par le client connecté
       → Pagination optionnelle: ?page=1&page_size=10

PATCH  /api/avis/456/modifier/
       → Modifie un avis existant (note et/ou commentaire)
       → Body: {"note": 4, "commentaire": "Très bien finalement"}
       → Vérifie que l'avis appartient au client connecté

DELETE /api/avis/456/supprimer/
       → Supprime un avis existant
       → Vérifie que l'avis appartient au client connecté

🌐 ENDPOINTS PUBLICS (sans authentification) :

GET    /api/salon/123/avis/
       → Affiche les avis publics d'un salon
       → Pagination: ?page=1&page_size=10
       → Inclut statistiques (moyenne, répartition des notes)
       → Utilisé pour afficher les avis sur la page publique du salon
"""