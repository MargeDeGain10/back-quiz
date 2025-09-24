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

from rest_framework import viewsets
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.openapi import AutoSchema

from .serializers import (
    LoginSerializer, LogoutSerializer, UserProfileSerializer, ChangePasswordSerializer,
    PasswordResetSerializer, UserCreateSerializer, StagiaireCreateSerializer,
    StagiaireUpdateSerializer, StagiaireDetailSerializer
)
from .permissions import IsAdmin, IsAdminOrStagiaire
from .filters import StagiaireFilter
from .models import Stagiaire

User = get_user_model()


class LoginView(APIView):
    """
    Vue de connexion personnalisée avec JWT
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description='Connexion réussie',
                response={
                    'type': 'object',
                    'properties': {
                        'refresh': {'type': 'string', 'description': 'Token de rafraîchissement JWT'},
                        'access': {'type': 'string', 'description': 'Token d\'accès JWT'},
                        'user': {'type': 'object', 'description': 'Informations de l\'utilisateur'}
                    }
                }
            ),
            400: OpenApiResponse(description='Erreurs de validation')
        },
        summary='Connexion utilisateur',
        description='Authentifie un utilisateur avec login/password et retourne les tokens JWT',
        tags=['Authentication']
    )
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

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                description='Déconnexion réussie',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'description': 'Message de confirmation'}
                    }
                }
            ),
            400: OpenApiResponse(description='Erreur lors de la déconnexion')
        },
        summary='Déconnexion utilisateur',
        description='Déconnecte l\'utilisateur et blackliste le token de rafraîchissement',
        tags=['Authentication']
    )
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


class AdminCreateView(APIView):
    """
    Vue pour créer un administrateur (admin seulement)
    """
    permission_classes = [IsAdmin]

    @extend_schema(
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(
                description='Administrateur créé avec succès',
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description='Erreurs de validation'),
            403: OpenApiResponse(description='Permission refusée - Admin requis')
        },
        summary='Créer un administrateur',
        description='Crée un nouvel administrateur. Accessible uniquement aux administrateurs.',
        tags=['Admin Management']
    )
    def post(self, request):
        # Forcer le rôle ADMIN
        data = request.data.copy()
        data['role'] = 'ADMIN'

        serializer = UserCreateSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserProfileSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StagiaireViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion CRUD des stagiaires par les administrateurs
    """
    permission_classes = [IsAdmin]
    filterset_class = StagiaireFilter
    search_fields = ['user__nom', 'user__prenom', 'user__email', 'user__login', 'societe']
    ordering_fields = ['user__nom', 'user__prenom', 'user__date_joined', 'societe']
    ordering = ['user__nom', 'user__prenom']

    def get_queryset(self):
        """
        Retourner seulement les stagiaires
        """
        return Stagiaire.objects.select_related('user').filter(
            user__role='STAGIAIRE'
        )

    def get_serializer_class(self):
        """
        Retourner le serializer approprié selon l'action
        """
        if self.action == 'create':
            return StagiaireCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StagiaireUpdateSerializer
        else:
            return StagiaireDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Créer un nouveau stagiaire
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stagiaire = serializer.save()

        # Retourner la réponse avec le serializer de détail
        response_serializer = StagiaireDetailSerializer(stagiaire)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        """
        Suppression d'un stagiaire avec gestion des cascades
        """
        instance = self.get_object()
        user = instance.user

        # Vérifier s'il y a des parcours associés
        parcours_count = instance.parcours.count()

        if parcours_count > 0:
            return Response({
                'error': f'Impossible de supprimer ce stagiaire. Il a {parcours_count} parcours associé(s).',
                'detail': 'Vous devez d\'abord supprimer ou réassigner les parcours.',
                'parcours_count': parcours_count
            }, status=status.HTTP_409_CONFLICT)

        # Supprimer le stagiaire et l'utilisateur
        instance.delete()
        user.delete()

        return Response({
            'message': 'Stagiaire supprimé avec succès'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Statistiques générales des stagiaires
        """
        from django.db.models import Count, Avg, Q
        from responses.models import Parcours

        queryset = self.get_queryset()

        # Statistiques de base
        total_stagiaires = queryset.count()
        stagiaires_actifs = queryset.filter(user__is_active=True).count()
        stagiaires_inactifs = total_stagiaires - stagiaires_actifs

        # Statistiques des parcours
        parcours_stats = queryset.aggregate(
            avec_parcours=Count('parcours', distinct=True),
            parcours_termines=Count(
                'parcours',
                filter=Q(parcours__statut='TERMINE'),
                distinct=True
            ),
            note_moyenne_globale=Avg(
                'parcours__note_obtenue',
                filter=Q(parcours__statut='TERMINE')
            )
        )

        # Top sociétés
        top_societes = queryset.values('societe').annotate(
            count=Count('societe')
        ).order_by('-count')[:10]

        # Stagiaires récents (derniers 30 jours)
        from datetime import datetime, timedelta
        date_limite = datetime.now() - timedelta(days=30)
        nouveaux_stagiaires = queryset.filter(
            user__date_joined__gte=date_limite
        ).count()

        return Response({
            'total_stagiaires': total_stagiaires,
            'stagiaires_actifs': stagiaires_actifs,
            'stagiaires_inactifs': stagiaires_inactifs,
            'nouveaux_stagiaires_30j': nouveaux_stagiaires,
            'parcours': {
                'stagiaires_avec_parcours': parcours_stats['avec_parcours'],
                'parcours_termines': parcours_stats['parcours_termines'],
                'note_moyenne_globale': round(parcours_stats['note_moyenne_globale'], 2)
                                      if parcours_stats['note_moyenne_globale'] else None
            },
            'top_societes': top_societes
        })

    @action(detail=True, methods=['post'])
    def toggle_activation(self, request, pk=None):
        """
        Activer/désactiver un stagiaire
        """
        instance = self.get_object()
        user = instance.user

        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': f'Stagiaire {"activé" if user.is_active else "désactivé"} avec succès',
            'is_active': user.is_active
        })

    @action(detail=True, methods=['get'])
    def parcours(self, request, pk=None):
        """
        Récupérer les parcours d'un stagiaire spécifique
        """
        instance = self.get_object()
        parcours = instance.parcours.all().order_by('-date_realisation')

        # Pagination manuelle si nécessaire
        page = self.paginate_queryset(parcours)
        if page is not None:
            # Serializer des parcours (à implémenter dans l'app responses)
            serializer_data = []
            for p in page:
                serializer_data.append({
                    'id': p.id,
                    'questionnaire': {
                        'id': p.questionnaire.id,
                        'nom': p.questionnaire.nom
                    },
                    'date_realisation': p.date_realisation,
                    'statut': p.statut,
                    'note_obtenue': p.note_obtenue,
                    'temps_passe_minutes': p.temps_passe_minutes,
                    'progression_pourcentage': p.progression_pourcentage
                })
            return self.get_paginated_response(serializer_data)

        serializer_data = []
        for p in parcours:
            serializer_data.append({
                'id': p.id,
                'questionnaire': {
                    'id': p.questionnaire.id,
                    'nom': p.questionnaire.nom
                },
                'date_realisation': p.date_realisation,
                'statut': p.statut,
                'note_obtenue': p.note_obtenue,
                'temps_passe_minutes': p.temps_passe_minutes,
                'progression_pourcentage': p.progression_pourcentage
            })

        return Response(serializer_data)


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
