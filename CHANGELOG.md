# 📋 Changelog - Quiz Platform

## Version 2.0.0 - 2025-09-24

### 🚀 Changements majeurs

#### Réorganisation de l'API
- **BREAKING CHANGE** : Restructuration complète des endpoints par domaine fonctionnel
- Nouvelle organisation :
  - `/api/auth/` - Authentification
  - `/api/users/` - Profil utilisateur
  - `/api/stagiaires/` - Gestion stagiaires (Admin)
  - `/api/admins/` - Gestion admins (Admin)
  - `/api/quizzes/` - Questionnaires & questions
  - `/api/responses/` - Parcours & analyses

#### Simplification du modèle utilisateur
- **BREAKING CHANGE** : Suppression des champs `is_staff` et `is_superuser` de la base de données
- Conservation en tant que propriétés calculées basées sur le rôle
- Système de rôles simplifié : `ADMIN` et `STAGIAIRE` uniquement
- Suppression de `PermissionsMixin` - utilisation de propriétés personnalisées

#### Configuration base de données
- **BREAKING CHANGE** : PostgreSQL par défaut (plus de SQLite)
- Configuration via variables d'environnement `.env`
- Migration automatique des anciens champs utilisateur

### ✨ Nouvelles fonctionnalités

#### Endpoints d'administration
- `POST /api/admins/create/` - Créer des administrateurs
- Gestion complète des stagiaires via `/api/stagiaires/`
- Permissions strictes basées sur le rôle

#### Documentation améliorée
- Collection Postman mise à jour avec la nouvelle structure
- Documentation complète des endpoints (`docs/API_ENDPOINTS.md`)
- Annotations Swagger pour tous les endpoints d'authentification
- Exemples et descriptions détaillées

### 🔧 Améliorations

#### API et Documentation
- Interface Swagger UI plus claire et organisée
- Suppression des endpoints Djoser inutiles
- Réduction de la complexité de l'API
- Variables automatiques dans la collection Postman
- Scripts de test pour extraction des tokens

#### Configuration
- Fichier `.env.example` mis à jour
- Configuration CORS simplifiée
- Variables d'environnement documentées

### 🗑️ Suppressions

#### Endpoints supprimés
- Tous les endpoints Djoser (`/api/auth/djoser/`)
- Endpoints d'inscription publique
- Gestion des permissions Django complexes

#### Champs modèle supprimés
- `User.is_staff` (champ BD)
- `User.is_superuser` (champ BD)
- `User.groups` (champ BD)
- `User.user_permissions` (champ BD)

### 📦 Migration

#### Étapes de migration depuis v1.x
1. **Sauvegarder la base de données**
2. **Mettre à jour les variables d'environnement** :
   ```env
   DB_NAME=quiz_platform_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   ```
3. **Appliquer les migrations** :
   ```bash
   python manage.py migrate
   ```
4. **Mettre à jour les URLs frontend** :
   - `POST /api/users/login/` → `POST /api/auth/login/`
   - `POST /api/users/logout/` → `POST /api/auth/logout/`
   - etc.

5. **Vérifier l'authentification** :
   - Utiliser `"login"` au lieu de `"email"` pour la connexion
   - Tokens JWT inchangés

### 🐛 Corrections
- Correction des contraintes de base de données pour les nouveaux utilisateurs
- Gestion cohérente des permissions admin/stagiaire
- Validation améliorée des serializers

### ⚠️ Breaking Changes

1. **URLs changées** :
   ```diff
   - POST /api/users/login/
   + POST /api/auth/login/

   - POST /api/users/logout/
   + POST /api/auth/logout/

   - GET /api/users/stagiaires/
   + GET /api/stagiaires/

   - POST /api/users/create/
   + POST /api/admins/create/
   ```

2. **Base de données** :
   - Migration requise pour supprimer les anciens champs
   - PostgreSQL obligatoire

3. **Authentification** :
   - Champ `login` requis (plus `email`)
   - Suppression des endpoints Djoser

### 📚 Documentation mise à jour

- `README.md` - Guide d'installation et utilisation
- `docs/API_ENDPOINTS.md` - Documentation complète des endpoints
- `Quiz_Platform_Postman_Collection.json` - Collection Postman v2.0
- `.env.example` - Variables d'environnement

---

## Version 1.0.0 - 2025-09-20

### 🎯 Version initiale
- API REST complète avec Django REST Framework
- Authentification JWT
- Gestion des questionnaires et parcours
- Système d'analyse et recommandations
- Interface d'administration Django
- Documentation Swagger/OpenAPI