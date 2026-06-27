<template>
  <div class="node-shell" :class="{ 'student-shell': isStudent }">
    <div v-if="!isStudent" class="node-head">
      <span class="material-icons-round node-icon">{{ icon }}</span>
      <span class="node-type">{{ typeLabel }}</span>
      <span v-if="data.loading" class="spinner"></span>
    </div>
    <div class="node-title" :class="{ 'student-title': isStudent }">{{ data.label }}</div>
    <div v-if="subtitle && !isStudent" class="node-subtitle">{{ subtitle }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const typeMap = {
  group: { label: 'Grupo', icon: 'groups' },
  student_cluster: { label: 'Estudiantes', icon: 'view_list' },
  student: { label: 'Estudiante', icon: 'school' },
  area: { label: 'Área', icon: 'analytics' },
  competencia: { label: 'Competencia', icon: 'workspace_premium' },
};

const entityType = computed(() => props.data?.entityType || 'group');
const isStudent = computed(() => entityType.value === 'student');

const typeLabel = computed(() => typeMap[entityType.value]?.label || 'Nodo');
const icon = computed(() => typeMap[entityType.value]?.icon || 'hub');

const subtitle = computed(() => {
  const meta = props.data?.meta || {};
  if (entityType.value === 'group') {
    return `${meta.estudiantes || 0} estudiantes`;
  }
  if (entityType.value === 'student_cluster') {
    const total = meta.total || 0;
    return total === 1 ? '1 disponible' : `${total} disponibles`;
  }
  if (entityType.value === 'area') {
    const intentos = meta.intentos || 0;
    const promedio = meta.promedio ?? null;
    if (promedio === null) return `${intentos} intentos`;
    return `${intentos} intentos · ${Number(promedio).toFixed(1)}%`;
  }
  if (entityType.value === 'competencia') {
    const promedio = meta.promedio ?? null;
    if (promedio === null) return '';
    return `Promedio ${Number(promedio).toFixed(1)}%`;
  }
  return '';
});
</script>

<style scoped>
.node-shell {
  width: 100%;
  min-width: 210px;
  max-width: 260px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.student-shell {
  padding: 10px 12px;
}

.node-head {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 6px;
  width: 100%;
}

.node-icon {
  font-size: 16px;
  color: #475569;
}

.node-type {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.node-title {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
  width: 100%;
}

.student-title {
  font-size: 15px;
  line-height: 1.3;
}

.node-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #475569;
  width: 100%;
}

.spinner {
  margin-left: 4px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(99, 102, 241, 0.25);
  border-top-color: #6366f1;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
