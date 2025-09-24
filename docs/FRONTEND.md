# 🎨 Guide d'intégration Frontend Vue.js

Ce guide vous explique comment intégrer votre application Vue.js avec l'API Quiz Platform.

## 🔐 Configuration de l'authentification JWT

### Installation des dépendances

```bash
npm install axios @vueuse/core pinia
```

### Configuration Axios avec intercepteurs

Créez un fichier `src/utils/api.js` :

```javascript
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// Configuration de base
const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Intercepteur pour gérer le refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await authStore.refreshToken()
        originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        authStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api
```

### Store d'authentification avec Pinia

Créez `src/stores/auth.js` :

```javascript
import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('accessToken'),
    refreshToken: localStorage.getItem('refreshToken'),
    isLoading: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    isAdmin: (state) => state.user?.role === 'ADMIN',
    isStagiaire: (state) => state.user?.role === 'STAGIAIRE'
  },

  actions: {
    async login(credentials) {
      this.isLoading = true
      try {
        const response = await api.post('/users/login/', credentials)
        const { access, refresh, user } = response.data

        this.accessToken = access
        this.refreshToken = refresh
        this.user = user

        localStorage.setItem('accessToken', access)
        localStorage.setItem('refreshToken', refresh)

        return { success: true, user }
      } catch (error) {
        console.error('Erreur de connexion:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Erreur de connexion'
        }
      } finally {
        this.isLoading = false
      }
    },

    async register(userData) {
      this.isLoading = true
      try {
        await api.post('/users/register/', userData)
        return { success: true }
      } catch (error) {
        return {
          success: false,
          errors: error.response?.data || { general: 'Erreur d\'inscription' }
        }
      } finally {
        this.isLoading = false
      }
    },

    async refreshToken() {
      if (!this.refreshToken) {
        throw new Error('Pas de refresh token disponible')
      }

      try {
        const response = await api.post('/auth/jwt/refresh/', {
          refresh: this.refreshToken
        })

        this.accessToken = response.data.access
        localStorage.setItem('accessToken', response.data.access)

        return response.data.access
      } catch (error) {
        this.logout()
        throw error
      }
    },

    async fetchUser() {
      if (!this.accessToken) return

      try {
        const response = await api.get('/users/me/')
        this.user = response.data
      } catch (error) {
        console.error('Erreur lors de la récupération du profil:', error)
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    }
  }
})
```

## 📝 Services pour les questionnaires

Créez `src/services/quizService.js` :

```javascript
import api from '@/utils/api'

export const quizService = {
  // Récupérer tous les questionnaires
  async getQuestionnaires(params = {}) {
    const response = await api.get('/quizzes/questionnaires/', { params })
    return response.data
  },

  // Récupérer un questionnaire spécifique
  async getQuestionnaire(id) {
    const response = await api.get(`/quizzes/questionnaires/${id}/`)
    return response.data
  },

  // Créer un questionnaire (admin uniquement)
  async createQuestionnaire(data) {
    const response = await api.post('/quizzes/questionnaires/', data)
    return response.data
  },

  // Récupérer les questions d'un questionnaire
  async getQuestions(questionnaireId) {
    const response = await api.get(`/quizzes/questionnaires/${questionnaireId}/questions/`)
    return response.data
  },

  // Commencer un parcours
  async startParcours(questionnaireId) {
    const response = await api.post('/responses/parcours/', {
      questionnaire: questionnaireId
    })
    return response.data
  },

  // Récupérer un parcours
  async getParcours(id) {
    const response = await api.get(`/responses/parcours/${id}/`)
    return response.data
  },

  // Soumettre une réponse
  async submitAnswer(parcoursId, questionId, reponseIds) {
    const response = await api.post('/responses/reponses-utilisateur/', {
      parcours: parcoursId,
      question: questionId,
      reponses_selectionnees: reponseIds
    })
    return response.data
  },

  // Finaliser un parcours
  async finalizeParcours(parcoursId) {
    const response = await api.post(`/responses/parcours/${parcoursId}/finaliser/`)
    return response.data
  },

  // Récupérer les résultats
  async getResults(parcoursId) {
    const response = await api.get(`/responses/parcours/${parcoursId}/resultats/`)
    return response.data
  }
}
```

## 🎯 Composants Vue.js d'exemple

### Composant de connexion

```vue
<template>
  <div class="login-form">
    <h2>Connexion</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="email">Email :</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          required
          :disabled="authStore.isLoading"
        />
      </div>

      <div class="form-group">
        <label for="password">Mot de passe :</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          required
          :disabled="authStore.isLoading"
        />
      </div>

      <button
        type="submit"
        :disabled="authStore.isLoading"
        class="btn btn-primary"
      >
        {{ authStore.isLoading ? 'Connexion...' : 'Se connecter' }}
      </button>

      <div v-if="error" class="error">
        {{ error }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})

const error = ref('')

const handleLogin = async () => {
  error.value = ''

  const result = await authStore.login(form.value)

  if (result.success) {
    const redirectTo = result.user.role === 'ADMIN' ? '/admin/dashboard' : '/questionnaires'
    router.push(redirectTo)
  } else {
    error.value = result.error
  }
}
</script>
```

### Composant liste des questionnaires

```vue
<template>
  <div class="questionnaires-list">
    <h2>Questionnaires disponibles</h2>

    <div v-if="loading" class="loading">
      Chargement des questionnaires...
    </div>

    <div v-else-if="questionnaires.length === 0" class="empty">
      Aucun questionnaire disponible.
    </div>

    <div v-else class="questionnaires-grid">
      <div
        v-for="questionnaire in questionnaires"
        :key="questionnaire.id"
        class="questionnaire-card"
      >
        <h3>{{ questionnaire.nom }}</h3>
        <p>{{ questionnaire.description }}</p>

        <div class="questionnaire-meta">
          <span class="duration">⏱️ {{ questionnaire.duree_minutes }} min</span>
          <span class="questions">📝 {{ questionnaire.nombre_questions }} questions</span>
        </div>

        <button
          @click="startQuestionnaire(questionnaire.id)"
          class="btn btn-primary"
          :disabled="startingQuiz === questionnaire.id"
        >
          {{ startingQuiz === questionnaire.id ? 'Démarrage...' : 'Commencer' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { quizService } from '@/services/quizService'

const router = useRouter()

const questionnaires = ref([])
const loading = ref(true)
const startingQuiz = ref(null)

const loadQuestionnaires = async () => {
  try {
    const response = await quizService.getQuestionnaires()
    questionnaires.value = response.results || response
  } catch (error) {
    console.error('Erreur lors du chargement des questionnaires:', error)
  } finally {
    loading.value = false
  }
}

const startQuestionnaire = async (questionnaireId) => {
  startingQuiz.value = questionnaireId

  try {
    const parcours = await quizService.startParcours(questionnaireId)
    router.push(`/quiz/${parcours.id}`)
  } catch (error) {
    console.error('Erreur lors du démarrage du questionnaire:', error)
    alert('Erreur lors du démarrage du questionnaire')
  } finally {
    startingQuiz.value = null
  }
}

onMounted(() => {
  loadQuestionnaires()
})
</script>
```

### Composant de passage de quiz

```vue
<template>
  <div class="quiz-container">
    <div v-if="loading" class="loading">
      Chargement du questionnaire...
    </div>

    <div v-else-if="parcours && currentQuestion" class="quiz-content">
      <!-- Header avec progression -->
      <div class="quiz-header">
        <h2>{{ parcours.questionnaire.nom }}</h2>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: `${progressPercentage}%` }"
          ></div>
        </div>
        <span class="progress-text">
          Question {{ currentQuestionIndex + 1 }} sur {{ questions.length }}
        </span>
      </div>

      <!-- Question actuelle -->
      <div class="question-container">
        <h3>{{ currentQuestion.intitule }}</h3>

        <div class="answers">
          <label
            v-for="reponse in currentQuestion.reponses"
            :key="reponse.id"
            class="answer-option"
          >
            <input
              v-if="isMultipleChoice"
              v-model="selectedAnswers"
              type="checkbox"
              :value="reponse.id"
            />
            <input
              v-else
              v-model="selectedAnswers"
              type="radio"
              :value="[reponse.id]"
            />
            <span>{{ reponse.texte }}</span>
          </label>
        </div>
      </div>

      <!-- Controls -->
      <div class="quiz-controls">
        <button
          @click="previousQuestion"
          :disabled="currentQuestionIndex === 0"
          class="btn btn-secondary"
        >
          Précédent
        </button>

        <button
          v-if="currentQuestionIndex < questions.length - 1"
          @click="nextQuestion"
          :disabled="!selectedAnswers.length"
          class="btn btn-primary"
        >
          Suivant
        </button>

        <button
          v-else
          @click="finishQuiz"
          :disabled="!selectedAnswers.length || finishing"
          class="btn btn-success"
        >
          {{ finishing ? 'Finalisation...' : 'Terminer' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { quizService } from '@/services/quizService'

const route = useRoute()
const router = useRouter()

const parcours = ref(null)
const questions = ref([])
const currentQuestionIndex = ref(0)
const answers = ref({})
const loading = ref(true)
const finishing = ref(false)

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])
const selectedAnswers = computed({
  get: () => answers.value[currentQuestion.value?.id] || [],
  set: (value) => {
    if (currentQuestion.value) {
      answers.value[currentQuestion.value.id] = Array.isArray(value) ? value : [value]
    }
  }
})

const isMultipleChoice = computed(() => {
  if (!currentQuestion.value) return false
  return currentQuestion.value.reponses.filter(r => r.est_correcte).length > 1
})

const progressPercentage = computed(() => {
  return ((currentQuestionIndex.value + 1) / questions.value.length) * 100
})

const loadQuiz = async () => {
  try {
    const parcoursData = await quizService.getParcours(route.params.id)
    parcours.value = parcoursData

    const questionsData = await quizService.getQuestions(parcoursData.questionnaire.id)
    questions.value = questionsData
  } catch (error) {
    console.error('Erreur lors du chargement du quiz:', error)
    router.push('/questionnaires')
  } finally {
    loading.value = false
  }
}

const nextQuestion = async () => {
  await submitCurrentAnswer()
  if (currentQuestionIndex.value < questions.value.length - 1) {
    currentQuestionIndex.value++
  }
}

const previousQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
  }
}

const submitCurrentAnswer = async () => {
  if (!selectedAnswers.value.length) return

  try {
    await quizService.submitAnswer(
      parcours.value.id,
      currentQuestion.value.id,
      selectedAnswers.value
    )
  } catch (error) {
    console.error('Erreur lors de la soumission de la réponse:', error)
  }
}

const finishQuiz = async () => {
  finishing.value = true

  try {
    await submitCurrentAnswer()
    await quizService.finalizeParcours(parcours.value.id)
    router.push(`/results/${parcours.value.id}`)
  } catch (error) {
    console.error('Erreur lors de la finalisation:', error)
    alert('Erreur lors de la finalisation du questionnaire')
  } finally {
    finishing.value = false
  }
}

onMounted(() => {
  loadQuiz()
})
</script>
```

## 🛡️ Guard de route pour l'authentification

Créez `src/router/guards.js` :

```javascript
import { useAuthStore } from '@/stores/auth'

export const authGuard = (to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
}

export const adminGuard = (to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.isAuthenticated) {
    next('/login')
  } else if (!authStore.isAdmin) {
    next('/questionnaires')
  } else {
    next()
  }
}
```

## 🎨 Configuration des routes

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { authGuard, adminGuard } from './guards'

const routes = [
  {
    path: '/',
    redirect: '/questionnaires'
  },
  {
    path: '/login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/questionnaires',
    component: () => import('@/views/Questionnaires.vue'),
    beforeEnter: authGuard
  },
  {
    path: '/quiz/:id',
    component: () => import('@/views/Quiz.vue'),
    beforeEnter: authGuard
  },
  {
    path: '/results/:id',
    component: () => import('@/views/Results.vue'),
    beforeEnter: authGuard
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/Dashboard.vue'),
    beforeEnter: adminGuard
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

## 📱 Variables d'environnement Frontend

Créez `.env.local` dans votre projet Vue.js :

```env
VUE_APP_API_URL=http://localhost:8000/api
VUE_APP_REFRESH_TOKEN_INTERVAL=55000
VUE_APP_DEBUG=true
```

Pour la production :

```env
VUE_APP_API_URL=https://votre-api.com/api
VUE_APP_REFRESH_TOKEN_INTERVAL=55000
VUE_APP_DEBUG=false
```

## ⚡ Optimisations et bonnes pratiques

### Gestion des erreurs globale

```javascript
// src/utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response?.status === 401) {
    // Redirection vers login
    window.location.href = '/login'
  } else if (error.response?.status >= 500) {
    // Erreur serveur
    console.error('Erreur serveur:', error)
    return 'Erreur serveur. Veuillez réessayer plus tard.'
  } else if (error.response?.data?.detail) {
    return error.response.data.detail
  } else {
    return 'Une erreur est survenue'
  }
}
```

### Composable pour les questionnaires

```javascript
// src/composables/useQuiz.js
import { ref } from 'vue'
import { quizService } from '@/services/quizService'

export function useQuiz() {
  const questionnaires = ref([])
  const loading = ref(false)
  const error = ref(null)

  const loadQuestionnaires = async () => {
    loading.value = true
    error.value = null

    try {
      const data = await quizService.getQuestionnaires()
      questionnaires.value = data.results || data
    } catch (err) {
      error.value = 'Erreur lors du chargement des questionnaires'
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  return {
    questionnaires,
    loading,
    error,
    loadQuestionnaires
  }
}
```

## 🔧 Configuration de build pour production

Dans `vue.config.js` :

```javascript
module.exports = {
  publicPath: process.env.NODE_ENV === 'production' ? '/quiz-app/' : '/',

  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },

  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    }
  }
}
```

---

Ce guide vous donne tous les éléments nécessaires pour intégrer votre frontend Vue.js avec l'API Quiz Platform. Les exemples incluent la gestion complète de l'authentification JWT, les appels API et les composants prêts à l'emploi.