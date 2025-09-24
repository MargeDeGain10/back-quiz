from django.urls import path
from . import views

urlpatterns = [
    # Profil utilisateur authentifié
    path('me/', views.UserProfileView.as_view(), name='user_profile'),
]