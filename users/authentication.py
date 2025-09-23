from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class CustomAuthenticationBackend(BaseBackend):
    """
    Backend d'authentification personnalisé qui :
    - Nettoie les espaces avant/après login et mot de passe
    - Rend le login insensible à la casse
    - Authentifie par login ou email
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Nettoyer les espaces et convertir en minuscules
        username = username.strip().lower()
        password = password.strip()

        try:
            # Chercher l'utilisateur par login ou email (insensible à la casse)
            user = User.objects.get(
                Q(login__iexact=username) | Q(email__iexact=username)
            )

            # Vérifier le mot de passe
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        except User.DoesNotExist:
            # Exécuter une vérification de mot de passe factice pour éviter
            # les attaques de timing
            User().set_password(password)

        return None

    def user_can_authenticate(self, user):
        """
        Rejeter les utilisateurs avec is_active=False. Les backends personnalisés peuvent
        remplacer cette méthode s'ils ont des exigences d'utilisateur actif différentes.
        """
        return getattr(user, 'is_active', None)

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None