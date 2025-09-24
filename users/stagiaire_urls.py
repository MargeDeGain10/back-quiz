from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'', views.StagiaireViewSet, basename='stagiaire')

urlpatterns = [
    # API Stagiaires (Admin uniquement) - CRUD complet
    path('', include(router.urls)),
]