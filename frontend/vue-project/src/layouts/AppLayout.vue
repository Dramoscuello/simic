<template>
  <div class="font-sans bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 antialiased overflow-hidden transition-colors duration-300">
    <div class="flex h-screen w-full">
      <!-- Sidebar Centralizado -->
      <!-- Mobile Overlay -->
      <div 
        v-if="isSidebarOpen" 
        @click="isSidebarOpen = false"
        class="fixed inset-0 z-30 bg-slate-900/50 backdrop-blur-sm lg:hidden transition-opacity"
      ></div>

      <!-- Sidebar Centralizado -->
      <AppSidebar
        class="fixed inset-y-0 left-0 z-40 lg:static transform transition-transform duration-300 lg:transform-none shadow-xl lg:shadow-none"
        :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
        :userName="userName"
        :userRole="userRoleLabel"
        :institutionName="userInstitutionName"
        :navigationGroups="navigationGroups"
        @logout="logout"
        @close-mobile="isSidebarOpen = false"
      />
      
      <!-- Main Content Centralizado -->
      <main class="flex h-full flex-1 flex-col overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-300">
        <!-- Header Centralizado -->
        <AppHeader
          :title="headerTitle"
          :userName="userName"
          searchPlaceholder="Buscar..."
          :notificationCount="notificacionesStore.unreadCount"
          :notifications="notificacionesStore.items"
          :notificationsLoading="notificacionesStore.loading"
          :notificationsError="notificacionesStore.error"
          :canShowNotifications="canShowNotifications"
          @toggle-sidebar="isSidebarOpen = !isSidebarOpen"
          @open-notifications="handleOpenNotifications"
          @notification-click="handleNotificationClick"
          @notification-mark-all-read="handleMarkAllRead"
        />
        
        <!-- Aquí se cargan las vistas hijas (Dashboard, Simulacros, etc) -->
         <div class="flex-1 overflow-y-auto p-8">
             <router-view v-slot="{ Component }">
                 <component :is="Component" />
             </router-view>
         </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useNotificacionesStore } from '../stores/notificaciones';
import { useRouter, useRoute } from 'vue-router';
import AppSidebar from '../components/layout/AppSidebar.vue';
import AppHeader from '../components/layout/AppHeader.vue';

const authStore = useAuthStore();
const notificacionesStore = useNotificacionesStore();
const router = useRouter();
const route = useRoute();

const isSidebarOpen = ref(false);

// Cerrar sidebar al cambiar de ruta en móvil
watch(() => route.path, () => {
    isSidebarOpen.value = false;
});

// --- Lógica Centralizada de Usuario ---
const userName = computed(() => {
  return authStore.user?.nombre || authStore.user?.email || 'Usuario';
});

const userInstitutionName = computed(() => {
    return authStore.user?.institucion?.nombre || '';
});

const userRole = computed(() => authStore.user?.rol?.nombre || 'guest');
const canShowNotifications = computed(() => ['admin', 'docente'].includes(userRole.value));

const userRoleLabel = computed(() => {
    const map = {
        'admin': 'Admin institucional',
        'docente': 'Docente',
        'estudiante': 'Estudiante'
    };
    return map[userRole.value] || userRole.value;
});

// --- Lógica Centralizada de Título ---
const headerTitle = computed(() => {
    // Si la ruta tiene un título estático, úsalo
    if (route.meta.title) return route.meta.title;
    
    // Header especial para Dashboard
    if (route.name === 'Dashboard') {
         return userInstitutionName.value ? `Bienvenido, ${userInstitutionName.value}` : 'Panel de control';
    }
    
    return 'Plataforma ICFES';
});

// --- Lógica Centralizada de Menú ---
const navigationGroups = computed(() => {
  const role = userRole.value;
  
  // Grupo General
  const generalItems = [
     { to: '/dashboard', icon: 'dashboard', label: 'Dashboard' }
  ];
  
  // Reportes y Análisis para Admin y Docente
  if (role === 'admin' || role === 'docente') {
      generalItems.push({ to: '/reportes', icon: 'bar_chart', label: 'Reportes' });
      generalItems.push({ to: '/analisis', icon: 'account_tree', label: 'Análisis' });
  }

  // Mensajería para Admin y Docente
  if (role === 'admin' || role === 'docente') {
      generalItems.push({ to: '/mensajeria', icon: 'forum', label: 'Mensajería' });
  }

  const groups = [
    {
      title: 'General',
      items: generalItems
    }
  ];

  if (role === 'admin') {
    groups.push({
      title: 'Gestión administrativa',
      items: [
        { to: '/crear-usuario', icon: 'person_add', label: 'Gestión de usuarios' }
      ]
    });

    const academicItems = [
        { to: '/mi-institucion', icon: 'school', label: 'Mi institución' },
        { to: '/grupos', icon: 'group_work', label: 'Grupos' },
        { to: '/estudiantes', icon: 'groups', label: 'Estudiantes' },
        { to: '/simulacros', icon: 'assignment', label: 'Simulacros' },
        { to: '/revisiones', icon: 'flag', label: 'Revisión de preguntas' },
        { to: '/inspeccion', icon: 'policy', label: 'Inspección de fraude' }
    ];

    groups.push({
      title: 'Gestión académica',
      items: academicItems
    });
  } else if (role === 'docente') {
    groups.push({
      title: 'Seguimiento',
      items: [
        { to: '/simulacros', icon: 'assignment', label: 'Simulacros' }
      ]
    });
  } else if (role === 'estudiante') {
    groups.push({
      title: 'Mi aprendizaje',
      items: [
        { to: '/simulacros', icon: 'assignment', label: 'Mis simulacros' }
      ]
    });
  }

  groups.push({
    title: 'Sistema',
    items: [
      { to: '/perfil', icon: 'person', label: 'Perfil' }
    ]
  });
  
  return groups;
});

const logout = () => {
  notificacionesStore.stopPolling();
  notificacionesStore.resetState();
  authStore.logout();
  router.push('/login');
};

const handleOpenNotifications = async () => {
  if (!canShowNotifications.value) return;
  notificacionesStore.setIsOpen(true);
  await notificacionesStore.fetchNotifications({ includeRead: false, limit: 20, offset: 0 });
};

const handleMarkAllRead = async () => {
  await notificacionesStore.markAllAsRead();
};

const handleNotificationClick = async (notification) => {
  if (!notification?.id) return;

  const marked = await notificacionesStore.markAsRead(notification.id);
  if (!marked) return;

  const payload = notification.payload_json || {};
  if (notification.tipo === 'mensaje_nuevo') {
    const conversacionId = payload.conversacion_id;
    if (conversacionId) {
      await router.push({
        path: '/mensajeria',
        query: { conversacion_id: String(conversacionId) }
      });
    } else {
      await router.push('/mensajeria');
    }
    return;
  }

  // Puedes agregar aquí otros manejos de notificación si son necesarios
};

watch(
  canShowNotifications,
  async (enabled) => {
    if (enabled) {
      notificacionesStore.startPolling(30000);
      await notificacionesStore.fetchUnreadCount();
      return;
    }

    notificacionesStore.stopPolling();
    notificacionesStore.resetState();
  },
  { immediate: true }
);

onUnmounted(() => {
  notificacionesStore.stopPolling();
});
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}
</style>
