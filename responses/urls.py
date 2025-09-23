from django.urls import path
from . import views

urlpatterns = [
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
]