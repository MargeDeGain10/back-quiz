# 🔧 Variables d'environnement

Ce document détaille toutes les variables d'environnement disponibles pour configurer l'application Quiz Platform.

## 📋 Fichier .env

Créez un fichier `.env` à la racine de votre projet avec les variables suivantes :

## 🔐 Configuration de base

### SECRET_KEY
**Obligatoire** - Clé secrète Django pour le chiffrement et la sécurité.

```env
SECRET_KEY=votre_cle_secrete_django_tres_longue_et_complexe_ici
```

**Génération** :
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### DEBUG
**Optionnel** - Mode debug (par défaut : False)

```env
DEBUG=True              # Développement
DEBUG=False             # Production
```

⚠️ **Important** : Toujours mettre `False` en production !

### ALLOWED_HOSTS
**Optionnel** - Hosts autorisés (séparés par des virgules)

```env
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com
```

## 🗄️ Configuration de la base de données

### SQLite (par défaut)
Aucune configuration requise pour le développement.

### PostgreSQL (production recommandée)

```env
# Nom de la base de données
DB_NAME=quiz_platform

# Utilisateur PostgreSQL
DB_USER=quiz_user

# Mot de passe PostgreSQL
DB_PASSWORD=motdepasse_secure

# Hôte PostgreSQL
DB_HOST=localhost

# Port PostgreSQL (par défaut : 5432)
DB_PORT=5432
```

### MySQL (alternative)

```env
DB_ENGINE=mysql
DB_NAME=quiz_platform
DB_USER=quiz_user
DB_PASSWORD=motdepasse_secure
DB_HOST=localhost
DB_PORT=3306
```

## 🌐 Configuration Frontend

### FRONTEND_URL
**Optionnel** - URL du frontend pour les liens de réinitialisation

```env
FRONTEND_URL=http://localhost:3000          # Développement
FRONTEND_URL=https://quiz.votre-site.com    # Production
```

### CORS_ALLOWED_ORIGINS
**Optionnel** - Domaines autorisés pour CORS (séparés par des virgules)

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://quiz.votre-site.com
```

## 📧 Configuration Email

### Variables email générales

```env
# Backend email Django
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Serveur SMTP
EMAIL_HOST=smtp.gmail.com

# Port SMTP
EMAIL_PORT=587

# Email d'expédition
EMAIL_HOST_USER=votre@email.com

# Mot de passe ou app password
EMAIL_HOST_PASSWORD=votre_mot_de_passe

# Utiliser TLS
EMAIL_USE_TLS=True

# Email par défaut pour les envois
DEFAULT_FROM_EMAIL=Quiz Platform <noreply@votre-site.com>
```

### Exemples pour différents fournisseurs

#### Gmail
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@gmail.com
EMAIL_HOST_PASSWORD=votre_app_password
```

#### Outlook/Hotmail
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@outlook.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe
```

#### SendGrid
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=votre_api_key_sendgrid
```

## 🔑 Configuration JWT

### ACCESS_TOKEN_LIFETIME
**Optionnel** - Durée de vie du token d'accès (en minutes)

```env
ACCESS_TOKEN_LIFETIME=60           # 1 heure (défaut)
ACCESS_TOKEN_LIFETIME=1440         # 24 heures
```

### REFRESH_TOKEN_LIFETIME
**Optionnel** - Durée de vie du token de refresh (en jours)

```env
REFRESH_TOKEN_LIFETIME=7           # 7 jours (défaut)
REFRESH_TOKEN_LIFETIME=30          # 30 jours
```

### JWT_ALGORITHM
**Optionnel** - Algorithme de chiffrement JWT

```env
JWT_ALGORITHM=HS256                # Par défaut
JWT_ALGORITHM=RS256                # Avec clés RSA
```

## 📊 Configuration Cache (Redis)

```env
# URL Redis complète
REDIS_URL=redis://localhost:6379/0

# Ou configuration détaillée
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=mot_de_passe_redis

# Timeout cache (en secondes)
CACHE_TIMEOUT=300                  # 5 minutes
```

## 📈 Configuration Logging

### LOG_LEVEL
**Optionnel** - Niveau de logging

```env
LOG_LEVEL=DEBUG                    # Développement
LOG_LEVEL=INFO                     # Production
LOG_LEVEL=WARNING                  # Production critique
LOG_LEVEL=ERROR                    # Erreurs uniquement
```

### LOG_FILE
**Optionnel** - Fichier de logs

```env
LOG_FILE=/var/log/quiz-platform/app.log
```

## 🛡️ Configuration Sécurité

### CSRF_TRUSTED_ORIGINS
**Optionnel** - Domaines de confiance pour CSRF

```env
CSRF_TRUSTED_ORIGINS=https://quiz.votre-site.com,https://admin.votre-site.com
```

### SECURE_SSL_REDIRECT
**Optionnel** - Redirection forcée HTTPS

```env
SECURE_SSL_REDIRECT=True           # Production
SECURE_SSL_REDIRECT=False          # Développement
```

### SESSION_COOKIE_SECURE
**Optionnel** - Cookies sécurisés

```env
SESSION_COOKIE_SECURE=True         # Production HTTPS
SESSION_COOKIE_SECURE=False        # Développement HTTP
```

## ☁️ Configuration Cloud & Stockage

### AWS S3 (stockage de fichiers)

```env
AWS_ACCESS_KEY_ID=votre_access_key
AWS_SECRET_ACCESS_KEY=votre_secret_key
AWS_STORAGE_BUCKET_NAME=quiz-platform-files
AWS_S3_REGION_NAME=eu-west-1
AWS_S3_CUSTOM_DOMAIN=cdn.votre-site.com
```

### Google Cloud Storage

```env
GS_BUCKET_NAME=quiz-platform-files
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## 📱 Configuration Mobile/API

### API_VERSION
**Optionnel** - Version de l'API

```env
API_VERSION=v1
```

### RATE_LIMIT
**Optionnel** - Limite de requêtes par minute

```env
RATE_LIMIT_LOGIN=5                 # 5 tentatives de connexion/minute
RATE_LIMIT_API=100                 # 100 requêtes API/minute
```

## 🐳 Configuration Docker

### DJANGO_SETTINGS_MODULE
**Optionnel** - Module de settings Django

```env
DJANGO_SETTINGS_MODULE=quiz_platform.settings.production
```

### WORKERS
**Optionnel** - Nombre de workers Gunicorn

```env
WORKERS=4
```

## 📋 Exemples de fichiers .env

### Développement (.env.development)

```env
# Configuration de base
SECRET_KEY=dev_key_not_for_production_use_only
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données (SQLite par défaut)
# Pas de configuration nécessaire

# Frontend
FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email (optionnel en dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# JWT
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=7

# Logging
LOG_LEVEL=DEBUG
```

### Test (.env.test)

```env
# Configuration minimale pour les tests
SECRET_KEY=test_key_for_automated_testing_only
DEBUG=False

# Base de données en mémoire
DATABASE_URL=sqlite:///:memory:

# Désactiver les emails
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend

# Cache en mémoire
CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
```

### Production (.env.production)

```env
# Configuration de base
SECRET_KEY=your_super_secret_production_key_here
DEBUG=False
ALLOWED_HOSTS=quiz.votre-site.com,www.quiz.votre-site.com

# Base de données PostgreSQL
DB_NAME=quiz_platform_prod
DB_USER=quiz_user_prod
DB_PASSWORD=super_secure_password_here
DB_HOST=db.internal
DB_PORT=5432

# Frontend
FRONTEND_URL=https://quiz.votre-site.com
CORS_ALLOWED_ORIGINS=https://quiz.votre-site.com

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=sendgrid_api_key_here
DEFAULT_FROM_EMAIL=Quiz Platform <noreply@votre-site.com>

# JWT
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=7

# Redis
REDIS_URL=redis://redis.internal:6379/0

# Sécurité
CSRF_TRUSTED_ORIGINS=https://quiz.votre-site.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True

# Stockage
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=quiz-platform-prod
AWS_S3_REGION_NAME=eu-west-1

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/quiz-platform/app.log

# Performance
WORKERS=4
```

## 🔍 Validation des variables

Pour vérifier votre configuration :

```bash
# Vérifier les variables chargées
python manage.py check

# Tester la connexion DB
python manage.py dbshell

# Vérifier la configuration email
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'Message', 'from@test.com', ['to@test.com'])"
```

## ⚠️ Sécurité

### Variables sensibles
Ces variables **NE DOIVENT JAMAIS** être commitées :

- `SECRET_KEY`
- `DB_PASSWORD`
- `EMAIL_HOST_PASSWORD`
- `AWS_SECRET_ACCESS_KEY`
- Tous les mots de passe et clés API

### Bonnes pratiques

1. **Utilisez des outils** comme `django-environ` ou `python-decouple`
2. **Chiffrez** les secrets en production
3. **Rotez** régulièrement les clés sensibles
4. **Limitez** l'accès aux fichiers `.env`
5. **Versionez** un fichier `.env.example` sans valeurs sensibles

### Exemple .env.example

```env
# Configuration de base
SECRET_KEY=your_secret_key_here
DEBUG=True_or_False
ALLOWED_HOSTS=localhost,your_domain.com

# Base de données
DB_NAME=database_name
DB_USER=database_user
DB_PASSWORD=database_password
DB_HOST=database_host
DB_PORT=database_port

# Email
EMAIL_HOST=smtp_server
EMAIL_PORT=smtp_port
EMAIL_HOST_USER=email_username
EMAIL_HOST_PASSWORD=email_password

# Frontend
FRONTEND_URL=frontend_url
CORS_ALLOWED_ORIGINS=allowed_origins

# Optionnel
REDIS_URL=redis_connection_string
AWS_ACCESS_KEY_ID=aws_access_key
AWS_SECRET_ACCESS_KEY=aws_secret_key
```

---

Cette documentation couvre tous les aspects de configuration de l'application Quiz Platform. Adaptez les valeurs selon votre environnement et vos besoins spécifiques.