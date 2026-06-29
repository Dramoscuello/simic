<template>
  <div class="mx-auto w-full max-w-7xl space-y-8">
    <!-- Welcome Section -->
    <section class="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
      <div>
        <p v-if="institutionName" class="text-sm text-indigo-600 dark:text-indigo-400 font-medium mb-1">{{ institutionName }}</p>
        <h1 class="text-3xl font-bold text-slate-800 dark:text-white mb-2">¡Hola, {{ firstName }}! 👋</h1>
        <p class="text-slate-500 dark:text-slate-400 text-lg">Estás construyendo tu futuro, paso a paso.</p>
      </div>
      
      <!-- Active Simulacro Card -->
      <div v-if="activeSimulacro" class="w-full md:w-auto bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row items-center gap-6 min-w-[400px]">
        <div class="flex-1 w-full">
          <div class="flex justify-between items-center mb-2">
            <span class="text-sm font-bold text-slate-700 dark:text-slate-200">Simulacro reciente</span>
            <span class="text-xs font-semibold text-primary dark:text-primary-400 bg-primary/10 dark:bg-primary/20 px-2 py-1 rounded-full">Disponible</span>
          </div>
          <p class="text-sm text-slate-600 dark:text-slate-300 font-medium mb-1">{{ activeSimulacro.titulo }}</p>
          <p class="text-xs text-slate-400 dark:text-slate-500">{{ activeSimulacro.total_preguntas }} preguntas • {{ activeSimulacro.tiempo_limite }} min</p>
        </div>
        <router-link 
          :to="`/simulacros/${activeSimulacro.id}`"
          class="w-full sm:w-auto px-6 py-2.5 bg-primary hover:bg-indigo-600 dark:hover:bg-indigo-500 text-white rounded-xl font-medium shadow-lg shadow-primary/20 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
        >
          {{ hasStarted(activeSimulacro.id) ? 'Continuar' : 'Empezar' }}
          <span class="material-icons-round text-[18px]">play_arrow</span>
        </router-link>
      </div>
      
      <div v-else class="w-full md:w-auto bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 flex items-center gap-4 min-w-[300px]">
          <div class="h-10 w-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-400 dark:text-slate-500">
              <span class="material-icons-round">check</span>
          </div>
          <p class="text-sm text-slate-500 dark:text-slate-400">No tienes simulacros activos por ahora.</p>
      </div>
    </section>
    
    <!-- Main Grid -->
    <section class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Global Performance (Mock Data for now) -->
      <div class="lg:col-span-1 bg-white dark:bg-slate-800 rounded-3xl p-8 shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col items-center justify-center text-center relative overflow-hidden">
        <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 dark:bg-primary/10 rounded-bl-full -mr-8 -mt-8"></div>
        <h2 class="text-lg font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
          <span class="material-icons-round text-primary dark:text-primary-400">monitoring</span>
          Desempeño global
        </h2>
        <div class="relative w-48 h-48 mb-6 chart-bg">
          <div class="w-full h-full rounded-full" :style="{ background: `conic-gradient(#6366f1 ${globalScore}%, var(--chart-bg) 0)` }"></div>
          <div class="absolute inset-4 bg-white dark:bg-slate-800 rounded-full flex flex-col items-center justify-center shadow-inner dark:shadow-none dark:border dark:border-slate-700">
            <span class="text-4xl font-extrabold text-slate-800 dark:text-white">{{ globalScore }}%</span>
            <span class="text-sm font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wide mt-1">Promedio</span>
          </div>
        </div>
        <div class="px-4 py-2 rounded-xl text-sm font-medium border flex items-center gap-2" :class="performanceClass">
          <span class="material-symbols-outlined filled text-[18px]">{{ performanceIcon }}</span>
          {{ performanceMessage }}
        </div>
      </div>
      
      <!-- Area Results (Mock Data) -->
      <div class="lg:col-span-2 flex flex-col gap-6">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-bold text-slate-800 dark:text-white">Resultados por área</h2>
          <span class="text-sm text-slate-400 dark:text-slate-500">Basado en tus últimos intentos</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- Math -->
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow group cursor-default">
            <div class="flex justify-between items-start mb-3">
              <div class="p-2 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg text-emerald-600 dark:text-emerald-400 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/50 transition-colors">
                <span class="material-icons-round">calculate</span>
              </div>
              <span class="text-lg font-bold text-slate-800 dark:text-white">{{ getAreaStats('MATEMATICAS').estado === 'insufficient_data' ? '--' : getAreaStats('MATEMATICAS').puntaje + '%' }}</span>
            </div>
            <h3 class="font-semibold text-slate-700 dark:text-slate-200 mb-1">Matemáticas</h3>
            <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">{{ getAreaStats('MATEMATICAS').total_intentos }} intentos</p>
          </div>
          
          <!-- Reading -->
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow group cursor-default">
            <div class="flex justify-between items-start mb-3">
              <div class="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/50 transition-colors">
                <span class="material-icons-round">menu_book</span>
              </div>
              <span class="text-lg font-bold text-slate-800 dark:text-white">{{ getAreaStats('LECTURA_CRITICA').estado === 'insufficient_data' ? '--' : getAreaStats('LECTURA_CRITICA').puntaje + '%' }}</span>
            </div>
            <h3 class="font-semibold text-slate-700 dark:text-slate-200 mb-1">Lectura Crítica</h3>
            <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">{{ getAreaStats('LECTURA_CRITICA').total_intentos }} intentos</p>
          </div>
          
          <!-- English -->
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow group cursor-default">
            <div class="flex justify-between items-start mb-3">
              <div class="p-2 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg text-yellow-600 dark:text-yellow-400 group-hover:bg-yellow-100 dark:group-hover:bg-yellow-900/50 transition-colors">
                <span class="material-icons-round">translate</span>
              </div>
              <span class="text-lg font-bold text-slate-800 dark:text-white">{{ getAreaStats('INGLES').estado === 'insufficient_data' ? '--' : getAreaStats('INGLES').puntaje + '%' }}</span>
            </div>
            <h3 class="font-semibold text-slate-700 dark:text-slate-200 mb-1">Inglés</h3>
            <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">{{ getAreaStats('INGLES').total_intentos }} intentos</p>
          </div>
          
          <!-- Science -->
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow group cursor-default">
            <div class="flex justify-between items-start mb-3">
              <div class="p-2 bg-orange-50 dark:bg-orange-900/30 rounded-lg text-orange-600 dark:text-orange-400 group-hover:bg-orange-100 dark:group-hover:bg-orange-900/50 transition-colors">
                <span class="material-icons-round">science</span>
              </div>
              <span class="text-lg font-bold text-slate-800 dark:text-white">{{ getAreaStats('CIENCIAS_NATURALES').estado === 'insufficient_data' ? '--' : getAreaStats('CIENCIAS_NATURALES').puntaje + '%' }}</span>
            </div>
            <h3 class="font-semibold text-slate-700 dark:text-slate-200 mb-1">Ciencias Nat.</h3>
            <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">{{ getAreaStats('CIENCIAS_NATURALES').total_intentos }} intentos</p>
          </div>

          <!-- Social -->
          <div class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow group cursor-default">
            <div class="flex justify-between items-start mb-3">
              <div class="p-2 bg-rose-50 dark:bg-rose-900/30 rounded-lg text-rose-600 dark:text-rose-400 group-hover:bg-rose-100 dark:group-hover:bg-rose-900/50 transition-colors">
                <span class="material-icons-round">public</span>
              </div>
              <span class="text-lg font-bold text-slate-800 dark:text-white">{{ getAreaStats('SOCIALES_CIUDADANAS').estado === 'insufficient_data' ? '--' : getAreaStats('SOCIALES_CIUDADANAS').puntaje + '%' }}</span>
            </div>
            <h3 class="font-semibold text-slate-700 dark:text-slate-200 mb-1">Sociales</h3>
            <p class="text-xs text-slate-400 dark:text-slate-500 font-medium">{{ getAreaStats('SOCIALES_CIUDADANAS').total_intentos }} intentos</p>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Second Row: Resources & Shortcuts -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- Quick Shortcuts -->
      <div class="bg-white dark:bg-slate-800 rounded-3xl p-8 shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col h-full">
        <h3 class="font-bold text-lg text-slate-800 dark:text-white mb-6">Accesos rápidos</h3>
        <div class="grid grid-cols-2 gap-4">
             <router-link to="/simulacros" class="p-4 rounded-xl bg-slate-50 dark:bg-slate-700/50 hover:bg-white dark:hover:bg-slate-700/80 border border-slate-100 dark:border-slate-700 hover:border-primary/30 dark:hover:border-primary/50 hover:shadow-md hover:shadow-primary/5 transition-all text-center flex flex-col items-center gap-2 group">
                 <div class="h-10 w-10 rounded-full bg-primary/10 dark:bg-primary/20 text-primary dark:text-primary-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                     <span class="material-icons-round">assignment</span>
                 </div>
                 <span class="font-medium text-slate-700 dark:text-slate-200">Ver simulacros</span>
             </router-link>
             
             <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-700/50 border border-slate-100 dark:border-slate-700 text-center flex flex-col items-center gap-2 opacity-60 cursor-not-allowed">
                 <div class="h-10 w-10 rounded-full bg-slate-200 dark:bg-slate-600 text-slate-400 dark:text-slate-500 flex items-center justify-center">
                     <span class="material-icons-round">bar_chart</span>
                 </div>
                 <span class="font-medium text-slate-500 dark:text-slate-400">Mis reportes</span>
                 <span class="text-[10px] bg-slate-200 dark:bg-slate-600 px-2 py-0.5 rounded-full text-slate-500 dark:text-slate-300">Pronto</span>
             </div>
        </div>
      </div>
      
      <!-- Motivation/Tip -->
      <div class="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-3xl p-8 shadow-lg text-white flex flex-col justify-between">
          <div>
              <div class="flex items-center gap-2 mb-4 opacity-80">
                  <span class="material-icons-round">tips_and_updates</span>
                  <span class="text-sm font-bold uppercase tracking-wide">Tip del día</span>
              </div>
              <p class="text-xl font-medium leading-relaxed">
                  "{{ currentTip.contenido }}"
              </p>
          </div>
          <div class="mt-8 flex justify-end">
              <span class="text-sm opacity-60">{{ currentTip.autor }}</span>
          </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import api from '../api/axios';

const authStore = useAuthStore();

// User info
const userName = computed(() => {
  return authStore.user?.nombre || authStore.user?.email || 'Estudiante';
});

const firstName = computed(() => {
  const name = userName.value;
  if (!name) return 'Estudiante';
  if (name.includes('@')) {
    return name.split('@')[0];
  }
  return name.split(' ')[0];
});

const institutionName = computed(() => {
  return authStore.user?.institucion?.nombre || '';
});

// State for active simulacro and dashboard stats
const activeSimulacro = ref(null);
const dashboardStats = ref({
    global_score: 0,
    simulacros_completados: 0,
    areas_performance: []
});
const loading = ref(true);

// Computed values for UI
const globalScore = computed(() => dashboardStats.value.global_score);

const performanceClass = computed(() => {
    const score = globalScore.value;
    if (score === 0) return 'bg-slate-50 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-600';
    if (score >= 80) return 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
    if (score >= 60) return 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
    return 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800';
});

const performanceIcon = computed(() => {
     const score = globalScore.value;
     if (score === 0) return 'trending_flat';
     if (score >= 80) return 'trending_up';
     if (score >= 60) return 'check_circle';
     return 'priority_high';
});

const performanceMessage = computed(() => {
    const score = globalScore.value;
    if (score === 0) return 'Completa simulacros para ver tu nivel';
    if (score >= 80) return '¡Excelente desempeño!';
    if (score >= 60) return 'Vas por buen camino';
    return 'Necesitas reforzar algunas áreas';
});

// Tips Data
import tipsData from '../data/tips.json';

const currentTip = computed(() => {
    // Selección determinista basada en el día del año para que todos vean el mismo tip ese día
    // O aleatorio simple si se prefiere que cambie al recargar.
    // Usaremos "Tip del día" (rotación diaria)
    const dayOfYear = Math.floor((new Date() - new Date(new Date().getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);
    const index = dayOfYear % tipsData.length;
    return tipsData[index];
});

// Helper to get area data safely
const getAreaStats = (areaCode) => {
    if (!dashboardStats.value.areas_performance) return { puntaje: 0, estado: 'insufficient_data' };
    const area = dashboardStats.value.areas_performance.find(a => a.area === areaCode);
    return area || { puntaje: 0, estado: 'insufficient_data' };
};

// Fetch dashboard data
onMounted(async () => {
    try {
        loading.value = true;
        
        // 1. Fetch active simulacro
        const simsResponse = await api.get('/simulacros/?limit=5'); // Get recent ones
        const simulacros = simsResponse.data;
        activeSimulacro.value = simulacros.find(s => s.activo) || null;

        // 2. Fetch stats
        const statsResponse = await api.get('/estudiantes/dashboard-stats');
        dashboardStats.value = statsResponse.data.stats;
        
    } catch (e) {
        console.error("Error fetching dashboard data", e);
    } finally {
        loading.value = false;
    }
});

const hasStarted = (id) => false; // Placeholder logic for now

</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}

.chart-bg {
  --chart-bg: #f1f5f9; /* slate-100 equivalent */
}

/* Use global selector for dark mode as .dark usually sits on HTML tag */
:global(.dark) .chart-bg {
  --chart-bg: #1e293b; /* slate-800 equivalent */
}


/* We don't need custom classes for text-primary/bg-primary if we use tailwind colors correctly, 
   but keeping them for safety if specific hex was needed */
.text-primary {
  color: #6366f1;
}

.bg-primary {
  background-color: #6366f1;
}

.bg-primary\/5 {
  background-color: rgba(99, 102, 241, 0.05);
}
.bg-primary\/10 {
  background-color: rgba(99, 102, 241, 0.1);
}
</style>
