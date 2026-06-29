<template>
  <div class="w-full mx-auto max-w-7xl flex flex-col gap-6">
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col gap-6">
      <!-- KPI Skeleton -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="h-32 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"></div>
      </div>
      <!-- Charts Skeleton -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 h-80 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"></div>
        <div class="h-80 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"></div>
      </div>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-800 dark:text-white">Panel de control</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400">Gestión operativa del sistema</p>
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
              <h3 class="mt-2 text-3xl font-bold text-slate-800 dark:text-white">
                {{ formatNumber(kpi.value) }}
              </h3>
            </div>
            <div :class="getKpiIconClass(index)">
              <span class="material-icons-round">{{ getKpiIcon(index) }}</span>
            </div>
          </div>
          <div v-if="kpi.change_value" class="mt-4 flex items-center gap-1 text-sm">
            <span :class="getChangeClass(kpi.change_type)" class="flex items-center font-medium">
              <span class="material-icons-round text-[16px] mr-0.5">{{ getChangeIcon(kpi.change_type) }}</span>
              {{ kpi.change_value }}
            </span>
            <span class="text-slate-400 dark:text-slate-500">{{ kpi.change_label }}</span>
          </div>
          <div v-else class="mt-4 text-sm text-slate-400 dark:text-slate-500">
            {{ kpi.change_label }}
          </div>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Producción Semanal (Bar Chart) -->
        <div class="lg:col-span-2 rounded-xl bg-white dark:bg-slate-800 p-6 shadow-sm border border-slate-100 dark:border-slate-700">
          <div class="mb-6 flex items-center justify-between">
            <div>
              <h3 class="text-lg font-bold text-slate-800 dark:text-white">Ritmo de producción</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">Actividad de los últimos 7 días</p>
            </div>
          </div>
          
          <!-- Bar Chart -->
          <div class="relative h-64 w-full pt-4">
            <!-- Y-Axis Grid Lines -->
            <div class="absolute inset-0 flex flex-col justify-between text-xs text-slate-400 dark:text-slate-600">
              <div class="border-b border-dashed border-slate-200 dark:border-slate-700 w-full h-0"></div>
              <div class="border-b border-dashed border-slate-200 dark:border-slate-700 w-full h-0"></div>
              <div class="border-b border-dashed border-slate-200 dark:border-slate-700 w-full h-0"></div>
              <div class="border-b border-dashed border-slate-200 dark:border-slate-700 w-full h-0"></div>
              <div class="border-b border-slate-200 dark:border-slate-700 w-full h-0"></div>
            </div>
            
            <!-- Bars (Solo Simulacros Creados) -->
            <div class="relative flex h-full items-end justify-around gap-2 px-2 pb-8">
              <div 
                v-for="(dia, idx) in stats.produccion_semanal" 
                :key="idx"
                class="group relative flex flex-col items-center justify-end w-full max-w-16 h-full"
              >
                <!-- Barra de Simulacros Creados -->
                <div 
                  class="w-full rounded-t-md bg-gradient-to-t from-violet-600 to-violet-500 transition-all duration-300 group-hover:from-violet-700 group-hover:to-violet-600 cursor-pointer relative"
                  :style="{ height: getBarHeightRelative(dia.simulacros_creados) }"
                >
                  <!-- Tooltip al hover -->
                  <div 
                    class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-slate-800 dark:bg-slate-900 text-white text-xs font-semibold px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10"
                  >
                    {{ dia.simulacros_creados }} simulacro{{ dia.simulacros_creados !== 1 ? 's' : '' }}
                    <!-- Arrow -->
                    <div class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-slate-800 dark:border-t-slate-900"></div>
                  </div>
                </div>
                <!-- Día de la semana -->
                <span class="absolute -bottom-6 text-xs font-medium text-slate-600 dark:text-slate-400">
                  {{ dia.dia_corto }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Legend (Solo Creados) -->
          <div class="mt-6 flex items-center justify-center">
            <div class="flex items-center gap-2">
              <span class="h-3 w-3 rounded-full bg-violet-500"></span>
              <span class="text-xs font-medium text-slate-600 dark:text-slate-400">Simulacros creados</span>
            </div>
          </div>
        </div>

        <!-- Distribución por Área (Donut Chart) -->
        <div class="rounded-xl bg-white dark:bg-slate-800 p-6 shadow-sm border border-slate-100 dark:border-slate-700">
          <div class="mb-4">
            <h3 class="text-lg font-bold text-slate-800 dark:text-white">Distribución por Área</h3>
            <p class="text-sm text-slate-500 dark:text-slate-400">Catálogo de simulacros</p>
          </div>
          
          <!-- Donut Chart (CSS Only) -->
          <div class="flex flex-col items-center gap-4">
            <div class="relative h-44 w-44">
              <svg viewBox="0 0 36 36" class="w-full h-full transform -rotate-90">
                <circle
                  v-for="(area, idx) in donutSegments"
                  :key="idx"
                  cx="18"
                  cy="18"
                  r="15.9155"
                  fill="transparent"
                  :stroke="area.color"
                  stroke-width="3"
                  :stroke-dasharray="area.dashArray"
                  :stroke-dashoffset="area.offset"
                  class="transition-all duration-500"
                />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ totalSimulacros }}</span>
                <span class="text-xs text-slate-500 dark:text-slate-400">Total</span>
              </div>
            </div>
            
            <!-- Legend -->
            <div class="grid grid-cols-2 gap-x-4 gap-y-2 w-full">
              <div 
                v-for="area in stats.distribucion_areas" 
                :key="area.codigo"
                class="flex items-center gap-2"
              >
                <span 
                  class="h-2.5 w-2.5 rounded-full shrink-0"
                  :style="{ backgroundColor: area.color }"
                ></span>
                <span class="text-xs font-medium text-slate-600 dark:text-slate-400 truncate">
                  {{ area.codigo }}
                </span>
                <span class="text-xs text-slate-400 dark:text-slate-500 ml-auto">
                  {{ area.porcentaje }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tables Section -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <!-- Nuevas Instituciones -->
        <div class="rounded-xl bg-white dark:bg-slate-800 shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div class="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-50 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400">
                <span class="material-icons-round text-[20px]">domain_add</span>
              </div>
              <h3 class="text-base font-bold text-slate-800 dark:text-white">Nuevas instituciones</h3>
            </div>
            <router-link 
              to="/instituciones" 
              class="text-sm font-medium text-primary hover:text-indigo-700 dark:hover:text-indigo-400"
            >
              Ver Todas
            </router-link>
          </div>
          
          <div v-if="stats.instituciones_recientes.length === 0" class="p-8 text-center text-slate-500 dark:text-slate-400">
            <span class="material-icons-round text-4xl mb-2 opacity-50">domain_disabled</span>
            <p class="text-sm">No hay instituciones registradas</p>
          </div>
          
          <div v-else class="divide-y divide-slate-100 dark:divide-slate-700">
            <div 
              v-for="inst in stats.instituciones_recientes" 
              :key="inst.id"
              class="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors cursor-pointer"
              @click="$router.push(`/instituciones/${inst.id}`)"
            >
              <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center">
                  <span class="text-white font-bold text-sm">{{ getInitials(inst.nombre) }}</span>
                </div>
                <div>
                  <h4 class="font-semibold text-slate-800 dark:text-white text-sm">{{ inst.nombre }}</h4>
                  <p class="text-xs text-slate-500 dark:text-slate-400">{{ inst.ciudad || 'Sin ciudad' }}</p>
                </div>
              </div>
              <span class="text-xs text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">
                {{ inst.fecha }}
              </span>
            </div>
          </div>
        </div>

        <!-- Últimos Simulacros -->
        <div class="rounded-xl bg-white dark:bg-slate-800 shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div class="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400">
                <span class="material-icons-round text-[20px]">quiz</span>
              </div>
              <h3 class="text-base font-bold text-slate-800 dark:text-white">Últimos simulacros</h3>
            </div>
            <router-link 
              to="/simulacros" 
              class="text-sm font-medium text-primary hover:text-indigo-700 dark:hover:text-indigo-400"
            >
              Ver Todos
            </router-link>
          </div>
          
          <div v-if="stats.simulacros_recientes.length === 0" class="p-8 text-center text-slate-500 dark:text-slate-400">
            <span class="material-icons-round text-4xl mb-2 opacity-50">quiz</span>
            <p class="text-sm">No hay simulacros creados</p>
          </div>
          
          <div v-else class="divide-y divide-slate-100 dark:divide-slate-700">
            <div 
              v-for="sim in stats.simulacros_recientes" 
              :key="sim.id"
              class="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors cursor-pointer"
              @click="$router.push(`/simulacros`)"
            >
              <div class="flex items-center gap-3">
                <div 
                  class="h-10 w-10 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  :style="{ background: getAreaGradient(sim.area) }"
                >
                  {{ getAreaCode(sim.area) }}
                </div>
                <div>
                  <h4 class="font-semibold text-slate-800 dark:text-white text-sm truncate max-w-[180px]">{{ sim.titulo }}</h4>
                  <p class="text-xs text-slate-500 dark:text-slate-400">{{ sim.institucion_nombre }}</p>
                </div>
              </div>
              <div class="flex flex-col items-end gap-1">
                <div class="flex items-center gap-2">
                  <span 
                    class="text-xs px-2 py-1 rounded-full font-medium"
                    :class="sim.estado === 'activo' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'"
                  >
                    {{ sim.estado === 'activo' ? 'Activo' : 'Finalizado' }}
                  </span>
                  <span class="text-xs text-slate-400 dark:text-slate-500">
                    {{ sim.fecha }}
                  </span>
                </div>
                <!-- Badge Creador -->
                <span 
                  v-if="sim.created_by_tipo"
                  class="text-[10px] px-1.5 py-0.5 rounded font-medium truncate max-w-[100px]"
                  :class="sim.created_by_tipo === 'plataforma' ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'"
                  :title="sim.created_by_nombre"
                >
                  {{ sim.created_by_tipo === 'plataforma' ? 'SuperAdmin' : sim.created_by_nombre || 'Institución' }}
                </span>
              </div>
            </div>
          </div>
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
import { ref, computed, onMounted } from 'vue';
import api from '@/api/axios';

// State
const loading = ref(true);
const refreshing = ref(false);
const error = ref(null);
const stats = ref({
  kpis: [],
  produccion_semanal: [],
  distribucion_areas: [],
  instituciones_recientes: [],
  simulacros_recientes: []
});

// Computed
const maxProduccion = computed(() => {
  if (!stats.value.produccion_semanal.length) return 1;
  return Math.max(...stats.value.produccion_semanal.map(d => d.simulacros_creados), 1);
});

const totalSimulacros = computed(() => {
  return stats.value.distribucion_areas.reduce((sum, a) => sum + a.cantidad, 0);
});

const donutSegments = computed(() => {
  const circumference = 100;
  let offset = 0;
  
  return stats.value.distribucion_areas.map(area => {
    const dashLength = (area.porcentaje / 100) * circumference;
    const segment = {
      ...area,
      dashArray: `${dashLength} ${circumference - dashLength}`,
      offset: -offset
    };
    offset += dashLength;
    return segment;
  });
});

// Methods
const fetchStats = async ({ forceRefresh = false } = {}) => {
  try {
    error.value = null;
    const response = await api.get('/dashboard/superadmin/stats', {
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

const formatNumber = (num) => {
  return new Intl.NumberFormat('es-CO').format(num);
};

const getBarHeight = (value, max) => {
  if (max === 0 || value === 0) return '4px';
  const percentage = Math.max((value / max) * 100, 5);
  return `${percentage}%`;
};

// Nueva función: Altura relativa al máximo (el día con más simulacros = 100% altura)
const getBarHeightRelative = (value) => {
  if (value === 0) return '4px'; // Altura mínima visible
  const max = maxProduccion.value;
  if (max === 0) return '4px';
  // El día con más simulacros ocupa 100% del contenedor
  const percentage = (value / max) * 100;
  return `${percentage}%`;
};

const getKpiIcon = (index) => {
  const icons = ['domain', 'quiz', 'school', 'inventory_2'];
  return icons[index] || 'analytics';
};

const getKpiIconClass = (index) => {
  const classes = [
    'flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400',
    'flex h-10 w-10 items-center justify-center rounded-lg bg-violet-50 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400',
    'flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400',
    'flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400'
  ];
  return classes[index] || classes[0];
};

const getChangeClass = (type) => {
  const classes = {
    up: 'text-emerald-600 dark:text-emerald-400',
    down: 'text-rose-500 dark:text-rose-400',
    new: 'text-teal-600 dark:text-teal-400',
    neutral: 'text-slate-500 dark:text-slate-400'
  };
  return classes[type] || classes.neutral;
};

const getChangeIcon = (type) => {
  const icons = {
    up: 'trending_up',
    down: 'trending_down',
    new: 'add',
    neutral: 'remove'
  };
  return icons[type] || 'remove';
};

const getInitials = (name) => {
  return name
    .split(' ')
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase();
};

const getAreaCode = (area) => {
  const codes = {
    'Matemáticas': 'MAT',
    'MATEMATICAS': 'MAT',
    'Lectura Crítica': 'LC',
    'LECTURA_CRITICA': 'LC',
    'Ciencias Naturales': 'CN',
    'CIENCIAS_NATURALES': 'CN',
    'Ciencias Sociales': 'CS',
    'Sociales y Ciudadanas': 'CS',
    'SOCIALES_CIUDADANAS': 'CS',
    'Inglés': 'ING',
    'INGLES': 'ING',
  };
  return codes[area] || area.substring(0, 3).toUpperCase();
};

const getAreaGradient = (area) => {
  const gradients = {
    'Matemáticas': 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    'MATEMATICAS': 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    'Lectura Crítica': 'linear-gradient(135deg, #3b82f6, #2563eb)',
    'LECTURA_CRITICA': 'linear-gradient(135deg, #3b82f6, #2563eb)',
    'Ciencias Naturales': 'linear-gradient(135deg, #10b981, #059669)',
    'CIENCIAS_NATURALES': 'linear-gradient(135deg, #10b981, #059669)',
    'Ciencias Sociales': 'linear-gradient(135deg, #f59e0b, #d97706)',
    'Sociales y Ciudadanas': 'linear-gradient(135deg, #f59e0b, #d97706)',
    'SOCIALES_CIUDADANAS': 'linear-gradient(135deg, #f59e0b, #d97706)',
    'Inglés': 'linear-gradient(135deg, #ef4444, #dc2626)',
    'INGLES': 'linear-gradient(135deg, #ef4444, #dc2626)',
  };
  return gradients[area] || 'linear-gradient(135deg, #6b7280, #4b5563)';
};

// Lifecycle
onMounted(() => {
  fetchStats();
});
</script>

<style scoped>
.text-primary {
  color: #6366f1;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
