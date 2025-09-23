from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Parcours, ReponseUtilisateur, ReponseUtilisateurSelection
from quizzes.models import Questionnaire, Question, Reponse
from quizzes.serializers import QuestionnaireListSerializer, QuestionSerializer, ReponseSerializer
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