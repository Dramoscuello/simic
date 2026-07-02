<template>
  <div class="w-full">
    <!-- Student Dashboard Strategy -->
    <DashboardEstudiante v-if="userRole === 'estudiante'" />
    
    <!-- Admin Institución / Docente Dashboard Strategy (360°) -->
    <DashboardAdminInstitucion v-else-if="userRole === 'admin' || userRole === 'docente'" />
    
    <!-- Fallback for other roles -->
    <div v-else class="mx-auto flex w-full max-w-7xl flex-col gap-8 items-center justify-center py-16">
      <div class="text-center">
        <span class="material-icons-round text-6xl text-slate-300 dark:text-slate-600 mb-4">dashboard</span>
        <h2 class="text-xl font-bold text-slate-700 dark:text-slate-300 mb-2">Dashboard</h2>
        <p class="text-slate-500 dark:text-slate-400">Bienvenido al sistema SIMIC</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue';
import { useAuthStore } from '../stores/auth';

const DashboardEstudiante = defineAsyncComponent(() => import('./DashboardEstudiante.vue'));
const DashboardAdminInstitucion = defineAsyncComponent(() => import('@/components/dashboard/DashboardAdminInstitucion.vue'));

const authStore = useAuthStore();
const userRole = computed(() => authStore.user?.rol?.nombre || 'guest');
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}

.bg-primary {
  background-color: #6366f1;
}

.text-primary {
  color: #6366f1;
}
</style>
