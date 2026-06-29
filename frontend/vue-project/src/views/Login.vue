<template>
  <div class="bg-gray-100 dark:bg-slate-900 text-slate-800 dark:text-slate-100 transition-colors duration-300 min-h-screen font-sans">
    <div class="flex min-h-screen w-full">
      <!-- Left Panel - Branding (Hidden on mobile) -->
      <div class="hidden lg:flex w-1/2 bg-gradient-to-br from-[#6366f1] via-[#4f46e5] to-[#3b82f6] relative flex-col items-center justify-center p-12 overflow-hidden">
        <!-- Decorative Blurs -->
        <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-white opacity-10 rounded-full blur-3xl"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-500 opacity-20 rounded-full blur-3xl"></div>
        
        <div class="relative z-10 text-center">
          <h1 class="text-6xl font-extrabold text-white tracking-tight mb-4">SIMIC</h1>
          <p class="text-indigo-100 text-xl max-w-sm mx-auto">
            Crea simulacros y haz seguimiento a tus estudiantes.
          </p>
        </div>
        
        <div class="absolute bottom-12 z-10 text-indigo-200/80 text-sm text-center">
          © {{ currentYear }} SIMIC — Hecho con el ❤️ por un educador.
        </div>
      </div>
      
      <!-- Right Panel - Login Form -->
      <div class="w-full lg:w-1/2 flex items-center justify-center p-0 sm:p-8 lg:p-12 relative">
        <!-- Dark Mode Toggle -->
        <button
          @click="toggleDarkMode"
          class="absolute top-6 right-6 p-2 rounded-full bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors"
        >
          <span class="material-icons-round text-xl" v-if="!isDark">dark_mode</span>
          <span class="material-icons-round text-xl" v-else>light_mode</span>
        </button>
        
        <!-- Login Card -->
        <!-- Login Card -->
        <div class="w-full max-w-[440px] bg-white dark:bg-slate-800 min-h-screen sm:min-h-fit flex flex-col justify-center sm:block sm:rounded-2xl sm:shadow-xl dark:shadow-slate-900/50 p-8 sm:p-10 sm:border border-gray-100 dark:border-slate-700">
          <!-- Mobile Logo -->
          <div class="lg:hidden flex justify-center mb-8">
            <div class="w-12 h-12 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30 overflow-hidden">
              <img src="@/assets/logo.png" alt="SIMIC Logo" class="w-10 h-10 object-contain" />
            </div>
          </div>
          
          <!-- Header -->
          <div class="mb-8 text-center lg:text-left">
            <h2 class="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              {{ institutionName ? `Bienvenido a ${institutionName}` : 'Bienvenido' }}
            </h2>
            <p class="text-slate-500 dark:text-slate-400">
              {{ institutionName ? 'Ingresa tus credenciales para continuar.' : 'Plataforma de simulacros ICFES.' }}
            </p>
            <div v-if="setupSuccess" class="mt-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <p class="text-green-600 dark:text-green-400 text-sm">Configuración completada. Ahora puedes iniciar sesión.</p>
            </div>
          </div>
          
          <!-- Form -->
          <form @submit.prevent="handleLogin" class="space-y-6">
            <!-- Email Field -->
            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300" for="email">
                Correo Electrónico
              </label>
              <div class="relative group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span class="material-icons-round text-slate-400 group-focus-within:text-primary transition-colors text-xl">
                    mail_outline
                  </span>
                </div>
                <input
                  v-model="email"
                  type="email"
                  id="email"
                  placeholder="usuario@institucion.edu.co"
                  required
                  class="block w-full pl-10 pr-3 py-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all shadow-sm"
                />
              </div>
            </div>
            
            <!-- Password Field -->
            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300" for="password">
                Contraseña
              </label>
              <div class="relative group">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <span class="material-icons-round text-slate-400 group-focus-within:text-primary transition-colors text-xl">
                    lock_outline
                  </span>
                </div>
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  placeholder="••••••••"
                  required
                  class="block w-full pl-10 pr-10 py-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all shadow-sm"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors focus:outline-none"
                >
                  <span class="material-icons-round text-xl" :class="{ 'text-primary': showPassword }">
                    {{ showPassword ? 'visibility' : 'visibility_off' }}
                  </span>
                </button>
              </div>
            </div>
            
            <!-- Remember Me & Forgot Password -->
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <input
                  v-model="rememberMe"
                  type="checkbox"
                  id="remember-me"
                  class="h-4 w-4 text-primary focus:ring-primary border-slate-300 rounded dark:bg-slate-700 dark:border-slate-600 dark:checked:bg-primary cursor-pointer"
                />
                <label class="ml-2 block text-sm text-slate-600 dark:text-slate-400 cursor-pointer select-none" for="remember-me">
                  Recordarme
                </label>
              </div>
              <div class="text-sm">
                <a href="#" class="font-medium text-primary hover:text-indigo-500 transition-colors">
                  ¿Olvidaste tu contraseña?
                </a>
              </div>
            </div>
            
            <!-- Error Message -->
            <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-center gap-2">
              <span class="material-icons-round text-red-500 text-xl">error_outline</span>
              <p class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
            </div>
            
            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="loading"
              class="w-full flex justify-center items-center gap-2 py-3.5 px-4 border border-transparent rounded-lg shadow-lg shadow-indigo-500/20 text-sm font-semibold text-white bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] hover:from-[#4f46e5] hover:to-[#7c3aed] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transform active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="loading" class="material-icons-round animate-spin text-xl">refresh</span>
              <span>{{ loading ? 'Ingresando...' : 'Ingresar' }}</span>
            </button>

            <div v-if="!institutionConfigured" class="mt-4 text-center">
              <p class="text-sm text-slate-500 dark:text-slate-400 mb-2">¿Aún no has configurado la plataforma?</p>
              <button
                type="button"
                @click="router.push('/setup')"
                class="text-indigo-600 dark:text-indigo-400 font-medium hover:underline"
              >
                Configurar ahora
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter, useRoute } from 'vue-router';
import { getInstitucionPublic } from '../api/setup';

// Form state
const email = ref('');
const password = ref('');
const rememberMe = ref(false);
const currentYear = computed(() => new Date().getFullYear());
const showPassword = ref(false);
const error = ref('');
const loading = ref(false);

// Dark mode state
const isDark = ref(false);

// Auth store and router
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const institutionName = ref('');
const institutionConfigured = ref(true);
const setupSuccess = ref(false);

// Toggle dark mode
const toggleDarkMode = () => {
  isDark.value = !isDark.value;
  document.documentElement.classList.toggle('dark', isDark.value);
  localStorage.setItem('darkMode', isDark.value ? 'true' : 'false');
};

// Check for saved dark mode preference and institution info
onMounted(async () => {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode === 'true') {
    isDark.value = true;
    document.documentElement.classList.add('dark');
  }

  setupSuccess.value = route.query.setup === 'success';

  try {
    const { data } = await getInstitucionPublic();
    institutionName.value = data.nombre || '';
    institutionConfigured.value = data.configured;
  } catch (e) {
    institutionConfigured.value = false;
  }
});

// Handle login
const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    await authStore.login(email.value, password.value);
    router.push('/dashboard');
  } catch (err) {
    error.value = 'Credenciales inválidas o error de conexión.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* Google Fonts loaded via index.html or main.css */
.font-sans {
  font-family: 'Inter', sans-serif;
}

/* Primary color for Tailwind */
.bg-primary {
  background-color: #6366f1;
}

.text-primary {
  color: #6366f1;
}

.focus\:ring-primary:focus {
  --tw-ring-color: #6366f1;
}

/* Background pattern */
.bg-pattern {
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
</style>
