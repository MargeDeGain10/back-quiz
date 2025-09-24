# 📚 Documentation API

Documentation complète de l'API REST Quiz Platform.

## 🔗 URLs de base

- **API Base URL** : `http://localhost:8000/api/`
- **Swagger UI** : `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc** : `http://localhost:8000/api/schema/redoc/`
- **Schema OpenAPI** : `http://localhost:8000/api/schema/`

## 🔐 Authentification

L'API utilise l'authentification JWT (JSON Web Token).

### Obtenir un token

**POST** `/api/users/login/`

```json
{
  "email": "user@example.com",
  "password": "motdepasse"
}
```

**Réponse** :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "nom": "Dupont",
    "prenom": "Jean",
    "role": "STAGIAIRE"
  }
}
```

### Utiliser le token

Inclure dans les headers de toutes les requêtes authentifiées :

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Rafraîchir le token

**POST** `/api/auth/jwt/refresh/`

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 👥 Gestion des utilisateurs

### Inscription

**POST** `/api/users/register/`

```json
{
  "email": "nouveau@example.com",
  "password": "motdepasse123",
  "nom": "Martin",
  "prenom": "Paul",
  "login": "pmartin",
  "role": "STAGIAIRE"
}
```

**Réponse** : `201 Created`
```json
{
  "id": 2,
  "email": "nouveau@example.com",
  "nom": "Martin",
  "prenom": "Paul",
  "login": "pmartin",
  "role": "STAGIAIRE",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

### Profil utilisateur

**GET** `/api/users/me/`

**Réponse** :
```json
{
  "id": 1,
  "email": "user@example.com",
  "nom": "Dupont",
  "prenom": "Jean",
  "login": "jdupont",
  "role": "STAGIAIRE",
  "date_joined": "2024-01-10T08:00:00Z",
  "stagiaire_profile": {
    "societe": "Tech Corp"
  }
}
```

### Mise à jour du profil

**PATCH** `/api/users/me/`

```json
{
  "nom": "Nouveau Nom",
  "stagiaire_profile": {
    "societe": "Nouvelle Société"
  }
}
```

### Liste des utilisateurs (Admin uniquement)

**GET** `/api/users/`

**Paramètres de requête** :
- `role` : Filtrer par rôle (`ADMIN`, `STAGIAIRE`)
- `search` : Recherche par nom, prénom ou email
- `ordering` : Tri (`date_joined`, `-date_joined`, `nom`, etc.)

**Réponse** :
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "admin@example.com",
      "nom": "Admin",
      "prenom": "Super",
      "role": "ADMIN",
      "date_joined": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## 📝 Questionnaires

### Liste des questionnaires

**GET** `/api/quizzes/questionnaires/`

**Paramètres de requête** :
- `search` : Recherche dans le nom et description
- `duree_min` : Durée minimale en minutes
- `duree_max` : Durée maximale en minutes
- `ordering` : Tri par `nom`, `date_creation`, `duree_minutes`

**Réponse** :
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "nom": "JavaScript Fundamentals",
      "description": "Test des bases de JavaScript",
      "duree_minutes": 30,
      "nombre_questions": 15,
      "date_creation": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### Détail d'un questionnaire

**GET** `/api/quizzes/questionnaires/{id}/`

**Réponse** :
```json
{
  "id": 1,
  "nom": "JavaScript Fundamentals",
  "description": "Test des bases de JavaScript",
  "duree_minutes": 30,
  "nombre_questions": 15,
  "date_creation": "2024-01-01T10:00:00Z",
  "questions": [
    {
      "id": 1,
      "intitule": "Qu'est-ce que JavaScript?",
      "reponses": [
        {
          "id": 1,
          "texte": "Un langage de programmation",
          "est_correcte": true
        },
        {
          "id": 2,
          "texte": "Un framework CSS",
          "est_correcte": false
        }
      ]
    }
  ]
}
```

### Créer un questionnaire (Admin uniquement)

**POST** `/api/quizzes/questionnaires/`

```json
{
  "nom": "Python Basics",
  "description": "Introduction à Python",
  "duree_minutes": 45
}
```

### Questions d'un questionnaire

**GET** `/api/quizzes/questionnaires/{id}/questions/`

**Réponse** :
```json
[
  {
    "id": 1,
    "intitule": "Qu'est-ce qu'une variable en Python?",
    "reponses": [
      {
        "id": 1,
        "texte": "Un conteneur pour stocker des données",
        "est_correcte": true
      }
    ]
  }
]
```

### Créer une question (Admin uniquement)

**POST** `/api/quizzes/questions/`

```json
{
  "questionnaire": 1,
  "intitule": "Quelle est la syntaxe pour déclarer une fonction en Python?",
  "reponses": [
    {
      "texte": "def ma_fonction():",
      "est_correcte": true
    },
    {
      "texte": "function ma_fonction():",
      "est_correcte": false
    }
  ]
}
```

## 🎯 Passage de questionnaires

### Commencer un parcours

**POST** `/api/responses/parcours/`

```json
{
  "questionnaire": 1
}
```

**Réponse** :
```json
{
  "id": 10,
  "questionnaire": {
    "id": 1,
    "nom": "JavaScript Fundamentals",
    "duree_minutes": 30
  },
  "stagiaire": {
    "user": {
      "nom": "Dupont",
      "prenom": "Jean"
    }
  },
  "statut": "EN_COURS",
  "date_realisation": "2024-01-15T14:00:00Z",
  "temps_passe_sec": 0,
  "progression_pourcentage": 0.0
}
```

### Détail d'un parcours

**GET** `/api/responses/parcours/{id}/`

**Réponse** :
```json
{
  "id": 10,
  "questionnaire": {
    "id": 1,
    "nom": "JavaScript Fundamentals",
    "nombre_questions": 15
  },
  "statut": "EN_COURS",
  "temps_passe_sec": 450,
  "progression_pourcentage": 66.7,
  "note_obtenue": null,
  "niveau_performance": "Non évalué"
}
```

### Soumettre une réponse

**POST** `/api/responses/reponses-utilisateur/`

```json
{
  "parcours": 10,
  "question": 1,
  "reponses_selectionnees": [1, 3],
  "temps_reponse_sec": 45
}
```

**Réponse** :
```json
{
  "id": 25,
  "question": {
    "id": 1,
    "intitule": "Qu'est-ce que JavaScript?"
  },
  "reponses_selectionnees": [1, 3],
  "temps_reponse_sec": 45,
  "est_correcte": true,
  "score_obtenu": "1.00",
  "efficacite_temporelle": 1.33
}
```

### Finaliser un parcours

**POST** `/api/responses/parcours/{id}/finaliser/`

```json
{
  "temps_total_sec": 1800,
  "avec_penalites": false
}
```

**Réponse** :
```json
{
  "id": 10,
  "statut": "TERMINE",
  "note_obtenue": "85.50",
  "note_sur_20": "17.10",
  "temps_passe_sec": 1800,
  "niveau_performance": "Excellent",
  "recommandations": [
    "Excellent travail ! Continuez sur cette voie"
  ]
}
```

### Résultats détaillés

**GET** `/api/responses/parcours/{id}/resultats/`

**Réponse** :
```json
{
  "parcours": {
    "id": 10,
    "note_obtenue": "85.50",
    "note_sur_20": "17.10",
    "temps_passe_minutes": 30.0,
    "niveau_performance": "Excellent"
  },
  "statistiques": {
    "questions_correctes": 12,
    "questions_partiellement_correctes": 2,
    "questions_incorrectes": 1,
    "taux_reussite": 80.0,
    "temps_moyen_par_question": 120.0,
    "efficacite_temporelle": 0.71
  },
  "details_reponses": [
    {
      "question": {
        "id": 1,
        "intitule": "Qu'est-ce que JavaScript?"
      },
      "reponses_selectionnees": [
        {
          "id": 1,
          "texte": "Un langage de programmation",
          "est_correcte": true
        }
      ],
      "est_correcte": true,
      "score_obtenu": "1.00",
      "temps_reponse_sec": 45
    }
  ],
  "recommandations": [
    "Excellent travail ! Continuez sur cette voie"
  ]
}
```

## 📊 Analytics et statistiques

### Dashboard admin

**GET** `/api/responses/dashboard/` (Admin uniquement)

**Réponse** :
```json
{
  "stats_globales": {
    "nombre_stagiaires": 25,
    "nombre_questionnaires": 8,
    "nombre_parcours_termines": 120,
    "taux_completion_moyen": 85.5,
    "note_moyenne_globale": 14.2
  },
  "questionnaires_populaires": [
    {
      "questionnaire": "JavaScript Fundamentals",
      "nombre_passages": 45,
      "note_moyenne": 16.8
    }
  ],
  "performances_recentes": [
    {
      "stagiaire": "Jean Dupont",
      "questionnaire": "Python Basics",
      "note": 18.5,
      "date": "2024-01-15T14:00:00Z"
    }
  ]
}
```

### Statistiques d'un stagiaire

**GET** `/api/responses/stagiaires/{id}/statistiques/`

**Réponse** :
```json
{
  "stagiaire": {
    "nom": "Dupont",
    "prenom": "Jean",
    "societe": "Tech Corp"
  },
  "statistiques": {
    "nombre_questionnaires_termines": 5,
    "note_moyenne": 15.8,
    "note_moyenne_sur_20": 15.8,
    "temps_total_formation_heures": 3.5,
    "niveau_global": "Avancé"
  },
  "parcours": [
    {
      "questionnaire": "JavaScript Fundamentals",
      "note_obtenue": 17.5,
      "date_realisation": "2024-01-15T14:00:00Z",
      "temps_passe_minutes": 28
    }
  ],
  "domaines_amelioration": [
    {
      "questionnaire": "CSS Advanced",
      "note": 9.5,
      "recommandations": [
        "Revoir les concepts de base avant de retenter"
      ]
    }
  ]
}
```

### Analyses d'un questionnaire

**GET** `/api/responses/questionnaires/{id}/analyses/`

**Réponse** :
```json
{
  "questionnaire": {
    "nom": "JavaScript Fundamentals",
    "nombre_questions": 15
  },
  "statistiques": {
    "nombre_passages": 45,
    "note_moyenne": 16.8,
    "note_mediane": 17.0,
    "temps_moyen_completion_minutes": 28.5,
    "taux_abandon": 5.5,
    "niveau_difficulte_global": "Moyen"
  },
  "questions_difficiles": [
    {
      "question": {
        "intitule": "Expliquez les closures en JavaScript"
      },
      "taux_reussite": 35.0,
      "niveau_difficulte": "Très difficile"
    }
  ],
  "distribution_notes": {
    "0-5": 2,
    "6-10": 5,
    "11-15": 15,
    "16-20": 23
  }
}
```

## 🔍 Filtrage et recherche

### Paramètres communs

Tous les endpoints de liste supportent ces paramètres :

- **page** : Numéro de page (pagination)
- **page_size** : Taille de page (max 100)
- **ordering** : Tri (préfixer par `-` pour l'ordre décroissant)
- **search** : Recherche textuelle

### Exemples de filtrage

```bash
# Questionnaires créés cette semaine
GET /api/quizzes/questionnaires/?date_creation__gte=2024-01-10

# Parcours terminés par un stagiaire
GET /api/responses/parcours/?stagiaire=5&statut=TERMINE

# Recherche d'utilisateurs
GET /api/users/?search=jean&role=STAGIAIRE

# Tri par note décroissante
GET /api/responses/parcours/?ordering=-note_obtenue
```

## ⚠️ Gestion des erreurs

### Codes de réponse HTTP

- **200** : Succès
- **201** : Créé avec succès
- **400** : Données invalides
- **401** : Non authentifié
- **403** : Accès refusé
- **404** : Ressource non trouvée
- **429** : Trop de requêtes
- **500** : Erreur serveur

### Format des erreurs

```json
{
  "detail": "Message d'erreur principal",
  "errors": {
    "field_name": ["Message d'erreur spécifique au champ"]
  },
  "code": "error_code"
}
```

### Exemples d'erreurs

#### Validation de données
```json
{
  "detail": "Données invalides",
  "errors": {
    "email": ["Cette adresse email existe déjà"],
    "password": ["Le mot de passe doit contenir au moins 8 caractères"]
  }
}
```

#### Authentification
```json
{
  "detail": "Token invalide ou expiré",
  "code": "token_not_valid"
}
```

#### Permissions
```json
{
  "detail": "Vous n'avez pas la permission d'effectuer cette action",
  "code": "permission_denied"
}
```

## 🚀 Limites et quotas

### Rate limiting

- **Connexion** : 5 tentatives par minute par IP
- **API générale** : 100 requêtes par minute par utilisateur
- **Upload de fichiers** : 10 requêtes par minute

### Pagination

- **Taille par défaut** : 20 éléments
- **Taille maximale** : 100 éléments

### Réponses

Format de pagination standard :
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

## 💡 Conseils d'utilisation

### Performance

1. **Utilisez la pagination** pour les listes importantes
2. **Filtrez côté serveur** plutôt que côté client
3. **Mettez en cache** les données statiques (questionnaires)
4. **Préchargez** les relations avec `select_related`

### Sécurité

1. **Stockez les tokens** de manière sécurisée
2. **Implémentez le refresh** automatique des tokens
3. **Validez toujours** les données côté client ET serveur
4. **Loggez** les actions sensibles

### Intégration

1. **Testez avec Swagger UI** avant l'intégration
2. **Utilisez des outils** comme Postman pour les tests
3. **Implementez une gestion d'erreur** robuste
4. **Documentez** vos intégrations spécifiques

---

Cette documentation couvre tous les endpoints disponibles. Pour des exemples d'intégration complets, consultez le guide Frontend Vue.js.