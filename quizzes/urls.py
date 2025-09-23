from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'questionnaires', views.QuestionnaireViewSet, basename='questionnaire')
router.register(r'questions', views.QuestionViewSet, basename='question')

urlpatterns = [
    # API Questionnaires et Questions (Admin uniquement)
    path('', include(router.urls)),
]