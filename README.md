# 🎯 Quiz Platform API

Une plateforme complète de quiz et questionnaires avec API REST avancée, gestion des utilisateurs, scoring intelligent et analyses détaillées.

## 🚀 Fonctionnalités

### 👥 Gestion des utilisateurs
- **Authentification JWT** sécurisée avec refresh tokens
- **Rôles utilisateurs** : Administrateurs et Stagiaires
- **Profils personnalisés** avec informations de société
- **Gestion des permissions** granulaire

### 📝 Système de questionnaires
- **CRUD complet** pour les questionnaires et questions
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
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
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

# Base de données (optionnel pour dev)
DB_NAME=quiz_platform
DB_USER=postgres
DB_PASSWORD=motdepasse
DB_HOST=localhost
DB_PORT=5432

# Frontend
FRONTEND_URL=http://localhost:3000

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=motdepasse
```

### 5. Migrations et données de démonstration
```bash
python manage.py migrate
python manage.py create_demo_data
```

### 6. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 7. Lancer le serveur
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
# Inscription
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "stagiaire@test.com",
    "password": "motdepasse123",
    "nom": "Dupont",
    "prenom": "Jean",
    "login": "jdupont",
    "role": "STAGIAIRE"
  }'

# Connexion
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "stagiaire@test.com",
    "password": "motdepasse123"
  }'
```

### Accès aux questionnaires
```bash
# Liste des questionnaires
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/quizzes/questionnaires/

# Commencer un questionnaire
curl -X POST http://localhost:8000/api/responses/parcours/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"questionnaire": 1}'
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
Pour utiliser PostgreSQL en production, décommentez la configuration dans `settings.py` et configurez les variables d'environnement correspondantes.

### CORS pour frontend
Les domaines autorisés sont configurés dans `CORS_ALLOWED_ORIGINS`. Ajoutez votre domaine frontend pour la production.

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

---

**Quiz Platform** - Plateforme de formation et d'évaluation nouvelle génération 🎯