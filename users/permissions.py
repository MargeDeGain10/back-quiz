from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les administrateurs.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsStagiaire(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les stagiaires.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'STAGIAIRE'
        )


class IsAdminOrStagiaire(permissions.BasePermission):
    """
    Permission qui autorise les admins et les stagiaires authentifiés.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'STAGIAIRE']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les propriétaires d'un objet ou les admins.
    """

    def has_object_permission(self, request, view, obj):
        # Les admins ont accès à tout
        if request.user.role == 'ADMIN':
            return True

        # Les stagiaires ne peuvent accéder qu'à leurs propres données
        if request.user.role == 'STAGIAIRE':
            # Pour les objets Stagiaire
            if hasattr(obj, 'user'):
                return obj.user == request.user
            # Pour les objets Parcours
            elif hasattr(obj, 'stagiaire'):
                return obj.stagiaire.user == request.user
            # Pour les objets User directement
            elif hasattr(obj, 'id') and hasattr(request.user, 'id'):
                return obj.id == request.user.id

        return False


class IsAdminOrReadOnlyForStagiaire(permissions.BasePermission):
    """
    Permission qui donne accès complet aux admins et lecture seule aux stagiaires.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Les admins ont tous les droits
        if request.user.role == 'ADMIN':
            return True

        # Les stagiaires ont seulement le droit de lecture
        if request.user.role == 'STAGIAIRE':
            return request.method in permissions.SAFE_METHODS

        return False