<template>
  <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden hover:shadow-md transition-all group h-full flex flex-col">
    <!-- Card Header -->
    <div class="p-6 pb-4 flex-1">
      <div class="flex items-start justify-between mb-4">
        <span :class="getAreaBadgeClass(simulacro.area)" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold">
          {{ getAreaLabel(simulacro.area) }}
        </span>
        <div class="flex items-center gap-2">
          <!-- Visibility Badge (Admins Only) -->
          <span v-if="userRole !== 'estudiante'" 
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border"
            :class="simulacro.activo ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border-indigo-100 dark:border-indigo-800' : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-600'"
            :title="simulacro.activo ? 'Visible para estudiantes' : 'Oculto para estudiantes'"
          >
            <span class="material-icons-round text-[12px]">{{ simulacro.activo ? 'visibility' : 'visibility_off' }}</span>
            {{ simulacro.activo ? 'Visible' : 'Oculto' }}
          </span>

          <span :class="getStatusClass(simulacro)" class="inline-flex items-center gap-1 text-xs font-medium">
            <span class="w-2 h-2 rounded-full" :class="getStatusDotClass(simulacro)"></span>
            {{ getStatusLabel(simulacro) }}
          </span>
          <!-- Dropdown Menu (Para admins) -->
          <div v-if="userRole === 'admin' || userRole === 'admin'" class="relative">
            <button 
              @click="toggleMenu"
              class="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
              ref="menuButton"
            >
              <span class="material-icons-round text-[20px]">more_vert</span>
            </button>
            <Menu ref="menu" :model="menuItems" :popup="true" />
          </div>
        </div>
      </div>
      
      <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-2 group-hover:text-primary dark:group-hover:text-primary transition-colors line-clamp-2">
        {{ simulacro.titulo }}
      </h3>
      <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-3 min-h-[40px]">
        {{ simulacro.descripcion || 'Sin descripción' }}
      </p>
    </div>
    
    <!-- Card Stats -->
    <div class="px-6 pb-4">
      <div class="flex items-center gap-6 text-sm text-slate-600 dark:text-slate-400">
        <div class="flex items-center gap-2">
          <span class="material-icons-round text-slate-400 dark:text-slate-500 text-[18px]">help_outline</span>
          <span><strong>{{ simulacro.total_preguntas || 0 }}</strong> preguntas</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="material-icons-round text-slate-400 dark:text-slate-500 text-[18px]">timer</span>
          <span><strong>{{ simulacro.duracion_minutos || 60 }}</strong> min</span>
        </div>
      </div>
    </div>
    
    <!-- Card Meta -->
    <div class="px-6 pb-4">
      <div class="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1">
            <span class="material-icons-round text-[16px]">event</span>
            <span>Creado: {{ formatDate(simulacro.created_at) }}</span>
          </div>
        </div>
        <!-- Badge Creador (Solo para admins) -->
        <span 
          v-if="userRole !== 'estudiante' && simulacro.created_by_nombre"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold truncate max-w-[100px]"
          :class="simulacro.created_by_tipo === 'superadmin' ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'"
          :title="simulacro.created_by_nombre"
        >
          {{ simulacro.created_by_nombre }}
        </span>
      </div>
    </div>
    
    <!-- Card Actions -->
    <div class="px-6 py-4 bg-slate-50 dark:bg-slate-700/30 border-t border-slate-100 dark:border-slate-700 flex items-center gap-3 mt-auto">
      <router-link 
        v-if="userRole === 'estudiante' && activeTab === 'realizado'"
        :to="`/simulacros/${simulacro.id}/revision`"
        class="flex-1 flex items-center justify-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg py-2.5 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 hover:border-slate-300 dark:hover:border-slate-500 transition-colors"
      >
        <span class="material-icons-round text-[18px]">fact_check</span>
        Resultados
      </router-link>
      <router-link 
        v-else-if="userRole === 'estudiante' && simulacro.mi_intento_activo"
        :to="`/simulacros/${simulacro.id}`"
        class="flex-1 flex items-center justify-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg py-2.5 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 hover:border-slate-300 dark:hover:border-slate-500 transition-colors"
      >
        <span class="material-icons-round text-[18px]">play_circle</span>
        Continuar
      </router-link>
      <button
        v-else-if="userRole === 'estudiante' && simulacro.estado === 'finalizado' && !simulacro.mi_intento_activo"
        disabled
        class="flex-1 flex items-center justify-center gap-2 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg py-2.5 text-sm font-medium text-slate-400 dark:text-slate-600 cursor-not-allowed"
      >
        <span class="material-icons-round text-[18px]">lock</span>
        Cerrado
      </button>
      <router-link 
        v-else
        :to="userRole === 'estudiante' ? `/simulacros/${simulacro.id}` : `/simulacros/${simulacro.id}/presentar`"
        class="flex-1 flex items-center justify-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg py-2.5 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 hover:border-slate-300 dark:hover:border-slate-500 transition-colors"
      >
        <span class="material-icons-round text-[18px]">
          {{ userRole === 'estudiante' ? 'play_arrow' : 'visibility' }}
        </span>
        {{ userRole === 'estudiante' ? 'Empezar' : 'Ver' }}
      </router-link>
      
      <router-link 
        v-if="userRole === 'admin'"
        :to="`/simulacros/${simulacro.id}/editar`"
        class="flex items-center justify-center gap-2 bg-primary hover:bg-indigo-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors border border-transparent"
      >
        <span class="material-icons-round text-[18px]">edit</span>
        Editar
      </router-link>
      
      <!-- Botón Editar para Admin IE -->
      <button 
        v-if="userRole === 'admin'"
        @click="$emit('edit', simulacro)"
        class="flex items-center justify-center gap-2 bg-primary hover:bg-indigo-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors border border-transparent"
      >
        <span class="material-icons-round text-[18px]">settings</span>
        Configurar
      </button>
    </div>
  </div>
</template>

<script setup>
import { defineProps, ref } from 'vue';
import Menu from 'primevue/menu';

const props = defineProps({
  simulacro: {
    type: Object,
    required: true
  },
  userRole: {
    type: String,
    default: 'guest'
  },
  activeTab: {
    type: String,
    default: 'pendiente'
  }
});

const emit = defineEmits(['edit', 'delete', 'exportPdf', 'generateAnswerSheets', 'uploadOMR', 'reset']);

import { computed } from 'vue';

// Menu dropdown
const menu = ref(null);

// Menu items dinámico según rol y estado del simulacro
const menuItems = computed(() => {
  const items = [
    {
      label: 'Descargar simulacro',
      icon: 'pi pi-file-pdf',
      class: 'text-rose-600',
      command: () => {
        emit('exportPdf', props.simulacro);
      }
    },
    {
      label: 'Hojas de respuestas',
      icon: 'pi pi-book',
      class: 'text-purple-600',
      command: () => {
        emit('generateAnswerSheets', props.simulacro);
      }
    }
  ];

  // Opción de Subir Evidencias OMR - Solo para admin y simulacros finalizados
  if (props.userRole === 'admin' && props.simulacro.estado === 'finalizado') {
    items.push({
      label: 'Subir evidencias OMR',
      icon: 'pi pi-upload',
      class: 'text-teal-600',
      command: () => {
        emit('uploadOMR', props.simulacro);
      }
    });
    items.push({
      label: 'Reintentar simulacro',
      icon: 'pi pi-refresh',
      class: 'text-amber-600',
      command: () => {
        emit('reset', props.simulacro);
      }
    });
  }

  items.push({ separator: true });

  // Solo admin puede eliminar simulacros
  if (props.userRole === 'admin') {
    items.push({
      label: 'Eliminar',
      icon: 'pi pi-trash',
      class: 'text-red-600',
      command: () => {
        emit('delete', props.simulacro);
      }
    });
  }

  return items;
});

const toggleMenu = (event) => {
  menu.value.toggle(event);
};

// Helpers de presentación
const getAreaLabel = (area) => {
  const labels = {
    'MATEMATICAS': 'Matemáticas',
    'LECTURA_CRITICA': 'Lectura Crítica',
    'CIENCIAS_NATURALES': 'Ciencias Nat.',
    'SOCIALES_CIUDADANAS': 'Sociales',
    'INGLES': 'Inglés'
  };
  return labels[area] || area || 'Sin área';
};

const getAreaBadgeClass = (area) => {
  const classes = {
    'MATEMATICAS': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
    'LECTURA_CRITICA': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    'CIENCIAS_NATURALES': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
    'SOCIALES_CIUDADANAS': 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300',
    'INGLES': 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300'
  };
  return classes[area] || 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
};

const getStatusLabel = (simulacro) => {
  if (props.userRole.toLowerCase() === 'estudiante' && props.activeTab === 'realizado') return 'Finalizado';
  const labels = {
    'activo': 'Activo',
    'finalizado': 'Finalizado'
  };
  return labels[simulacro.estado] || 'Desconocido';
};

const getStatusClass = (simulacro) => {
  if (props.userRole.toLowerCase() === 'estudiante' && props.activeTab === 'realizado') return 'text-primary dark:text-indigo-400';
  const classes = {
    'activo': 'text-emerald-600 dark:text-emerald-400',
    'finalizado': 'text-slate-400 dark:text-slate-500'
  };
  return classes[simulacro.estado] || 'text-slate-400 dark:text-slate-500';
};

const getStatusDotClass = (simulacro) => {
  if (props.userRole.toLowerCase() === 'estudiante' && props.activeTab === 'realizado') return 'bg-primary dark:bg-indigo-400';
  const classes = {
    'activo': 'bg-emerald-500',
    'finalizado': 'bg-slate-300 dark:bg-slate-600'
  };
  return classes[simulacro.estado] || 'bg-slate-300 dark:bg-slate-600';
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
};
</script>
