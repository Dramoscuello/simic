import { defineStore } from 'pinia';
import { ref } from 'vue';

import api from '../api/axios';
import { useAuthStore } from './auth';

const ALLOWED_ROLES = ['admin', 'docente'];

export const useNotificacionesStore = defineStore('notificaciones', () => {
  const items = ref([]);
  const unreadCount = ref(0);
  const isOpen = ref(false);
  const loading = ref(false);
  const error = ref(null);
  const lastFetchAt = ref(null);

  let pollingTimer = null;

  const canUseNotifications = () => {
    const authStore = useAuthStore();
    const role = authStore.user?.rol?.nombre;
    return ALLOWED_ROLES.includes(role);
  };

  const resetState = () => {
    items.value = [];
    unreadCount.value = 0;
    isOpen.value = false;
    loading.value = false;
    lastFetchAt.value = null;
  };

  const fetchUnreadCount = async () => {
    if (!canUseNotifications()) {
      resetState();
      return 0;
    }

    try {
      const res = await api.get('/notificaciones/unread-count');
      unreadCount.value = res.data?.unread_count || 0;
      lastFetchAt.value = new Date().toISOString();
      return unreadCount.value;
    } catch (error) {
      console.error('Error obteniendo contador de notificaciones', error);
      return unreadCount.value;
    }
  };

  const fetchNotifications = async ({ includeRead = false, limit = 20, offset = 0 } = {}) => {
    if (!canUseNotifications()) {
      resetState();
      return [];
    }

    loading.value = true;
    error.value = null;
    try {
      // IMPORTANT: Add trailing slash to avoid 307 Redirect which loses /api prefix behind Nginx
      const res = await api.get('/notificaciones/', {
        params: {
          include_read: includeRead,
          limit,
          offset,
        },
      });
      items.value = Array.isArray(res.data) ? res.data : [];
      lastFetchAt.value = new Date().toISOString();
      return items.value;
    } catch (err) {
      console.error('Error obteniendo notificaciones', err);
      error.value = 'No se pudieron cargar las notificaciones.';
      return [];
    } finally {
      loading.value = false;
    }
  };

  const markAsRead = async (notificationId) => {
    const index = items.value.findIndex((n) => n.id === notificationId);
    const previous = index >= 0 ? items.value[index] : null;

    if (index >= 0) {
      items.value.splice(index, 1);
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    }

    try {
      await api.patch(`/notificaciones/${notificationId}/read`);
      return true;
    } catch (error) {
      console.error('Error marcando notificación como leída', error);
      if (previous) {
        items.value.splice(index >= 0 ? index : 0, 0, previous);
        unreadCount.value += 1;
      }
      return false;
    }
  };

  const markAllAsRead = async () => {
    if (!canUseNotifications()) {
      resetState();
      return 0;
    }

    try {
      const res = await api.post('/notificaciones/read-all');
      const updatedCount = res.data?.updated_count || 0;
      items.value = [];
      unreadCount.value = 0;
      return updatedCount;
    } catch (error) {
      console.error('Error marcando todas las notificaciones como leídas', error);
      return 0;
    }
  };

  const setIsOpen = (value) => {
    isOpen.value = value;
  };

  const stopPolling = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
  };

  const startPolling = (intervalMs = 30000) => {
    stopPolling();
    if (!canUseNotifications()) {
      resetState();
      return;
    }

    fetchUnreadCount();
    pollingTimer = setInterval(() => {
      fetchUnreadCount();
    }, intervalMs);
  };

  return {
    items,
    unreadCount,
    isOpen,
    loading,
    lastFetchAt,
    fetchUnreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    setIsOpen,
    startPolling,
    stopPolling,
    resetState,
    error
  };
});
