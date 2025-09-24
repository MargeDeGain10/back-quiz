from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('STAGIAIRE', 'Stagiaire'),
    ]

    nom = models.CharField(max_length=120)
    prenom = models.CharField(max_length=120)
    login = models.CharField(max_length=120, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['login', 'nom', 'prenom', 'role']

    class Meta:
        db_table = 'utilisateur'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_stagiaire(self):
        return self.role == 'STAGIAIRE'

    # Propriétés pour la compatibilité avec Django admin
    @property
    def is_staff(self):
        """Les admins peuvent accéder à l'admin Django"""
        return self.role == 'ADMIN'

    @property
    def is_superuser(self):
        """Les admins sont des superusers"""
        return self.role == 'ADMIN'

    def has_perm(self, _perm, _obj=None):
        """Les admins ont toutes les permissions"""
        return self.role == 'ADMIN'

    def has_module_perms(self, _app_label):
        """Les admins ont accès à tous les modules"""
        return self.role == 'ADMIN'


class Stagiaire(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='stagiaire_profile'
    )
    societe = models.CharField(max_length=180, null=True, blank=True)

    class Meta:
        db_table = 'stagiaire'
        verbose_name = 'Stagiaire'
        verbose_name_plural = 'Stagiaires'

    def __str__(self):
        return f"Stagiaire: {self.user.prenom} {self.user.nom}"

    def save(self, *args, **kwargs):
        if self.user.role != 'STAGIAIRE':
            raise ValueError("Un profil stagiaire ne peut être créé que pour un utilisateur avec le rôle STAGIAIRE")
        super().save(*args, **kwargs)
