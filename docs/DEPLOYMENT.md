# 🚀 Guide de déploiement

Ce guide détaille les différentes méthodes de déploiement de Quiz Platform en production.

## 🐳 Déploiement avec Docker (Recommandé)

### Prérequis
- Docker
- Docker Compose
- Domaine configuré (optionnel)

### Structure des fichiers

Créez les fichiers suivants :

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=quiz_platform.settings

# Dossier de travail
WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY . .

# Script d'entrée
RUN chmod +x ./docker-entrypoint.sh

# Port d'exposition
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["./docker-entrypoint.sh"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME:-quiz_platform}
      POSTGRES_USER: ${DB_USER:-quiz_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  web:
    build: .
    restart: always
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env

  nginx:
    image: nginx:alpine
    restart: always
    depends_on:
      - web
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - static_volume:/var/www/static
      - media_volume:/var/www/media

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

#### docker-entrypoint.sh
```bash
#!/bin/bash

# Attendre que PostgreSQL soit prêt
echo "Attente de PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL est prêt !"

# Migrations Django
echo "Application des migrations..."
python manage.py migrate

# Collecte des fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer des données de démonstration si nécessaire
if [ "$CREATE_DEMO_DATA" = "true" ]; then
  echo "Création des données de démonstration..."
  python manage.py create_demo_data
fi

# Démarrer Gunicorn
echo "Démarrage de l'application..."
exec gunicorn quiz_platform.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${WORKERS:-4} \
  --worker-class gevent \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --keep-alive 5 \
  --log-level info \
  --access-logfile - \
  --error-logfile -
```

#### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name quiz.votre-domaine.com;

        # Redirection HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name quiz.votre-domaine.com;

        # SSL
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Headers sécurité
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Fichiers statiques
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /var/www/media/;
            expires 1y;
        }

        # API
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Limitation du taux de requêtes
        location /api/users/login/ {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://web;
        }
    }

    # Zones de limitation
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/m;
}
```

### Déploiement

1. **Préparer l'environnement** :
```bash
# Variables d'environnement production
cp .env.example .env.production
# Éditer .env.production avec vos valeurs

# Certificats SSL (Let's Encrypt recommandé)
mkdir ssl
# Placer cert.pem et key.pem dans ssl/
```

2. **Construire et lancer** :
```bash
docker-compose up -d --build
```

3. **Vérifications** :
```bash
# Status des services
docker-compose ps

# Logs
docker-compose logs -f web

# Accès au shell Django
docker-compose exec web python manage.py shell
```

## ☁️ Déploiement Cloud

### AWS (Amazon Web Services)

#### Architecture recommandée
- **ECS Fargate** pour les containers
- **RDS PostgreSQL** pour la base de données
- **ElastiCache Redis** pour le cache
- **ALB** pour le load balancing
- **CloudFront** pour le CDN
- **S3** pour les fichiers statiques

#### Configuration ECS

```yaml
# docker-compose.aws.yml
version: '3.8'
services:
  web:
    image: your-registry.amazonaws.com/quiz-platform:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/quiz-platform
        awslogs-region: eu-west-1
        awslogs-stream-prefix: web
```

### Google Cloud Platform

#### Configuration Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/quiz-platform', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/quiz-platform']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'quiz-platform'
      - '--image'
      - 'gcr.io/$PROJECT_ID/quiz-platform'
      - '--region'
      - 'europe-west1'
      - '--platform'
      - 'managed'
```

### DigitalOcean Apps

```yaml
# .do/app.yaml
name: quiz-platform
services:
- name: web
  source_dir: /
  github:
    repo: your-username/quiz-platform
    branch: main
  run_command: gunicorn quiz_platform.wsgi:application --bind 0.0.0.0:8080
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
    type: SECRET
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}

databases:
- name: db
  engine: PG
  version: "13"

static_sites:
- name: frontend
  source_dir: /frontend/dist
  github:
    repo: your-username/quiz-frontend
    branch: main
```

## 🔧 Configuration avancée

### Gunicorn optimisé

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Sécurité
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
worker_tmp_dir = "/dev/shm"
```

### Settings production

```python
# quiz_platform/settings/production.py
from .base import *
import os

DEBUG = False

# Hosts autorisés
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Base de données
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}

# Cache Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Stockage S3
if os.environ.get('AWS_ACCESS_KEY_ID'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Sécurité
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/quiz-platform/app.log',
            'maxBytes': 1024*1024*50,  # 50 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## 📊 Monitoring et observabilité

### Health check endpoint

```python
# quiz_platform/health.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    status = {"status": "healthy", "checks": {}}

    # Test base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    # Test Redis
    try:
        cache.set("health_check", "ok", 1)
        cache.get("health_check")
        status["checks"]["cache"] = "ok"
    except Exception as e:
        status["checks"]["cache"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    return JsonResponse(status)
```

### Métriques Prometheus

```python
# requirements.txt
django-prometheus==2.3.1

# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    # ... autres apps
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... autres middlewares
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Configuration Prometheus
PROMETHEUS_EXPORT_MIGRATIONS = False
```

### Alertes (exemple avec AlertManager)

```yaml
# alerts.yml
groups:
- name: quiz-platform
  rules:
  - alert: HighErrorRate
    expr: rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Taux d'erreur élevé détecté"

  - alert: DatabaseConnectionIssue
    expr: up{job="quiz-platform-db"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Problème de connexion à la base de données"
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python manage.py test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3

    - name: Deploy to production
      uses: docker/build-push-action@v3
      with:
        context: .
        push: true
        tags: ${{ secrets.REGISTRY_URL }}/quiz-platform:latest

    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.4
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /app/quiz-platform
          docker-compose pull
          docker-compose up -d
```

## 💾 Sauvegarde et restauration

### Script de sauvegarde automatique

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="quiz_platform"

# Sauvegarde PostgreSQL
docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# Sauvegarde des fichiers media
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" media/

# Nettoyage (garder 7 jours)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Sauvegarde terminée : $DATE"
```

### Cron pour sauvegarde quotidienne

```bash
# Ajouter au crontab
0 2 * * * /app/backup.sh >> /var/log/backup.log 2>&1
```

## 🔧 Dépannage

### Problèmes courants

#### Erreur de connexion base de données
```bash
# Vérifier la connectivité
docker-compose exec web python manage.py dbshell

# Logs PostgreSQL
docker-compose logs db
```

#### Problème de permissions
```bash
# Vérifier les permissions des volumes
ls -la volumes/

# Recréer les volumes
docker-compose down -v
docker-compose up -d
```

#### Lenteur de l'application
```bash
# Profiling Django
pip install django-debug-toolbar

# Monitoring des requêtes
docker-compose exec web python manage.py shell
>>> from django.db import connection
>>> connection.queries
```

### Commandes utiles

```bash
# Redémarrage rapide
docker-compose restart web

# Reconstruction complète
docker-compose down && docker-compose up -d --build

# Logs en temps réel
docker-compose logs -f

# Shell Django
docker-compose exec web python manage.py shell

# Migrations
docker-compose exec web python manage.py migrate

# Création d'un superuser
docker-compose exec web python manage.py createsuperuser
```

---

Ce guide couvre tous les aspects du déploiement de Quiz Platform, de la configuration simple avec Docker aux déploiements cloud avancés avec monitoring complet.