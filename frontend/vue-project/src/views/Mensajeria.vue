<template>
  <div class="flex h-full gap-4">
    <Toast />

    <!-- Sidebar -->
    <div class="w-80 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl flex flex-col shadow-sm overflow-hidden">
      <div class="p-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
        <h2 class="font-bold text-slate-800 dark:text-white mb-2">Mensajería</h2>
        <button
          @click="openNewChatModal"
          class="w-full bg-primary hover:bg-indigo-600 text-white py-2 px-3 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
          :disabled="loadingChats"
        >
          <span class="material-icons-round text-lg">add_comment</span>
          Nueva conversación
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div v-if="loadingChats" class="flex flex-col items-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>

        <div v-else-if="chats.length === 0" class="p-6 text-center text-slate-500 text-sm">
          No hay conversaciones. Inicia una nueva.
        </div>

        <div v-else class="flex flex-col">
          <div
            v-for="chat in chats"
            :key="chat.id"
            @click="selectChat(chat)"
            class="p-4 border-b border-slate-50 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer transition-colors"
            :class="{ 'bg-indigo-50 dark:bg-indigo-900/20': selectedChat?.id === chat.id }"
          >
            <div class="flex justify-between items-start mb-1">
              <h4 class="font-semibold text-sm text-slate-900 dark:text-slate-100 truncate pr-2">
                {{ chat.otro_participante_nombre }}
              </h4>
              <div class="flex flex-col items-end gap-1">
                <span class="text-[10px] text-slate-400 whitespace-nowrap">{{ formatDate(chat.ultimo_mensaje_at) }}</span>
                <span v-if="chat.mensajes_nuevos > 0" class="min-w-5 h-5 px-1 inline-flex items-center justify-center rounded-full bg-rose-500 text-white text-[10px] font-bold">
                  {{ chat.mensajes_nuevos }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <p class="text-xs text-slate-500 dark:text-slate-400 truncate">{{ chat.ultimo_mensaje || '...' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl flex flex-col shadow-sm overflow-hidden">
      <div v-if="!selectedChat" class="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
        <span class="material-icons-round text-6xl mb-4 text-slate-200 dark:text-slate-700">forum</span>
        <p class="text-lg font-medium text-slate-600 dark:text-slate-300">Selecciona una conversación</p>
        <p class="text-sm">O inicia una nueva desde el menú lateral.</p>
      </div>

      <template v-else>
        <div class="p-4 border-b border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-between shadow-sm z-10">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900 dark:to-purple-900 flex items-center justify-center text-indigo-700 dark:text-indigo-300 font-bold">
              {{ selectedChat.otro_participante_nombre?.substring(0, 2).toUpperCase() }}
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white text-sm">{{ selectedChat.otro_participante_nombre }}</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                {{ selectedChat.otro_participante_rol === 'admin' ? 'Directivo' : 'Docente' }}
                <span v-if="selectedChat.otro_participante_sede"> · {{ selectedChat.otro_participante_sede }}</span>
              </p>
            </div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-900/50" ref="messagesContainer">
          <div v-if="loadingMessages" class="flex justify-center py-4">
            <span class="animate-spin h-6 w-6 border-2 border-primary rounded-full border-t-transparent"></span>
          </div>

          <div v-for="msg in messages" :key="msg.id" class="flex flex-col gap-1" :class="{ 'items-end': isMine(msg), 'items-start': !isMine(msg) }">
            <div
              class="max-w-[75%] px-4 py-3 rounded-2xl text-sm shadow-sm relative group"
              :class="[
                isMine(msg)
                  ? 'bg-primary text-white rounded-tr-none'
                  : 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white rounded-tl-none border border-slate-200 dark:border-slate-600'
              ]"
            >
              <p v-if="msg.contenido" class="whitespace-pre-wrap leading-relaxed">{{ msg.contenido }}</p>
              <img
                v-if="msg.imagen_adjunto"
                :src="msg.imagen_adjunto"
                class="max-w-full max-h-64 rounded-lg mt-1 cursor-pointer object-contain"
                @click="openImagePreview(msg.imagen_adjunto)"
              />
              <span
                class="text-[10px] absolute bottom-1 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                :class="isMine(msg) ? 'text-indigo-200' : 'text-slate-400'"
              >
                {{ formatTime(msg.created_at) }}
              </span>
            </div>
          </div>

          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center text-slate-400">
            <span class="material-icons-round text-5xl mb-3 text-slate-200 dark:text-slate-700">chat_bubble_outline</span>
            <p class="text-sm">Envía un mensaje para empezar la conversación</p>
          </div>
        </div>

        <div class="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
          <!-- Pending image preview -->
          <div v-if="pendingImage" class="mb-2 flex items-center gap-2 p-2 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
            <img :src="pendingImage" class="h-12 w-12 rounded-lg object-cover border border-slate-200 dark:border-slate-600" />
            <div class="flex-1 min-w-0">
              <p class="text-xs text-slate-600 dark:text-slate-400 truncate">Imagen adjunta</p>
            </div>
            <button
              @click="pendingImage = null"
              class="p-1 text-slate-400 hover:text-rose-500 rounded transition-colors"
            >
              <span class="material-icons-round text-[18px]">close</span>
            </button>
          </div>

          <div class="flex items-end gap-2 bg-slate-100 dark:bg-slate-900 p-2 rounded-xl border border-slate-200 dark:border-slate-600 focus-within:ring-2 focus-within:ring-primary/50 transition-all">
            <button
              class="p-2 text-slate-400 hover:text-primary hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors flex-shrink-0"
              title="Adjuntar imagen"
              @click="triggerFileInput"
            >
              <span class="material-icons-round transform rotate-90">attachment</span>
            </button>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onFileSelected"
            />
            <textarea
              ref="messageInputRef"
              v-model="newMessage"
              @keydown.enter.prevent="sendMessage"
              placeholder="Escribe un mensaje..."
              class="w-full bg-transparent border-none focus:ring-0 text-sm max-h-32 min-h-[44px] py-3 text-slate-700 dark:text-gray-200 resize-none"
              rows="1"
            ></textarea>

            <button
              @click="sendMessage"
              :disabled="sending || (!newMessage.trim() && !pendingImage)"
              class="p-2 bg-primary hover:bg-indigo-600 disabled:opacity-50 disabled:bg-slate-300 text-white rounded-lg shadow-sm transition-all flex-shrink-0"
            >
              <span v-if="sending" class="animate-spin h-5 w-5 border-2 border-white rounded-full border-t-transparent"></span>
              <span v-else class="material-icons-round">send</span>
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Modal Nueva Conversación -->
    ...
    <div v-if="showNewChatModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="showNewChatModal = false"></div>
      <div class="relative w-full max-w-md bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-700/50">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white">Nueva conversación</h3>
          <button @click="showNewChatModal = false" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <span class="material-icons-round">close</span>
          </button>
        </div>

        <div class="p-4">
          <div class="relative mb-3">
            <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <span class="material-icons-round text-[20px]">search</span>
            </span>
            <input
              v-model="userSearchQuery"
              type="text"
              placeholder="Buscar por nombre o email..."
              class="pl-10 w-full h-[42px] rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            />
          </div>

          <div class="max-h-64 overflow-y-auto space-y-1">
            <div v-if="loadingUsers" class="flex justify-center py-4">
              <span class="animate-spin h-5 w-5 border-2 border-primary rounded-full border-t-transparent"></span>
            </div>

            <div v-else-if="filteredAvailableUsers.length === 0" class="text-center py-4 text-slate-400 text-sm">
              No se encontraron usuarios
            </div>

            <button
              v-for="user in filteredAvailableUsers"
              :key="user.id"
              @click="startChatWith(user)"
              class="w-full text-left px-4 py-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-3"
            >
              <div class="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm shrink-0">
                {{ user.nombre?.charAt(0).toUpperCase() }}
              </div>
              <div class="min-w-0">
                <p class="text-sm font-medium text-slate-800 dark:text-white truncate">{{ user.nombre }}</p>
                <p class="text-xs text-slate-500 dark:text-slate-400 truncate">
                  {{ user.rol === 'admin' ? 'Directivo' : 'Docente' }}
                  <span v-if="user.sede_nombre"> · {{ user.sede_nombre }}</span>
                </p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <div v-if="imagePreviewSrc" class="fixed inset-0 z-50 flex items-center justify-center p-4" @click="imagePreviewSrc = null">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm"></div>
      <img :src="imagePreviewSrc" class="relative max-w-full max-h-[90vh] rounded-xl shadow-2xl object-contain" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useNotificacionesStore } from '../stores/notificaciones';
import api from '../api/axios';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { format } from 'date-fns';
import { useRoute } from 'vue-router';

const authStore = useAuthStore();
const notificacionesStore = useNotificacionesStore();
const route = useRoute();
const toast = useToast();
const userId = computed(() => authStore.user?.id);

// State
const chats = ref([]);
const selectedChat = ref(null);
const messages = ref([]);
const loadingChats = ref(false);
const loadingMessages = ref(false);
const sending = ref(false);
const newMessage = ref('');
const messagesContainer = ref(null);
const messageInputRef = ref(null);
const fileInputRef = ref(null);
const imagePreviewSrc = ref(null);
const pendingImage = ref(null);
let pingInterval = null;

// New chat modal
const showNewChatModal = ref(false);
const userSearchQuery = ref('');
const availableUsers = ref([]);
const loadingUsers = ref(false);

const filteredAvailableUsers = computed(() => {
  if (!userSearchQuery.value) return availableUsers.value;
  const q = userSearchQuery.value.toLowerCase();
  return availableUsers.value.filter(u =>
    u.nombre?.toLowerCase().includes(q) ||
    u.email?.toLowerCase().includes(q)
  );
});

// --- Chat selection ---
const selectChat = async (chat) => {
  selectedChat.value = chat;
  loadingMessages.value = true;
  messages.value = [];
  try {
    const res = await api.get(`/mensajeria/conversaciones/${chat.id}/mensajes`);
    messages.value = res.data;
    scrollToBottom();
    await marcarNuevosComoLeidos(chat.id);
    startPing(chat.id);
  } catch (e) {
    console.error(e);
  } finally {
    loadingMessages.value = false;
  }
};

const marcarNuevosComoLeidos = async (conversacionId) => {
  try {
    await api.post(`/mensajeria/conversaciones/${conversacionId}/marcar-nuevos-como-leidos`);
    const chatLocal = chats.value.find(c => c.id === conversacionId);
    if (chatLocal) chatLocal.mensajes_nuevos = 0;
    if (selectedChat.value?.id === conversacionId) selectedChat.value.mensajes_nuevos = 0;
    await notificacionesStore.fetchUnreadCount();
  } catch (e) {
    console.error(e);
  }
};

// --- Ping ---
const startPing = (conversacionId) => {
  stopPing();
  pingInterval = setInterval(() => {
    api.post(`/mensajeria/conversaciones/${conversacionId}/ping`).catch(() => {});
  }, 30000);
};

const stopPing = () => {
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }
};

// --- Fetch chats ---
const fetchChats = async () => {
  loadingChats.value = true;
  try {
    const res = await api.get('/mensajeria/conversaciones');
    chats.value = res.data;
  } catch (e) {
    console.error(e);
  } finally {
    loadingChats.value = false;
  }
};

// --- New chat ---
const openNewChatModal = async () => {
  showNewChatModal.value = true;
  loadingUsers.value = true;
  userSearchQuery.value = '';
  try {
    const res = await api.get('/mensajeria/usuarios-disponibles');
    availableUsers.value = res.data;
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los usuarios', life: 3000 });
  } finally {
    loadingUsers.value = false;
  }
};

const startChatWith = async (user) => {
  showNewChatModal.value = false;
  try {
    const res = await api.post('/mensajeria/enviar', {
      destinatario_id: user.id,
      contenido: '👋 Hola',
    });

    await fetchChats();
    const chat = chats.value.find(c => c.otro_participante_id === user.id);
    if (chat) await selectChat(chat);
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo iniciar la conversación', life: 3000 });
  }
};

// --- File attachment ---
const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const onFileSelected = (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    pendingImage.value = reader.result;
  };
  reader.readAsDataURL(file);
  e.target.value = '';
};

const openImagePreview = (src) => {
  imagePreviewSrc.value = src;
};

// --- Send message ---
const sendMessage = async () => {
  if ((!newMessage.value.trim() && !pendingImage.value) || !selectedChat.value) return;

  const content = newMessage.value;
  const image = pendingImage.value;
  newMessage.value = '';
  pendingImage.value = null;
  sending.value = true;

  try {
    const payload = {
      conversacion_id: selectedChat.value.id,
      contenido: content || null,
    };
    if (image) payload.imagen_adjunto = image;

    const res = await api.post('/mensajeria/enviar', payload);

    messages.value.push(res.data);
    scrollToBottom();

    const chatIdx = chats.value.findIndex(c => c.id === selectedChat.value.id);
    if (chatIdx !== -1) {
      chats.value[chatIdx].ultimo_mensaje = content;
      chats.value[chatIdx].ultimo_mensaje_at = new Date().toISOString();
      const c = chats.value.splice(chatIdx, 1)[0];
      chats.value.unshift(c);
    }
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Fallo el envío', life: 3000 });
    newMessage.value = content;
    pendingImage.value = image;
  } finally {
    sending.value = false;
    await nextTick();
    messageInputRef.value?.focus();
  }
};

const isMine = (msg) => msg.remitente_id === userId.value;

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try { return format(new Date(dateStr), 'dd/MM HH:mm'); } catch { return ''; }
};

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  try { return format(new Date(dateStr), 'HH:mm'); } catch { return ''; }
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// --- Route query ---
const openChatFromRouteQuery = async () => {
  const raw = route.query.conversacion_id;
  const parsed = Number(Array.isArray(raw) ? raw[0] : raw);
  if (!Number.isInteger(parsed) || parsed <= 0) return;

  let chat = chats.value.find(c => c.id === parsed);
  if (!chat) {
    await fetchChats();
    chat = chats.value.find(c => c.id === parsed);
  }
  if (chat && selectedChat.value?.id !== chat.id) {
    await selectChat(chat);
  }
};

watch(() => route.query.conversacion_id, () => {
  openChatFromRouteQuery();
});

onMounted(async () => {
  await fetchChats();
  await openChatFromRouteQuery();
});

onBeforeUnmount(() => {
  stopPing();
});
</script>

<style scoped>
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 20px; }
.dark ::-webkit-scrollbar-thumb { background-color: #475569; }
.bg-primary { background-color: #6366f1; }
.animate-in { animation-fill-mode: both; }
.fade-in { animation-name: fadeIn; }
.zoom-in-95 { animation-name: zoomIn95; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes zoomIn95 { from { transform: scale(0.95); } to { transform: scale(1); } }
</style>
