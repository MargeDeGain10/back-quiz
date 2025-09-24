from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, login, nom, prenom, role, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        if not login:
            raise ValueError('Le login est obligatoire')
        if not nom:
            raise ValueError('Le nom est obligatoire')
        if not prenom:
            raise ValueError('Le prénom est obligatoire')
        if not role:
            raise ValueError('Le rôle est obligatoire')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            login=login,
            nom=nom,
            prenom=prenom,
            role=role,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, login, nom, prenom, password=None, **extra_fields):
        """
        Créer un superuser (admin) - Les champs is_staff et is_superuser sont gérés par les propriétés
        """
        return self.create_user(email, login, nom, prenom, 'ADMIN', password, **extra_fields)