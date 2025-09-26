# 🚀 Guide de Démarrage Rapide - Authentification

Guide pratique pour utiliser tous les endpoints d'authentification de Quiz Platform.

## 🎯 **Endpoints disponibles**

```
/api/auth/
├── login/                      # Connexion utilisateur
├── logout/                     # Déconnexion + blacklist token
├── token/refresh/              # Renouvellement token JWT
├── check-auth/                 # Vérification état authentification
├── change-password/            # Changement mot de passe
├── reset-password/             # Demande réinitialisation par email
└── reset-password-confirm/     # Confirmation réinitialisation avec token
```

---

## 🔐 **1. Authentification de base**

### **Connexion**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": "admin",
    "password": "admin123"
  }'
```

**Réponse :**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "nom": "Admin",
    "prenom": "Super",
    "email": "admin@example.com",
    "role": "ADMIN"
  }
}
```

### **Vérification d'authentification**
```bash
curl -X GET http://localhost:8000/api/auth/check-auth/ \
  -H "Authorization: Bearer <access_token>"
```

### **Renouvellement de token**
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### **Déconnexion**
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

---

## 🔑 **2. Gestion des mots de passe**

### **Changer son mot de passe (utilisateur connecté)**
```bash
curl -X POST http://localhost:8000/api/auth/change-password/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "ancien_mot_de_passe",
    "new_password": "nouveau_mot_de_passe_securise",
    "confirm_password": "nouveau_mot_de_passe_securise"
  }'
```

---

## 🔄 **3. Réinitialisation de mot de passe**

### **Méthode recommandée (Mode DEBUG)**

#### **Étape 1 : Demander la réinitialisation**
```bash
curl -X POST http://localhost:8000/api/auth/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

#### **Réponse avec debug_info :**
```json
{
  "message": "Email de réinitialisation envoyé avec succès",
  "reset_link": "http://localhost:3000/reset-password/MQ/abc123.../",
  "debug_info": {
    "uidb64": "MQ",
    "token": "abc123def456ghi789",
    "user_id": 1,
    "email": "user@example.com",
    "expires_in_hours": 24
  }
}
```

#### **Étape 2 : Confirmer avec les valeurs debug_info**
```bash
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "MQ",
    "token": "abc123def456ghi789",
    "new_password": "nouveau_mot_de_passe_securise",
    "confirm_password": "nouveau_mot_de_passe_securise"
  }'
```

---

## 📱 **4. Exemples avec JavaScript/Fetch**

### **Classe utilitaire d'authentification :**
```javascript
class AuthAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  async login(login, password) {
    const response = await fetch(`${this.baseURL}/api/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access;
      this.refreshToken = data.refresh;
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      return data;
    }
    throw new Error('Login failed');
  }

  async changePassword(oldPassword, newPassword) {
    const response = await fetch(`${this.baseURL}/api/auth/change-password/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.accessToken}`
      },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: newPassword
      })
    });

    return response.json();
  }

  async requestPasswordReset(email) {
    const response = await fetch(`${this.baseURL}/api/auth/reset-password/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    return response.json();
  }

  async confirmPasswordReset(uidb64, token, newPassword) {
    const response = await fetch(`${this.baseURL}/api/auth/reset-password-confirm/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uidb64,
        token,
        new_password: newPassword,
        confirm_password: newPassword
      })
    });

    return response.json();
  }

  async logout() {
    if (this.refreshToken) {
      await fetch(`${this.baseURL}/api/auth/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.accessToken}`
        },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.accessToken = null;
    this.refreshToken = null;
  }
}
```

### **Utilisation :**
```javascript
const auth = new AuthAPI();

// Connexion
try {
  const result = await auth.login('admin', 'admin123');
  console.log('Connecté:', result.user);
} catch (error) {
  console.error('Erreur de connexion:', error);
}

// Changer mot de passe
try {
  const result = await auth.changePassword('ancien_mdp', 'nouveau_mdp');
  console.log('Mot de passe changé:', result.message);
} catch (error) {
  console.error('Erreur changement mot de passe:', error);
}

// Réinitialisation
try {
  const resetData = await auth.requestPasswordReset('user@example.com');
  if (resetData.debug_info) {
    // En développement, utiliser debug_info
    await auth.confirmPasswordReset(
      resetData.debug_info.uidb64,
      resetData.debug_info.token,
      'nouveau_mot_de_passe'
    );
  }
} catch (error) {
  console.error('Erreur réinitialisation:', error);
}
```

---

## ✅ **5. Codes de réponse et gestion d'erreurs**

### **Codes de succès :**
- **200** - OK (login, change-password, etc.)
- **201** - Created (création réussie)
- **204** - No Content (logout)

### **Codes d'erreur courants :**
- **400** - Bad Request (données invalides)
- **401** - Unauthorized (token manquant/invalide)
- **404** - Not Found (utilisateur inexistant)

### **Exemples de gestion d'erreurs :**
```javascript
async function handleAuthRequest(requestFn) {
  try {
    const response = await requestFn();
    if (!response.ok) {
      const errorData = await response.json();

      switch (response.status) {
        case 400:
          console.error('Données invalides:', errorData);
          break;
        case 401:
          console.error('Non authentifié - token expiré?');
          // Rediriger vers login
          break;
        case 404:
          console.error('Utilisateur non trouvé');
          break;
        default:
          console.error('Erreur serveur:', errorData);
      }
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Erreur réseau:', error);
    return null;
  }
}
```

---

## 🔒 **6. Sécurité et bonnes pratiques**

### **Stockage des tokens :**
```javascript
// ✅ Recommandé - localStorage pour SPA simple
localStorage.setItem('access_token', token);

// ✅ Plus sécurisé - httpOnly cookies (nécessite config serveur)
// Les tokens sont automatiquement inclus dans les requêtes

// ❌ Éviter - variables globales JavaScript
window.accessToken = token; // Vulnérable aux attaques XSS
```

### **Gestion de l'expiration :**
```javascript
async function makeAuthenticatedRequest(url, options = {}) {
  let token = localStorage.getItem('access_token');

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    // Token expiré, essayer de le renouveler
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      const refreshResponse = await fetch('/api/auth/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken })
      });

      if (refreshResponse.ok) {
        const data = await refreshResponse.json();
        localStorage.setItem('access_token', data.access);

        // Réessayer la requête originale
        return fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${data.access}`
          }
        });
      }
    }

    // Rediriger vers login si refresh échoue
    window.location.href = '/login';
  }

  return response;
}
```

### **Validation côté client :**
```javascript
function validatePassword(password) {
  const errors = [];

  if (password.length < 8) {
    errors.push('Le mot de passe doit contenir au moins 8 caractères');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins une minuscule');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins une majuscule');
  }

  if (!/\d/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins un chiffre');
  }

  return errors;
}
```

---

## 🧪 **7. Tests et debugging**

### **Variables d'environnement recommandées :**
```bash
# .env.local pour le développement
DEBUG=True
SECRET_KEY=your-dev-secret-key
FRONTEND_URL=http://localhost:3000

# Pour tester les emails en développement
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### **Commandes utiles pour les tests :**
```bash
# Vérifier la configuration
python manage.py check

# Créer un utilisateur de test
python manage.py shell
>>> from users.models import User
>>> User.objects.create_user(login='test', email='test@test.com', password='test123', nom='Test', prenom='User', role='STAGIAIRE')

# Voir les logs en temps réel
tail -f logs/django.log
```

---

Ce guide couvre tous les aspects essentiels de l'authentification Quiz Platform. Pour plus de détails, consultez la documentation complète dans `docs/API_ENDPOINTS.md` ! 🚀