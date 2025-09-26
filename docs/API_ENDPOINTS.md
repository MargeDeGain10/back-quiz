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
└── parcours/       # Parcours & analyses
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
    "user": {
      "id": 1,
      "email": "admin@example.com",
      "nom": "Admin",
      "prenom": "Super",
      "login": "admin",
      "role": "ADMIN",
      "is_active": true
    }
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
- **Description** : Demander une réinitialisation de mot de passe par email
- **Body** :
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response (DEBUG mode)** :
  ```json
  {
    "message": "Email de réinitialisation envoyé avec succès",
    "reset_link": "http://localhost:3000/reset-password/MQ/abc123.../",
    "debug_info": {
      "uidb64": "MQ",
      "token": "abc123def456ghi789",
      "user_id": 1,
      "email": "user@example.com",
      "expires_in_hours": 24,
      "note": "Ces informations sont disponibles uniquement en mode DEBUG"
    }
  }
  ```

### Reset Password Confirm
- **POST** `/api/auth/reset-password-confirm/`
- **Description** : Confirmer la réinitialisation avec le token reçu par email
- **Body** :
  ```json
  {
    "uidb64": "MQ",
    "token": "abc123def456ghi789",
    "new_password": "nouveau_mot_de_passe_securise",
    "confirm_password": "nouveau_mot_de_passe_securise"
  }
  ```
- **Response** :
  ```json
  {
    "message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter avec votre nouveau mot de passe."
  }
  ```


---

## 👤 Profil Utilisateur - `/api/users/`

### Mon Profil
- **GET** `/api/users/me/`
- **Description** : Récupérer mon profil utilisateur complet
- **Auth** : Bearer Token requis
- **Response** :
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "nom": "Dupont",
    "prenom": "Jean",
    "login": "jdupont",
    "role": "STAGIAIRE",
    "is_active": true,
    "date_joined": "2024-01-15T10:00:00Z",
    "stagiaire_profile": {
      "societe": "TechCorp"
    }
  }
  ```

### Modifier Mon Profil
- **PUT** `/api/users/me/`
- **PATCH** `/api/users/me/`
- **Description** : Modifier mon profil utilisateur
- **Auth** : Bearer Token requis
- **Body** :
  ```json
  {
    "nom": "Nouveau Nom",
    "prenom": "Nouveau Prénom",
    "email": "nouveau@email.com",
    "stagiaire_profile": {
      "societe": "Nouvelle Société"
    }
  }
  ```

---

## 👥 Gestion des Stagiaires - `/api/stagiaires/` 🔒 Admin

### Lister les Stagiaires
- **GET** `/api/stagiaires/`
- **Description** : Liste paginée des stagiaires avec filtres
- **Auth** : Bearer Token (Admin) requis
- **Filtres** : `?search=nom&ordering=nom&societe=TechCorp`
- **Response** :
  ```json
  {
    "count": 50,
    "next": "http://api/stagiaires/?page=2",
    "previous": null,
    "results": [
      {
        "user_id": 2,
        "email": "stagiaire@example.com",
        "nom": "Dupont",
        "prenom": "Jean",
        "login": "jdupont",
        "is_active": true,
        "date_joined": "2024-01-15T10:00:00Z",
        "societe": "TechCorp"
      }
    ]
  }
  ```

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
    "societe": "TechCorp"
  }
  ```

### CRUD Stagiaires
- **GET** `/api/stagiaires/{id}/` - Détail d'un stagiaire
- **PUT** `/api/stagiaires/{id}/` - Modifier un stagiaire
- **PATCH** `/api/stagiaires/{id}/` - Modifier partiellement
- **DELETE** `/api/stagiaires/{id}/` - Supprimer un stagiaire

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
- **Description** : Liste paginée des questionnaires avec recherche et filtres
- **Auth** : Bearer Token (Admin) requis
- **Filtres** : `?search=Python&ordering=-date_creation&duree_minutes=30`
- **Response** :
  ```json
  {
    "count": 25,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "nom": "Quiz Python Avancé",
        "description": "Test sur les concepts avancés",
        "date_creation": "2024-01-15T10:00:00Z",
        "duree_minutes": 30,
        "nombre_questions": 15
      }
    ]
  }
  ```

### Créer un Questionnaire
- **POST** `/api/quizzes/questionnaires/`
- **Description** : Créer un nouveau questionnaire
- **Auth** : Bearer Token (Admin) requis
- **Body** :
  ```json
  {
    "nom": "Quiz Python Avancé",
    "description": "Test sur les concepts avancés de Python",
    "duree_minutes": 30
  }
  ```

### CRUD Questionnaires
- **GET** `/api/quizzes/questionnaires/{id}/` - Détail complet
- **PUT** `/api/quizzes/questionnaires/{id}/` - Modifier
- **PATCH** `/api/quizzes/questionnaires/{id}/` - Modification partielle
- **DELETE** `/api/quizzes/questionnaires/{id}/` - Supprimer (avec vérifications)

### Actions Spéciales Questionnaires
- **GET** `/api/quizzes/questionnaires/{id}/statistiques/` - Statistiques détaillées
- **GET** `/api/quizzes/questionnaires/statistiques_globales/` - Stats générales
- **GET** `/api/quizzes/questionnaires/{id}/questions/` - Questions d'un questionnaire

### Questions
- **GET** `/api/quizzes/questions/` - Liste des questions avec filtres
- **POST** `/api/quizzes/questions/` - Créer une question
- **GET** `/api/quizzes/questions/{id}/` - Détail d'une question
- **PUT** `/api/quizzes/questions/{id}/` - Modifier une question
- **PATCH** `/api/quizzes/questions/{id}/` - Modification partielle
- **DELETE** `/api/quizzes/questions/{id}/` - Supprimer (avec vérifications)

### Structure Question/Réponse
```json
{
  "id": 1,
  "questionnaire": 1,
  "intitule": "Quelle est la différence entre une liste et un tuple ?",
  "reponses": [
    {
      "id": 1,
      "texte": "Les listes sont mutables, les tuples immutables",
      "est_correcte": true
    },
    {
      "id": 2,
      "texte": "Aucune différence",
      "est_correcte": false
    }
  ],
  "nombre_reponses": 4
}
```

---

## 🎯 Parcours de Quiz - `/api/parcours/`

### Pour les Stagiaires

#### Questionnaires Disponibles
- **GET** `/api/parcours/questionnaires-disponibles/`
- **Description** : Liste des questionnaires accessibles au stagiaire connecté
- **Auth** : Bearer Token (Stagiaire) requis
- **Response** :
  ```json
  [
    {
      "id": 1,
      "nom": "Quiz Python Débutant",
      "description": "Introduction à Python",
      "duree_minutes": 20,
      "nombre_questions": 10,
      "deja_realise": false
    }
  ]
  ```

#### Mes Parcours
- **GET** `/api/parcours/`
- **Description** : Liste de mes parcours (historique complet)
- **Auth** : Bearer Token (Stagiaire) requis
- **Filtres** : `?statut=TERMINE&ordering=-date_realisation`

#### Démarrer un Parcours
- **POST** `/api/parcours/`
- **Description** : Commencer un nouveau quiz
- **Auth** : Bearer Token (Stagiaire) requis
- **Body** :
  ```json
  {
    "questionnaire_id": 1
  }
  ```
- **Response** :
  ```json
  {
    "id": 15,
    "questionnaire": {
      "id": 1,
      "nom": "Quiz Python",
      "duree_minutes": 30
    },
    "statut": "EN_COURS",
    "date_realisation": "2024-01-15T14:30:00Z"
  }
  ```

#### Progression du Parcours
- **GET** `/api/parcours/{id}/`
  - **Description** : État actuel du parcours
  - **Response** : Statut, progression, temps écoulé

- **GET** `/api/parcours/{id}/question-courante/`
  - **Description** : Question actuelle à répondre
  - **Response** : Question avec ses réponses possibles

- **POST** `/api/parcours/{id}/repondre/`
  - **Description** : Répondre à la question courante
  - **Body** :
    ```json
    {
      "reponses_ids": [1, 3],
      "temps_reponse_sec": 45
    }
    ```

- **POST** `/api/parcours/{id}/terminer/`
  - **Description** : Terminer le quiz et calculer les résultats
  - **Body** :
    ```json
    {
      "temps_total_sec": 1200
    }
    ```

#### Résultats et Analyses
- **GET** `/api/parcours/{id}/resultats/`
  - **Description** : Résultats détaillés d'un parcours terminé
  - **Response** :
    ```json
    {
      "parcours": {
        "id": 15,
        "questionnaire": "Quiz Python",
        "statut": "TERMINE",
        "note_obtenue": 85.5,
        "note_sur_20": 17.1,
        "temps_passe_minutes": 25.5
      },
      "statistiques": {
        "questions_correctes": 12,
        "questions_partiellement_correctes": 2,
        "questions_incorrectes": 1,
        "taux_reussite": 80.0,
        "temps_moyen_par_question": 102.0
      },
      "reponses": [...]
    }
    ```

- **GET** `/api/parcours/{id}/resultats-detailles/`
  - **Description** : Analyse avancée avec recommandations personnalisées

- **GET** `/api/parcours/mes-recommandations/`
  - **Description** : Recommandations personnalisées basées sur l'historique

### Pour les Admins 🔒

#### Analytics Avancées
- **GET** `/api/parcours/stagiaire/{id}/synthese/`
  - **Description** : Synthèse complète d'un stagiaire
  - **Auth** : Bearer Token (Admin) requis

- **GET** `/api/parcours/questionnaire/{id}/statistiques-avancees/`
  - **Description** : Statistiques avancées d'un questionnaire
  - **Auth** : Bearer Token (Admin) requis

- **GET** `/api/parcours/rapports/synthese-globale/`
  - **Description** : Dashboard global de la plateforme
  - **Auth** : Bearer Token (Admin) requis

- **GET** `/api/parcours/rapports/questions-difficiles/`
  - **Description** : Analyse des questions problématiques
  - **Auth** : Bearer Token (Admin) requis

#### Export et Maintenance
- **GET** `/api/parcours/rapports/export/`
  - **Description** : Export CSV des données (parcours, notes, statistiques)
  - **Auth** : Bearer Token (Admin) requis
  - **Params** : `?format=csv&date_debut=2024-01-01&date_fin=2024-12-31`

- **POST** `/api/parcours/maintenance/recalculer-analyses/`
  - **Description** : Recalcul des analyses et statistiques
  - **Auth** : Bearer Token (Admin) requis

---

## 🗃️ Modèles de Données

### Utilisateur (User)
```json
{
  "id": 1,
  "email": "user@example.com",
  "nom": "Dupont",
  "prenom": "Jean",
  "login": "jdupont",
  "role": "STAGIAIRE|ADMIN",
  "is_active": true,
  "date_joined": "2024-01-15T10:00:00Z"
}
```

### Stagiaire (Profil étendu)
```json
{
  "user": {...},
  "societe": "TechCorp"
}
```

### Questionnaire
```json
{
  "id": 1,
  "nom": "Quiz Python Avancé",
  "description": "Test sur les concepts avancés",
  "date_creation": "2024-01-15T10:00:00Z",
  "duree_minutes": 30,
  "nombre_questions": 15
}
```

### Parcours
```json
{
  "id": 15,
  "stagiaire": 2,
  "questionnaire": 1,
  "date_realisation": "2024-01-15T14:30:00Z",
  "temps_passe_sec": 1530,
  "note_obtenue": 85.5,
  "note_sur_20": 17.1,
  "statut": "EN_COURS|TERMINE|ABANDONNE",
  "progression_pourcentage": 80.0,
  "niveau_performance": "Très bien"
}
```

### Système de Notation

#### Algorithme de Calcul
- **Choix unique** : Tout correct (1.0) ou tout faux (0.0)
- **Choix multiples** : Score partiel basé sur les bonnes réponses sélectionnées
- **Formule standard** : `bonnes_selections / total_reponses_correctes`
- **Avec pénalités** : `max(0, (bonnes - mauvaises) / total_correctes)`

#### Niveaux de Performance
- **Excellent** : ≥ 16/20
- **Très bien** : 14-16/20
- **Bien** : 12-14/20
- **Assez bien** : 10-12/20
- **Insuffisant** : < 10/20

---

## 📖 Documentation Interactive - `/api/schema/`

### Accès à la Documentation
- **GET** `/api/schema/` - Schema OpenAPI JSON
- **GET** `/api/schema/swagger-ui/` - Interface Swagger UI
- **GET** `/api/schema/redoc/` - Interface ReDoc

---

## 🔒 Authentification et Permissions

### Système de Rôles
- **ADMIN** : Accès complet (CRUD questionnaires, gestion utilisateurs, analytics)
- **STAGIAIRE** : Accès limité (quiz, profil personnel, historique personnel)

### Format des Tokens
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Durée de Vie
- **Access Token** : 1 heure
- **Refresh Token** : 7 jours (avec rotation automatique)

---

## 📱 Codes de Réponse HTTP

### Succès
- **200** - OK (données récupérées)
- **201** - Created (ressource créée)
- **204** - No Content (suppression réussie)

### Erreurs Client
- **400** - Bad Request (données invalides)
- **401** - Unauthorized (token manquant/invalide)
- **403** - Forbidden (permissions insuffisantes)
- **404** - Not Found (ressource inexistante)
- **409** - Conflict (contrainte métier violée)

### Erreurs Serveur
- **500** - Internal Server Error (erreur serveur)

---

## 🚀 Collection Postman

Importez le fichier `Quiz_Platform_Postman_Collection.json` pour tester tous les endpoints avec des exemples préconfigurés et des variables automatiques pour les tokens.

**Workflow recommandé :**
1. **Login** → Récupération des tokens
2. **Création de contenu** (Admin) → Questionnaires et questions
3. **Passage de quiz** (Stagiaire) → Parcours complet
4. **Analyse des résultats** → Statistiques et rapports

## 📊 Endpoints Supprimés

Les endpoints suivants ont été supprimés lors de l'optimisation :
- ❌ `POST /api/quizzes/questionnaires/{id}/ajouter_question/`
- ❌ `POST /api/quizzes/questionnaires/{id}/dupliquer/`
- ❌ `POST /api/quizzes/questions/{id}/dupliquer/`

**Raison** : Redondance avec les endpoints CRUD standards des questions.