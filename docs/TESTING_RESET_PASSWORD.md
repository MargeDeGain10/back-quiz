# 🧪 Guide de Test - Réinitialisation de Mot de Passe

Guide complet pour tester les endpoints de réinitialisation de mot de passe en développement.

## 🎯 **Vue d'ensemble**

Le système de réinitialisation de mot de passe propose **3 méthodes de test** en développement :

1. **Mode DEBUG avec informations détaillées** (Recommandé)
2. **Endpoint de génération de token de test** (Le plus pratique)
3. **Génération manuelle de tokens** (Pour comprendre le processus)

---

## 🚀 **Méthode 1 : Mode DEBUG (Recommandé)**

### **Étape 1 : Demander une réinitialisation**

```bash
curl -X POST http://localhost:8000/api/auth/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### **Réponse en mode DEBUG :**

```json
{
  "message": "Email de réinitialisation envoyé avec succès",
  "reset_link": "http://localhost:3000/reset-password/MQ/abc123def456/",
  "debug_info": {
    "uidb64": "MQ",
    "token": "abc123def456ghi789jkl",
    "user_id": 1,
    "email": "user@example.com",
    "expires_in_hours": 24,
    "note": "Ces informations sont disponibles uniquement en mode DEBUG"
  }
}
```

### **Étape 2 : Utiliser les paramètres debug_info**

```bash
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "MQ",
    "token": "abc123def456ghi789jkl",
    "new_password": "nouveau_mot_de_passe_securise",
    "confirm_password": "nouveau_mot_de_passe_securise"
  }'
```

---

## ⚡ **Méthode 2 : Endpoint de Test (Le plus pratique)**

### **Étape 1 : Générer un token de test**

```bash
curl -X POST http://localhost:8000/api/auth/generate-test-reset-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### **Réponse de l'endpoint de test :**

```json
{
  "message": "Token de test généré avec succès",
  "user_info": {
    "id": 1,
    "email": "user@example.com",
    "nom": "Dupont",
    "prenom": "Jean",
    "is_active": true
  },
  "token_info": {
    "uidb64": "MQ",
    "token": "abc123def456ghi789",
    "expires_in_hours": 24
  },
  "test_payload": {
    "uidb64": "MQ",
    "token": "abc123def456ghi789",
    "new_password": "nouveau_mot_de_passe_123",
    "confirm_password": "nouveau_mot_de_passe_123"
  },
  "test_endpoint": "/api/auth/reset-password-confirm/",
  "instructions": "Copiez le test_payload et utilisez-le pour tester l'endpoint reset-password-confirm"
}
```

### **Étape 2 : Utiliser directement le test_payload**

```bash
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "MQ",
    "token": "abc123def456ghi789",
    "new_password": "nouveau_mot_de_passe_123",
    "confirm_password": "nouveau_mot_de_passe_123"
  }'
```

---

## 🔧 **Méthode 3 : Génération Manuelle (Avancée)**

### **Via Django Shell :**

```python
# Accéder au shell Django
python manage.py shell

# Dans le shell
from users.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

# Récupérer l'utilisateur
user = User.objects.get(email='user@example.com')

# Générer les tokens
token = default_token_generator.make_token(user)
uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

print(f"uidb64: {uidb64}")
print(f"token: {token}")
```

### **Ensuite utiliser les tokens générés :**

```bash
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "TOKENS_GENERÉS_CI_DESSUS",
    "token": "TOKENS_GENERÉS_CI_DESSUS",
    "new_password": "nouveau_mot_de_passe_securise",
    "confirm_password": "nouveau_mot_de_passe_securise"
  }'
```

---

## 🧪 **Scénarios de Test Complets**

### **Test 1 : Workflow complet réussi**

```bash
# 1. Créer un utilisateur de test (si nécessaire)
curl -X POST http://localhost:8000/api/stagiaires/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "nom": "Test",
    "prenom": "User",
    "login": "testuser",
    "societe": "Test Corp"
  }'

# 2. Générer un token de test
curl -X POST http://localhost:8000/api/auth/generate-test-reset-token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 3. Utiliser le token pour réinitialiser
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "COPIER_DEPUIS_REPONSE",
    "token": "COPIER_DEPUIS_REPONSE",
    "new_password": "nouveau_mot_de_passe_123",
    "confirm_password": "nouveau_mot_de_passe_123"
  }'

# 4. Tester la connexion avec le nouveau mot de passe
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": "testuser",
    "password": "nouveau_mot_de_passe_123"
  }'
```

### **Test 2 : Erreurs de validation**

```bash
# Test avec mots de passe non correspondants
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "MQ",
    "token": "token_valide",
    "new_password": "password123",
    "confirm_password": "password456"
  }'

# Réponse attendue : Erreur de validation
{
  "confirm_password": ["Les mots de passe ne correspondent pas."]
}
```

### **Test 3 : Token expiré/invalide**

```bash
# Test avec token invalide
curl -X POST http://localhost:8000/api/auth/reset-password-confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "uidb64": "MQ",
    "token": "token_invalide_ou_expire",
    "new_password": "password123",
    "confirm_password": "password123"
  }'

# Réponse attendue : Erreur de token
{
  "non_field_errors": ["Token de réinitialisation expiré ou invalide."]
}
```

---

## ⚙️ **Configuration requise**

### **Settings Django :**

```python
# settings.py
DEBUG = True  # OBLIGATOIRE pour les fonctions de test

FRONTEND_URL = 'http://localhost:3000'  # URL de votre frontend

# Token de réinitialisation valide 24h par défaut
```

### **Vérifier la configuration :**

```bash
# Vérifier que DEBUG est activé
curl http://localhost:8000/api/auth/generate-test-reset-token/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com"}'

# Si DEBUG=False, vous obtiendrez :
{
  "error": "Cet endpoint n'est disponible qu'en mode DEBUG"
}
```

---

## 📱 **Test avec Postman**

### **Collection Postman mise à jour :**

1. **Import** la collection `Quiz_Platform_Postman_Collection.json`

2. **Nouvelles requêtes ajoutées :**
   - `Auth/Generate Test Reset Token`
   - `Auth/Reset Password Confirm`
   - `Auth/Reset Password (with DEBUG info)`

3. **Variables automatiques :**
   - `{{reset_uidb64}}` - Extrait automatiquement de la réponse
   - `{{reset_token}}` - Extrait automatiquement de la réponse

4. **Workflow Postman :**
   - Exécuter "Generate Test Reset Token"
   - Les variables sont automatiquement définies
   - Exécuter "Reset Password Confirm" (utilise les variables)

---

## 🎯 **Conseils de Test**

### **Bonnes pratiques :**

1. **Toujours tester en mode DEBUG** pour avoir toutes les informations
2. **Créer des utilisateurs de test dédiés** pour éviter d'affecter les vraies données
3. **Vérifier les contraintes de mot de passe** (minimum 8 caractères, etc.)
4. **Tester les cas d'erreur** autant que les cas de succès
5. **Vérifier l'expiration des tokens** (24h)

### **Utilisateurs de test recommandés :**

```json
{
  "email": "test-reset@example.com",
  "login": "test-reset",
  "nom": "Test",
  "prenom": "Reset",
  "password": "initial-password-123"
}
```

### **Debugging :**

```bash
# Vérifier si l'utilisateur existe
curl -X POST http://localhost:8000/api/auth/generate-test-reset-token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "email_a_tester@example.com"}'

# Vérifier l'état du token
# (Les tokens sont valides 24h, utilisez toujours un token frais)
```

---

## 🚨 **Sécurité - Important**

### **⚠️ En production (DEBUG=False) :**

- L'endpoint `generate-test-reset-token` **n'est pas accessible**
- Les `debug_info` **ne sont pas incluses** dans les réponses
- Les emails de réinitialisation sont **réellement envoyés**
- Aucune information utilisateur n'est **révélée**

### **✅ En développement (DEBUG=True) :**

- Toutes les fonctions de test sont **disponibles**
- Les informations de debug sont **incluses**
- Les liens de réinitialisation sont **affichés directement**
- L'endpoint de test est **actif**

---

Cette configuration vous donne **maximum de flexibilité** pour tester la réinitialisation de mot de passe selon vos besoins ! 🎉