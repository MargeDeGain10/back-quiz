from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from users.permissions import IsAdmin
from .models import Questionnaire, Question
from .serializers import (
    QuestionnaireListSerializer, QuestionnaireDetailSerializer,
    QuestionnaireCreateUpdateSerializer, QuestionnaireStatsSerializer,
    QuestionDetailSerializer, QuestionCreateUpdateSerializer
)
from .filters import QuestionnaireFilter, QuestionFilter


class QuestionnaireViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion CRUD des questionnaires par les administrateurs
    """
    permission_classes = [IsAdmin]
    filterset_class = QuestionnaireFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'date_creation', 'duree_minutes']
    ordering = ['-date_creation']

    def get_queryset(self):
        """
        Retourner tous les questionnaires avec optimisations
        """
        return Questionnaire.objects.prefetch_related('questions__reponses').all()

    def get_serializer_class(self):
        """
        Retourner le serializer approprié selon l'action
        """
        if self.action == 'list':
            return QuestionnaireListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return QuestionnaireCreateUpdateSerializer
        elif self.action == 'statistiques':
            return QuestionnaireStatsSerializer
        else:
            return QuestionnaireDetailSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Suppression d'un questionnaire avec vérifications
        """
        instance = self.get_object()

        # Vérifier s'il y a des parcours associés
        parcours_count = instance.parcours.count()

        if parcours_count > 0:
            return Response({
                'error': f'Impossible de supprimer ce questionnaire. Il est utilisé dans {parcours_count} parcours.',
                'detail': 'Vous devez d\'abord supprimer les parcours associés.',
                'parcours_count': parcours_count
            }, status=status.HTTP_409_CONFLICT)

        # Supprimer le questionnaire (cascade supprime questions et réponses)
        instance.delete()

        return Response({
            'message': 'Questionnaire supprimé avec succès'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """
        Statistiques détaillées d'un questionnaire
        """
        instance = self.get_object()
        serializer = QuestionnaireStatsSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques_globales(self, request):
        """
        Statistiques générales des questionnaires
        """
        from django.db.models import Avg, Count, Sum
        from responses.models import Parcours

        questionnaires = self.get_queryset()

        # Statistiques de base
        total_questionnaires = questionnaires.count()
        questionnaires_avec_questions = questionnaires.filter(
            questions__isnull=False
        ).distinct().count()

        # Statistiques des questions
        questions_stats = questionnaires.aggregate(
            total_questions=Count('questions'),
            questions_par_questionnaire=Avg('questions__id')
        )

        # Statistiques d'utilisation
        parcours_stats = Parcours.objects.aggregate(
            total_parcours=Count('id'),
            parcours_termines=Count('id', filter=Q(statut='TERMINE')),
            note_moyenne_globale=Avg('note_obtenue', filter=Q(statut='TERMINE'))
        )

        # Questionnaires les plus utilisés
        questionnaires_populaires = questionnaires.annotate(
            nb_parcours=Count('parcours')
        ).order_by('-nb_parcours')[:5]

        popular_data = []
        for q in questionnaires_populaires:
            popular_data.append({
                'id': q.id,
                'nom': q.nom,
                'nombre_parcours': q.nb_parcours,
                'nombre_questions': q.nombre_questions
            })

        # Questionnaires récents (30 derniers jours)
        from datetime import datetime, timedelta
        date_limite = datetime.now() - timedelta(days=30)
        nouveaux_questionnaires = questionnaires.filter(
            date_creation__gte=date_limite
        ).count()

        return Response({
            'total_questionnaires': total_questionnaires,
            'questionnaires_avec_questions': questionnaires_avec_questions,
            'questionnaires_vides': total_questionnaires - questionnaires_avec_questions,
            'nouveaux_questionnaires_30j': nouveaux_questionnaires,
            'questions': {
                'total_questions': questions_stats['total_questions'] or 0,
                'moyenne_par_questionnaire': round(questions_stats['questions_par_questionnaire'], 1)
                                           if questions_stats['questions_par_questionnaire'] else 0
            },
            'utilisation': {
                'total_parcours': parcours_stats['total_parcours'] or 0,
                'parcours_termines': parcours_stats['parcours_termines'] or 0,
                'note_moyenne_globale': round(parcours_stats['note_moyenne_globale'], 2)
                                      if parcours_stats['note_moyenne_globale'] else None
            },
            'questionnaires_populaires': popular_data
        })


    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Récupérer toutes les questions d'un questionnaire
        """
        instance = self.get_object()
        questions = instance.questions.prefetch_related('reponses').all()

        # Pagination manuelle si nécessaire
        page = self.paginate_queryset(questions)
        if page is not None:
            serializer = QuestionDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = QuestionDetailSerializer(questions, many=True)
        return Response(serializer.data)



class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion CRUD des questions individuelles
    """
    permission_classes = [IsAdmin]
    filterset_class = QuestionFilter
    search_fields = ['intitule', 'questionnaire__nom']
    ordering_fields = ['id', 'questionnaire__nom']
    ordering = ['questionnaire__nom', 'id']

    def get_queryset(self):
        """
        Retourner toutes les questions avec optimisations
        """
        return Question.objects.select_related('questionnaire').prefetch_related('reponses').all()

    def get_serializer_class(self):
        """
        Retourner le serializer approprié selon l'action
        """
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateUpdateSerializer
        else:
            return QuestionDetailSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Suppression d'une question avec vérifications
        """
        instance = self.get_object()

        # Vérifier s'il y a des réponses utilisateur associées
        reponses_utilisateur_count = instance.reponses_utilisateur.count()

        if reponses_utilisateur_count > 0:
            return Response({
                'error': f'Impossible de supprimer cette question. Elle a {reponses_utilisateur_count} réponse(s) d\'utilisateur.',
                'detail': 'Vous devez d\'abord supprimer les réponses utilisateur associées.',
                'reponses_count': reponses_utilisateur_count
            }, status=status.HTTP_409_CONFLICT)

        questionnaire_nom = instance.questionnaire.nom
        instance.delete()

        return Response({
            'message': f'Question supprimée avec succès du questionnaire "{questionnaire_nom}"'
        }, status=status.HTTP_204_NO_CONTENT)


