<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6">
    <Toast />
    <ConfirmDialog />
    
   
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Total revisiones</p>
            <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{{ stats.total }}</p>
          </div>
          <div class="p-3 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
            <span class="material-icons-round">flag</span>
          </div>
        </div>
      </div>
      
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-amber-200 dark:border-amber-800">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-amber-600 dark:text-amber-400">Pendientes</p>
            <p class="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">{{ stats.pendientes }}</p>
          </div>
          <div class="p-3 rounded-lg bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
            <span class="material-icons-round">pending_actions</span>
          </div>
        </div>
      </div>
      
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-emerald-200 dark:border-emerald-800">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-emerald-600 dark:text-emerald-400">Resueltas</p>
            <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{{ stats.resueltas }}</p>
          </div>
          <div class="p-3 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
            <span class="material-icons-round">check_circle</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Filters -->
    <div class="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-100 dark:border-slate-700">
      <div class="flex flex-wrap items-center gap-4">
        <!-- Filtro Estado -->
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-500 dark:text-slate-400">Estado</label>
          <Select 
            v-model="filterEstado" 
            :options="estadoOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todos"
            class="w-40"
            :pt="{
              root: { class: 'border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700' },
              label: { class: 'text-slate-700 dark:text-white text-sm' },
              dropdown: { class: 'text-slate-400' },
              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
            }"
            showClear
          />
        </div>
        
        <!-- Filtro Sede -->
        <div v-if="sedes.length > 1" class="flex flex-col gap-1">
          <label class="text-xs text-slate-500 dark:text-slate-400">Sede</label>
          <Select 
            v-model="filterSede" 
            :options="sedes"
            optionLabel="nombre"
            optionValue="id"
            placeholder="Todas"
            class="w-64"
            :pt="{
              root: { class: 'border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700' },
              label: { class: 'text-slate-700 dark:text-white text-sm' },
              dropdown: { class: 'text-slate-400' },
              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
            }"
            filter
            filterPlaceholder="Buscar..."
            showClear
          />
        </div>
        
        <!-- Botón Limpiar -->
        <button 
          @click="clearFilters"
          class="mt-auto px-3 py-2 rounded-lg text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors flex items-center gap-1"
        >
          <span class="material-icons-round text-[18px]">clear_all</span>
          Limpiar
        </button>
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="filteredReviews.length === 0" class="bg-white dark:bg-slate-800 rounded-xl p-12 shadow-sm border border-slate-100 dark:border-slate-700 text-center">
      <div class="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
        <span class="material-icons-round text-slate-400 dark:text-slate-500 text-3xl">inbox</span>
      </div>
      <h3 class="text-lg font-semibold text-slate-700 dark:text-slate-300 mb-2">No hay revisiones</h3>
      <p class="text-slate-500 dark:text-slate-400">{{ filterEstado === false ? 'No hay revisiones pendientes' : 'No se encontraron revisiones con los filtros aplicados' }}</p>
    </div>
    
    <!-- Reviews Table -->
    <div v-else class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Pregunta</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Simulacro</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Sede</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Nota</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
              <th class="px-4 py-3 text-right text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr v-for="review in filteredReviews" :key="review.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
              <!-- Pregunta -->
              <td class="px-4 py-4">
                <div class="flex items-start gap-3">
                  <span class="flex-shrink-0 inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-sm font-bold">
                    {{ review.pregunta_numero }}
                  </span>
                  <div class="min-w-0">
                    <p class="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">{{ review.pregunta_enunciado || 'Sin enunciado' }}</p>
                    <span class="text-xs text-slate-400 dark:text-slate-500">{{ getAreaLabel(review.area) }}</span>
                  </div>
                </div>
              </td>
              
              <!-- Simulacro -->
              <td class="px-4 py-4">
                <div>
                  <p class="text-sm font-medium text-slate-700 dark:text-slate-300 truncate max-w-[200px]">{{ review.simulacro_titulo }}</p>
                </div>
              </td>
              
              <!-- Sede -->
              <td class="px-4 py-4">
                <span class="text-sm text-slate-600 dark:text-slate-400">{{ review.sede_nombre || review.institucion_nombre || '-' }}</span>
              </td>
              
              <!-- Nota -->
              <td class="px-4 py-4 max-w-[300px]">
                <p class="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">{{ review.revision }}</p>
                <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">Por {{ review.usuario_nombre || 'Usuario' }} • {{ formatDate(review.created_at) }}</p>
              </td>
              
              <!-- Estado -->
              <td class="px-4 py-4">
                <span 
                  :class="review.resuelto ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'"
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
                >
                  <span class="material-icons-round text-[14px]">{{ review.resuelto ? 'check_circle' : 'pending' }}</span>
                  {{ review.resuelto ? 'Resuelto' : 'Pendiente' }}
                </span>
              </td>
              
              <!-- Acciones -->
              <td class="px-4 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <!-- Ver detalle de la nota -->
                  <button 
                    @click="openDetailModal(review)"
                    class="p-2 rounded-lg text-slate-400 hover:text-primary hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                    title="Ver nota completa"
                  >
                    <span class="material-icons-round text-[20px]">visibility</span>
                  </button>
                  
                  <!-- Marcar como resuelto -->
                  <button 
                    v-if="!review.resuelto"
                    @click="markAsResolved(review)"
                    class="p-2 rounded-lg text-emerald-500 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/30 transition-colors"
                    title="Marcar como resuelto"
                  >
                    <span class="material-icons-round text-[20px]">check_circle</span>
                  </button>
                  
                  <!-- Reabar (si está resuelto) -->
                  <button 
                    v-else
                    @click="markAsUnresolved(review.id)"
                    class="p-2 rounded-lg text-amber-500 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/30 transition-colors"
                    title="Reabrir revisión"
                  >
                    <span class="material-icons-round text-[20px]">replay</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Modal de Detalle de Nota -->
    <div 
      v-if="showDetailModal && selectedReview" 
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div 
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="closeDetailModal"
      ></div>
      
      <!-- Modal Content -->
      <div class="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-700">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <span class="material-icons-round text-amber-600 dark:text-amber-400">flag</span>
            </div>
            <div>
              <h3 class="text-lg font-bold text-slate-800 dark:text-white">Nota de revisión</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">Pregunta {{ selectedReview.pregunta_numero }} • {{ getAreaLabel(selectedReview.area) }}</p>
            </div>
          </div>
          <button 
            @click="closeDetailModal"
            class="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            <span class="material-icons-round">close</span>
          </button>
        </div>
        
        <!-- Body -->
        <div class="flex-1 overflow-y-auto px-6 py-4">
          <!-- Info del Simulacro -->
          <div class="mb-4 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
            <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Simulacro</p>
            <p class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ selectedReview.simulacro_titulo }}</p>
            <p class="text-xs text-slate-400 dark:text-slate-500" v-if="selectedReview.sede_nombre || selectedReview.institucion_nombre">
              {{ selectedReview.sede_nombre || selectedReview.institucion_nombre }}
            </p>
          </div>
          
          <!-- Enunciado de la Pregunta -->
          <div class="mb-4" v-if="selectedReview.pregunta_enunciado">
            <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Enunciado</p>
            <p class="text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-700/50 p-3 rounded-lg">{{ selectedReview.pregunta_enunciado }}</p>
          </div>
          
          <!-- Nota Completa -->
          <div class="mb-4">
            <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">Nota de revisión</p>
            <div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 rounded-lg p-4">
              <p class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{{ selectedReview.revision }}</p>
            </div>
          </div>
          
          <!-- Metadata -->
          <div class="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
            <span>Por {{ selectedReview.usuario_nombre || 'Usuario' }}</span>
            <span>{{ formatDate(selectedReview.created_at) }}</span>
          </div>
          
          <!-- Estado -->
          <div class="mt-4 flex items-center gap-2">
            <span 
              :class="selectedReview.resuelto ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
            >
              <span class="material-icons-round text-[14px]">{{ selectedReview.resuelto ? 'check_circle' : 'pending' }}</span>
              {{ selectedReview.resuelto ? 'Resuelto' : 'Pendiente' }}
            </span>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <button 
            @click="closeDetailModal"
            class="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            Cerrar
          </button>
          <router-link 
            :to="`/simulacros/${selectedReview.simulacro_id}/editar`"
            class="px-4 py-2 rounded-lg text-sm font-medium text-white bg-primary hover:bg-primary/90 transition-colors flex items-center gap-2"
            @click="closeDetailModal"
          >
            <span class="material-icons-round text-[18px]">edit</span>
            Ir a simulacro
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useSedesStore } from '../stores/sedes';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import Toast from 'primevue/toast';
import ConfirmDialog from 'primevue/confirmdialog';
import Select from 'primevue/select';
import api from '../api/axios';

const authStore = useAuthStore();
const sedesStore = useSedesStore();
const toast = useToast();
const confirm = useConfirm();
const userRole = computed(() => authStore.user?.rol?.nombre || 'guest');

// Estado
const loading = ref(true);
const reviews = ref([]);
const sedes = ref([]);
const showDetailModal = ref(false);
const selectedReview = ref(null);
const stats = ref({ total: 0, pendientes: 0, resueltas: 0 });

// Opciones de filtros
const estadoOptions = [
  { label: 'Pendientes', value: false },
  { label: 'Resueltas', value: true }
];

// Filtros
const filterEstado = ref(false); // Por defecto mostrar pendientes
const filterSede = ref(null);

// Computed
const filteredReviews = computed(() => {
  let result = reviews.value;
  
  if (filterEstado.value !== null) {
    result = result.filter(r => r.resuelto === filterEstado.value);
  }
  
  if (filterSede.value) {
    result = result.filter(r => r.sede_id === filterSede.value);
  }
  
  return result;
});

// Métodos
const fetchReviews = async () => {
  loading.value = true;
  try {
    const params = {};
    if (filterSede.value) {
      params.sede_id = filterSede.value;
    }
    
    const response = await api.get('/reviews/all', { params });
    reviews.value = response.data.reviews || [];
    stats.value = {
      total: response.data.total,
      pendientes: response.data.pendientes,
      resueltas: response.data.resueltas
    };
  } catch (error) {
    console.error('Error fetching reviews:', error);
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar las revisiones',
      life: 5000
    });
  } finally {
    loading.value = false;
  }
};

const fetchSedes = async () => {
  try {
    const data = await sedesStore.fetchSedes(authStore.user?.institucion_id);
    sedes.value = data || [];
  } catch (error) {
    console.error('Error fetching sedes:', error);
  }
};

const markAsResolvedDirect = async (reviewId) => {
  try {
    await api.patch(`/reviews/${reviewId}`, { resuelto: true });
    
    // Actualizar localmente
    const idx = reviews.value.findIndex(r => r.id === reviewId);
    if (idx !== -1) {
      reviews.value[idx].resuelto = true;
    }
    
    // Actualizar stats
    stats.value.pendientes--;
    stats.value.resueltas++;
    
    toast.add({
      severity: 'success',
      summary: 'Revisión resuelta',
      detail: 'La revisión ha sido marcada como resuelta',
      life: 2000
    });
  } catch (error) {
    console.error('Error marking as resolved:', error);
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo actualizar la revisión',
      life: 5000
    });
  }
};

const markAsResolved = (review) => {
  if (!review?.id) return;

  if (userRole.value !== 'admin') {
    markAsResolvedDirect(review.id);
    return;
  }

  confirm.require({
    message: `¿Confirmas marcar como resuelta la revisión de la pregunta #${review.pregunta_numero}?`,
    header: 'Confirmar resolución',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-success',
    rejectClass: 'p-button-secondary p-button-outlined',
    acceptLabel: 'Sí, resolver',
    rejectLabel: 'Cancelar',
    accept: async () => {
      await markAsResolvedDirect(review.id);
    }
  });
};

const markAsUnresolved = async (reviewId) => {
  try {
    await api.patch(`/reviews/${reviewId}`, { resuelto: false });
    
    // Actualizar localmente
    const idx = reviews.value.findIndex(r => r.id === reviewId);
    if (idx !== -1) {
      reviews.value[idx].resuelto = false;
    }
    
    // Actualizar stats
    stats.value.pendientes++;
    stats.value.resueltas--;
    
    toast.add({
      severity: 'info',
      summary: 'Revisión reabierta',
      detail: 'La revisión ha sido marcada como pendiente',
      life: 2000
    });
  } catch (error) {
    console.error('Error marking as unresolved:', error);
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudo actualizar la revisión',
      life: 5000
    });
  }
};

const clearFilters = () => {
  filterEstado.value = null;
  filterSede.value = null;
};

const openDetailModal = (review) => {
  selectedReview.value = review;
  showDetailModal.value = true;
};

const closeDetailModal = () => {
  showDetailModal.value = false;
  selectedReview.value = null;
};

const getAreaLabel = (area) => {
  const labels = {
    'MATEMATICAS': 'Matemáticas',
    'LECTURA_CRITICA': 'Lectura Crítica',
    'CIENCIAS_NATURALES': 'Ciencias Naturales',
    'SOCIALES_CIUDADANAS': 'Sociales',
    'INGLES': 'Inglés'
  };
  return labels[area] || area || 'Sin área';
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('es-CO', { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric'
  });
};

// Lifecycle
onMounted(async () => {
  await Promise.all([
    fetchReviews(),
    fetchSedes()
  ]);
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bg-primary {
  background-color: #5a5cf2;
}

.text-primary {
  color: #5a5cf2;
}
</style>
