import django_filters
from django.db.models import Q
from .models import Questionnaire, Question


class QuestionnaireFilter(django_filters.FilterSet):
    """
    Filtre pour la recherche et le filtrage des questionnaires
    """
    # Recherche textuelle
    search = django_filters.CharFilter(method='filter_search', label='Recherche')

    # Filtres spécifiques
    nom = django_filters.CharFilter(field_name='nom', lookup_expr='icontains')
    description = django_filters.CharFilter(field_name='description', lookup_expr='icontains')

    # Filtres de dates
    date_creation_after = django_filters.DateFilter(
        field_name='date_creation',
        lookup_expr='gte',
        label='Créé après'
    )
    date_creation_before = django_filters.DateFilter(
        field_name='date_creation',
        lookup_expr='lte',
        label='Créé avant'
    )

    # Filtres sur la durée
    duree_min = django_filters.NumberFilter(
        field_name='duree_minutes',
        lookup_expr='gte',
        label='Durée minimale (minutes)'
    )
    duree_max = django_filters.NumberFilter(
        field_name='duree_minutes',
        lookup_expr='lte',
        label='Durée maximale (minutes)'
    )

    # Filtres sur le nombre de questions
    nombre_questions_min = django_filters.NumberFilter(
        method='filter_nombre_questions_min',
        label='Nombre minimum de questions'
    )
    nombre_questions_max = django_filters.NumberFilter(
        method='filter_nombre_questions_max',
        label='Nombre maximum de questions'
    )

    # Filtres sur l'utilisation
    has_parcours = django_filters.BooleanFilter(
        method='filter_has_parcours',
        label='A des parcours'
    )
    recently_used = django_filters.BooleanFilter(
        method='filter_recently_used',
        label='Utilisé récemment (30 derniers jours)'
    )

    class Meta:
        model = Questionnaire
        fields = [
            'search', 'nom', 'description',
            'date_creation_after', 'date_creation_before',
            'duree_min', 'duree_max',
            'nombre_questions_min', 'nombre_questions_max',
            'has_parcours', 'recently_used'
        ]

    def filter_search(self, queryset, name, value):
        """
        Recherche globale dans nom et description
        """
        if value:
            return queryset.filter(
                Q(nom__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset

    def filter_nombre_questions_min(self, queryset, name, value):
        """
        Filtrer par nombre minimum de questions
        """
        if value:
            from django.db.models import Count
            return queryset.annotate(
                nb_questions=Count('questions')
            ).filter(nb_questions__gte=value)
        return queryset

    def filter_nombre_questions_max(self, queryset, name, value):
        """
        Filtrer par nombre maximum de questions
        """
        if value:
            from django.db.models import Count
            return queryset.annotate(
                nb_questions=Count('questions')
            ).filter(nb_questions__lte=value)
        return queryset

    def filter_has_parcours(self, queryset, name, value):
        """
        Filtrer par présence de parcours
        """
        if value is True:
            return queryset.filter(parcours__isnull=False).distinct()
        elif value is False:
            return queryset.filter(parcours__isnull=True)
        return queryset

    def filter_recently_used(self, queryset, name, value):
        """
        Filtrer par utilisation récente
        """
        if value is True:
            from datetime import datetime, timedelta
            date_limite = datetime.now() - timedelta(days=30)
            return queryset.filter(
                parcours__date_realisation__gte=date_limite
            ).distinct()
        elif value is False:
            from datetime import datetime, timedelta
            date_limite = datetime.now() - timedelta(days=30)
            return queryset.exclude(
                parcours__date_realisation__gte=date_limite
            ).distinct()
        return queryset


class QuestionFilter(django_filters.FilterSet):
    """
    Filtre pour la recherche et le filtrage des questions
    """
    # Recherche textuelle
    search = django_filters.CharFilter(method='filter_search', label='Recherche')

    # Filtres spécifiques
    intitule = django_filters.CharFilter(field_name='intitule', lookup_expr='icontains')
    questionnaire = django_filters.NumberFilter(field_name='questionnaire__id')
    questionnaire_nom = django_filters.CharFilter(
        field_name='questionnaire__nom',
        lookup_expr='icontains'
    )

    # Filtres sur le nombre de réponses
    nombre_reponses_min = django_filters.NumberFilter(
        method='filter_nombre_reponses_min',
        label='Nombre minimum de réponses'
    )
    nombre_reponses_max = django_filters.NumberFilter(
        method='filter_nombre_reponses_max',
        label='Nombre maximum de réponses'
    )

    class Meta:
        model = Question
        fields = [
            'search', 'intitule', 'questionnaire', 'questionnaire_nom',
            'nombre_reponses_min', 'nombre_reponses_max'
        ]

    def filter_search(self, queryset, name, value):
        """
        Recherche globale dans intitulé et nom du questionnaire
        """
        if value:
            return queryset.filter(
                Q(intitule__icontains=value) |
                Q(questionnaire__nom__icontains=value)
            )
        return queryset

    def filter_nombre_reponses_min(self, queryset, name, value):
        """
        Filtrer par nombre minimum de réponses
        """
        if value:
            from django.db.models import Count
            return queryset.annotate(
                nb_reponses=Count('reponses')
            ).filter(nb_reponses__gte=value)
        return queryset

    def filter_nombre_reponses_max(self, queryset, name, value):
        """
        Filtrer par nombre maximum de réponses
        """
        if value:
            from django.db.models import Count
            return queryset.annotate(
                nb_reponses=Count('reponses')
            ).filter(nb_reponses__lte=value)
        return queryset