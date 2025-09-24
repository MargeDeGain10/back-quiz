from rest_framework import serializers
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
from datetime import timedelta
from .models import (
    Parcours, ReponseUtilisateur, ReponseUtilisateurSelection,
    AnalyseQuestion, AnalyseStagiaire, AnalyseQuestionnaire
)
from quizzes.models import Questionnaire, Question, Reponse
from quizzes.serializers import QuestionnaireListSerializer, QuestionSerializer, ReponseSerializer
from users.models import Stagiaire
from users.permissions import IsStagiaire


class QuestionnairesDisponiblesSerializer(serializers.ModelSerializer):
    nombre_questions = serializers.IntegerField(read_only=True)
    duree_minutes = serializers.IntegerField(source='duree', read_only=True)
    deja_realise = serializers.SerializerMethodField()

    class Meta:
        model = Questionnaire
        fields = [
            'id', 'nom', 'description', 'duree_minutes',
            'nombre_questions', 'deja_realise'
        ]

    def get_deja_realise(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'stagiaire_profile'):
            return Parcours.objects.filter(
                stagiaire=request.user.stagiaire_profile,
                questionnaire=obj,
                statut__in=['TERMINE', 'ABANDONNE']
            ).exists()
        return False


class ParcoursListSerializer(serializers.ModelSerializer):
    questionnaire_nom = serializers.CharField(source='questionnaire.nom', read_only=True)
    temps_passe_minutes = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    progression_pourcentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = Parcours
        fields = [
            'id', 'questionnaire_nom', 'date_realisation', 'temps_passe_minutes',
            'note_obtenue', 'statut', 'progression_pourcentage'
        ]


class ParcoursDetailSerializer(serializers.ModelSerializer):
    questionnaire = QuestionnaireListSerializer(read_only=True)
    temps_passe_minutes = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    progression_pourcentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    question_courante_numero = serializers.SerializerMethodField()
    total_questions = serializers.IntegerField(source='questionnaire.nombre_questions', read_only=True)
    temps_limite_minutes = serializers.IntegerField(source='questionnaire.duree', read_only=True)
    temps_restant_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Parcours
        fields = [
            'id', 'questionnaire', 'date_realisation', 'temps_passe_minutes',
            'note_obtenue', 'statut', 'progression_pourcentage', 'question_courante_numero',
            'total_questions', 'temps_limite_minutes', 'temps_restant_minutes'
        ]

    def get_question_courante_numero(self, obj):
        return obj.reponses_utilisateur.count() + 1

    def get_temps_restant_minutes(self, obj):
        if obj.questionnaire.duree and obj.statut == 'EN_COURS':
            temps_ecoule = (timezone.now() - obj.date_realisation).total_seconds() / 60
            temps_restant = obj.questionnaire.duree - temps_ecoule
            return max(0, round(temps_restant, 1))
        return None


class QuestionCouranteSerializer(serializers.ModelSerializer):
    reponses = serializers.SerializerMethodField()
    numero_question = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'intitule', 'reponses', 'numero_question', 'total_questions'
        ]

    def get_reponses(self, obj):
        return ReponseSerializer(obj.reponses.all(), many=True).data

    def get_numero_question(self, obj):
        parcours = self.context.get('parcours')
        if parcours:
            return parcours.reponses_utilisateur.count() + 1
        return 1

    def get_total_questions(self, obj):
        parcours = self.context.get('parcours')
        if parcours:
            return parcours.questionnaire.nombre_questions
        return obj.questionnaire.nombre_questions


class ReponseUtilisateurSerializer(serializers.ModelSerializer):
    reponses_selectionnees_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    temps_reponse_sec = serializers.IntegerField(write_only=True, required=False, default=0)

    class Meta:
        model = ReponseUtilisateur
        fields = ['id', 'question', 'reponses_selectionnees_ids', 'temps_reponse_sec']
        read_only_fields = ['id']

    def validate_reponses_selectionnees_ids(self, value):
        if value:
            question = self.initial_data.get('question')
            if question:
                valid_reponse_ids = Reponse.objects.filter(question_id=question).values_list('id', flat=True)
                for reponse_id in value:
                    if reponse_id not in valid_reponse_ids:
                        raise serializers.ValidationError(
                            f"La réponse {reponse_id} n'appartient pas à cette question."
                        )
        return value


class ReponseUtilisateurDetailSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    reponses_selectionnees = serializers.SerializerMethodField()
    est_correcte = serializers.SerializerMethodField()

    class Meta:
        model = ReponseUtilisateur
        fields = ['id', 'question', 'reponses_selectionnees', 'est_correcte']

    def get_reponses_selectionnees(self, obj):
        return ReponseSerializer(obj.reponses_selectionnees, many=True).data

    def get_est_correcte(self, obj):
        reponses_correctes = obj.question.reponses_correctes
        reponses_selectionnees = obj.reponses_selectionnees
        return (set(reponses_correctes) == set(reponses_selectionnees) and
                reponses_correctes.count() > 0)


class ParcoursResultatsSerializer(serializers.ModelSerializer):
    questionnaire = QuestionnaireListSerializer(read_only=True)
    reponses_utilisateur = ReponseUtilisateurDetailSerializer(many=True, read_only=True)
    temps_passe_minutes = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    total_questions = serializers.IntegerField(source='questionnaire.nombre_questions', read_only=True)
    questions_correctes = serializers.SerializerMethodField()
    pourcentage_reussite = serializers.SerializerMethodField()

    class Meta:
        model = Parcours
        fields = [
            'id', 'questionnaire', 'date_realisation', 'temps_passe_minutes',
            'note_obtenue', 'statut', 'total_questions', 'questions_correctes',
            'pourcentage_reussite', 'reponses_utilisateur'
        ]

    def get_questions_correctes(self, obj):
        correctes = 0
        for reponse_user in obj.reponses_utilisateur.all():
            reponses_correctes = reponse_user.question.reponses_correctes
            reponses_selectionnees = reponse_user.reponses_selectionnees
            if (set(reponses_correctes) == set(reponses_selectionnees) and
                reponses_correctes.count() > 0):
                correctes += 1
        return correctes

    def get_pourcentage_reussite(self, obj):
        if obj.note_obtenue is not None:
            return float(obj.note_obtenue)
        return obj.calculer_note()


class DemarrerParcoursSerializer(serializers.Serializer):
    questionnaire_id = serializers.IntegerField()

    def validate_questionnaire_id(self, value):
        try:
            questionnaire = Questionnaire.objects.get(id=value)
        except Questionnaire.DoesNotExist:
            raise serializers.ValidationError("Questionnaire introuvable.")

        request = self.context.get('request')
        if request and hasattr(request.user, 'stagiaire_profile'):
            parcours_en_cours = Parcours.objects.filter(
                stagiaire=request.user.stagiaire_profile,
                questionnaire=questionnaire,
                statut='EN_COURS'
            ).exists()

            if parcours_en_cours:
                raise serializers.ValidationError(
                    "Vous avez déjà un parcours en cours pour ce questionnaire."
                )

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        questionnaire = Questionnaire.objects.get(id=validated_data['questionnaire_id'])

        parcours = Parcours.objects.create(
            stagiaire=request.user.stagiaire_profile,
            questionnaire=questionnaire,
            statut='EN_COURS',
            temps_passe_sec=0
        )

        return parcours


# ============ NOUVEAUX SERIALIZERS AVANCÉS ============

class ReponseUtilisateurDetailledSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour les réponses avec scores et temps"""
    question = QuestionSerializer(read_only=True)
    reponses_selectionnees = ReponseSerializer(many=True, read_only=True)
    est_correcte = serializers.BooleanField(read_only=True)
    est_partiellement_correcte = serializers.BooleanField(read_only=True)
    score_calcule = serializers.SerializerMethodField()
    efficacite_temporelle = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    temps_reponse_minutes = serializers.SerializerMethodField()

    class Meta:
        model = ReponseUtilisateur
        fields = [
            'id', 'question', 'reponses_selectionnees', 'est_correcte',
            'est_partiellement_correcte', 'score_obtenu', 'score_calcule',
            'temps_reponse_sec', 'temps_reponse_minutes', 'efficacite_temporelle',
            'date_reponse'
        ]

    def get_score_calcule(self, obj):
        return float(obj.calculer_score())

    def get_temps_reponse_minutes(self, obj):
        return round(obj.temps_reponse_sec / 60, 1) if obj.temps_reponse_sec > 0 else 0


class ParcoursResultatsDetaillesSerializer(serializers.ModelSerializer):
    """Serializer pour résultats détaillés avec analyses avancées"""
    questionnaire = QuestionnaireListSerializer(read_only=True)
    stagiaire_nom = serializers.CharField(source='stagiaire.user.nom', read_only=True)
    stagiaire_prenom = serializers.CharField(source='stagiaire.user.prenom', read_only=True)
    stagiaire_societe = serializers.CharField(source='stagiaire.societe', read_only=True)

    # Scores et notes
    note_sur_20 = serializers.DecimalField(max_digits=4, decimal_places=2, read_only=True)
    niveau_performance = serializers.CharField(read_only=True)

    # Temps et progression
    temps_passe_minutes = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    temps_moyen_par_question = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    progression_pourcentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    # Statistiques détaillées
    statistiques_detaillees = serializers.SerializerMethodField()
    recommandations = serializers.ListField(read_only=True)

    # Réponses détaillées
    reponses_utilisateur = ReponseUtilisateurDetailledSerializer(many=True, read_only=True)

    # Comparaison avec autres stagiaires
    comparaison_moyenne = serializers.SerializerMethodField()

    class Meta:
        model = Parcours
        fields = [
            'id', 'questionnaire', 'stagiaire_nom', 'stagiaire_prenom', 'stagiaire_societe',
            'date_realisation', 'statut', 'note_obtenue', 'note_sur_20', 'niveau_performance',
            'temps_passe_minutes', 'temps_moyen_par_question', 'progression_pourcentage',
            'penalites_appliquees', 'statistiques_detaillees', 'recommandations',
            'reponses_utilisateur', 'comparaison_moyenne'
        ]

    def get_statistiques_detaillees(self, obj):
        return obj.calculer_statistiques_detaillees()

    def get_comparaison_moyenne(self, obj):
        """Compare avec la moyenne des autres stagiaires"""
        autres_parcours = Parcours.objects.filter(
            questionnaire=obj.questionnaire,
            statut='TERMINE'
        ).exclude(id=obj.id)

        if not autres_parcours.exists():
            return None

        moyenne_note = autres_parcours.aggregate(avg=Avg('note_obtenue'))['avg']
        moyenne_temps = autres_parcours.aggregate(avg=Avg('temps_passe_sec'))['avg']

        return {
            'note_moyenne_autres': round(moyenne_note, 2) if moyenne_note else None,
            'temps_moyen_autres_minutes': round(moyenne_temps / 60, 1) if moyenne_temps else None,
            'meilleur_que_pourcentage': self._calculer_classement(obj, autres_parcours),
            'nombre_comparaisons': autres_parcours.count()
        }

    def _calculer_classement(self, obj, autres_parcours):
        """Calcule le pourcentage de stagiaires moins performants"""
        if obj.note_obtenue is None:
            return None

        moins_performants = autres_parcours.filter(note_obtenue__lt=obj.note_obtenue).count()
        total = autres_parcours.count()

        if total > 0:
            return round((moins_performants / total) * 100, 1)
        return None


class AnalyseQuestionSerializer(serializers.ModelSerializer):
    """Serializer pour l'analyse des questions"""
    question = QuestionSerializer(read_only=True)
    niveau_difficulte = serializers.CharField(read_only=True)
    temps_moyen_minutes = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseQuestion
        fields = [
            'question', 'nombre_tentatives', 'nombre_reussites', 'taux_reussite',
            'niveau_difficulte', 'temps_moyen_reponse', 'temps_moyen_minutes',
            'derniere_mise_a_jour'
        ]

    def get_temps_moyen_minutes(self, obj):
        return round(obj.temps_moyen_reponse / 60, 1) if obj.temps_moyen_reponse > 0 else 0


class AnalyseStagiaireSerializer(serializers.ModelSerializer):
    """Serializer pour l'analyse des stagiaires"""
    stagiaire_nom = serializers.CharField(source='stagiaire.user.nom', read_only=True)
    stagiaire_prenom = serializers.CharField(source='stagiaire.user.prenom', read_only=True)
    stagiaire_email = serializers.CharField(source='stagiaire.user.email', read_only=True)
    stagiaire_societe = serializers.CharField(source='stagiaire.societe', read_only=True)
    temps_formation_heures = serializers.DecimalField(max_digits=6, decimal_places=1, read_only=True)
    domaines_amelioration = serializers.SerializerMethodField()
    evolution_performance = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseStagiaire
        fields = [
            'stagiaire_nom', 'stagiaire_prenom', 'stagiaire_email', 'stagiaire_societe',
            'nombre_questionnaires_termines', 'note_moyenne', 'note_moyenne_sur_20',
            'temps_total_formation', 'temps_formation_heures', 'niveau_global',
            'domaines_amelioration', 'evolution_performance', 'derniere_mise_a_jour'
        ]

    def get_domaines_amelioration(self, obj):
        return obj.obtenir_domaines_amelioration()

    def get_evolution_performance(self, obj):
        """Retourne l'évolution des performances dans le temps"""
        parcours = obj.stagiaire.parcours.filter(statut='TERMINE').order_by('date_realisation')

        if parcours.count() < 2:
            return None

        evolution = []
        for p in parcours:
            evolution.append({
                'date': p.date_realisation,
                'questionnaire': p.questionnaire.nom,
                'note': p.note_obtenue,
                'note_sur_20': p.note_sur_20
            })

        # Calcul de la tendance
        notes = [p.note_obtenue for p in parcours if p.note_obtenue is not None]
        if len(notes) >= 2:
            tendance = "En progression" if notes[-1] > notes[0] else "En régression" if notes[-1] < notes[0] else "Stable"
        else:
            tendance = "Insuffisant de données"

        return {
            'parcours': evolution,
            'tendance': tendance,
            'progression_totale': notes[-1] - notes[0] if len(notes) >= 2 else 0
        }


class AnalyseQuestionnaireSerializer(serializers.ModelSerializer):
    """Serializer pour l'analyse des questionnaires"""
    questionnaire = QuestionnaireListSerializer(read_only=True)
    niveau_difficulte_global = serializers.CharField(read_only=True)
    temps_moyen_minutes = serializers.DecimalField(max_digits=6, decimal_places=1, read_only=True)
    questions_difficiles = serializers.SerializerMethodField()
    repartition_notes = serializers.SerializerMethodField()

    class Meta:
        model = AnalyseQuestionnaire
        fields = [
            'questionnaire', 'nombre_passages', 'note_moyenne', 'note_mediane',
            'niveau_difficulte_global', 'temps_moyen_completion', 'temps_moyen_minutes',
            'taux_abandon', 'questions_difficiles', 'repartition_notes',
            'derniere_mise_a_jour'
        ]

    def get_questions_difficiles(self, obj):
        questions = obj.obtenir_questions_difficiles()
        return AnalyseQuestionSerializer([q['question'].analyse for q in questions], many=True).data

    def get_repartition_notes(self, obj):
        """Analyse de la répartition des notes"""
        parcours_termines = obj.questionnaire.parcours.filter(statut='TERMINE', note_obtenue__isnull=False)

        if not parcours_termines.exists():
            return None

        ranges = {
            '0-5': 0, '5-10': 0, '10-15': 0, '15-20': 0
        }

        for parcours in parcours_termines:
            note_20 = (parcours.note_obtenue / 100) * 20
            if note_20 < 5:
                ranges['0-5'] += 1
            elif note_20 < 10:
                ranges['5-10'] += 1
            elif note_20 < 15:
                ranges['10-15'] += 1
            else:
                ranges['15-20'] += 1

        total = parcours_termines.count()
        return {
            'repartition': ranges,
            'pourcentages': {k: round((v/total)*100, 1) for k, v in ranges.items()},
            'total_evaluations': total
        }


class SyntheseStagiaireSerializer(serializers.ModelSerializer):
    """Serializer pour la synthèse complète d'un stagiaire (pour admins)"""
    user_info = serializers.SerializerMethodField()
    analyse = AnalyseStagiaireSerializer(read_only=True)
    derniers_parcours = serializers.SerializerMethodField()
    statistiques_globales = serializers.SerializerMethodField()
    badges_obtenus = serializers.SerializerMethodField()

    class Meta:
        model = Stagiaire
        fields = [
            'user_info', 'societe', 'analyse', 'derniers_parcours',
            'statistiques_globales', 'badges_obtenus'
        ]

    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'nom': obj.user.nom,
            'prenom': obj.user.prenom,
            'email': obj.user.email,
            'date_inscription': obj.user.date_joined,
            'is_active': obj.user.is_active
        }

    def get_derniers_parcours(self, obj):
        parcours = obj.parcours.all().order_by('-date_realisation')[:5]
        return ParcoursListSerializer(parcours, many=True).data

    def get_statistiques_globales(self, obj):
        """Statistiques globales du stagiaire"""
        parcours_total = obj.parcours.count()
        parcours_termines = obj.parcours.filter(statut='TERMINE').count()
        parcours_abandonnes = obj.parcours.filter(statut='ABANDONNE').count()

        return {
            'total_parcours': parcours_total,
            'parcours_termines': parcours_termines,
            'parcours_abandonnes': parcours_abandonnes,
            'taux_completion': round((parcours_termines / parcours_total) * 100, 1) if parcours_total > 0 else 0,
            'premier_parcours': obj.parcours.order_by('date_realisation').first().date_realisation if obj.parcours.exists() else None,
            'dernier_parcours': obj.parcours.order_by('-date_realisation').first().date_realisation if obj.parcours.exists() else None
        }

    def get_badges_obtenus(self, obj):
        """Système de badges basé sur les performances"""
        badges = []

        try:
            analyse = obj.analyse

            # Badge perfectionniste
            parcours_parfaits = obj.parcours.filter(statut='TERMINE', note_obtenue=100).count()
            if parcours_parfaits >= 3:
                badges.append({
                    'nom': 'Perfectionniste',
                    'description': f'{parcours_parfaits} questionnaires réussis à 100%',
                    'icone': '🎯'
                })

            # Badge rapidité
            parcours_rapides = obj.parcours.filter(
                statut='TERMINE',
                temps_moyen_par_question__lt=60  # Moins d'1 minute par question
            ).count()
            if parcours_rapides >= 2:
                badges.append({
                    'nom': 'Éclair',
                    'description': f'{parcours_rapides} questionnaires complétés rapidement',
                    'icone': '⚡'
                })

            # Badge persévérance
            if analyse.nombre_questionnaires_termines >= 10:
                badges.append({
                    'nom': 'Persévérant',
                    'description': f'{analyse.nombre_questionnaires_termines} questionnaires terminés',
                    'icone': '🔥'
                })

            # Badge excellence
            if analyse.note_moyenne_sur_20 >= 16:
                badges.append({
                    'nom': 'Excellence',
                    'description': f'Moyenne générale: {analyse.note_moyenne_sur_20}/20',
                    'icone': '🏆'
                })

        except AnalyseStagiaire.DoesNotExist:
            pass

        return badges


class StatistiquesGlobalesSerializer(serializers.Serializer):
    """Serializer pour les statistiques globales du système"""
    statistiques_generales = serializers.SerializerMethodField()
    top_stagiaires = serializers.SerializerMethodField()
    top_questionnaires = serializers.SerializerMethodField()
    tendances_temporelles = serializers.SerializerMethodField()
    statistiques_societes = serializers.SerializerMethodField()

    def get_statistiques_generales(self, obj):
        total_stagiaires = Stagiaire.objects.count()
        total_questionnaires = Questionnaire.objects.count()
        total_parcours = Parcours.objects.count()
        parcours_termines = Parcours.objects.filter(statut='TERMINE').count()

        return {
            'total_stagiaires': total_stagiaires,
            'stagiaires_actifs': Stagiaire.objects.filter(user__is_active=True).count(),
            'total_questionnaires': total_questionnaires,
            'total_parcours': total_parcours,
            'parcours_termines': parcours_termines,
            'taux_completion_global': round((parcours_termines / total_parcours) * 100, 1) if total_parcours > 0 else 0,
            'note_moyenne_globale': self._calculer_note_moyenne_globale()
        }

    def get_top_stagiaires(self, obj):
        """Top 10 des meilleurs stagiaires"""
        analyses = AnalyseStagiaire.objects.filter(
            nombre_questionnaires_termines__gte=2
        ).order_by('-note_moyenne_sur_20')[:10]

        return [{
            'nom': analyse.stagiaire.user.nom,
            'prenom': analyse.stagiaire.user.prenom,
            'societe': analyse.stagiaire.societe,
            'note_moyenne': analyse.note_moyenne_sur_20,
            'questionnaires_termines': analyse.nombre_questionnaires_termines
        } for analyse in analyses]

    def get_top_questionnaires(self, obj):
        """Questionnaires les plus populaires"""
        analyses = AnalyseQuestionnaire.objects.filter(
            nombre_passages__gte=1
        ).order_by('-nombre_passages')[:10]

        return [{
            'nom': analyse.questionnaire.nom,
            'nombre_passages': analyse.nombre_passages,
            'note_moyenne': analyse.note_moyenne,
            'taux_abandon': analyse.taux_abandon
        } for analyse in analyses]

    def get_tendances_temporelles(self, obj):
        """Tendances d'activité des 6 derniers mois"""
        from django.db.models.functions import TruncMonth
        from datetime import datetime, timedelta
        from django.db.models import Q

        six_months_ago = timezone.now() - timedelta(days=180)

        parcours_par_mois = Parcours.objects.filter(
            date_realisation__gte=six_months_ago
        ).annotate(
            mois=TruncMonth('date_realisation')
        ).values('mois').annotate(
            total=Count('id'),
            termines=Count('id', filter=Q(statut='TERMINE'))
        ).order_by('mois')

        return [{
            'mois': item['mois'].strftime('%Y-%m'),
            'total_parcours': item['total'],
            'parcours_termines': item['termines'],
            'taux_completion': round((item['termines'] / item['total']) * 100, 1) if item['total'] > 0 else 0
        } for item in parcours_par_mois]

    def get_statistiques_societes(self, obj):
        """Statistiques par société"""
        from django.db.models import Q

        stats_societes = Stagiaire.objects.values('societe').annotate(
            nombre_stagiaires=Count('id'),
            parcours_termines=Count('parcours', filter=Q(parcours__statut='TERMINE')),
            note_moyenne=Avg('parcours__note_obtenue', filter=Q(parcours__statut='TERMINE'))
        ).order_by('-nombre_stagiaires')[:10]

        return [{
            'societe': stat['societe'],
            'nombre_stagiaires': stat['nombre_stagiaires'],
            'parcours_termines': stat['parcours_termines'] or 0,
            'note_moyenne': round(stat['note_moyenne'], 2) if stat['note_moyenne'] else 0
        } for stat in stats_societes]

    def _calculer_note_moyenne_globale(self):
        """Calcule la note moyenne globale du système"""
        moyenne = Parcours.objects.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).aggregate(avg=Avg('note_obtenue'))['avg']

        return round(moyenne, 2) if moyenne else 0

    def to_representation(self, instance):
        # Cette méthode est appelée pour sérialiser les données
        # On passe un objet factice car on n'a pas besoin d'instance spécifique
        return {
            'statistiques_generales': self.get_statistiques_generales(None),
            'top_stagiaires': self.get_top_stagiaires(None),
            'top_questionnaires': self.get_top_questionnaires(None),
            'tendances_temporelles': self.get_tendances_temporelles(None),
            'statistiques_societes': self.get_statistiques_societes(None)
        }