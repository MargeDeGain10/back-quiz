import django_filters
from django.db.models import Q
from .models import User, Stagiaire


class StagiaireFilter(django_filters.FilterSet):
    """
    Filtre pour la recherche et le filtrage des stagiaires
    """
    # Recherche textuelle
    search = django_filters.CharFilter(method='filter_search', label='Recherche')

    # Filtres spécifiques
    nom = django_filters.CharFilter(field_name='user__nom', lookup_expr='icontains')
    prenom = django_filters.CharFilter(field_name='user__prenom', lookup_expr='icontains')
    societe = django_filters.CharFilter(field_name='societe', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    login = django_filters.CharFilter(field_name='user__login', lookup_expr='icontains')

    # Filtres de statut
    is_active = django_filters.BooleanFilter(field_name='user__is_active')

    # Filtres de dates
    date_joined_after = django_filters.DateFilter(
        field_name='user__date_joined',
        lookup_expr='gte',
        label='Inscrit après'
    )
    date_joined_before = django_filters.DateFilter(
        field_name='user__date_joined',
        lookup_expr='lte',
        label='Inscrit avant'
    )

    # Filtres sur les parcours
    has_parcours = django_filters.BooleanFilter(
        method='filter_has_parcours',
        label='A des parcours'
    )
    parcours_completed = django_filters.BooleanFilter(
        method='filter_parcours_completed',
        label='A des parcours terminés'
    )

    class Meta:
        model = Stagiaire
        fields = [
            'search', 'nom', 'prenom', 'societe', 'email', 'login',
            'is_active', 'date_joined_after', 'date_joined_before',
            'has_parcours', 'parcours_completed'
        ]

    def filter_search(self, queryset, name, value):
        """
        Recherche globale dans nom, prénom, email, login, société
        """
        if value:
            return queryset.filter(
                Q(user__nom__icontains=value) |
                Q(user__prenom__icontains=value) |
                Q(user__email__icontains=value) |
                Q(user__login__icontains=value) |
                Q(societe__icontains=value)
            )
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

    def filter_parcours_completed(self, queryset, name, value):
        """
        Filtrer par parcours terminés
        """
        if value is True:
            return queryset.filter(parcours__statut='TERMINE').distinct()
        elif value is False:
            return queryset.exclude(parcours__statut='TERMINE').distinct()
        return queryset