<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-6">
    <Toast />

    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Gestión de usuarios</h2>
        <p class="text-slate-500 dark:text-slate-400">Administra docentes y directivos de la plataforma</p>
      </div>
      <button
        @click="openCreateModal"
        class="flex items-center justify-center gap-2 bg-primary hover:bg-indigo-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shadow-sm"
      >
        <span class="material-icons-round text-[20px]">add</span>
        Crear usuario
      </button>
    </div>

    <!-- Filters -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
      <div class="relative">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
          <span class="material-icons-round text-[20px]">search</span>
        </span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Buscar por nombre o email..."
          class="pl-10 w-full h-[42px] rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all placeholder-slate-400 dark:placeholder-slate-500"
        />
      </div>

      <div>
        <Select
          v-model="selectedRole"
          :options="roleFilterOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Filtrar por rol"
          class="w-full"
          showClear
          :pt="selectPt"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <!-- Table -->
    <div v-else class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm text-left text-slate-600 dark:text-slate-300">
          <thead class="bg-slate-50 dark:bg-slate-700/50 text-xs uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th class="px-6 py-4">Nombre</th>
              <th class="px-6 py-4">Email</th>
              <th class="px-6 py-4">Rol</th>
              <th class="px-6 py-4">Sede</th>
              <th class="px-6 py-4 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr
              v-for="user in filteredUsers"
              :key="user.id"
              class="hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 transition-colors"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-300 font-bold border border-slate-200 dark:border-slate-600">
                    {{ getInitials(user.nombre) }}
                  </div>
                  <span class="font-semibold text-slate-900 dark:text-white">{{ user.nombre }}</span>
                </div>
              </td>
              <td class="px-6 py-4">{{ user.email || 'N/A' }}</td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                  :class="user.rol?.nombre === 'admin' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300' : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'"
                >
                  {{ user.rol?.nombre === 'admin' ? 'Directivo' : 'Docente' }}
                </span>
              </td>
              <td class="px-6 py-4 text-slate-500 dark:text-slate-400">{{ user.sede?.nombre || '—' }}</td>
              <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button
                    @click="openEditModal(user)"
                    class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    title="Editar"
                  >
                    <span class="material-icons-round text-[20px]">edit</span>
                  </button>
                  <button
                    @click="confirmDelete(user)"
                    class="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    title="Eliminar"
                  >
                    <span class="material-icons-round text-[20px]">delete</span>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredUsers.length === 0">
              <td colspan="5" class="px-6 py-8 text-center text-slate-400 dark:text-slate-500">
                No se encontraron usuarios.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Crear/Editar -->
    <div v-if="modal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 w-full max-w-lg rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-700/50">
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">{{ modal.isEdit ? 'Editar usuario' : 'Crear usuario' }}</h3>
          <button @click="closeModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <span class="material-icons-round">close</span>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombres <span class="text-rose-500">*</span></label>
            <input
              v-model="modal.nombres"
              type="text"
              required
              placeholder="Ej: Carlos Andrés"
              class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Apellidos <span class="text-rose-500">*</span></label>
            <input
              v-model="modal.apellidos"
              type="text"
              required
              placeholder="Ej: Gómez Rodríguez"
              class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email <span class="text-rose-500">*</span></label>
            <input
              v-model="modal.email"
              type="email"
              required
              placeholder="usuario@institucion.edu.co"
              class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Rol <span class="text-rose-500">*</span></label>
            <Select
              v-model="modal.rol"
              :options="rolOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Selecciona un rol"
              class="w-full"
              :pt="selectPt"
            />
          </div>

          <div v-if="modal.rol === 'docente'">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Sede <span class="text-rose-500">*</span></label>
            <Select
              v-model="modal.sede_id"
              :options="sedes"
              optionLabel="nombre"
              optionValue="id"
              placeholder="Selecciona una sede"
              class="w-full"
              :pt="selectPt"
            />
          </div>

          <div v-if="!modal.isEdit">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Contraseña <span class="text-rose-500">*</span></label>
            <div class="flex gap-2">
              <input
                v-model="modal.password"
                type="text"
                required
                placeholder=""
                class="flex-1 px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              />
              <button
                type="button"
                @click="generatePassword"
                class="px-3 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium transition-colors border border-slate-200 dark:border-slate-600 whitespace-nowrap"
              >
                <span class="material-icons-round text-[18px] align-middle mr-1">casino</span>
                Generar
              </button>
            </div>
            <p class="mt-1 text-xs transition-colors duration-200" :class="passwordStrength.class">
              {{ passwordStrength.text }}
            </p>

            <div v-if="passwordStrength.valid" class="mt-3 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="material-icons-round text-emerald-600 dark:text-emerald-400 text-[18px] shrink-0">key</span>
                  <code class="text-sm font-mono text-emerald-800 dark:text-emerald-300 break-all">{{ modal.password }}</code>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <button type="button" @click="copyPassword" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1">
                    <span class="material-icons-round text-[14px]">content_copy</span>
                    Copiar
                  </button>
                  <button type="button" @click="downloadTxt" class="px-3 py-1.5 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-medium transition-colors border border-slate-200 dark:border-slate-600 flex items-center gap-1">
                    <span class="material-icons-round text-[14px]">download</span>
                    TXT
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="modal.isEdit">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nueva contraseña <span class="text-xs text-slate-400">(opcional)</span></label>
            <div class="flex gap-2">
              <input
                v-model="modal.password"
                type="text"
                placeholder="Dejar en blanco para mantener la actual"
                class="flex-1 px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              />
              <button
                type="button"
                @click="generatePassword"
                class="px-3 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium transition-colors border border-slate-200 dark:border-slate-600 whitespace-nowrap"
              >
                <span class="material-icons-round text-[18px] align-middle mr-1">casino</span>
                Generar
              </button>
            </div>
            <p v-if="modal.password" class="mt-1 text-xs transition-colors duration-200" :class="passwordStrength.class">
              {{ passwordStrength.text }}
            </p>

            <div v-if="passwordStrength.valid" class="mt-3 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="material-icons-round text-emerald-600 dark:text-emerald-400 text-[18px] shrink-0">key</span>
                  <code class="text-sm font-mono text-emerald-800 dark:text-emerald-300 break-all">{{ modal.password }}</code>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <button type="button" @click="copyPassword" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1">
                    <span class="material-icons-round text-[14px]">content_copy</span>
                    Copiar
                  </button>
                  <button type="button" @click="downloadTxt" class="px-3 py-1.5 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-medium transition-colors border border-slate-200 dark:border-slate-600 flex items-center gap-1">
                    <span class="material-icons-round text-[14px]">download</span>
                    TXT
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="closeModal" class="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg font-medium transition-colors">
              Cancelar
            </button>
            <button type="submit" :disabled="saving || !canSave" class="px-4 py-2 bg-primary hover:bg-indigo-600 text-white rounded-lg font-medium shadow-sm transition-all disabled:opacity-50">
              {{ saving ? 'Guardando...' : modal.isEdit ? 'Actualizar' : 'Crear usuario' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useSedesStore } from '../stores/sedes';
import { useAuthStore } from '../stores/auth';
import Select from 'primevue/select';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import api from '../api/axios';

const sedesStore = useSedesStore();
const authStore = useAuthStore();
const toast = useToast();
const confirm = useConfirm();

const PASSWORD_PATTERN = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{8,}$/;

const sedes = computed(() => sedesStore.sedes);
const loading = ref(false);
const saving = ref(false);
const passwordActionDone = ref(false);
const searchQuery = ref('');
const selectedRole = ref(null);

const users = ref([]);
const roleIds = ref({ docente: null, admin: null });

const rolOptions = [
  { label: 'Docente', value: 'docente' },
  { label: 'Directivo', value: 'admin' },
];

const roleFilterOptions = [
  { label: 'Docente', value: 'docente' },
  { label: 'Directivo', value: 'admin' },
];

const modal = ref({
  show: false,
  isEdit: false,
  editId: null,
  nombres: '',
  apellidos: '',
  email: '',
  rol: null,
  sede_id: null,
  password: '',
});

const passwordStrength = computed(() => {
  const pwd = modal.value.password || '';
  if (!pwd) return { text: 'Mínimo 8 caracteres, al menos una letra, un número y un carácter especial', class: 'text-slate-400 dark:text-slate-500', valid: false };
  if (PASSWORD_PATTERN.test(pwd)) return { text: 'Contraseña válida', class: 'text-emerald-600 dark:text-emerald-400', valid: true };
  return { text: 'Mínimo 8 caracteres, al menos una letra, un número y un carácter especial', class: 'text-rose-500 dark:text-rose-400', valid: false };
});

const canSave = computed(() => {
  if (!modal.value.isEdit) {
    if (!PASSWORD_PATTERN.test(modal.value.password || '')) return false;
    if (!passwordActionDone.value) return false;
  }
  return true;
});

const filteredUsers = computed(() => {
  let list = users.value;
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(u =>
      u.nombre?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q)
    );
  }
  if (selectedRole.value) {
    list = list.filter(u => u.rol?.nombre === selectedRole.value);
  }
  return list;
});

const selectPt = {
  root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
  trigger: { class: 'text-slate-500 dark:text-slate-400' },
  panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
  item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' },
};

async function fetchUsers() {
  loading.value = true;
  try {
    const params = { limit: 200 };
    if (authStore.user?.institucion_id) params.institucion_id = authStore.user.institucion_id;
    const { data } = await api.get('/usuarios/', { params });
    users.value = (data || []).filter(u =>
      u.id !== authStore.user?.id &&
      u.rol?.nombre !== 'estudiante'
    );
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los usuarios', life: 3000 });
  } finally {
    loading.value = false;
  }
}

function openCreateModal() {
  modal.value = {
    show: true,
    isEdit: false,
    editId: null,
    nombres: '',
    apellidos: '',
    email: '',
    rol: null,
    sede_id: null,
    password: '',
  };
  passwordActionDone.value = false;
}

function openEditModal(user) {
  const [nombres, ...apellidos] = (user.nombre || '').split(' ');
  modal.value = {
    show: true,
    isEdit: true,
    editId: user.id,
    nombres: nombres || '',
    apellidos: apellidos.join(' ') || '',
    email: user.email || '',
    rol: user.rol?.nombre || null,
    sede_id: user.sede_id || null,
    password: '',
  };
  passwordActionDone.value = false;
}

function closeModal() {
  modal.value.show = false;
  passwordActionDone.value = false;
}

function generatePassword() {
  const letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const numbers = '0123456789';
  const specials = '!@#$%^&*()_+-=[]{}|;:,.<>?';
  const all = letters + numbers + specials;

  let pwd = '';
  pwd += letters[Math.floor(Math.random() * letters.length)];
  pwd += numbers[Math.floor(Math.random() * numbers.length)];
  pwd += specials[Math.floor(Math.random() * specials.length)];
  for (let i = pwd.length; i < 12; i++) pwd += all[Math.floor(Math.random() * all.length)];
  pwd = pwd.split('').sort(() => Math.random() - 0.5).join('');

  modal.value.password = pwd;
  passwordActionDone.value = false;
}

async function copyPassword() {
  try {
    await navigator.clipboard.writeText(modal.value.password);
    passwordActionDone.value = true;
    toast.add({ severity: 'success', summary: 'Copiado', detail: 'Contraseña copiada al portapapeles', life: 2000 });
  } catch {
    passwordActionDone.value = true;
    toast.add({ severity: 'info', summary: 'Contraseña', detail: modal.value.password, life: 5000 });
  }
}

function downloadTxt() {
  const nombreCompleto = `${modal.value.nombres} ${modal.value.apellidos}`.trim() || 'Sin nombre';
  const content = [
    '=== Datos del Usuario ===',
    `Nombre: ${nombreCompleto}`,
    `Email: ${modal.value.email}`,
    `Rol: ${rolOptions.find(r => r.value === modal.value.rol)?.label || modal.value.rol}`,
    `Sede: ${sedes.value.find(s => s.id === modal.value.sede_id)?.nombre || 'N/A'}`,
    `Contraseña: ${modal.value.password}`,
    '',
    'Guarda esta información en un lugar seguro.'
  ].join('\n');

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `credenciales_${nombreCompleto.replace(/\s+/g, '_').toLowerCase()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
  passwordActionDone.value = true;
}

async function handleSubmit() {
  if (!modal.value.rol) {
    toast.add({ severity: 'warn', summary: 'Rol requerido', detail: 'Selecciona un rol para el usuario', life: 4000 });
    return;
  }
  if (modal.value.rol === 'docente' && !modal.value.sede_id) {
    toast.add({ severity: 'warn', summary: 'Sede requerida', detail: 'Selecciona una sede para el docente', life: 4000 });
    return;
  }

  saving.value = true;
  try {
    if (modal.value.isEdit) {
      const payload = {
        nombre: `${modal.value.nombres} ${modal.value.apellidos}`.trim(),
        email: modal.value.email,
        rol_id: modal.value.rol === 'docente' ? roleIds.value.docente : roleIds.value.admin,
        sede_id: modal.value.rol === 'docente' ? modal.value.sede_id : null,
      };
      if (modal.value.password && PASSWORD_PATTERN.test(modal.value.password)) {
        payload.password = modal.value.password;
      }
      await api.put(`/usuarios/${modal.value.editId}`, payload);
      toast.add({ severity: 'success', summary: 'Actualizado', detail: 'Usuario actualizado', life: 3000 });
    } else {
      const payload = {
        nombre: `${modal.value.nombres} ${modal.value.apellidos}`.trim(),
        email: modal.value.email,
        tipo_documento: 'CC',
        numero_documento: `DOC-${Date.now()}`,
        institucion_id: authStore.user.institucion_id,
        rol_id: modal.value.rol === 'docente' ? roleIds.value.docente : roleIds.value.admin,
        sede_id: modal.value.rol === 'docente' ? modal.value.sede_id : null,
        password: modal.value.password,
        activo: true,
      };
      await api.post('/usuarios/', payload);
      toast.add({ severity: 'success', summary: 'Creado', detail: 'Usuario creado exitosamente', life: 3000 });
    }
    closeModal();
    await fetchUsers();
  } catch (e) {
    const detail = e.response?.data?.detail || e.message || 'Error';
    toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
  } finally {
    saving.value = false;
  }
}

function confirmDelete(user) {
  confirm.require({
    message: `¿Eliminar a "${user.nombre}"?`,
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Eliminar',
    rejectLabel: 'Cancelar',
    acceptProps: { severity: 'danger' },
    accept: async () => {
      try {
        await api.delete(`/usuarios/${user.id}`);
        toast.add({ severity: 'success', summary: 'Eliminado', detail: 'Usuario eliminado', life: 3000 });
        await fetchUsers();
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || 'No se pudo eliminar', life: 5000 });
      }
    }
  });
}

function getInitials(name) {
  if (!name) return '??';
  return name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
}

onMounted(async () => {
  await sedesStore.fetchSedes(authStore.user?.institucion_id);
  const { data: rolesData } = await api.get('/roles/');
  rolesData.forEach(r => {
    if (r.nombre === 'docente') roleIds.value.docente = r.id;
    if (r.nombre === 'admin') roleIds.value.admin = r.id;
  });
  await fetchUsers();
});
</script>

<style scoped>
.bg-primary { background-color: #6366f1; }
.text-primary { color: #6366f1; }
.animate-in { animation-fill-mode: both; }
.fade-in { animation-name: fadeIn; }
.zoom-in { animation-name: zoomIn; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes zoomIn { from { transform: scale(0.95); } to { transform: scale(1); } }
</style>
