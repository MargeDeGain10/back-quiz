from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentification JWT
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profil utilisateur
    path('me/', views.UserProfileView.as_view(), name='user_profile'),
    path('check-auth/', views.check_auth, name='check_auth'),

    # Gestion des mots de passe
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('reset-password/', views.PasswordResetView.as_view(), name='reset_password'),

    # Création d'utilisateurs (admin seulement)
    path('create/', views.UserCreateView.as_view(), name='user_create'),
]