from django.urls import path
from . import views

urlpatterns = [
    # Création d'administrateurs (Admin uniquement)
    path('create/', views.AdminCreateView.as_view(), name='admin_create'),
]