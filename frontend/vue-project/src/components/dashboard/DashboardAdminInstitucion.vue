<template>
  <div class="w-full mx-auto max-w-7xl flex flex-col gap-6">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col gap-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="h-32 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"></div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 h-80 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"></div>
        <div class="h-80 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"></div>
      </div>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Header with Selector -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-800 dark:text-white">Inteligencia académica 360°</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400">Resultados consolidados de tu institución</p>
        </div>
        <button 
          @click="refreshData" 
          :disabled="refreshing"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors text-sm font-medium disabled:opacity-50"
        >
          <span class="material-icons-round text-[18px]" :class="{ 'animate-spin': refreshing }">refresh</span>
          Actualizar
        </button>
      </div>

      <!-- KPI Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="(kpi, index) in stats.kpis" 
          :key="index"
          class="relative overflow-hidden rounded-xl bg-white dark:bg-slate-800 p-5 shadow-sm border border-slate-100 dark:border-slate-700 group hover:shadow-md transition-all"
        >
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm font-medium text-slate-500 dark:text-slate-400">{{ kpi.label }}</p>
              <h3 class="mt-2 text-xl font-bold text-slate-800 dark:text-white">{{ kpi.value }}</h3>
            </div>
            <div :class="getKpiIconClass(kpi.color)">
              <span class="material-icons-round">{{ kpi.icon }}</span>
            </div>
          </div>
          <!-- Progress bar or subtitle -->
          <div v-if="kpi.progress !== null && kpi.progress !== undefined" class="mt-4">
            <div class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2">
              <div 
                class="h-2 rounded-full transition-all"
                :class="getProgressBarClass(kpi.color)"
                :style="{ width: `${Math.min(kpi.progress, 100)}%` }"
              ></div>
            </div>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">{{ kpi.subtitle }}</p>
          </div>
          <div v-else-if="kpi.subtitle" class="mt-4 text-sm text-slate-400 dark:text-slate-500">
            {{ kpi.subtitle }}
          </div>
        </div>
      </div>

      <!-- Charts Row 1: Distribution -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Distribution Donut por Área (Slider) -->
        <div class="rounded-xl bg-white dark:bg-slate-800 p-6 shadow-sm border border-slate-100 dark:border-slate-700">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-slate-800 dark:text-white">Distribución de niveles</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">Por área ICFES</p>
            </div>
            <!-- Navigation Dots -->
            <div class="flex items-center gap-2">
              <button 
                @click="prevArea"
                class="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              >
                <span class="material-icons-round text-sm text-slate-600 dark:text-slate-400">chevron_left</span>
              </button>
              <div class="flex gap-1">
                <span 
                  v-for="(area, idx) in stats.distribucion_por_area"
                  :key="area.area"
                  @click="currentAreaIndex = idx"
                  class="w-2 h-2 rounded-full cursor-pointer transition-all"
                  :class="idx === currentAreaIndex ? 'bg-primary scale-125' : 'bg-slate-300 dark:bg-slate-600 hover:bg-slate-400'"
                ></span>
              </div>
              <button 
                @click="nextArea"
                class="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              >
                <span class="material-icons-round text-sm text-slate-600 dark:text-slate-400">chevron_right</span>
              </button>
            </div>
          </div>
          
          <!-- Slider Content -->
          <div v-if="stats.distribucion_por_area.length > 0" class="relative overflow-hidden">
            <transition name="slide" mode="out-in">
              <div :key="currentAreaIndex" class="flex flex-col items-center gap-4">
                <!-- Area Badge -->
                <div 
                  class="px-3 py-1 rounded-full text-xs font-bold"
                  :style="{ backgroundColor: currentArea.area_color + '20', color: currentArea.area_color }"
                >
                  {{ currentArea.area_codigo }} · {{ currentArea.area }}
                </div>
                
                <!-- Donut Chart -->
                <div class="relative h-36 w-36">
                  <div 
                    class="w-full h-full rounded-full"
                    :style="{ background: currentAreaConicGradient }"
                  ></div>
                  <div class="absolute inset-3 bg-white dark:bg-slate-800 rounded-full flex flex-col items-center justify-center shadow-inner">
                    <span class="text-xl font-bold text-slate-800 dark:text-white">{{ currentArea.total_evaluados }}</span>
                    <span class="text-[10px] text-slate-400 dark:text-slate-500">Evaluados</span>
                  </div>
                </div>
                
                <!-- Legend -->
                <div class="grid grid-cols-2 gap-x-4 gap-y-1.5 w-full text-sm">
                  <div 
                    v-for="nivel in currentArea.niveles" 
                    :key="nivel.nivel"
                    class="flex items-center gap-2"
                  >
                    <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: nivel.color }"></span>
                    <span class="text-slate-600 dark:text-slate-400 text-xs">{{ nivel.nivel }}</span>
                    <span class="text-slate-400 dark:text-slate-500 ml-auto text-xs font-medium">{{ nivel.porcentaje }}%</span>
                  </div>
                </div>
              </div>
            </transition>
          </div>
          
          <div v-else class="flex h-48 items-center justify-center text-slate-400 dark:text-slate-500">
            <div class="text-center">
              <span class="material-icons-round text-4xl mb-2 opacity-50">pie_chart</span>
              <p class="text-sm">Sin datos de distribución</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Heatmap: Areas vs Grupos (Semáforo) -->
      <div v-if="stats.heatmap_grupos.length > 0" class="rounded-xl bg-white dark:bg-slate-800 p-6 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h3 class="text-lg font-bold text-slate-800 dark:text-white">Semáforo de desempeño</h3>
            <p class="text-sm text-slate-500 dark:text-slate-400">Áreas vs Grupos (click para ver detalle)</p>
          </div>
          <div class="flex items-center gap-4 text-xs">
            <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-emerald-500"></span> Alto (80+)</div>
            <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-indigo-500"></span> Medio (60-79)</div>
            <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-amber-500"></span> Bajo (40-59)</div>
            <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-red-500"></span> Crítico (&lt;40)</div>
          </div>
        </div>
        
        <div class="overflow-x-auto">
          <div class="flex gap-2 flex-wrap">
            <div 
              v-for="cell in stats.heatmap_grupos"
              :key="`${cell.area}-${cell.grupo_id}`"
              class="p-3 rounded-lg cursor-pointer transition-all hover:scale-105 hover:shadow-lg min-w-[120px]"
              :style="{ backgroundColor: cell.color + '20', borderLeft: `4px solid ${cell.color}` }"
              @click="showGroupDetail(cell)"
            >
              <p class="text-xs font-medium text-slate-500 dark:text-slate-400">{{ cell.grupo }}</p>
              <p class="font-bold text-slate-800 dark:text-white text-lg">{{ cell.promedio }}%</p>
              <p class="text-xs text-slate-400 dark:text-slate-500">{{ getAreaShort(cell.area) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tables Row: Groups + Top Students -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <!-- Rendimiento por grupo -->
        <div class="rounded-xl bg-white dark:bg-slate-800 shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div class="p-5 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400">
                <span class="material-icons-round text-[20px]">groups</span>
              </div>
              <h3 class="text-base font-bold text-slate-800 dark:text-white">Rendimiento por grupo</h3>
            </div>
          </div>
          
          <div v-if="stats.rendimiento_grupos.length === 0" class="p-8 text-center text-slate-500 dark:text-slate-400">
            <span class="material-icons-round text-4xl mb-2 opacity-50">group_off</span>
            <p class="text-sm">Sin datos de grupos</p>
          </div>
          
          <div v-else class="max-h-[320px] overflow-y-auto">
            <table class="w-full text-sm text-left">
              <thead class="text-slate-500 dark:text-slate-400 font-medium">
                <tr>
                  <th class="px-5 py-3 sticky top-0 z-10 bg-slate-50 dark:bg-slate-700/50">Grupo</th>
                  <th class="px-5 py-3 text-center sticky top-0 z-10 bg-slate-50 dark:bg-slate-700/50">Estudiantes</th>
                  <th class="px-5 py-3 text-center sticky top-0 z-10 bg-slate-50 dark:bg-slate-700/50">Promedio</th>
                  <th class="px-5 py-3 text-right sticky top-0 z-10 bg-slate-50 dark:bg-slate-700/50">Nivel</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr
                  v-for="grupo in stats.rendimiento_grupos"
                  :key="grupo.id"
                  class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors cursor-pointer"
                  @click="$router.push(`/grupos/${grupo.id}`)"
                >
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ grupo.nombre }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-400 text-center">{{ grupo.total_estudiantes }}</td>
                  <td class="px-5 py-4 font-bold text-center" :style="{ color: grupo.color }">{{ grupo.promedio }}%</td>
                  <td class="px-5 py-4 text-right">
                    <span
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getNivelBadgeClass(grupo.nivel)"
                    >
                      {{ capitalizeFirst(grupo.nivel) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top 5 estudiantes -->
        <div class="rounded-xl bg-white dark:bg-slate-800 shadow-sm border border-slate-100 dark:border-slate-700">
          <div class="p-5 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400">
                <span class="material-icons-round text-[20px]">emoji_events</span>
              </div>
              <h3 class="text-base font-bold text-slate-800 dark:text-white">Top 5 estudiantes</h3>
            </div>
          </div>
          
          <div v-if="stats.top_estudiantes.length === 0" class="p-8 text-center text-slate-500 dark:text-slate-400">
            <span class="material-icons-round text-4xl mb-2 opacity-50">school</span>
            <p class="text-sm">Sin datos de estudiantes</p>
          </div>
          
          <div v-else class="p-3 space-y-1">
            <div
              v-for="est in top5Estudiantes"
              :key="est.id"
              class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors cursor-pointer"
              @click="$router.push(`/usuarios/${est.id}`)"
            >
              <div class="flex items-center gap-4">
                <div 
                  class="w-8 h-8 flex items-center justify-center rounded-full font-bold text-sm border"
                  :class="getPositionClass(est.posicion)"
                >
                  {{ est.posicion }}
                </div>
                <div>
                  <p class="font-semibold text-slate-900 dark:text-white text-sm">{{ est.nombre }}</p>
                  <p class="text-xs text-slate-500 dark:text-slate-400">{{ est.grupo_nombre || 'Sin grupo' }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-bold text-slate-900 dark:text-white">{{ est.puntaje }}</p>
                <p class="text-xs font-medium" :class="getPuntajeLabel(est.puntaje).class">{{ getPuntajeLabel(est.puntaje).text }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Competencias a Fortalecer -->
      <div v-if="stats.competencias_debiles.length > 0" class="rounded-xl bg-white dark:bg-slate-800 p-6 shadow-sm border border-slate-100 dark:border-slate-700">
        <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4">Competencias a Fortalecer</h3>
        <div class="flex flex-wrap gap-3">
          <span 
            v-for="comp in stats.competencias_debiles"
            :key="comp.nombre"
            class="px-4 py-2 rounded-lg text-sm font-medium border inline-flex items-center gap-2"
            :class="getCompetenciaBadgeClass(comp.nivel)"
          >
            <span>{{ comp.nombre }}</span>
            <span class="text-xs opacity-60">·</span>
            <span class="text-xs opacity-75">{{ comp.area }}</span>
          </span>
        </div>
      </div>
    </template>

    <!-- Error State -->
    <div v-if="error" class="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-6 text-center">
      <span class="material-icons-round text-4xl text-red-500 mb-2">error</span>
      <p class="text-red-700 dark:text-red-400 font-medium">{{ error }}</p>
      <button @click="fetchStats" class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors">
        Reintentar
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import api from '@/api/axios';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const institutionName = computed(() => authStore.user?.institucion?.nombre || '');

// State
const loading = ref(true);
const refreshing = ref(false);
const error = ref(null);
const stats = ref({
  kpis: [],
  heatmap_grupos: [],
  distribucion_por_area: [],
  rendimiento_grupos: [],
  top_estudiantes: [],
  top_progreso: [],
  competencias_debiles: [],
  tasa_finalizacion: 0
});

// Slider state
const currentAreaIndex = ref(0);
let autoSlideInterval = null;

// Current area computed
const currentArea = computed(() => {
  if (!stats.value.distribucion_por_area.length) {
    return {
      area: '',
      area_codigo: '',
      area_color: '#6b7280',
      total_evaluados: 0,
      niveles: []
    };
  }
  return stats.value.distribucion_por_area[currentAreaIndex.value];
});

const top5Estudiantes = computed(() => {
  return (stats.value.top_estudiantes || []).slice(0, 5);
});

// Conic gradient for current area
const currentAreaConicGradient = computed(() => {
  const niveles = currentArea.value.niveles;
  if (!niveles || !niveles.length) return '#e2e8f0';
  
  let cumulative = 0;
  const stops = niveles.map(n => {
    const start = cumulative;
    cumulative += n.porcentaje;
    return `${n.color} ${start}% ${cumulative}%`;
  });
  
  return `conic-gradient(${stops.join(', ')})`;
});

// Slider navigation
const nextArea = () => {
  const total = stats.value.distribucion_por_area.length;
  if (total === 0) return;
  currentAreaIndex.value = (currentAreaIndex.value + 1) % total;
  resetAutoSlide();
};

const prevArea = () => {
  const total = stats.value.distribucion_por_area.length;
  if (total === 0) return;
  currentAreaIndex.value = (currentAreaIndex.value - 1 + total) % total;
  resetAutoSlide();
};

const startAutoSlide = () => {
  autoSlideInterval = setInterval(() => {
    const total = stats.value.distribucion_por_area.length;
    if (total > 0) {
      currentAreaIndex.value = (currentAreaIndex.value + 1) % total;
    }
  }, 5000); // Cambiar cada 5 segundos
};

const resetAutoSlide = () => {
  if (autoSlideInterval) {
    clearInterval(autoSlideInterval);
  }
  startAutoSlide();
};

// Methods
const fetchStats = async ({ forceRefresh = false } = {}) => {
  try {
    error.value = null;
    const response = await api.get('/dashboard/institucion/stats', {
      params: forceRefresh ? { _ts: Date.now() } : undefined
    });
    stats.value = response.data;
  } catch (err) {
    console.error('Error fetching dashboard stats:', err);
    error.value = err.response?.data?.detail || 'Error al cargar los datos del dashboard';
  } finally {
    loading.value = false;
  }
};

const refreshData = async () => {
  refreshing.value = true;
  await fetchStats({ forceRefresh: true });
  refreshing.value = false;
};

const filterByLevel = (nivel) => {
  console.log('Filter by level:', nivel);
  // TODO: Navigate to students filtered by level
};

const showGroupDetail = (cell) => {
  console.log('Show group detail:', cell);
  // TODO: Open modal or navigate
};

const getKpiIconClass = (color) => {
  const classes = {
    blue: 'flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400',
    purple: 'flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400',
    emerald: 'flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400',
    amber: 'flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400'
  };
  return classes[color] || classes.blue;
};

const getProgressBarClass = (color) => {
  const classes = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500'
  };
  return classes[color] || classes.blue;
};

const getAreaShort = (area) => {
  const shorts = {
    'Matemáticas': 'MAT',
    'MATEMATICAS': 'MAT',
    'Lectura Crítica': 'LC',
    'LECTURA_CRITICA': 'LC',
    'Ciencias Naturales': 'CN',
    'CIENCIAS_NATURALES': 'CN',
    'Ciencias Sociales': 'SOC',
    'SOCIALES_CIUDADANAS': 'SOC',
    'Inglés': 'ING',
    'INGLES': 'ING',
  };
  return shorts[area] || area.substring(0, 3);
};

const getNivelBadgeClass = (nivel) => {
  const classes = {
    alto: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
    medio: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
    bajo: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
    critico: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
  };
  return classes[nivel] || classes.medio;
};

const getCompetenciaBadgeClass = (nivel) => {
  const classes = {
    critico: 'bg-rose-50 text-rose-700 border-rose-100 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-800',
    bajo: 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-800',
    medio: 'bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:border-slate-600'
  };
  return classes[nivel] || classes.medio;
};

const getPositionClass = (pos) => {
  const classes = {
    1: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    2: 'bg-slate-200 text-slate-700 border-slate-300',
    3: 'bg-orange-100 text-orange-700 border-orange-200'
  };
  return classes[pos] || 'bg-slate-100 text-slate-600 border-slate-200';
};

const getPuntajeLabel = (puntaje) => {
  if (puntaje >= 90) return { text: 'Sobresaliente', class: 'text-emerald-500' };
  if (puntaje >= 80) return { text: 'Excelente', class: 'text-primary' };
  if (puntaje >= 60) return { text: 'Bueno', class: 'text-blue-500' };
  return { text: 'Regular', class: 'text-amber-500' };
};

const capitalizeFirst = (str) => str.charAt(0).toUpperCase() + str.slice(1);

// Lifecycle
onMounted(() => {
  fetchStats();
  startAutoSlide();
});

onUnmounted(() => {
  if (autoSlideInterval) {
    clearInterval(autoSlideInterval);
  }
});
</script>

<style scoped>
.text-primary {
  color: #6366f1;
}

.bg-primary {
  background-color: #6366f1;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease-out;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
