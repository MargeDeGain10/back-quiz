from django.db import models
from django.core.validators import MinValueValidator


class Questionnaire(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    duree_minutes = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'questionnaire'
        verbose_name = 'Questionnaire'
        verbose_name_plural = 'Questionnaires'
        ordering = ['-date_creation']

    def __str__(self):
        return self.nom

    @property
    def nombre_questions(self):
        return self.questions.count()


class Question(models.Model):
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    intitule = models.TextField()

    class Meta:
        db_table = 'question'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f"Question {self.id}: {self.intitule[:50]}..."

    @property
    def nombre_reponses(self):
        return self.reponses.count()

    @property
    def reponses_correctes(self):
        return self.reponses.filter(est_correcte=True)


class Reponse(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='reponses'
    )
    texte = models.TextField()
    est_correcte = models.BooleanField(default=False)

    class Meta:
        db_table = 'reponse'
        verbose_name = 'Réponse'
        verbose_name_plural = 'Réponses'

    def __str__(self):
        status = "✓" if self.est_correcte else "✗"
        return f"{status} {self.texte[:50]}..."
