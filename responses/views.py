from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from users.permissions import IsStagiaire
from .models import Parcours, ReponseUtilisateur, ReponseUtilisateurSelection
from .serializers import (
    QuestionnairesDisponiblesSerializer, ParcoursListSerializer,
    ParcoursDetailSerializer, QuestionCouranteSerializer,
    ReponseUtilisateurSerializer, ParcoursResultatsSerializer,
    DemarrerParcoursSerializer
)
from quizzes.models import Questionnaire, Question, Reponse


class QuestionnairesDisponiblesListView(generics.ListAPIView):
    serializer_class = QuestionnairesDisponiblesSerializer
    permission_classes = [IsAuthenticated, IsStagiaire]

    def get_queryset(self):
        return Questionnaire.objects.all().order_by('nom')


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStagiaire])
def demarrer_parcours(request):
    serializer = DemarrerParcoursSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        try:
            parcours = serializer.save()
            return Response(
                ParcoursDetailSerializer(parcours, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la création du parcours: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParcoursDetailView(generics.RetrieveAPIView):
    serializer_class = ParcoursDetailSerializer
    permission_classes = [IsAuthenticated, IsStagiaire]

    def get_queryset(self):
        return Parcours.objects.filter(stagiaire=self.request.user.stagiaire_profile)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStagiaire])
def question_courante(request, parcours_id):
    parcours = get_object_or_404(
        Parcours,
        id=parcours_id,
        stagiaire=request.user.stagiaire_profile
    )

    if parcours.statut != 'EN_COURS':
        return Response(
            {'error': 'Ce parcours n\'est plus en cours.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier le temps limite si défini
    if parcours.questionnaire.duree:
        temps_ecoule = (timezone.now() - parcours.date_realisation).total_seconds() / 60
        if temps_ecoule > parcours.questionnaire.duree:
            # Terminer automatiquement le parcours
            parcours.statut = 'ABANDONNE'
            parcours.temps_passe_sec = int(temps_ecoule * 60)
            parcours.save()
            return Response(
                {'error': 'Temps limite dépassé. Le parcours a été automatiquement abandonné.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Récupérer les questions du questionnaire dans l'ordre
    questions = parcours.questionnaire.questions.all().order_by('id')
    questions_repondues = parcours.reponses_utilisateur.values_list('question_id', flat=True)

    # Trouver la prochaine question non répondue
    question_courante = None
    for question in questions:
        if question.id not in questions_repondues:
            question_courante = question
            break

    if not question_courante:
        return Response(
            {'error': 'Toutes les questions ont été répondues. Veuillez terminer le parcours.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = QuestionCouranteSerializer(
        question_courante,
        context={'request': request, 'parcours': parcours}
    )
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStagiaire])
def repondre_question(request, parcours_id):
    parcours = get_object_or_404(
        Parcours,
        id=parcours_id,
        stagiaire=request.user.stagiaire_profile
    )

    if parcours.statut != 'EN_COURS':
        return Response(
            {'error': 'Ce parcours n\'est plus en cours.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier le temps limite
    if parcours.questionnaire.duree:
        temps_ecoule = (timezone.now() - parcours.date_realisation).total_seconds() / 60
        if temps_ecoule > parcours.questionnaire.duree:
            parcours.statut = 'ABANDONNE'
            parcours.temps_passe_sec = int(temps_ecoule * 60)
            parcours.save()
            return Response(
                {'error': 'Temps limite dépassé.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    question_id = request.data.get('question_id')
    if not question_id:
        return Response(
            {'error': 'L\'ID de la question est requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier que la question appartient au questionnaire
    try:
        question = Question.objects.get(
            id=question_id,
            questionnaire=parcours.questionnaire
        )
    except Question.DoesNotExist:
        return Response(
            {'error': 'Cette question n\'appartient pas au questionnaire du parcours.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier qu'on n'a pas déjà répondu à cette question
    if ReponseUtilisateur.objects.filter(parcours=parcours, question=question).exists():
        return Response(
            {'error': 'Vous avez déjà répondu à cette question.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reponses_selectionnees_ids = request.data.get('reponses_selectionnees_ids', [])
    temps_reponse_sec = request.data.get('temps_reponse_sec', 0)

    # Valider les réponses sélectionnées
    if reponses_selectionnees_ids:
        valid_reponse_ids = list(question.reponses.values_list('id', flat=True))
        for reponse_id in reponses_selectionnees_ids:
            if reponse_id not in valid_reponse_ids:
                return Response(
                    {'error': f'La réponse {reponse_id} n\'appartient pas à cette question.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    try:
        with transaction.atomic():
            # Créer la réponse utilisateur
            reponse_utilisateur = ReponseUtilisateur.objects.create(
                parcours=parcours,
                question=question
            )

            # Ajouter les sélections de réponses
            for reponse_id in reponses_selectionnees_ids:
                reponse = Reponse.objects.get(id=reponse_id)
                ReponseUtilisateurSelection.objects.create(
                    reponse_utilisateur=reponse_utilisateur,
                    reponse=reponse
                )

            # Mettre à jour le temps passé
            parcours.temps_passe_sec += temps_reponse_sec
            parcours.save()

            return Response(
                {
                    'message': 'Réponse enregistrée avec succès.',
                    'progression': f"{parcours.reponses_utilisateur.count()}/{parcours.questionnaire.nombre_questions}"
                },
                status=status.HTTP_201_CREATED
            )

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'enregistrement: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStagiaire])
def terminer_parcours(request, parcours_id):
    parcours = get_object_or_404(
        Parcours,
        id=parcours_id,
        stagiaire=request.user.stagiaire_profile
    )

    if parcours.statut != 'EN_COURS':
        return Response(
            {'error': 'Ce parcours n\'est plus en cours.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    action = request.data.get('action', 'terminer')  # 'terminer' ou 'abandonner'
    temps_final_sec = request.data.get('temps_final_sec', 0)

    try:
        with transaction.atomic():
            # Mettre à jour le temps passé
            if temps_final_sec > 0:
                parcours.temps_passe_sec = temps_final_sec
            else:
                temps_ecoule = (timezone.now() - parcours.date_realisation).total_seconds()
                parcours.temps_passe_sec = int(temps_ecoule)

            if action == 'abandonner':
                parcours.statut = 'ABANDONNE'
                parcours.note_obtenue = None
                message = 'Parcours abandonné.'
            else:
                parcours.statut = 'TERMINE'
                parcours.note_obtenue = parcours.calculer_note()
                message = f'Parcours terminé. Note obtenue: {parcours.note_obtenue}/100'

            parcours.save()

            return Response(
                {
                    'message': message,
                    'parcours': ParcoursDetailSerializer(parcours, context={'request': request}).data
                },
                status=status.HTTP_200_OK
            )

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la finalisation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MesParcoursListView(generics.ListAPIView):
    serializer_class = ParcoursListSerializer
    permission_classes = [IsAuthenticated, IsStagiaire]

    def get_queryset(self):
        return Parcours.objects.filter(
            stagiaire=self.request.user.stagiaire_profile
        ).order_by('-date_realisation')


class ParcoursResultatsView(generics.RetrieveAPIView):
    serializer_class = ParcoursResultatsSerializer
    permission_classes = [IsAuthenticated, IsStagiaire]

    def get_queryset(self):
        return Parcours.objects.filter(
            stagiaire=self.request.user.stagiaire_profile,
            statut__in=['TERMINE', 'ABANDONNE']
        )
