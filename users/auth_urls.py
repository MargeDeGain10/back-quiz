from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentification JWT
    path('login/', views.LoginView.as_view(), name='auth_login'),
    path('logout/', views.LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),

    # Vérification d'authentification
    path('check-auth/', views.check_auth, name='auth_check'),

    # Gestion des mots de passe
    path('change-password/', views.ChangePasswordView.as_view(), name='auth_change_password'),
    path('reset-password/', views.PasswordResetView.as_view(), name='auth_reset_password'),
]