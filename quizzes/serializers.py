from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Questionnaire, Question, Reponse


class ReponseSerializer(serializers.ModelSerializer):
    """
    Serializer pour les réponses d'une question
    """
    question_id = serializers.ReadOnlyField(source='question.id')

    class Meta:
        model = Reponse
        fields = ['id', 'question_id', 'texte', 'est_correcte']

    def validate_texte(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Le texte de la réponse ne peut pas être vide.')
        return value.strip()


class QuestionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage détaillé d'une question avec ses réponses
    """
    reponses = ReponseSerializer(many=True, read_only=True)
    nombre_reponses = serializers.ReadOnlyField()
    questionnaire_id = serializers.ReadOnlyField(source='questionnaire.id')

    class Meta:
        model = Question
        fields = ['id', 'questionnaire_id', 'intitule', 'reponses', 'nombre_reponses']


class QuestionNestedSerializer(serializers.ModelSerializer):
    """
    Serializer pour les questions imbriquées dans un questionnaire (sans questionnaire_id)
    """
    reponses = ReponseSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'intitule', 'reponses']

    def validate_intitule(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('L\'intitulé de la question ne peut pas être vide.')
        return value.strip()

    def validate_reponses(self, value):
        if len(value) < 2:
            raise serializers.ValidationError('Une question doit avoir au moins 2 réponses.')

        if len(value) > 5:
            raise serializers.ValidationError('Une question ne peut pas avoir plus de 5 réponses.')

        # Vérifier qu'il y a au moins une réponse correcte
        correctes = [r for r in value if r.get('est_correcte', False)]

        if len(correctes) == 0:
            # Marquer la première réponse comme correcte par défaut
            value[0]['est_correcte'] = True

        return value


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer/modifier une question avec ses réponses (pour endpoint indépendant)
    """
    reponses = ReponseSerializer(many=True)
    questionnaire_id = serializers.IntegerField(required=True)

    class Meta:
        model = Question
        fields = ['id', 'questionnaire_id', 'intitule', 'reponses']

    def validate_intitule(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('L\'intitulé de la question ne peut pas être vide.')
        return value.strip()

    def validate_reponses(self, value):
        if len(value) < 2:
            raise serializers.ValidationError('Une question doit avoir au moins 2 réponses.')

        if len(value) > 5:
            raise serializers.ValidationError('Une question ne peut pas avoir plus de 5 réponses.')

        # Vérifier qu'il y a au moins une réponse correcte
        correctes = [r for r in value if r.get('est_correcte', False)]

        if len(correctes) == 0:
            # Marquer la première réponse comme correcte par défaut
            value[0]['est_correcte'] = True

        return value



    def validate_questionnaire_id(self, value):
        if value is not None:
            try:
                Questionnaire.objects.get(id=value)
            except Questionnaire.DoesNotExist:
                raise serializers.ValidationError('Le questionnaire spécifié n\'existe pas.')
        return value

    def create(self, validated_data):
        reponses_data = validated_data.pop('reponses')
        questionnaire_id = validated_data.pop('questionnaire_id', None)

        if questionnaire_id is None:
            raise serializers.ValidationError('Le champ questionnaire_id est requis.')

        with transaction.atomic():
            questionnaire = Questionnaire.objects.get(id=questionnaire_id)
            question = Question.objects.create(questionnaire=questionnaire, **validated_data)

            for reponse_data in reponses_data:
                Reponse.objects.create(question=question, **reponse_data)

            return question

    def update(self, instance, validated_data):
        reponses_data = validated_data.pop('reponses', None)

        with transaction.atomic():
            # Mettre à jour la question
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Mettre à jour les réponses si fournies
            if reponses_data is not None:
                # Supprimer les anciennes réponses
                instance.reponses.all().delete()

                # Créer les nouvelles réponses
                for reponse_data in reponses_data:
                    Reponse.objects.create(question=instance, **reponse_data)

            return instance


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer simple pour une question (pour les stagiaires)
    """
    reponses = ReponseSerializer(many=True, read_only=True)
    questionnaire_id = serializers.ReadOnlyField(source='questionnaire.id')

    class Meta:
        model = Question
        fields = ['id', 'questionnaire_id', 'intitule', 'reponses']


class QuestionnaireListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des questionnaires
    """
    questions = QuestionDetailSerializer(many=True, read_only=True)
    nombre_questions = serializers.ReadOnlyField()

    class Meta:
        model = Questionnaire
        fields = [
            'id', 'nom', 'description', 'date_creation',
            'duree_minutes', 'questions', 'nombre_questions'
        ]


class QuestionnaireDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'affichage détaillé d'un questionnaire avec ses questions
    """
    questions = QuestionDetailSerializer(many=True, read_only=True)
    nombre_questions = serializers.ReadOnlyField()

    # Statistiques
    nombre_parcours = serializers.SerializerMethodField()
    note_moyenne = serializers.SerializerMethodField()
    derniere_utilisation = serializers.SerializerMethodField()

    class Meta:
        model = Questionnaire
        fields = [
            'id', 'nom', 'description', 'date_creation',
            'duree_minutes', 'questions', 'nombre_questions',
            'nombre_parcours', 'note_moyenne', 'derniere_utilisation'
        ]

    def get_nombre_parcours(self, obj):
        return obj.parcours.count()

    def get_note_moyenne(self, obj):
        from django.db.models import Avg
        avg_note = obj.parcours.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).aggregate(avg=Avg('note_obtenue'))['avg']

        return round(avg_note, 2) if avg_note else None

    def get_derniere_utilisation(self, obj):
        dernier_parcours = obj.parcours.order_by('-date_realisation').first()
        return dernier_parcours.date_realisation if dernier_parcours else None


class QuestionnaireCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer/modifier un questionnaire avec ses questions
    """
    questions = QuestionNestedSerializer(many=True, required=False)

    class Meta:
        model = Questionnaire
        fields = ['id', 'nom', 'description', 'duree_minutes', 'questions']

    def validate_nom(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Le nom du questionnaire ne peut pas être vide.')

        nom = value.strip()

        # Vérifier l'unicité du nom (exclure l'instance actuelle lors de la mise à jour)
        queryset = Questionnaire.objects.filter(nom__iexact=nom)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError('Un questionnaire avec ce nom existe déjà.')

        return nom

    def validate_description(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError('La description ne peut pas être vide si elle est fournie.')
        return value.strip() if value else value

    def validate_duree_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError('La durée doit être positive.')
        return value

    def validate_questions(self, value):
        if value and len(value) == 0:
            raise serializers.ValidationError('Si des questions sont fournies, il doit y en avoir au moins une.')
        return value

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])

        with transaction.atomic():
            questionnaire = Questionnaire.objects.create(**validated_data)

            for question_data in questions_data:
                reponses_data = question_data.pop('reponses', [])
                question = Question.objects.create(questionnaire=questionnaire, **question_data)

                # Appliquer la validation des réponses
                if len(reponses_data) < 2:
                    raise serializers.ValidationError('Chaque question doit avoir au moins 2 réponses.')

                if len(reponses_data) > 5:
                    raise serializers.ValidationError('Chaque question ne peut pas avoir plus de 5 réponses.')

                # Vérifier qu'il y a au moins une réponse correcte
                correctes = [r for r in reponses_data if r.get('est_correcte', False)]
                if len(correctes) == 0:
                    reponses_data[0]['est_correcte'] = True

                for reponse_data in reponses_data:
                    Reponse.objects.create(question=question, **reponse_data)

            return questionnaire

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)

        with transaction.atomic():
            # Mettre à jour le questionnaire
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Mettre à jour les questions si fournies
            if questions_data is not None:
                # Supprimer les anciennes questions (cascade supprime les réponses)
                instance.questions.all().delete()

                # Créer les nouvelles questions
                for question_data in questions_data:
                    reponses_data = question_data.pop('reponses', [])
                    question = Question.objects.create(questionnaire=instance, **question_data)

                    # Appliquer la validation des réponses
                    if len(reponses_data) < 2:
                        raise serializers.ValidationError('Chaque question doit avoir au moins 2 réponses.')

                    if len(reponses_data) > 5:
                        raise serializers.ValidationError('Chaque question ne peut pas avoir plus de 5 réponses.')

                    # Vérifier qu'il y a au moins une réponse correcte
                    correctes = [r for r in reponses_data if r.get('est_correcte', False)]
                    if len(correctes) == 0:
                        reponses_data[0]['est_correcte'] = True

                    for reponse_data in reponses_data:
                        Reponse.objects.create(question=question, **reponse_data)

            return instance


class QuestionnaireStatsSerializer(serializers.ModelSerializer):
    """
    Serializer pour les statistiques détaillées d'un questionnaire
    """
    nombre_questions = serializers.ReadOnlyField()
    nombre_parcours = serializers.SerializerMethodField()
    nombre_parcours_termines = serializers.SerializerMethodField()
    note_moyenne = serializers.SerializerMethodField()
    note_mediane = serializers.SerializerMethodField()
    note_minimale = serializers.SerializerMethodField()
    note_maximale = serializers.SerializerMethodField()
    temps_moyen_minutes = serializers.SerializerMethodField()
    taux_reussite = serializers.SerializerMethodField()
    derniere_utilisation = serializers.SerializerMethodField()
    utilisation_par_mois = serializers.SerializerMethodField()

    class Meta:
        model = Questionnaire
        fields = [
            'id', 'nom', 'nombre_questions', 'duree_minutes',
            'nombre_parcours', 'nombre_parcours_termines',
            'note_moyenne', 'note_mediane', 'note_minimale', 'note_maximale',
            'temps_moyen_minutes', 'taux_reussite', 'derniere_utilisation',
            'utilisation_par_mois'
        ]

    def get_nombre_parcours(self, obj):
        return obj.parcours.count()

    def get_nombre_parcours_termines(self, obj):
        return obj.parcours.filter(statut='TERMINE').count()

    def get_note_moyenne(self, obj):
        from django.db.models import Avg
        avg_note = obj.parcours.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).aggregate(avg=Avg('note_obtenue'))['avg']
        return round(avg_note, 2) if avg_note else None

    def get_note_mediane(self, obj):
        from django.db.models import Count
        parcours_notes = obj.parcours.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).values_list('note_obtenue', flat=True).order_by('note_obtenue')

        if parcours_notes:
            n = len(parcours_notes)
            if n % 2 == 0:
                return round((parcours_notes[n//2-1] + parcours_notes[n//2]) / 2, 2)
            else:
                return round(parcours_notes[n//2], 2)
        return None

    def get_note_minimale(self, obj):
        from django.db.models import Min
        min_note = obj.parcours.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).aggregate(min=Min('note_obtenue'))['min']
        return round(min_note, 2) if min_note else None

    def get_note_maximale(self, obj):
        from django.db.models import Max
        max_note = obj.parcours.filter(
            statut='TERMINE',
            note_obtenue__isnull=False
        ).aggregate(max=Max('note_obtenue'))['max']
        return round(max_note, 2) if max_note else None

    def get_temps_moyen_minutes(self, obj):
        from django.db.models import Avg
        avg_temps = obj.parcours.filter(
            statut='TERMINE'
        ).aggregate(avg=Avg('temps_passe_sec'))['avg']
        return round(avg_temps / 60, 1) if avg_temps else None

    def get_taux_reussite(self, obj):
        parcours_termines = obj.parcours.filter(statut='TERMINE')
        if not parcours_termines.exists():
            return None

        parcours_reussis = parcours_termines.filter(note_obtenue__gte=10)  # Seuil de réussite à 10/20
        return round((parcours_reussis.count() / parcours_termines.count()) * 100, 1)

    def get_derniere_utilisation(self, obj):
        dernier_parcours = obj.parcours.order_by('-date_realisation').first()
        return dernier_parcours.date_realisation if dernier_parcours else None

    def get_utilisation_par_mois(self, obj):
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        from datetime import datetime, timedelta

        # Derniers 6 mois
        six_months_ago = datetime.now() - timedelta(days=180)

        utilisation = obj.parcours.filter(
            date_realisation__gte=six_months_ago
        ).annotate(
            mois=TruncMonth('date_realisation')
        ).values('mois').annotate(
            count=Count('id')
        ).order_by('mois')

        return [
            {
                'mois': item['mois'].strftime('%Y-%m'),
                'utilisations': item['count']
            } for item in utilisation
        ]