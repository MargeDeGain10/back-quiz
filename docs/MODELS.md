# 📊 Modèles de Données - Quiz Platform

Documentation complète des modèles de données, leurs relations et fonctionnalités.

## 🏗️ Vue d'ensemble de l'architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    users    │    │   quizzes   │    │  responses  │
│             │    │             │    │             │
│   User      │    │Questionnaire│    │  Parcours   │
│ Stagiaire   │    │  Question   │    │ReponseUser  │
│             │    │  Reponse    │    │  Analyses   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                          │
              ┌─────────────┴─────────────┐
              │     Relations Métier      │
              │  - Parcours de quiz       │
              │  - Système de notation    │
              │  - Analytics automatiques │
              └───────────────────────────┘
```

## 👥 Module Users

### User (Utilisateur de base)
**Table** : `utilisateur`

Modèle utilisateur personnalisé basé sur `AbstractBaseUser`.

#### Champs
```python
{
    "id": "AutoField (PK)",
    "nom": "CharField(120) - Nom de famille",
    "prenom": "CharField(120) - Prénom",
    "login": "CharField(120, unique=True) - Identifiant de connexion",
    "email": "EmailField(254, unique=True) - Email unique",
    "role": "CharField(10) - ADMIN|STAGIAIRE",
    "is_active": "BooleanField(default=True) - Compte actif",
    "date_joined": "DateTimeField(auto_now_add=True) - Date de création",
    "password": "CharField - Mot de passe haché"
}
```

#### Propriétés métier
- `is_admin` : Vérifie si l'utilisateur est administrateur
- `is_stagiaire` : Vérifie si l'utilisateur est stagiaire
- `is_staff` : Compatibilité Django Admin (admins uniquement)
- `is_superuser` : Compatibilité Django Admin (admins uniquement)

#### Méthodes
- `has_perm()` : Gestion des permissions (admins ont toutes les permissions)
- `has_module_perms()` : Accès aux modules (admins uniquement)

#### Exemple d'utilisation
```python
# Création d'un admin
admin = User.objects.create_superuser(
    login='admin',
    email='admin@example.com',
    password='secure_password',
    nom='Administrateur',
    prenom='Principal'
)

# Création d'un stagiaire
stagiaire_user = User.objects.create_user(
    login='jdupont',
    email='jean.dupont@example.com',
    password='password123',
    nom='Dupont',
    prenom='Jean',
    role='STAGIAIRE'
)
```

### Stagiaire (Profil étendu)
**Table** : `stagiaire`

Extension du modèle User pour les stagiaires avec informations supplémentaires.

#### Champs
```python
{
    "user": "OneToOneField(User, PK, related_name='stagiaire_profile')",
    "societe": "CharField(180, null=True, blank=True) - Société d'origine"
}
```

#### Relations
- **User** : Relation 1:1 avec User (CASCADE)
- **Parcours** : Relation 1:N via `stagiaire.parcours.all()`
- **Analyse** : Relation 1:1 via `stagiaire.analyse`

#### Validation métier
```python
def save(self, *args, **kwargs):
    if self.user.role != 'STAGIAIRE':
        raise ValueError("Seul un utilisateur STAGIAIRE peut avoir ce profil")
    super().save(*args, **kwargs)
```

---

## 📚 Module Quizzes

### Questionnaire
**Table** : `questionnaire`

Conteneur principal pour les questions d'un quiz.

#### Champs
```python
{
    "id": "AutoField (PK)",
    "nom": "CharField(200) - Nom du questionnaire",
    "description": "TextField(null=True, blank=True) - Description détaillée",
    "date_creation": "DateTimeField(auto_now_add=True) - Date de création",
    "duree_minutes": "IntegerField(validators=[MinValueValidator(1)]) - Durée autorisée"
}
```

#### Relations
- **Questions** : Relation 1:N via `questionnaire.questions.all()`
- **Parcours** : Relation 1:N via `questionnaire.parcours.all()`
- **Analyse** : Relation 1:1 via `questionnaire.analyse`

#### Propriétés calculées
- `nombre_questions` : Compte le nombre de questions associées
- `duree` : Alias pour `duree_minutes`

#### Exemple d'usage
```python
# Création d'un questionnaire
questionnaire = Questionnaire.objects.create(
    nom="Python - Concepts de base",
    description="Introduction aux concepts fondamentaux de Python",
    duree_minutes=30
)

# Accès aux questions
questions = questionnaire.questions.all()
nombre_total = questionnaire.nombre_questions
```

### Question
**Table** : `question`

Questions individuelles appartenant à un questionnaire.

#### Champs
```python
{
    "id": "AutoField (PK)",
    "questionnaire": "ForeignKey(Questionnaire, CASCADE, related_name='questions')",
    "intitule": "TextField - Énoncé de la question"
}
```

#### Relations
- **Questionnaire** : Relation N:1 avec Questionnaire
- **Réponses** : Relation 1:N via `question.reponses.all()`
- **Réponses utilisateur** : Relation 1:N via `question.reponses_utilisateur.all()`
- **Analyse** : Relation 1:1 via `question.analyse`

#### Propriétés calculées
- `nombre_reponses` : Nombre total de réponses possibles
- `reponses_correctes` : QuerySet des bonnes réponses uniquement

### Reponse (Réponse possible)
**Table** : `reponse`

Réponses possibles pour chaque question (choix multiples supportés).

#### Champs
```python
{
    "id": "AutoField (PK)",
    "question": "ForeignKey(Question, CASCADE, related_name='reponses')",
    "texte": "TextField - Texte de la réponse",
    "est_correcte": "BooleanField(default=False) - Marque la bonne réponse"
}
```

#### Relations
- **Question** : Relation N:1 avec Question
- **Sélections utilisateur** : Relation 1:N via `reponse.reponse_utilisateur_selections.all()`

#### Représentation
```python
def __str__(self):
    status = "✓" if self.est_correcte else "✗"
    return f"{status} {self.texte[:50]}..."
```

---

## 🎯 Module Responses (Parcours et Analyses)

### Parcours
**Table** : `parcours`

Instance d'un stagiaire passant un questionnaire spécifique.

#### Champs principaux
```python
{
    "id": "AutoField (PK)",
    "stagiaire": "ForeignKey(Stagiaire, CASCADE, related_name='parcours')",
    "questionnaire": "ForeignKey(Questionnaire, CASCADE, related_name='parcours')",
    "date_realisation": "DateTimeField(auto_now_add=True)",
    "temps_passe_sec": "IntegerField(default=0, validators=[MinValueValidator(0)])",
    "statut": "CharField(10, choices=STATUT_CHOICES, default='EN_COURS')"
}
```

#### Champs de notation
```python
{
    "note_obtenue": "DecimalField(5,2, null=True, validators=[0-100])",
    "note_sur_20": "DecimalField(4,2, null=True, validators=[0-20])",
    "penalites_appliquees": "BooleanField(default=False)",
    "temps_moyen_par_question": "DecimalField(6,2, null=True)"
}
```

#### Choix de statut
```python
STATUT_CHOICES = [
    ('EN_COURS', 'En cours'),
    ('TERMINE', 'Terminé'),
    ('ABANDONNE', 'Abandonné'),
]
```

#### Contraintes uniques
```python
class Meta:
    unique_together = ['stagiaire', 'questionnaire']  # Un parcours par questionnaire par stagiaire
```

#### Propriétés calculées

##### Temps et progression
- `temps_passe_minutes` : Temps en minutes (arrondi à 1 décimale)
- `progression_pourcentage` : Pourcentage de questions répondues

##### Performance
- `niveau_performance` : Classification basée sur note_sur_20
  - Excellent (≥16), Très bien (14-16), Bien (12-14), Assez bien (10-12), Insuffisant (<10)

##### Recommandations
- `recommandations` : Liste de suggestions personnalisées basées sur les performances

#### Méthodes de calcul de score

##### Calcul de note principal
```python
def calculer_note(self, avec_penalites=False):
    """
    Calcul de note avancé avec support choix multiples

    Returns:
        float: Note en pourcentage (0-100)
    """
```

##### Algorithme de scoring par question
```python
def _calculer_score_question(self, reponse_user, avec_penalites=False):
    """
    Logique de scoring sophistiquée :

    CHOIX UNIQUE (1 bonne réponse):
    - Tout correct = 1.0 point
    - Tout faux = 0.0 point

    CHOIX MULTIPLES (plusieurs bonnes réponses):
    - Standard: bonnes_selections / total_correctes
    - Avec pénalités: max(0, (bonnes - mauvaises) / total_correctes)
    """
```

##### Analyses statistiques
```python
def calculer_statistiques_detaillees(self):
    """
    Retourne:
    {
        'questions_correctes': int,
        'questions_partiellement_correctes': int,
        'questions_incorrectes': int,
        'taux_reussite': float,
        'temps_moyen_par_question': float,
        'efficacite_temporelle': float
    }
    """
```

### ReponseUtilisateur
**Table** : `reponse_utilisateur`

Réponse d'un stagiaire à une question spécifique lors d'un parcours.

#### Champs
```python
{
    "id": "AutoField (PK)",
    "parcours": "ForeignKey(Parcours, CASCADE, related_name='reponses_utilisateur')",
    "question": "ForeignKey(Question, CASCADE, related_name='reponses_utilisateur')",
    "temps_reponse_sec": "IntegerField(default=0, validators=[MinValueValidator(0)])",
    "date_reponse": "DateTimeField(default=timezone.now)",
    "score_obtenu": "DecimalField(3,2, null=True, validators=[0-1])"
}
```

#### Contraintes
```python
class Meta:
    unique_together = ['parcours', 'question']  # Une réponse par question par parcours
```

#### Propriétés métier
- `reponses_selectionnees` : QuerySet des réponses choisies
- `est_correcte` : Booléen - réponse entièrement correcte
- `est_partiellement_correcte` : Booléen - au moins une bonne réponse
- `efficacite_temporelle` : Ratio score/temps

#### Méthodes
- `calculer_score(avec_penalites=False)` : Calcule le score pour cette réponse

### ReponseUtilisateurSelection
**Table** : `reponse_utilisateur_selection`

Table de liaison many-to-many entre ReponseUtilisateur et Reponse.

#### Champs
```python
{
    "id": "AutoField (PK)",
    "reponse_utilisateur": "ForeignKey(ReponseUtilisateur, CASCADE, related_name='selections')",
    "reponse": "ForeignKey(Reponse, CASCADE, related_name='reponse_utilisateur_selections')"
}
```

#### Contraintes
```python
class Meta:
    unique_together = ['reponse_utilisateur', 'reponse']
```

#### Validation métier
```python
def clean(self):
    if self.reponse.question != self.reponse_utilisateur.question:
        raise ValidationError("La réponse doit appartenir à la même question")
```

---

## 📈 Modèles d'Analyse

### AnalyseQuestion
**Table** : `analyse_question`

Statistiques automatiques pour chaque question.

#### Champs
```python
{
    "question": "OneToOneField(Question, CASCADE, related_name='analyse')",
    "nombre_tentatives": "IntegerField(default=0)",
    "nombre_reussites": "IntegerField(default=0)",
    "taux_reussite": "DecimalField(5,2, default=0)",
    "temps_moyen_reponse": "DecimalField(6,2, default=0)",
    "derniere_mise_a_jour": "DateTimeField(auto_now=True)"
}
```

#### Propriété calculée
- `niveau_difficulte` : "Facile" (≥80%), "Moyen" (≥60%), "Difficile" (≥40%), "Très difficile" (<40%)

#### Méthode de mise à jour
```python
def mettre_a_jour_statistiques(self):
    """Met à jour automatiquement toutes les statistiques"""
```

### AnalyseStagiaire
**Table** : `analyse_stagiaire`

Analyse globale des performances d'un stagiaire.

#### Champs
```python
{
    "stagiaire": "OneToOneField(Stagiaire, CASCADE, related_name='analyse')",
    "nombre_questionnaires_termines": "IntegerField(default=0)",
    "note_moyenne": "DecimalField(4,2, default=0)",
    "note_moyenne_sur_20": "DecimalField(4,2, default=0)",
    "temps_total_formation": "IntegerField(default=0)",  # en secondes
    "niveau_global": "CharField(20, default='Débutant')",
    "derniere_mise_a_jour": "DateTimeField(auto_now=True)"
}
```

#### Niveaux globaux
- **Expert** : ≥ 16/20
- **Avancé** : 14-16/20
- **Intermédiaire** : 12-14/20
- **Novice** : 10-12/20
- **Débutant** : < 10/20

#### Propriétés
- `temps_formation_heures` : Temps total en heures

#### Méthodes
- `mettre_a_jour_statistiques()` : Recalcule toutes les métriques
- `obtenir_domaines_amelioration()` : Identifie les questionnaires à retravailler

### AnalyseQuestionnaire
**Table** : `analyse_questionnaire`

Statistiques globales pour chaque questionnaire.

#### Champs
```python
{
    "questionnaire": "OneToOneField(Questionnaire, CASCADE, related_name='analyse')",
    "nombre_passages": "IntegerField(default=0)",
    "note_moyenne": "DecimalField(5,2, default=0)",
    "note_mediane": "DecimalField(5,2, default=0)",
    "temps_moyen_completion": "IntegerField(default=0)",  # en secondes
    "taux_abandon": "DecimalField(5,2, default=0)",
    "derniere_mise_a_jour": "DateTimeField(auto_now=True)"
}
```

#### Propriétés calculées
- `temps_moyen_minutes` : Temps moyen en minutes
- `niveau_difficulte_global` : Niveau basé sur la note moyenne

#### Méthodes
- `mettre_a_jour_statistiques()` : Recalcule toutes les statistiques
- `obtenir_questions_difficiles(seuil=60)` : Identifie les questions problématiques

---

## 🔄 Relations et Flux de données

### Schéma relationnel principal

```
User (1) ←→ (1) Stagiaire
   ↓
Stagiaire (1) ←→ (N) Parcours ←→ (1) Questionnaire
   ↓                    ↓              ↓
   ↓            ReponseUtilisateur    Question (N) ←→ (N) Reponse
   ↓                    ↓              ↓
AnalyseStagiaire       ↓        AnalyseQuestion
                       ↓
           ReponseUtilisateurSelection
```

### Flux typique d'un parcours

1. **Création du parcours**
   ```python
   parcours = Parcours.objects.create(
       stagiaire=stagiaire,
       questionnaire=questionnaire
   )
   ```

2. **Réponse aux questions**
   ```python
   reponse_user = ReponseUtilisateur.objects.create(
       parcours=parcours,
       question=question,
       temps_reponse_sec=45
   )

   # Sélections multiples
   for reponse_id in [1, 3]:
       ReponseUtilisateurSelection.objects.create(
           reponse_utilisateur=reponse_user,
           reponse_id=reponse_id
       )
   ```

3. **Calcul des scores**
   ```python
   parcours.note_obtenue = parcours.calculer_note()
   parcours.note_sur_20 = parcours.calculer_note_sur_20()
   parcours.statut = 'TERMINE'
   parcours.save()
   ```

4. **Mise à jour des analyses**
   ```python
   # Automatique ou via endpoint maintenance
   question.analyse.mettre_a_jour_statistiques()
   stagiaire.analyse.mettre_a_jour_statistiques()
   questionnaire.analyse.mettre_a_jour_statistiques()
   ```

---

## 🔧 Optimisations et performances

### Index de base de données recommandés
```sql
-- Index composites pour les requêtes fréquentes
CREATE INDEX idx_parcours_stagiaire_statut ON parcours(stagiaire_id, statut);
CREATE INDEX idx_reponse_user_parcours_question ON reponse_utilisateur(parcours_id, question_id);
CREATE INDEX idx_user_role_active ON utilisateur(role, is_active);
```

### Requêtes optimisées
```python
# Éviter les N+1 queries
parcours = Parcours.objects.select_related(
    'stagiaire__user', 'questionnaire'
).prefetch_related(
    'reponses_utilisateur__selections__reponse'
)

questionnaires = Questionnaire.objects.prefetch_related(
    'questions__reponses'
)
```

### Recommandations d'usage

1. **Créer les analyses automatiquement** lors de la première utilisation
2. **Mettre à jour périodiquement** les statistiques via task asynchrone
3. **Utiliser les propriétés calculées** plutôt que de recalculer à chaque fois
4. **Implémenter la pagination** pour les listes importantes
5. **Monitorer les performances** des calculs de score sur gros volumes

---

## 🧪 Exemples d'utilisation avancée

### Créer un parcours complet avec scores
```python
from django.db import transaction

with transaction.atomic():
    # 1. Créer le parcours
    parcours = Parcours.objects.create(
        stagiaire=stagiaire,
        questionnaire=questionnaire
    )

    # 2. Répondre aux questions
    for question in questionnaire.questions.all():
        reponse_user = ReponseUtilisateur.objects.create(
            parcours=parcours,
            question=question,
            temps_reponse_sec=random.randint(30, 120)
        )

        # Sélectionner des réponses aléatoires
        reponses_choisies = random.sample(
            list(question.reponses.all()),
            k=random.randint(1, 2)
        )

        for reponse in reponses_choisies:
            ReponseUtilisateurSelection.objects.create(
                reponse_utilisateur=reponse_user,
                reponse=reponse
            )

    # 3. Finaliser avec calcul de scores
    parcours.note_obtenue = parcours.calculer_note()
    parcours.note_sur_20 = parcours.calculer_note_sur_20()
    parcours.statut = 'TERMINE'
    parcours.save()
```

### Analyses et rapports
```python
# Rapport de performance stagiaire
def generer_rapport_stagiaire(stagiaire_id):
    stagiaire = Stagiaire.objects.get(id=stagiaire_id)
    analyse = stagiaire.analyse

    return {
        'info_generale': {
            'nom_complet': f"{stagiaire.user.prenom} {stagiaire.user.nom}",
            'societe': stagiaire.societe,
            'niveau_global': analyse.niveau_global
        },
        'performances': {
            'questionnaires_termines': analyse.nombre_questionnaires_termines,
            'note_moyenne': analyse.note_moyenne_sur_20,
            'temps_formation_heures': analyse.temps_formation_heures
        },
        'domaines_amelioration': analyse.obtenir_domaines_amelioration(),
        'parcours_recents': stagiaire.parcours.filter(
            statut='TERMINE'
        ).order_by('-date_realisation')[:5]
    }
```

Cette documentation couvre l'ensemble des modèles et leurs interactions. La plateforme utilise un système sophistiqué de notation et d'analyse qui permet un suivi précis des performances et des recommandations personnalisées.