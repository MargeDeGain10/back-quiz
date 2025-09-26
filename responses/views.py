from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from users.permissions import IsStagiaire, IsAdmin
from users.models import Stagiaire
from .models import (
    Parcours, ReponseUtilisateur, ReponseUtilisateurSelection,
    AnalyseQuestion, AnalyseStagiaire, AnalyseQuestionnaire
)
from .serializers import (
    QuestionnairesDisponiblesSerializer, ParcoursListSerializer,
    ParcoursDetailSerializer, QuestionCouranteSerializer,
    ReponseUtilisateurSerializer, ParcoursResultatsSerializer,
    DemarrerParcoursSerializer, ParcoursResultatsDetaillesSerializer,
    AnalyseQuestionSerializer, AnalyseStagiaireSerializer,
    AnalyseQuestionnaireSerializer, SyntheseStagiaireSerializer,
    StatistiquesGlobalesSerializer, RepondreQuestionSerializer
)
from quizzes.models import Questionnaire, Question, Reponse


class QuestionnairesDisponiblesListView(generics.ListAPIView):
    serializer_class = QuestionnairesDisponiblesSerializer
    permission_classes = [IsAuthenticated, IsStagiaire]

    def get_queryset(self):
        return Questionnaire.objects.all().order_by('nom')


class ParcoursListCreateView(generics.ListCreateAPIView):
    """
    GET: Liste des parcours (stagiaires: leurs parcours, admins: tous les parcours)
    POST: Démarrer un nouveau parcours (stagiaires uniquement)
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, 'stagiaire_profile'):
            # Stagiaire : ses propres parcours
            return Parcours.objects.filter(
                stagiaire=self.request.user.stagiaire_profile
            ).order_by('-date_realisation')
        else:
            # Admin : tous les parcours
            return Parcours.objects.all().order_by('-date_realisation')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DemarrerParcoursSerializer
        return ParcoursListSerializer

    def create(self, request, *args, **kwargs):
        # Seuls les stagiaires peuvent démarrer des parcours
        if not hasattr(request.user, 'stagiaire_profile'):
            return Response(
                {'error': 'Seuls les stagiaires peuvent démarrer des parcours.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data, context={'request': request})

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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, 'stagiaire_profile'):
            # Stagiaire : ses propres parcours uniquement
            return Parcours.objects.filter(stagiaire=self.request.user.stagiaire_profile)
        else:
            # Admin : tous les parcours
            return Parcours.objects.all()


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


@extend_schema(
    request=RepondreQuestionSerializer,
    responses={
        200: {"description": "Réponse enregistrée avec succès"},
        400: {"description": "Erreur de validation"},
    },
    description="Répondre à une question dans un parcours en cours",
    summary="Répondre à une question"
)
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
                question=question,
                temps_reponse_sec=temps_reponse_sec
            )

            # Ajouter les sélections de réponses
            for reponse_id in reponses_selectionnees_ids:
                reponse = Reponse.objects.get(id=reponse_id)
                ReponseUtilisateurSelection.objects.create(
                    reponse_utilisateur=reponse_utilisateur,
                    reponse=reponse
                )

            # Calculer et sauvegarder le score de cette réponse
            reponse_utilisateur.score_obtenu = reponse_utilisateur.calculer_score()
            reponse_utilisateur.save()

            # Mettre à jour le temps passé du parcours
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
                parcours.note_sur_20 = None
                message = 'Parcours abandonné.'
            else:
                parcours.statut = 'TERMINE'
                parcours.note_obtenue = parcours.calculer_note()
                parcours.note_sur_20 = parcours.calculer_note_sur_20()
                parcours.temps_moyen_par_question = parcours.calculer_temps_moyen_par_question()
                message = f'Parcours terminé. Note obtenue: {parcours.note_obtenue}/100 ({parcours.note_sur_20}/20)'

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


# ============ NOUVELLES VUES AVANCÉES ============

class ParcoursResultatsDetaillesView(generics.RetrieveAPIView):
    """Vue pour résultats détaillés avec analyses avancées"""
    serializer_class = ParcoursResultatsDetaillesSerializer
    permission_classes = [IsAuthenticated, IsStagiaire]

    def get_queryset(self):
        return Parcours.objects.filter(
            stagiaire=self.request.user.stagiaire_profile,
            statut__in=['TERMINE', 'ABANDONNE']
        )

    def retrieve(self, request, *args, **kwargs):
        parcours = self.get_object()

        # Calculer et sauvegarder la note sur 20 si pas déjà fait
        if parcours.note_sur_20 is None:
            parcours.note_sur_20 = parcours.calculer_note_sur_20()
            parcours.temps_moyen_par_question = parcours.calculer_temps_moyen_par_question()
            parcours.save()

        # Calculer les scores détaillés pour chaque réponse
        for reponse_user in parcours.reponses_utilisateur.all():
            if reponse_user.score_obtenu is None:
                reponse_user.score_obtenu = reponse_user.calculer_score()
                reponse_user.save()

        return super().retrieve(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def synthese_stagiaire(request, stagiaire_id):
    """Vue synthèse complète d'un stagiaire pour les admins"""
    try:
        stagiaire = Stagiaire.objects.get(id=stagiaire_id)

        # Créer ou mettre à jour l'analyse du stagiaire
        analyse, created = AnalyseStagiaire.objects.get_or_create(stagiaire=stagiaire)
        analyse.mettre_a_jour_statistiques()

        serializer = SyntheseStagiaireSerializer(stagiaire, context={'request': request})
        return Response(serializer.data)

    except Stagiaire.DoesNotExist:
        return Response(
            {'error': 'Stagiaire introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def statistiques_questionnaire_avancees(request, questionnaire_id):
    """Statistiques avancées d'un questionnaire pour les admins"""
    try:
        questionnaire = Questionnaire.objects.get(id=questionnaire_id)

        # Créer ou mettre à jour l'analyse du questionnaire
        analyse, created = AnalyseQuestionnaire.objects.get_or_create(questionnaire=questionnaire)
        analyse.mettre_a_jour_statistiques()

        # Mettre à jour les analyses des questions
        for question in questionnaire.questions.all():
            analyse_question, created = AnalyseQuestion.objects.get_or_create(question=question)
            analyse_question.mettre_a_jour_statistiques()

        serializer = AnalyseQuestionnaireSerializer(analyse, context={'request': request})
        return Response(serializer.data)

    except Questionnaire.DoesNotExist:
        return Response(
            {'error': 'Questionnaire introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def synthese_globale(request):
    """Dashboard principal avec statistiques globales pour les admins"""

    # Mettre à jour les analyses de tous les stagiaires actifs
    for stagiaire in Stagiaire.objects.filter(user__is_active=True):
        if stagiaire.parcours.filter(statut='TERMINE').exists():
            analyse, created = AnalyseStagiaire.objects.get_or_create(stagiaire=stagiaire)
            analyse.mettre_a_jour_statistiques()

    # Mettre à jour les analyses de tous les questionnaires utilisés
    for questionnaire in Questionnaire.objects.filter(parcours__isnull=False).distinct():
        analyse, created = AnalyseQuestionnaire.objects.get_or_create(questionnaire=questionnaire)
        analyse.mettre_a_jour_statistiques()

    # Utiliser un objet factice car le serializer n'a pas besoin d'instance
    serializer = StatistiquesGlobalesSerializer()
    data = serializer.to_representation(None)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def analyse_questions_difficiles(request):
    """Endpoint pour analyser les questions les plus difficiles du système"""
    seuil = request.GET.get('seuil', 60)
    try:
        seuil = float(seuil)
    except (ValueError, TypeError):
        seuil = 60

    questions_difficiles = []

    # Analyser toutes les questions qui ont été tentées
    for question in Question.objects.filter(reponses_utilisateur__isnull=False).distinct():
        analyse, created = AnalyseQuestion.objects.get_or_create(question=question)
        analyse.mettre_a_jour_statistiques()

        if analyse.taux_reussite < seuil and analyse.nombre_tentatives >= 3:  # Au moins 3 tentatives
            questions_difficiles.append(analyse)

    # Trier par taux de réussite croissant (plus difficile en premier)
    questions_difficiles.sort(key=lambda x: x.taux_reussite)

    serializer = AnalyseQuestionSerializer(questions_difficiles[:20], many=True)  # Top 20
    return Response({
        'seuil_utilise': seuil,
        'nombre_questions_analysees': len(questions_difficiles),
        'questions_difficiles': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def export_donnees(request):
    """Export des données en CSV pour reporting"""
    import csv
    from django.http import HttpResponse
    from io import StringIO

    type_export = request.data.get('type', 'parcours')

    if type_export == 'parcours':
        # Export des parcours terminés
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="parcours_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Stagiaire', 'Email', 'Société', 'Questionnaire',
            'Date', 'Statut', 'Note (/100)', 'Note (/20)', 'Temps (min)',
            'Questions correctes', 'Total questions'
        ])

        for parcours in Parcours.objects.filter(statut__in=['TERMINE', 'ABANDONNE']).select_related(
            'stagiaire__user', 'questionnaire'
        ):
            stats = parcours.calculer_statistiques_detaillees()
            writer.writerow([
                parcours.id,
                f"{parcours.stagiaire.user.prenom} {parcours.stagiaire.user.nom}",
                parcours.stagiaire.user.email,
                parcours.stagiaire.societe,
                parcours.questionnaire.nom,
                parcours.date_realisation.strftime('%Y-%m-%d %H:%M'),
                parcours.statut,
                parcours.note_obtenue or 0,
                parcours.note_sur_20 or 0,
                parcours.temps_passe_minutes,
                stats['questions_correctes'],
                parcours.questionnaire.nombre_questions
            ])

        return response

    elif type_export == 'stagiaires':
        # Export des analyses stagiaires
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stagiaires_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Nom', 'Prénom', 'Email', 'Société', 'Questionnaires terminés',
            'Note moyenne (/20)', 'Temps total (h)', 'Niveau', 'Actif'
        ])

        for analyse in AnalyseStagiaire.objects.select_related('stagiaire__user'):
            writer.writerow([
                analyse.stagiaire.user.nom,
                analyse.stagiaire.user.prenom,
                analyse.stagiaire.user.email,
                analyse.stagiaire.societe,
                analyse.nombre_questionnaires_termines,
                analyse.note_moyenne_sur_20,
                analyse.temps_formation_heures,
                analyse.niveau_global,
                'Oui' if analyse.stagiaire.user.is_active else 'Non'
            ])

        return response

    else:
        return Response(
            {'error': 'Type d\'export non supporté. Utilisez "parcours" ou "stagiaires".'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mes_recommandations(request):
    """Recommandations personnalisées pour le stagiaire connecté"""
    if not hasattr(request.user, 'stagiaire_profile'):
        return Response(
            {'error': 'Accès réservé aux stagiaires.'},
            status=status.HTTP_403_FORBIDDEN
        )

    stagiaire = request.user.stagiaire_profile

    # Créer ou mettre à jour l'analyse
    analyse, created = AnalyseStagiaire.objects.get_or_create(stagiaire=stagiaire)
    analyse.mettre_a_jour_statistiques()

    recommandations = {
        'niveau_actuel': analyse.niveau_global,
        'note_moyenne': analyse.note_moyenne_sur_20,
        'points_forts': [],
        'points_amelioration': analyse.obtenir_domaines_amelioration(),
        'questionnaires_suggeres': [],
        'objectifs_personnalises': []
    }

    # Identifier les points forts
    parcours_excellents = stagiaire.parcours.filter(
        statut='TERMINE',
        note_sur_20__gte=16
    ).count()

    if parcours_excellents > 0:
        recommandations['points_forts'].append(
            f"Excellente performance sur {parcours_excellents} questionnaire(s)"
        )

    parcours_rapides = stagiaire.parcours.filter(
        statut='TERMINE',
        temps_moyen_par_question__lt=60
    ).count()

    if parcours_rapides > 0:
        recommandations['points_forts'].append(
            f"Rapidité d'exécution sur {parcours_rapides} questionnaire(s)"
        )

    # Suggérer des questionnaires
    questionnaires_non_tentes = Questionnaire.objects.exclude(
        parcours__stagiaire=stagiaire
    )

    if questionnaires_non_tentes.exists():
        # Suggérer les questionnaires les plus populaires non tentés
        for questionnaire in questionnaires_non_tentes[:3]:
            recommandations['questionnaires_suggeres'].append({
                'id': questionnaire.id,
                'nom': questionnaire.nom,
                'description': questionnaire.description,
                'duree_minutes': questionnaire.duree_minutes,
                'nombre_questions': questionnaire.nombre_questions
            })

    # Objectifs personnalisés
    if analyse.note_moyenne_sur_20 < 12:
        recommandations['objectifs_personnalises'].append(
            "Objectif: Atteindre une moyenne de 12/20"
        )
    elif analyse.note_moyenne_sur_20 < 16:
        recommandations['objectifs_personnalises'].append(
            "Objectif: Atteindre une moyenne de 16/20 (niveau Excellence)"
        )

    if analyse.nombre_questionnaires_termines < 5:
        recommandations['objectifs_personnalises'].append(
            "Objectif: Terminer 5 questionnaires pour débloquer le badge Persévérant"
        )

    return Response(recommandations)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def recalculer_analyses(request):
    """Recalcule toutes les analyses du système (utile après des modifications)"""
    operations = {
        'stagiaires_analyses': 0,
        'questionnaires_analyses': 0,
        'questions_analysees': 0
    }

    # Recalculer analyses stagiaires
    for stagiaire in Stagiaire.objects.all():
        if stagiaire.parcours.exists():
            analyse, created = AnalyseStagiaire.objects.get_or_create(stagiaire=stagiaire)
            analyse.mettre_a_jour_statistiques()
            operations['stagiaires_analyses'] += 1

    # Recalculer analyses questionnaires
    for questionnaire in Questionnaire.objects.filter(parcours__isnull=False).distinct():
        analyse, created = AnalyseQuestionnaire.objects.get_or_create(questionnaire=questionnaire)
        analyse.mettre_a_jour_statistiques()
        operations['questionnaires_analyses'] += 1

        # Recalculer analyses questions
        for question in questionnaire.questions.all():
            if question.reponses_utilisateur.exists():
                analyse_q, created = AnalyseQuestion.objects.get_or_create(question=question)
                analyse_q.mettre_a_jour_statistiques()
                operations['questions_analysees'] += 1

    return Response({
        'message': 'Recalcul terminé avec succès',
        'operations_effectuees': operations
    })
