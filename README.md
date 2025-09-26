# 🎯 Quiz Platform API

Une plateforme complète de quiz et questionnaires avec API REST optimisée, gestion des utilisateurs simplifiée et analyses détaillées avancées.

## 🚀 Fonctionnalités

### 👥 Gestion des utilisateurs simplifiée
- **Authentification JWT** sécurisée avec refresh tokens automatiques
- **Système de rôles simplifié** : `ADMIN` et `STAGIAIRE` uniquement
- **API organisée** par domaine fonctionnel pour une meilleure clarté
- **Gestion des permissions** basée sur le rôle avec middleware sécurisé

### 📝 Système de questionnaires optimisé
- **CRUD complet** pour les questionnaires et questions (Admin)
- **Questions à choix unique ou multiples** avec validation métier
- **Système de réponses flexible** avec gestion des bonnes/mauvaises réponses
- **Gestion du temps** par questionnaire avec contrôles avancés
- **Validation des contraintes** métier (suppression sécurisée, etc.)

### 🎯 Passage de quiz avancé
- **Suivi en temps réel** de la progression avec état persistant
- **Calcul de score sophistiqué** avec algorithmes de notation avancés
- **Support choix multiples** avec scoring partiel intelligent
- **Pénalités optionnelles** pour les mauvaises réponses
- **Recommandations personnalisées** basées sur l'analyse des performances
- **Analyse temporelle** de l'efficacité (score/temps)

### 📊 Analytics et reporting avancés
- **Analyses détaillées** par stagiaire, questionnaire et question
- **Statistiques globales** avec tendances et métriques comparatives
- **Identification automatique** des domaines d'amélioration
- **Dashboard admin** avec métriques complètes en temps réel
- **Export CSV** pour analyses externes
- **Système de recommandations** basé sur l'IA

### 🔄 Nouvelles fonctionnalités
- **Système d'analyses automatiques** - AnalyseStagiaire, AnalyseQuestionnaire, AnalyseQuestion
- **Calculs de performance** - Efficacité temporelle, niveaux de difficulté
- **Maintenance automatisée** - Recalcul des statistiques
- **API optimisée** - Suppression des endpoints redondants

## 🛠️ Stack technique

- **Backend** : Django 4.2.7 + Django REST Framework 3.14.0
- **Base de données** : PostgreSQL (production) / SQLite (développement)
- **Authentification** : JWT avec django-rest-framework-simplejwt
- **Documentation API** : DRF Spectacular (OpenAPI 3.0) avec Swagger UI
- **CORS** : django-cors-headers pour intégration frontend
- **Validation** : django-filter pour filtrage avancé et recherche
- **Sécurité** : Permissions personnalisées et validation métier

## 📋 Prérequis

- Python 3.8+
- pip
- Virtualenv (recommandé)
- PostgreSQL 12+ (pour la production)

## ⚡ Installation rapide

### 1. Cloner le repository
```bash
git clone <repository-url>
cd projet_quiz
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de l'environnement
Créer un fichier `.env` à la racine :
```env
# Configuration de base
SECRET_KEY=votre_cle_secrete_django_super_longue_et_securisee
DEBUG=True

# Configuration de base de données (PostgreSQL recommandé)
DB_NAME=quiz_platform_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# CORS et Frontend
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

# Configuration JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Email (optionnel pour reset password)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password
```

### 5. Créer la base de données
```bash
# PostgreSQL (recommandé pour production)
createdb quiz_platform_db

# Ou SQLite (automatique, pour développement)
# Rien à faire, Django créera automatiquement db.sqlite3
```

### 6. Migrations et initialisation
```bash
python manage.py migrate
```

### 7. Créer un administrateur
```bash
python manage.py shell
>>> from users.models import User
>>> admin = User.objects.create_superuser(
...     login='admin',
...     email='admin@example.com',
...     password='admin123',
...     nom='Administrateur',
...     prenom='Principal'
... )
>>> exit()
```

### 8. Lancer le serveur
```bash
python manage.py runserver
```

L'API sera accessible sur `http://localhost:8000`

## 📚 Accès à la documentation

### 🔍 Documentation API interactive
- **Swagger UI** : `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc** : `http://localhost:8000/api/schema/redoc/`
- **Schema OpenAPI** : `http://localhost:8000/api/schema/`

### 🔐 Interface d'administration
- **Django Admin** : `http://localhost:8000/admin/`
- Login : admin / admin123

### 📄 Documentation détaillée
- **API Endpoints** : `docs/API_ENDPOINTS.md` - Guide complet des endpoints
- **Guide Auth Rapide** : `docs/AUTH_QUICKSTART.md` - Démarrage rapide authentification
- **Test Reset Password** : `docs/TESTING_RESET_PASSWORD.md` - Guide de test complet
- **Modèles de données** : `docs/MODELS.md` - Documentation détaillée des modèles
- **Frontend Integration** : `docs/FRONTEND.md`
- **Déploiement** : `docs/DEPLOYMENT.md`

## 🏗️ Architecture du projet

```
quiz_platform/
├── quiz_platform/          # Configuration Django
│   ├── settings.py         # Settings avec config environnement
│   ├── urls.py            # URLs principales organisées
│   └── wsgi.py            # Point d'entrée WSGI
├── users/                  # Gestion utilisateurs et authentification
│   ├── models.py          # User, Stagiaire (profils étendus)
│   ├── serializers.py     # Sérialisation avec validation
│   ├── views.py           # ViewSets et logique auth
│   ├── permissions.py     # Permissions personnalisées
│   ├── managers.py        # Custom UserManager
│   └── auth_urls.py       # URLs authentification
├── quizzes/               # Questionnaires et questions
│   ├── models.py          # Questionnaire, Question, Reponse
│   ├── serializers.py     # Sérialisation avec validation métier
│   ├── views.py           # CRUD optimisé avec statistiques
│   ├── filters.py         # Filtres avancés
│   └── urls.py           # URLs questionnaires
├── responses/             # Parcours, analyses et statistiques
│   ├── models.py          # Parcours, ReponseUtilisateur, Analyses*
│   ├── serializers.py     # Calculs de scores avancés
│   ├── views.py           # Logique métier complexe
│   └── urls.py           # URLs parcours et analytics
└── docs/                  # Documentation complète
    ├── API_ENDPOINTS.md   # Documentation API mise à jour
    ├── FRONTEND.md        # Guide intégration frontend
    └── DEPLOYMENT.md      # Guide de déploiement
```

## 🎮 Utilisation rapide

### Structure API organisée

L'API est maintenant organisée par domaine fonctionnel :

```
/api/
├── auth/           # Authentification JWT complète
├── users/          # Profil utilisateur personnel
├── stagiaires/     # Gestion stagiaires (Admin)
├── admins/         # Gestion admins (Admin)
├── quizzes/        # Questionnaires & questions (Admin)
└── parcours/       # Parcours de quiz & analyses
```

### 🔐 Endpoints d'authentification complets

```
/api/auth/
├── login/                      # Connexion utilisateur
├── logout/                     # Déconnexion + blacklist token
├── token/refresh/              # Renouvellement token JWT
├── check-auth/                 # Vérification état authentification
├── change-password/            # Changement mot de passe (authentifié)
├── reset-password/             # Demande réinitialisation par email
└── reset-password-confirm/     # Confirmation réinitialisation avec token
```

### Authentification et premiers pas

```bash
# 1. Connexion admin
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": "admin",
    "password": "admin123"
  }'

# Response: { "refresh": "...", "access": "...", "user": {...} }

# 2. Créer un stagiaire (nécessite token admin)
curl -X POST http://localhost:8000/api/stagiaires/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "stagiaire@test.com",
    "password": "motdepasse123",
    "confirm_password": "motdepasse123",
    "nom": "Dupont",
    "prenom": "Jean",
    "login": "jdupont",
    "societe": "TechCorp"
  }'

# 3. Créer un questionnaire
curl -X POST http://localhost:8000/api/quizzes/questionnaires/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Quiz Python Débutant",
    "description": "Introduction aux concepts de base",
    "duree_minutes": 30
  }'
```

### Workflow complet de quiz

```bash
# 1. Login stagiaire
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"login": "jdupont", "password": "motdepasse123"}'

# 2. Voir les questionnaires disponibles
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/parcours/questionnaires-disponibles/

# 3. Démarrer un parcours
curl -X POST http://localhost:8000/api/parcours/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"questionnaire_id": 1}'

# 4. Obtenir la question courante
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/parcours/1/question-courante/

# 5. Répondre à la question
curl -X POST http://localhost:8000/api/parcours/1/repondre/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reponses_ids": [1, 3], "temps_reponse_sec": 45}'

# 6. Terminer le parcours
curl -X POST http://localhost:8000/api/parcours/1/terminer/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"temps_total_sec": 1200}'

# 7. Voir les résultats détaillés
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/parcours/1/resultats-detailles/
```

## 🔧 Fonctionnalités avancées

### 📊 Système de notation intelligent

- **Choix unique** : Score binaire (1.0 ou 0.0)
- **Choix multiples** : Score partiel calculé
- **Formule standard** : `bonnes_selections / total_reponses_correctes`
- **Avec pénalités** : `max(0, (bonnes - mauvaises) / total_correctes)`

### 🎯 Analyses automatiques

Le système calcule automatiquement :
- **Performance par stagiaire** : Notes moyennes, temps de formation, niveau global
- **Difficulté des questions** : Taux de réussite, temps moyen de réponse
- **Efficacité des questionnaires** : Note médiane, taux d'abandon, questions difficiles

### 🔍 Recommandations personnalisées

- Domaines à améliorer basés sur les performances
- Suggestions de formation complémentaire
- Analyse de l'efficacité temporelle

## 🧪 Tests

```bash
# Tous les tests
python manage.py test

# Tests avec coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère un rapport HTML dans htmlcov/
```

## 🚀 Déploiement

Voir `docs/DEPLOYMENT.md` pour les instructions complètes de déploiement en production avec Docker et PostgreSQL.

### Variables de production importantes
```env
DEBUG=False
SECRET_KEY=votre_cle_super_securisee_en_production
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DB_HOST=votre-serveur-postgres
CORS_ALLOWED_ORIGINS=https://votre-frontend.com
```

## 🤝 Intégration frontend

### Vue.js / React / Angular
Voir `docs/FRONTEND.md` pour des guides complets incluant :
- Configuration JWT avec intercepteurs
- Gestion automatique des refresh tokens
- Composants d'authentification
- Gestion d'état des quiz
- Exemples de pages complètes

## 📈 Monitoring et maintenance

### Health checks
```bash
# Vérifier l'état de l'API
curl http://localhost:8000/api/auth/check-auth/

# Recalculer les analyses (admin)
curl -X POST http://localhost:8000/api/parcours/maintenance/recalculer-analyses/ \
  -H "Authorization: Bearer <admin_token>"

# Export des données
curl -H "Authorization: Bearer <admin_token>" \
  "http://localhost:8000/api/parcours/rapports/export/?format=csv"
```

## 🔄 Changements récents

### ✅ Endpoints optimisés
Les endpoints suivants ont été supprimés (redondance) :
- ❌ `POST /api/quizzes/questionnaires/{id}/ajouter_question/`
- ❌ `POST /api/quizzes/questionnaires/{id}/dupliquer/`
- ❌ `POST /api/quizzes/questions/{id}/dupliquer/`

### ✨ Nouvelles fonctionnalités
- **Analyses automatiques** avec modèles dédiés
- **Export CSV** des données de performance
- **Recommandations IA** personnalisées
- **API clarifiée** avec meilleure organisation

## 📞 Support et ressources

- **Documentation API interactive** : Swagger UI disponible localement
- **Collection Postman** : `Quiz_Platform_Postman_Collection.json` incluse
- **Exemples d'intégration** : Voir `docs/FRONTEND.md`
- **Issues** : Utiliser le système d'issues du repository

## 📄 Collection Postman

Une collection Postman complète est disponible : `Quiz_Platform_Postman_Collection.json`

### Fonctionnalités de la collection :
- ✅ Tous les endpoints avec exemples de données
- ✅ Variables automatiques pour les tokens JWT
- ✅ Scripts de test pour validation des réponses
- ✅ Organisation par domaines fonctionnels
- ✅ Workflow complet de bout en bout

### Import et utilisation :
1. Ouvrir Postman
2. Importer `Quiz_Platform_Postman_Collection.json`
3. Configurer les variables d'environnement (BASE_URL, etc.)
4. Commencer par Login pour récupérer les tokens
5. Tester les différents workflows selon votre rôle

---

**Quiz Platform** - Plateforme de formation et d'évaluation nouvelle génération 🎯

*Développée avec Django REST Framework pour une performance optimale et une évolutivité maximale.*