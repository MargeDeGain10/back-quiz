from django.urls import path
from . import views

urlpatterns = [
    # =================== ENDPOINTS STAGIAIRES ===================

    # Questionnaires disponibles pour les stagiaires
    path('questionnaires-disponibles/',
         views.QuestionnairesDisponiblesListView.as_view(),
         name='questionnaires-disponibles'),

    # Gestion des parcours
    path('parcours/',
         views.demarrer_parcours,
         name='demarrer-parcours'),

    path('parcours/<int:pk>/',
         views.ParcoursDetailView.as_view(),
         name='parcours-detail'),

    path('parcours/<int:parcours_id>/question-courante/',
         views.question_courante,
         name='question-courante'),

    path('parcours/<int:parcours_id>/repondre/',
         views.repondre_question,
         name='repondre-question'),

    path('parcours/<int:parcours_id>/terminer/',
         views.terminer_parcours,
         name='terminer-parcours'),

    # Historique et résultats
    path('mes-parcours/',
         views.MesParcoursListView.as_view(),
         name='mes-parcours'),

    path('parcours/<int:pk>/resultats/',
         views.ParcoursResultatsView.as_view(),
         name='parcours-resultats'),

    # =================== NOUVEAUX ENDPOINTS AVANCÉS ===================

    # Résultats détaillés avec analyses avancées
    path('parcours/<int:pk>/resultats-detailles/',
         views.ParcoursResultatsDetaillesView.as_view(),
         name='parcours-resultats-detailles'),

    # Recommandations personnalisées (stagiaires)
    path('mes-recommandations/',
         views.mes_recommandations,
         name='mes-recommandations'),

    # =================== ENDPOINTS ADMINS UNIQUEMENT ===================

    # Synthèse complète d'un stagiaire
    path('stagiaire/<int:stagiaire_id>/synthese/',
         views.synthese_stagiaire,
         name='synthese-stagiaire'),

    # Statistiques avancées d'un questionnaire
    path('questionnaire/<int:questionnaire_id>/statistiques-avancees/',
         views.statistiques_questionnaire_avancees,
         name='statistiques-questionnaire-avancees'),

    # Dashboard principal - synthèse globale
    path('rapports/synthese-globale/',
         views.synthese_globale,
         name='synthese-globale'),

    # Analyse des questions difficiles
    path('rapports/questions-difficiles/',
         views.analyse_questions_difficiles,
         name='analyse-questions-difficiles'),

    # Export des données en CSV
    path('rapports/export/',
         views.export_donnees,
         name='export-donnees'),

    # Recalcul des analyses (maintenance)
    path('maintenance/recalculer-analyses/',
         views.recalculer_analyses,
         name='recalculer-analyses'),
]