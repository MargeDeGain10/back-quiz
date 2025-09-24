# 📚 API Endpoints - Quiz Platform

Documentation complète des endpoints de l'API organisés par domaine fonctionnel.

## 🏗️ Architecture

L'API est organisée en domaines fonctionnels distincts pour une meilleure clarté :

```
/api/
├── auth/           # Authentification
├── users/          # Profil utilisateur
├── stagiaires/     # Gestion stagiaires (Admin)
├── admins/         # Gestion admins (Admin)
├── quizzes/        # Questionnaires & questions
└── responses/      # Parcours & analyses
```

## 🔐 Authentification - `/api/auth/`

### Login
- **POST** `/api/auth/login/`
- **Description** : Connexion utilisateur avec login/password
- **Body** :
  ```json
  {
    "login": "admin",
    "password": "admin123"
  }
  ```
- **Response** :
  ```json
  {
    "refresh": "eyJ...",
    "access": "eyJ...",
    "user": { ... }
  }
  ```

### Logout
- **POST** `/api/auth/logout/`
- **Description** : Déconnexion et blacklist du refresh token
- **Auth** : Bearer Token requis
- **Body** :
  ```json
  {
    "refresh_token": "eyJ..."
  }
  ```

### Refresh Token
- **POST** `/api/auth/token/refresh/`
- **Description** : Renouveler le token d'accès
- **Body** :
  ```json
  {
    "refresh": "eyJ..."
  }
  ```

### Check Auth
- **GET** `/api/auth/check-auth/`
- **Description** : Vérifier l'état d'authentification
- **Auth** : Bearer Token requis

### Change Password
- **POST** `/api/auth/change-password/`
- **Description** : Changer son mot de passe
- **Auth** : Bearer Token requis
- **Body** :
  ```json
  {
    "old_password": "ancien_mot_de_passe",
    "new_password": "nouveau_mot_de_passe"
  }
  ```

### Reset Password
- **POST** `/api/auth/reset-password/`
- **Description** : Réinitialiser le mot de passe par email
- **Body** :
  ```json
  {
    "email": "user@example.com"
  }
  ```

---

## 👤 Profil Utilisateur - `/api/users/`

### Mon Profil
- **GET** `/api/users/me/`
- **Description** : Récupérer mon profil utilisateur
- **Auth** : Bearer Token requis

### Modifier Mon Profil
- **PUT** `/api/users/me/`
- **Description** : Modifier mon profil utilisateur
- **Auth** : Bearer Token requis
- **Body** :
  ```json
  {
    "nom": "Nouveau Nom",
    "prenom": "Nouveau Prénom",
    "email": "nouveau@email.com"
  }
  ```

---

## 👥 Gestion des Stagiaires - `/api/stagiaires/` 🔒 Admin

### Lister les Stagiaires
- **GET** `/api/stagiaires/`
- **Description** : Liste paginée des stagiaires
- **Auth** : Bearer Token (Admin) requis
- **Filtres** : `?search=nom&ordering=nom`

### Créer un Stagiaire
- **POST** `/api/stagiaires/`
- **Description** : Créer un nouveau stagiaire
- **Auth** : Bearer Token (Admin) requis
- **Body** :
  ```json
  {
    "email": "stagiaire@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "nom": "Dupont",
    "prenom": "Jean",
    "login": "jdupont",
    "promotion": "2024",
    "specialite": "Développement Web"
  }
  ```

### Détail d'un Stagiaire
- **GET** `/api/stagiaires/{id}/`
- **Description** : Détails d'un stagiaire spécifique
- **Auth** : Bearer Token (Admin) requis

### Modifier un Stagiaire
- **PUT** `/api/stagiaires/{id}/`
- **Description** : Modifier les informations d'un stagiaire
- **Auth** : Bearer Token (Admin) requis
- **Body** :
  ```json
  {
    "nom": "Martin",
    "prenom": "Paul",
    "promotion": "2024",
    "specialite": "Data Science"
  }
  ```

### Supprimer un Stagiaire
- **DELETE** `/api/stagiaires/{id}/`
- **Description** : Supprimer un stagiaire
- **Auth** : Bearer Token (Admin) requis

---

## 🔑 Gestion des Admins - `/api/admins/` 🔒 Admin

### Créer un Administrateur
- **POST** `/api/admins/create/`
- **Description** : Créer un nouvel administrateur
- **Auth** : Bearer Token (Admin) requis
- **Body** :
  ```json
  {
    "email": "admin2@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "nom": "Administrateur",
    "prenom": "Second",
    "login": "admin2"
  }
  ```

---

## 📚 Questionnaires - `/api/quizzes/` 🔒 Admin

### Lister les Questionnaires
- **GET** `/api/quizzes/questionnaires/`
- **Description** : Liste des questionnaires
- **Auth** : Bearer Token (Admin) requis

### Créer un Questionnaire
- **POST** `/api/quizzes/questionnaires/`
- **Description** : Créer un nouveau questionnaire
- **Auth** : Bearer Token (Admin) requis
- **Body** :
  ```json
  {
    "titre": "Quiz Python Avancé",
    "description": "Test sur les concepts avancés",
    "duree_minutes": 30,
    "nombre_questions_affichees": 15,
    "seuil_reussite": 70,
    "actif": true
  }
  ```

### CRUD Questionnaires
- **GET** `/api/quizzes/questionnaires/{id}/` - Détail
- **PUT** `/api/quizzes/questionnaires/{id}/` - Modifier
- **DELETE** `/api/quizzes/questionnaires/{id}/` - Supprimer

### Questions
- **GET** `/api/quizzes/questions/` - Liste des questions
- **POST** `/api/quizzes/questions/` - Créer une question
- **GET/PUT/DELETE** `/api/quizzes/questions/{id}/` - CRUD question

---

## 🎯 Quiz et Réponses - `/api/responses/`

### Pour les Stagiaires

#### Questionnaires Disponibles
- **GET** `/api/responses/questionnaires-disponibles/`
- **Description** : Liste des questionnaires accessibles au stagiaire
- **Auth** : Bearer Token (Stagiaire) requis

#### Démarrer un Parcours
- **POST** `/api/responses/parcours/`
- **Description** : Commencer un nouveau quiz
- **Auth** : Bearer Token (Stagiaire) requis
- **Body** :
  ```json
  {
    "questionnaire_id": 1
  }
  ```

#### Progression du Parcours
- **GET** `/api/responses/parcours/{id}/` - État du parcours
- **GET** `/api/responses/parcours/{id}/question-courante/` - Question actuelle
- **POST** `/api/responses/parcours/{id}/repondre/` - Répondre à une question
- **POST** `/api/responses/parcours/{id}/terminer/` - Terminer le quiz

#### Mes Résultats
- **GET** `/api/responses/mes-parcours/` - Mon historique
- **GET** `/api/responses/parcours/{id}/resultats/` - Résultats d'un parcours
- **GET** `/api/responses/mes-recommandations/` - Recommandations personnalisées

### Pour les Admins 🔒

#### Analytics Avancées
- **GET** `/api/responses/stagiaire/{id}/synthese/` - Synthèse d'un stagiaire
- **GET** `/api/responses/questionnaire/{id}/statistiques-avancees/` - Stats questionnaire
- **GET** `/api/responses/rapports/synthese-globale/` - Dashboard global
- **GET** `/api/responses/rapports/questions-difficiles/` - Questions problématiques

#### Export et Maintenance
- **GET** `/api/responses/rapports/export/` - Export CSV des données
- **POST** `/api/responses/maintenance/recalculer-analyses/` - Recalcul des analyses

---

## 📖 Documentation - `/api/schema/`

### Accès à la Documentation
- **GET** `/api/schema/` - Schema OpenAPI JSON
- **GET** `/api/schema/swagger-ui/` - Interface Swagger UI
- **GET** `/api/schema/redoc/` - Interface ReDoc

---

## 🔒 Authentification et Permissions

### Système de Rôles
- **ADMIN** : Accès complet à tous les endpoints
- **STAGIAIRE** : Accès limité aux quiz et profil personnel

### Format des Tokens
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Durée de Vie
- **Access Token** : 1 heure
- **Refresh Token** : 7 jours (avec rotation)

---

## 📱 Codes de Réponse HTTP

### Succès
- **200** - OK
- **201** - Créé
- **204** - Pas de contenu

### Erreurs Client
- **400** - Requête invalide
- **401** - Non authentifié
- **403** - Accès refusé
- **404** - Non trouvé

### Erreurs Serveur
- **500** - Erreur interne du serveur

---

## 🚀 Collection Postman

Importez le fichier `Quiz_Platform_Postman_Collection.json` pour tester tous les endpoints avec des exemples préconfigurés et des variables automatiques pour les tokens.

**Usage recommandé :**
1. Commencer par Login
2. Utiliser les endpoints selon votre rôle
3. Les tokens sont gérés automatiquement