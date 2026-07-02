<template>
  <header class="relative z-20 flex h-16 w-full items-center justify-between border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-8 py-3 shadow-sm transition-colors duration-300">
    <div class="flex items-center gap-4">
      <!-- Mobile Menu Button -->
      <button 
        @click="$emit('toggle-sidebar')" 
        class="lg:hidden p-2 -ml-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
      >
        <span class="material-icons-round">menu</span>
      </button>
      <h2 class="text-xl font-bold text-slate-800 dark:text-white tracking-tight">{{ title }}</h2>
    </div>
    <div class="flex items-center gap-6">
      <div v-if="canShowNotifications" class="relative" ref="notificationRoot">
        <button
          @click="toggleNotifications"
          class="relative flex h-9 w-9 items-center justify-center rounded-full bg-slate-50 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          title="Notificaciones"
        >
          <span class="material-icons-round text-[22px]">notifications</span>
          <span
            v-if="notificationCount > 0"
            class="absolute -right-1 -top-1 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-[10px] text-white flex items-center justify-center"
          >
            {{ notificationCount > 99 ? '99+' : notificationCount }}
          </span>
        </button>

        <div
          v-if="isNotificationsOpen"
          class="absolute right-0 mt-3 w-[360px] max-h-[420px] overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-2xl z-[1100]"
        >
          <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-slate-800 dark:text-white">Notificaciones</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">No leídas: {{ notificationCount }}</p>
            </div>
            <button
              v-if="notificationCount > 0"
              @click="handleMarkAllRead"
              class="text-xs font-medium text-primary hover:underline"
            >
              Marcar todo
            </button>
          </div>

          <div v-if="notificationsLoading" class="p-6 text-center text-slate-500 dark:text-slate-400">
            Cargando...
          </div>

          <div v-else-if="notificationsError" class="p-6 text-center text-red-500 text-sm">
            <span class="block material-icons-round text-2xl mb-2">error_outline</span>
            {{ notificationsError }}
          </div>

          <div v-else-if="notifications.length === 0" class="p-6 text-center text-slate-500 dark:text-slate-400 text-sm">
            No tienes notificaciones pendientes.
          </div>

          <div v-else class="max-h-[340px] overflow-y-auto">
            <button
              v-for="notification in notifications"
              :key="notification.id"
              @click="handleNotificationClick(notification)"
              class="w-full text-left px-4 py-3 border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
            >
              <p class="text-sm font-semibold text-slate-800 dark:text-white">{{ notification.titulo }}</p>
              <p class="text-xs text-slate-600 dark:text-slate-300 mt-1">{{ notification.mensaje }}</p>
              <p class="text-[11px] text-slate-400 mt-1">{{ formatNotificationDate(notification.created_at) }}</p>
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="canShowNotifications" class="h-8 w-[1px] bg-slate-200 dark:bg-slate-700"></div>
      
      <!-- Dark Mode Toggle -->
      <button
        @click="toggleDarkMode"
        class="p-2 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors focus:outline-none"
        :title="isDark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
      >
        <span class="material-icons-round text-xl" v-if="!isDark">dark_mode</span>
        <span class="material-icons-round text-xl" v-else>light_mode</span>
      </button>

    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: 'Dashboard'
  },
  notificationCount: {
    type: Number,
    default: 0
  },
  notifications: {
    type: Array,
    default: () => []
  },
  notificationsLoading: {
    type: Boolean,
    default: false
  },
  notificationsError: {
    type: String,
    default: null
  },
  canShowNotifications: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits([
  'toggle-sidebar',
  'open-notifications',
  'notification-click',
  'notification-mark-all-read'
]);

// Dark mode logic
const isDark = ref(false);
const isNotificationsOpen = ref(false);
const notificationRoot = ref(null);

const toggleDarkMode = () => {
  isDark.value = !isDark.value;
  if (isDark.value) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  localStorage.setItem('darkMode', isDark.value ? 'true' : 'false');
};

const toggleNotifications = () => {
  isNotificationsOpen.value = !isNotificationsOpen.value;
  if (isNotificationsOpen.value) {
    emit('open-notifications');
  }
};

const handleNotificationClick = (notification) => {
  emit('notification-click', notification);
  isNotificationsOpen.value = false;
};

const handleMarkAllRead = () => {
  emit('notification-mark-all-read');
};

const handleOutsideClick = (event) => {
  if (!notificationRoot.value) return;
  if (!notificationRoot.value.contains(event.target)) {
    isNotificationsOpen.value = false;
  }
};

const formatNotificationDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

onMounted(() => {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode === 'true') {
    isDark.value = true;
    document.documentElement.classList.add('dark');
  } else {
    isDark.value = false;
    document.documentElement.classList.remove('dark');
  }

  document.addEventListener('click', handleOutsideClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick);
});
</script>

<style scoped>
/* No specific styles needed as we use Tailwind classes */
</style>
