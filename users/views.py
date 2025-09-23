from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.utils import timezone

from .serializers import (
    LoginSerializer, UserProfileSerializer, ChangePasswordSerializer,
    PasswordResetSerializer, UserCreateSerializer
)
from .permissions import IsAdmin, IsAdminOrStagiaire

User = get_user_model()


class LoginView(APIView):
    """
    Vue de connexion personnalisée avec JWT
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Mettre à jour le dernier login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)

            # Ajouter des claims personnalisés
            refresh['role'] = user.role
            refresh['nom'] = user.nom
            refresh['prenom'] = user.prenom

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Supprimé - remplacé par LoginView


class LogoutView(APIView):
    """
    Vue de déconnexion
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Déconnexion de la session Django
            logout(request)

            return Response({
                'message': 'Déconnexion réussie'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Erreur lors de la déconnexion'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    Vue pour récupérer le profil de l'utilisateur connecté
    """
    permission_classes = [IsAdminOrStagiaire]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """
        Mise à jour du profil utilisateur
        """
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Vue pour changer le mot de passe
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Mot de passe modifié avec succès'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    Vue pour demander une réinitialisation de mot de passe
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email__iexact=email.strip())

                # Générer un token de réinitialisation
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Envoyer l'email (à implémenter selon vos besoins)
                reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

                # Pour le développement, on peut juste retourner le lien
                return Response({
                    'message': 'Email de réinitialisation envoyé',
                    'reset_link': reset_link  # À retirer en production
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                # Ne pas révéler si l'email existe ou non
                return Response({
                    'message': 'Si cette adresse email existe, un email de réinitialisation a été envoyé'
                }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCreateView(APIView):
    """
    Vue pour créer un nouvel utilisateur (admin seulement)
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserProfileSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrStagiaire])
def check_auth(request):
    """
    Endpoint simple pour vérifier l'authentification
    """
    return Response({
        'authenticated': True,
        'user': UserProfileSerializer(request.user).data
    })
