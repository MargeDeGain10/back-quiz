# 🎯 Quiz Platform API

Une plateforme complète de quiz et questionnaires avec API REST minimaliste, gestion des utilisateurs simplifiée et analyses détaillées.

## 🚀 Fonctionnalités

### 👥 Gestion des utilisateurs simplifiée
- **Authentification JWT** sécurisée avec refresh tokens
- **Système de rôles simplifié** : `ADMIN` et `STAGIAIRE` uniquement
- **API organisée** par domaine fonctionnel
- **Gestion des permissions** basée sur le rôle

### 📝 Système de questionnaires
- **CRUD complet** pour les questionnaires et questions (Admin)
- **Questions à choix unique ou multiples**
- **Validation des contraintes métier**
- **Gestion du temps** par questionnaire

### 🎯 Passage de quiz avancé
- **Suivi en temps réel** de la progression
- **Calcul de score sophistiqué** avec pénalités optionnelles
- **Recommandations personnalisées** basées sur les performances
- **Analyse temporelle** de l'efficacité

### 📊 Analytics et reporting
- **Analyses détaillées** par stagiaire, questionnaire et question
- **Statistiques globales** et tendances
- **Identification automatique** des domaines d'amélioration
- **Dashboard admin** avec métriques complètes

## 🛠️ Stack technique

- **Backend** : Django 4.2.7 + Django REST Framework 3.14.0
- **Base de données** : PostgreSQL
- **Authentification** : JWT avec django-rest-framework-simplejwt
- **Documentation API** : DRF Spectacular (OpenAPI 3.0)
- **CORS** : django-cors-headers
- **Validation** : django-filter pour filtrage avancé

## 📋 Prérequis

- Python 3.8+
- pip
- Virtualenv (recommandé)
- PostgreSQL (pour la production)

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
SECRET_KEY=votre_cle_secrete_django_ici
DEBUG=True

# Configuration PostgreSQL
DB_NAME=quiz_platform_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Frontend et CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

# Email (optionnel)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password
```

### 5. Créer la base de données PostgreSQL
```bash
createdb quiz_platform_db
```

### 6. Migrations de base
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

## 🎮 Utilisation rapide

### Authentification
```bash
# Connexion avec l'admin créé
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": "admin",
    "password": "admin123"
  }'

# Créer un stagiaire (nécessite token admin)
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
    "promotion": "2024",
    "specialite": "Développement Web"
  }'
```

### Structure des endpoints
La nouvelle API est organisée par domaine fonctionnel :

#### 🔐 Authentification (`/api/auth/`)
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/logout/` - Déconnexion
- `POST /api/auth/token/refresh/` - Refresh token
- `GET /api/auth/check-auth/` - Vérifier auth
- `POST /api/auth/change-password/` - Changer mot de passe
- `POST /api/auth/reset-password/` - Reset mot de passe

#### 👤 Profil utilisateur (`/api/users/`)
- `GET /api/users/me/` - Mon profil
- `PUT /api/users/me/` - Modifier mon profil

#### 👥 Gestion des stagiaires (`/api/stagiaires/`) - Admin uniquement
- `GET /api/stagiaires/` - Lister stagiaires
- `POST /api/stagiaires/` - Créer stagiaire
- `GET /api/stagiaires/{id}/` - Détail stagiaire
- `PUT /api/stagiaires/{id}/` - Modifier stagiaire
- `DELETE /api/stagiaires/{id}/` - Supprimer stagiaire

#### 🔑 Gestion des admins (`/api/admins/`) - Admin uniquement
- `POST /api/admins/create/` - Créer administrateur

#### 📚 Quiz (`/api/quizzes/` et `/api/responses/`)
- Gestion des questionnaires, questions et réponses (inchangée)

### Utilisation des endpoints
```bash
# Accès aux questionnaires (Admin)
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/quizzes/questionnaires/

# Démarrer un quiz (Stagiaire)
curl -X POST http://localhost:8000/api/responses/parcours/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"questionnaire_id": 1}'

# Voir son profil
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/users/me/
```

## 🏗️ Architecture du projet

```
quiz_platform/
├── quiz_platform/          # Configuration Django
│   ├── settings.py         # Settings avec config environnement
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Point d'entrée WSGI
├── users/                  # Gestion utilisateurs
│   ├── models.py          # User, Stagiaire
│   ├── serializers.py     # Sérialisation API
│   ├── views.py           # ViewSets et authentification
│   └── tests/             # Tests unitaires
├── quizzes/               # Questionnaires et questions
│   ├── models.py          # Questionnaire, Question, Reponse
│   ├── serializers.py     # Sérialisation avec validation
│   ├── views.py           # CRUD complet
│   └── tests/             # Tests unitaires
├── responses/             # Parcours et analyses
│   ├── models.py          # Parcours, ReponseUtilisateur, Analyses
│   ├── serializers.py     # Calculs de scores
│   ├── views.py           # Logique métier avancée
│   └── tests/             # Tests unitaires et intégration
└── docs/                  # Documentation
    ├── API.md             # Documentation API détaillée
    ├── FRONTEND.md        # Guide intégration Vue.js
    └── DEPLOYMENT.md      # Guide de déploiement
```

## 🔧 Configuration avancée

### Variables d'environnement complètes
Voir le fichier `docs/ENVIRONMENT.md` pour la liste complète des variables disponibles.

### Base de données PostgreSQL
La plateforme est configurée pour utiliser PostgreSQL par défaut. Les variables d'environnement dans le fichier `.env` permettent de configurer la connexion.

### CORS pour frontend
Les domaines autorisés sont configurés dans `CORS_ALLOWED_ORIGINS`. Modifiez cette variable dans `.env` pour ajouter votre domaine frontend en production.

## 🧪 Tests

```bash
# Tous les tests
python manage.py test

# Tests avec coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère un rapport HTML
```

## 🚀 Déploiement

Voir `docs/DEPLOYMENT.md` pour les instructions complètes de déploiement en production avec Docker et PostgreSQL.

## 📈 Monitoring et logs

### Logs de développement
Les logs sont configurés pour afficher les informations importantes en console durant le développement.

### Health check
```bash
curl http://localhost:8000/api/health/
```

## 🤝 Intégration frontend

### Vue.js
Voir `docs/FRONTEND.md` pour le guide complet d'intégration avec Vue.js, incluant :
- Configuration JWT avec Axios
- Gestion des tokens de refresh
- Exemples de composants
- Gestion des erreurs

## 📞 Support

- **Documentation API** : Accessible via Swagger UI
- **Issues** : Utiliser le système d'issues du repository
- **Email** : contact@quiz-platform.com

## 📄 License

MIT License - voir le fichier LICENSE pour plus de détails.

## 📄 Collection Postman

Une collection Postman complète est disponible : `Quiz_Platform_Postman_Collection.json`

Cette collection inclut :
- Tous les endpoints avec exemples
- Variables automatiques pour les tokens
- Scripts de test pour l'extraction des données
- Organisation par domaines fonctionnels

### Importation
1. Ouvrir Postman
2. Importer le fichier `Quiz_Platform_Postman_Collection.json`
3. Configurer les variables d'environnement si nécessaire
4. Tester les endpoints en commençant par l'authentification

---

**Quiz Platform** - Plateforme de formation et d'évaluation nouvelle génération 🎯
