from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import math
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
    note_sur_20 = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    penalites_appliquees = models.BooleanField(default=False)
    temps_moyen_par_question = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
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

    def calculer_note(self, avec_penalites=False):
        """
        Calcul de note avancé avec gestion des choix multiples et pénalités
        """
        total_questions = self.questionnaire.nombre_questions
        if total_questions == 0:
            return 0

        score_total = Decimal('0')

        for reponse_user in self.reponses_utilisateur.all():
            score_question = self._calculer_score_question(reponse_user, avec_penalites)
            score_total += score_question

        note_pourcentage = (score_total / total_questions) * 100
        return round(float(note_pourcentage), 2)

    def _calculer_score_question(self, reponse_user, avec_penalites=False):
        """
        Calcule le score pour une question donnée
        """
        reponses_correctes = list(reponse_user.question.reponses_correctes.all())
        reponses_selectionnees = list(reponse_user.reponses_selectionnees.all())
        total_reponses = reponse_user.question.reponses.count()

        if not reponses_correctes:
            return Decimal('0')

        # Si aucune réponse sélectionnée
        if not reponses_selectionnees:
            return Decimal('0')

        # Calcul pour choix unique (1 seule bonne réponse)
        if len(reponses_correctes) == 1:
            if reponses_selectionnees == reponses_correctes:
                return Decimal('1')
            else:
                return Decimal('0')

        # Calcul pour choix multiples
        bonnes_selections = len(set(reponses_selectionnees) & set(reponses_correctes))
        mauvaises_selections = len(set(reponses_selectionnees) - set(reponses_correctes))
        reponses_correctes_manquees = len(set(reponses_correctes) - set(reponses_selectionnees))

        if avec_penalites:
            # Formule avec pénalités: (bonnes - mauvaises) / total_correctes
            score = (bonnes_selections - mauvaises_selections) / len(reponses_correctes)
            return max(Decimal('0'), Decimal(str(score)))
        else:
            # Formule standard: bonnes / total_correctes
            if bonnes_selections == len(reponses_correctes) and mauvaises_selections == 0:
                return Decimal('1')  # 100% correct
            elif bonnes_selections > 0:
                return Decimal(str(bonnes_selections / len(reponses_correctes)))
            else:
                return Decimal('0')

    def calculer_note_sur_20(self, avec_penalites=False):
        """
        Convertit la note pourcentage en note sur 20
        """
        note_100 = self.calculer_note(avec_penalites)
        note_20 = (note_100 / 100) * 20
        return round(note_20, 2)

    def calculer_temps_moyen_par_question(self):
        """
        Calcule le temps moyen passé par question
        """
        if self.temps_passe_sec > 0 and self.reponses_utilisateur.count() > 0:
            return float(round(self.temps_passe_sec / self.reponses_utilisateur.count(), 2))
        return float(0)

    def calculer_statistiques_detaillees(self):
        """
        Calcule des statistiques détaillées du parcours
        """
        total_questions = self.questionnaire.nombre_questions
        questions_repondues = self.reponses_utilisateur.count()

        if questions_repondues == 0:
            return {
                'questions_correctes': 0,
                'questions_partiellement_correctes': 0,
                'questions_incorrectes': 0,
                'taux_reussite': 0,
                'temps_moyen_par_question': 0,
                'efficacite_temporelle': 0
            }

        correctes = 0
        partiellement_correctes = 0
        incorrectes = 0

        for reponse_user in self.reponses_utilisateur.all():
            score = self._calculer_score_question(reponse_user, False)
            if score == 1:
                correctes += 1
            elif score > 0:
                partiellement_correctes += 1
            else:
                incorrectes += 1

        temps_moyen = self.calculer_temps_moyen_par_question()

        # Efficacité temporelle (score/temps)
        efficacite = 0
        if temps_moyen > 0:
            note = self.calculer_note()
            efficacite = round(note / temps_moyen, 2)

        return {
            'questions_correctes': correctes,
            'questions_partiellement_correctes': partiellement_correctes,
            'questions_incorrectes': incorrectes,
            'taux_reussite': round((correctes / questions_repondues) * 100, 1),
            'temps_moyen_par_question': temps_moyen,
            'efficacite_temporelle': efficacite
        }

    @property
    def niveau_performance(self):
        """
        Détermine le niveau de performance basé sur la note
        """
        if self.note_sur_20 is None:
            return "Non évalué"

        if self.note_sur_20 >= 16:
            return "Excellent"
        elif self.note_sur_20 >= 14:
            return "Très bien"
        elif self.note_sur_20 >= 12:
            return "Bien"
        elif self.note_sur_20 >= 10:
            return "Assez bien"
        else:
            return "Insuffisant"

    @property
    def recommandations(self):
        """
        Génère des recommandations personnalisées
        """
        stats = self.calculer_statistiques_detaillees()
        recommandations = []

        if stats['taux_reussite'] < 50:
            recommandations.append("Revoir les concepts de base avant de retenter")

        if stats['temps_moyen_par_question'] > 120:  # Plus de 2 minutes par question
            recommandations.append("Améliorer la gestion du temps")

        if stats['questions_partiellement_correctes'] > stats['questions_correctes']:
            recommandations.append("Être plus attentif aux détails des questions à choix multiples")

        if self.note_sur_20 and self.note_sur_20 < 10:
            recommandations.append("Suivre une formation complémentaire")

        if not recommandations:
            recommandations.append("Excellent travail ! Continuez sur cette voie")

        return recommandations


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
    temps_reponse_sec = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    date_reponse = models.DateTimeField(default=timezone.now)
    score_obtenu = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
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

    @property
    def est_correcte(self):
        """Vérifie si la réponse est entièrement correcte"""
        reponses_correctes = set(self.question.reponses_correctes.all())
        reponses_selectionnees = set(self.reponses_selectionnees.all())
        return reponses_correctes == reponses_selectionnees and len(reponses_correctes) > 0

    @property
    def est_partiellement_correcte(self):
        """Vérifie si la réponse est partiellement correcte"""
        reponses_correctes = set(self.question.reponses_correctes.all())
        reponses_selectionnees = set(self.reponses_selectionnees.all())
        intersection = reponses_correctes & reponses_selectionnees
        return len(intersection) > 0 and not self.est_correcte

    def calculer_score(self, avec_penalites=False):
        """Calcule le score pour cette réponse"""
        return self.parcours._calculer_score_question(self, avec_penalites)

    @property
    def efficacite_temporelle(self):
        """Ratio score/temps (plus c'est élevé, plus c'est efficace)"""
        if self.temps_reponse_sec > 0 and self.score_obtenu is not None:
            return round(float(self.score_obtenu) / (self.temps_reponse_sec / 60), 2)
        return 0


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


class AnalyseQuestion(models.Model):
    """Modèle pour analyser les statistiques d'une question"""
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name='analyse'
    )
    nombre_tentatives = models.IntegerField(default=0)
    nombre_reussites = models.IntegerField(default=0)
    taux_reussite = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    temps_moyen_reponse = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyse_question'
        verbose_name = 'Analyse question'
        verbose_name_plural = 'Analyses questions'

    def __str__(self):
        return f"Analyse - {self.question.intitule[:50]}..."

    def mettre_a_jour_statistiques(self):
        """Met à jour les statistiques de la question"""
        reponses = ReponseUtilisateur.objects.filter(question=self.question)
        self.nombre_tentatives = reponses.count()

        if self.nombre_tentatives > 0:
            reussites = sum(1 for r in reponses if r.est_correcte)
            self.nombre_reussites = reussites
            self.taux_reussite = round((reussites / self.nombre_tentatives) * 100, 2)

            temps_total = sum(r.temps_reponse_sec for r in reponses if r.temps_reponse_sec > 0)
            if temps_total > 0:
                self.temps_moyen_reponse = round(temps_total / self.nombre_tentatives, 2)

        self.save()

    @property
    def niveau_difficulte(self):
        """Détermine le niveau de difficulté basé sur le taux de réussite"""
        if self.taux_reussite >= 80:
            return "Facile"
        elif self.taux_reussite >= 60:
            return "Moyen"
        elif self.taux_reussite >= 40:
            return "Difficile"
        else:
            return "Très difficile"


class AnalyseStagiaire(models.Model):
    """Modèle pour analyser les performances d'un stagiaire"""
    stagiaire = models.OneToOneField(
        Stagiaire,
        on_delete=models.CASCADE,
        related_name='analyse'
    )
    nombre_questionnaires_termines = models.IntegerField(default=0)
    note_moyenne = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    note_moyenne_sur_20 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    temps_total_formation = models.IntegerField(default=0)  # en secondes
    niveau_global = models.CharField(max_length=20, default="Débutant")
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyse_stagiaire'
        verbose_name = 'Analyse stagiaire'
        verbose_name_plural = 'Analyses stagiaires'

    def __str__(self):
        return f"Analyse - {self.stagiaire.user.prenom} {self.stagiaire.user.nom}"

    def mettre_a_jour_statistiques(self):
        """Met à jour les statistiques du stagiaire"""
        parcours_termines = self.stagiaire.parcours.filter(statut='TERMINE')
        self.nombre_questionnaires_termines = parcours_termines.count()

        # Initialiser les valeurs par défaut
        self.note_moyenne = 0
        self.note_moyenne_sur_20 = 0
        self.temps_total_formation = 0
        self.niveau_global = "Débutant"

        if self.nombre_questionnaires_termines > 0:
            # Calcul de la note moyenne
            notes = [float(p.note_obtenue) for p in parcours_termines if p.note_obtenue is not None]
            if notes:
                self.note_moyenne = round(sum(notes) / len(notes), 2)
                self.note_moyenne_sur_20 = round((self.note_moyenne / 100) * 20, 2)

            # Temps total de formation
            self.temps_total_formation = sum(p.temps_passe_sec for p in parcours_termines)

            # Niveau global
            if self.note_moyenne_sur_20 >= 16:
                self.niveau_global = "Expert"
            elif self.note_moyenne_sur_20 >= 14:
                self.niveau_global = "Avancé"
            elif self.note_moyenne_sur_20 >= 12:
                self.niveau_global = "Intermédiaire"
            elif self.note_moyenne_sur_20 >= 10:
                self.niveau_global = "Novice"
            else:
                self.niveau_global = "Débutant"

        self.save()

    @property
    def temps_formation_heures(self):
        """Temps de formation en heures"""
        return round(self.temps_total_formation / 3600, 1)

    def obtenir_domaines_amelioration(self):
        """Identifie les domaines nécessitant amélioration"""
        parcours = self.stagiaire.parcours.filter(statut='TERMINE')
        domaines_faibles = []

        for parcours_item in parcours:
            if parcours_item.note_sur_20 and parcours_item.note_sur_20 < 12:
                domaines_faibles.append({
                    'questionnaire': parcours_item.questionnaire.nom,
                    'note': parcours_item.note_sur_20,
                    'recommandations': parcours_item.recommandations
                })

        return domaines_faibles


class AnalyseQuestionnaire(models.Model):
    """Modèle pour analyser les performances d'un questionnaire"""
    questionnaire = models.OneToOneField(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='analyse'
    )
    nombre_passages = models.IntegerField(default=0)
    note_moyenne = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    note_mediane = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    temps_moyen_completion = models.IntegerField(default=0)  # en secondes
    taux_abandon = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyse_questionnaire'
        verbose_name = 'Analyse questionnaire'
        verbose_name_plural = 'Analyses questionnaires'

    def __str__(self):
        return f"Analyse - {self.questionnaire.nom}"

    def mettre_a_jour_statistiques(self):
        """Met à jour les statistiques du questionnaire"""
        from django.db.models import Avg
        import statistics

        tous_parcours = self.questionnaire.parcours.all()
        parcours_termines = tous_parcours.filter(statut='TERMINE')
        parcours_abandonnes = tous_parcours.filter(statut='ABANDONNE')

        self.nombre_passages = tous_parcours.count()

        if self.nombre_passages > 0:
            # Taux d'abandon
            self.taux_abandon = round((parcours_abandonnes.count() / self.nombre_passages) * 100, 2)

        if parcours_termines.count() > 0:
            # Note moyenne
            notes = [p.note_obtenue for p in parcours_termines if p.note_obtenue is not None]
            if notes:
                self.note_moyenne = round(sum(notes) / len(notes), 2)
                # Note médiane
                self.note_mediane = round(statistics.median(notes), 2)

            # Temps moyen de completion
            temps_completion = [p.temps_passe_sec for p in parcours_termines]
            if temps_completion:
                self.temps_moyen_completion = round(sum(temps_completion) / len(temps_completion))

        self.save()

    @property
    def temps_moyen_minutes(self):
        """Temps moyen en minutes"""
        return round(self.temps_moyen_completion / 60, 1)

    @property
    def niveau_difficulte_global(self):
        """Niveau de difficulté global du questionnaire"""
        if self.note_moyenne >= 80:
            return "Facile"
        elif self.note_moyenne >= 65:
            return "Moyen"
        elif self.note_moyenne >= 50:
            return "Difficile"
        else:
            return "Très difficile"

    def obtenir_questions_difficiles(self, seuil=60):
        """Retourne les questions avec un taux de réussite inférieur au seuil"""
        questions_difficiles = []
        for question in self.questionnaire.questions.all():
            try:
                analyse = question.analyse
                if analyse.taux_reussite < seuil:
                    questions_difficiles.append({
                        'question': question,
                        'taux_reussite': analyse.taux_reussite,
                        'niveau_difficulte': analyse.niveau_difficulte
                    })
            except AnalyseQuestion.DoesNotExist:
                # Créer l'analyse si elle n'existe pas
                AnalyseQuestion.objects.create(question=question)

        return sorted(questions_difficiles, key=lambda x: x['taux_reussite'])
