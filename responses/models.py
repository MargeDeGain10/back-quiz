from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from users.models import Stagiaire
from quizzes.models import Questionnaire, Question, Reponse


class Parcours(models.Model):
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ABANDONNE', 'Abandonné'),
    ]

    stagiaire = models.ForeignKey(
        Stagiaire,
        on_delete=models.CASCADE,
        related_name='parcours'
    )
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='parcours'
    )
    date_realisation = models.DateTimeField(auto_now_add=True)
    temps_passe_sec = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    note_obtenue = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='EN_COURS'
    )

    class Meta:
        db_table = 'parcours'
        verbose_name = 'Parcours'
        verbose_name_plural = 'Parcours'
        unique_together = ['stagiaire', 'questionnaire']
        ordering = ['-date_realisation']

    def __str__(self):
        return f"Parcours {self.stagiaire.user.prenom} {self.stagiaire.user.nom} - {self.questionnaire.nom}"

    @property
    def temps_passe_minutes(self):
        return round(self.temps_passe_sec / 60, 1)

    @property
    def progression_pourcentage(self):
        total_questions = self.questionnaire.nombre_questions
        questions_repondues = self.reponses_utilisateur.count()
        if total_questions == 0:
            return 0
        return round((questions_repondues / total_questions) * 100, 1)

    def calculer_note(self):
        total_questions = self.questionnaire.nombre_questions
        if total_questions == 0:
            return 0

        bonnes_reponses = 0
        for reponse_user in self.reponses_utilisateur.all():
            reponses_correctes = reponse_user.question.reponses_correctes
            reponses_selectionnees = reponse_user.reponses_selectionnees.all()

            if (set(reponses_correctes) == set(reponses_selectionnees) and
                reponses_correctes.count() > 0):
                bonnes_reponses += 1

        note = (bonnes_reponses / total_questions) * 100
        return round(note, 2)


class ReponseUtilisateur(models.Model):
    parcours = models.ForeignKey(
        Parcours,
        on_delete=models.CASCADE,
        related_name='reponses_utilisateur'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='reponses_utilisateur'
    )

    class Meta:
        db_table = 'reponse_utilisateur'
        verbose_name = 'Réponse utilisateur'
        verbose_name_plural = 'Réponses utilisateur'
        unique_together = ['parcours', 'question']

    def __str__(self):
        return f"Réponse de {self.parcours.stagiaire.user.prenom} - Question {self.question.id}"

    @property
    def reponses_selectionnees(self):
        return Reponse.objects.filter(
            reponse_utilisateur_selections__reponse_utilisateur=self
        )


class ReponseUtilisateurSelection(models.Model):
    reponse_utilisateur = models.ForeignKey(
        ReponseUtilisateur,
        on_delete=models.CASCADE,
        related_name='selections'
    )
    reponse = models.ForeignKey(
        Reponse,
        on_delete=models.CASCADE,
        related_name='reponse_utilisateur_selections'
    )

    class Meta:
        db_table = 'reponse_utilisateur_selection'
        verbose_name = 'Sélection réponse utilisateur'
        verbose_name_plural = 'Sélections réponses utilisateur'
        unique_together = ['reponse_utilisateur', 'reponse']

    def __str__(self):
        return f"Sélection: {self.reponse_utilisateur} -> {self.reponse.texte[:30]}..."

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.reponse.question != self.reponse_utilisateur.question:
            raise ValidationError(
                "La réponse sélectionnée doit appartenir à la même question que la réponse utilisateur."
            )
