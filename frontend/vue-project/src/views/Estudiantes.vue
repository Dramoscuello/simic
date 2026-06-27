<template>
  <div class="mx-auto w-full max-w-7xl flex flex-col gap-6 relative p-6">
    <Toast />
    
    <!-- Header & Actions -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Estudiantes</h2>
        <p class="text-slate-500 dark:text-slate-400">Gestión y seguimiento académico</p>
      </div>
      <button
        v-if="isAdmin"
        @click="openModal()"
        class="flex items-center justify-center gap-2 bg-primary hover:bg-indigo-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shadow-sm"
      >
        <span class="material-icons-round text-[20px]">add</span>
        Nuevo estudiante
      </button>
    </div>

    <!-- Filters Section -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <!-- Search -->
        <div class="relative">
             <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                <span class="material-icons-round text-[20px]">search</span>
             </span>
             <input 
                v-model="searchQuery"
                type="text"
                placeholder="Buscar por nombre o documento..."
                class="pl-10 w-full h-[42px] rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all placeholder-slate-400 dark:placeholder-slate-500"
             />
        </div>

        <!-- Filter Sede -->
        <div>
             <Select 
                v-model="selectedSede" 
                :options="sedes" 
                optionLabel="nombre" 
                optionValue="id" 
                placeholder="Filtrar por Sedes" 
                class="w-full"
                showClear
                :pt="selectPt"
             />
        </div>

        <!-- Filter Grupo -->
        <div>
             <Select 
                v-model="selectedGrupo" 
                :options="filteredGrupos" 
                optionLabel="nombre" 
                optionValue="id" 
                placeholder="Todos los grupos" 
                class="w-full"
                showClear
                :pt="selectPt"
             >
                <template #option="slotProps">
                    <div>{{ slotProps.option.nombre }} — {{ slotProps.option.sede?.nombre || 'Sin sede' }}</div>
                </template>
                <template #value="slotProps">
                    <div v-if="slotProps.value" class="flex items-center">
                        <div class="text-slate-900 dark:text-white">{{ getGrupoLabel(slotProps.value) }}</div>
                    </div>
                    <span v-else class="text-slate-500 dark:text-slate-400">{{ slotProps.placeholder }}</span>
                </template>
             </Select>
        </div>
    </div>
    
    <!-- Table -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <!-- Loading -->
      <div v-if="loading" class="p-8 flex justify-center">
         <span class="animate-spin h-8 w-8 border-b-2 border-primary rounded-full"></span>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm text-left text-slate-600 dark:text-slate-300">
          <thead class="bg-slate-50 dark:bg-slate-700/50 text-xs uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th class="px-6 py-4">Estudiante</th>
              <th class="px-6 py-4">Documento</th>
              <th class="px-6 py-4">Grupo</th>
              <th class="px-6 py-4">Contacto</th>
              <th v-if="isAdmin" class="px-6 py-4 text-center">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr 
              v-for="est in filteredEstudiantes" 
              :key="est.id"
              class="hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 transition-colors group"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-300 font-bold border border-slate-200 dark:border-slate-600 group-hover:bg-white dark:group-hover:bg-slate-600 group-hover:border-primary dark:group-hover:border-primary group-hover:text-primary dark:group-hover:text-primary transition-colors">
                     {{ getInitials(est.nombre) }}
                  </div>
                  <div>
                    <div class="font-semibold text-slate-900 dark:text-white">{{ est.nombre || 'Sin Nombre' }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 font-mono text-slate-500 dark:text-slate-400">{{ est.numero_documento || 'N/A' }}</td>
              <td class="px-6 py-4">
                 <span v-if="est.grupo" class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300">
                    {{ est.grupo.nombre }} — {{ est.grupo.sede?.nombre || 'Sin sede' }}
                 </span>
                 <span v-else class="text-slate-400 dark:text-slate-500 italic text-xs">Sin grupo</span>
              </td>
              <td class="px-6 py-4">{{ est.email || 'N/A' }}</td>
              <td v-if="isAdmin" class="px-6 py-4 text-center">
                 <div class="flex items-center justify-center gap-1">
                    <button
                      @click.stop="openModal(est)"
                      class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      title="Editar"
                    >
                      <span class="material-icons-round text-[20px]">edit</span>
                    </button>
                    <button
                      @click.stop="confirmDelete(est)"
                      class="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Eliminar"
                    >
                      <span class="material-icons-round text-[20px]">delete</span>
                    </button>
                    <button
                      @click.stop="verDetalle(est)"
                      class="p-2 text-slate-400 hover:text-primary hover:bg-indigo-50 rounded-lg transition-colors"
                      title="Ver detalle"
                    >
                      <span class="material-icons-round">chevron_right</span>
                    </button>
                 </div>
              </td>
            </tr>
            <tr v-if="filteredEstudiantes.length === 0">
               <td :colspan="isAdmin ? 5 : 4" class="px-6 py-8 text-center text-slate-400 dark:text-slate-500">
                  No se encontraron estudiantes.
               </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Crear/Editar Estudiante -->
    <div v-if="modal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 w-full max-w-lg rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-700/50">
            <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">{{ modal.isEdit ? 'Editar estudiante' : 'Nuevo estudiante' }}</h3>
            <button @click="closeModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                <span class="material-icons-round">close</span>
            </button>
        </div>
        
        <form @submit.prevent="saveEstudiante" class="p-6 space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre completo <span class="text-rose-500">*</span></label>
                <input 
                    v-model="modal.data.nombre" 
                    type="text" 
                    required
                    placeholder="Ej: Ana María Gómez" 
                    class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tipo de documento <span class="text-rose-500">*</span></label>
                  <Select
                    v-model="modal.data.tipo_documento"
                    :options="tipoDocumentoOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Selecciona"
                    class="w-full"
                    :pt="selectPt"
                  />
              </div>
              <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Número de documento <span class="text-rose-500">*</span></label>
                  <input 
                      v-model="modal.data.numero_documento" 
                      type="text" 
                      required
                      placeholder="Ej: 1234567890" 
                      class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  />
              </div>
            </div>

            <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email</label>
                <input 
                    v-model="modal.data.email" 
                    type="email" 
                    placeholder="estudiante@ejemplo.com" 
                    class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
            </div>

            <div>
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Grupo</label>
                <Select
                  v-model="modal.data.grupo_id"
                  :options="grupos"
                  optionLabel="nombre"
                  optionValue="id"
                  placeholder="Sin grupo"
                  showClear
                  class="w-full"
                  :pt="selectPt"
                >
                  <template #option="slotProps">
                      <div>{{ slotProps.option.nombre }} — {{ slotProps.option.sede?.nombre || 'Sin sede' }}</div>
                  </template>
                </Select>
            </div>

            <div v-if="!modal.isEdit">
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Contraseña <span class="text-rose-500">*</span></label>
                <div class="flex gap-2">
                    <input 
                        v-model="modal.data.password" 
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
                <p
                    class="mt-1 text-xs transition-colors duration-200"
                    :class="passwordStrength.class"
                >
                    {{ passwordStrength.text }}
                </p>
                <div v-if="passwordStrength.valid" class="mt-3 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center gap-2 min-w-0">
                            <span class="material-icons-round text-emerald-600 dark:text-emerald-400 text-[18px] shrink-0">key</span>
                            <code class="text-sm font-mono text-emerald-800 dark:text-emerald-300 break-all">{{ modal.data.password }}</code>
                        </div>
                        <div class="flex items-center gap-2 shrink-0">
                            <button
                                type="button"
                                @click="copyPassword"
                                class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1"
                            >
                                <span class="material-icons-round text-[14px]">content_copy</span>
                                Copiar
                            </button>
                            <button
                                type="button"
                                @click="downloadTxt"
                                class="px-3 py-1.5 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-medium transition-colors border border-slate-200 dark:border-slate-600 flex items-center gap-1"
                            >
                                <span class="material-icons-round text-[14px]">download</span>
                                TXT
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div v-else>
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nueva contraseña <span class="text-xs text-slate-400">(opcional)</span></label>
                <input 
                    v-model="modal.data.password" 
                    type="password" 
                    placeholder="Dejar en blanco para mantener la actual" 
                    class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
            </div>

            <div class="flex items-center gap-2">
                <input id="est-activo" v-model="modal.data.activo" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary" />
                <label for="est-activo" class="text-sm text-slate-700 dark:text-slate-300">Estudiante activo</label>
            </div>
            
            <div class="flex justify-end gap-3 pt-2">
                <button type="button" @click="closeModal" class="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg font-medium transition-colors">
                    Cancelar
                </button>
                <button type="submit" :disabled="modal.saving || !canSave" class="px-4 py-2 bg-primary hover:bg-indigo-600 text-white rounded-lg font-medium shadow-sm transition-all disabled:opacity-50">
                    {{ modal.saving ? 'Guardando...' : 'Guardar' }}
                </button>
            </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useUsuariosStore } from '../stores/usuarios';
import { useSedesStore } from '../stores/sedes';
import { useGruposStore } from '../stores/grupos';
import Select from 'primevue/select';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import api from '../api/axios';

const router = useRouter();
const authStore = useAuthStore();
const usuariosStore = useUsuariosStore();
const sedesStore = useSedesStore();
const gruposStore = useGruposStore();
const toast = useToast();
const confirm = useConfirm();

const searchQuery = ref('');
const loading = ref(false);
const rolEstudianteId = ref(null);
const generatedPassword = ref('');
const passwordActionDone = ref(false);

const PASSWORD_PATTERN = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{8,}$/;

const passwordStrength = computed(() => {
    const pwd = modal.value.data.password || '';
    if (!pwd) return { text: 'Mínimo 8 caracteres, al menos una letra, un número y un carácter especial', class: 'text-slate-400 dark:text-slate-500', valid: false };
    if (PASSWORD_PATTERN.test(pwd)) return { text: 'Contraseña válida', class: 'text-emerald-600 dark:text-emerald-400', valid: true };
    return { text: 'Mínimo 8 caracteres, al menos una letra, un número y un carácter especial', class: 'text-rose-500 dark:text-rose-400', valid: false };
});

const canSave = computed(() => {
    if (!modal.value.isEdit) {
        if (!PASSWORD_PATTERN.test(modal.value.data.password || '')) return false;
        if (!passwordActionDone.value) return false;
        return true;
    }
    return true;
});

function generatePassword() {
    const letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    const specials = '!@#$%^&*()_+-=[]{}|;:,.<>?';
    const all = letters + numbers + specials;
    
    let pwd = '';
    pwd += letters[Math.floor(Math.random() * letters.length)];
    pwd += numbers[Math.floor(Math.random() * numbers.length)];
    pwd += specials[Math.floor(Math.random() * specials.length)];
    
    for (let i = pwd.length; i < 12; i++) {
        pwd += all[Math.floor(Math.random() * all.length)];
    }
    
    pwd = pwd.split('').sort(() => Math.random() - 0.5).join('');
    
    generatedPassword.value = pwd;
    modal.value.data.password = pwd;
    passwordActionDone.value = false;
}

async function copyPassword() {
    const pwd = modal.value.data.password;
    try {
        await navigator.clipboard.writeText(pwd);
        passwordActionDone.value = true;
        toast.add({ severity: 'success', summary: 'Copiado', detail: 'Contraseña copiada al portapapeles', life: 2000 });
    } catch {
        passwordActionDone.value = true;
        toast.add({ severity: 'info', summary: 'Contraseña', detail: pwd, life: 5000 });
    }
}

function downloadTxt() {
    const nombre = modal.value.data.nombre || 'Sin nombre';
    const documento = modal.value.data.numero_documento || 'N/A';
    const email = modal.value.data.email || 'N/A';
    const grupoLabel = getGrupoLabel(modal.value.data.grupo_id);
    
    const content = [
        '=== Datos del Estudiante ===',
        `Nombre: ${nombre}`,
        `Documento: ${modal.value.data.tipo_documento} ${documento}`,
        `Email: ${email}`,
        `Grupo: ${grupoLabel}`,
        `Contraseña: ${modal.value.data.password}`,
        '',
        'Guarda esta información en un lugar seguro.'
    ].join('\n');
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `credenciales_${nombre.replace(/\s+/g, '_').toLowerCase()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    passwordActionDone.value = true;
}

const isAdmin = computed(() => authStore.user?.rol?.nombre === 'admin');
const isInstitucionAdmin = computed(() => isAdmin.value && authStore.user?.institucion_id != null);

// Filtros
const selectedSede = ref(null);
const selectedGrupo = ref(null);

// Data
const sedes = computed(() => sedesStore.sedes);
const grupos = computed(() => gruposStore.grupos);
const estudiantes = computed(() => usuariosStore.usuarios);

const filteredGrupos = computed(() => {
    if (!selectedSede.value) return grupos.value;
    return grupos.value.filter(g => g.sede_id === selectedSede.value);
});

// Modal
const modal = ref({
    show: false,
    isEdit: false,
    saving: false,
    data: {
        id: null,
        nombre: '',
        email: '',
        tipo_documento: 'TI',
        numero_documento: '',
        grupo_id: null,
        password: '',
        activo: true
    }
});

const tipoDocumentoOptions = [
    { label: 'Tarjeta de Identidad', value: 'TI' },
    { label: 'Cédula de Ciudadanía', value: 'CC' },
    { label: 'Cédula de Extranjería', value: 'CE' },
    { label: 'Permiso Especial de Permanencia', value: 'PEP' }
];

const selectPt = {
    root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
    trigger: { class: 'text-slate-500 dark:text-slate-400' },
    panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
    item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' },
    filterInput: { class: 'w-full p-2 border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-white rounded-md' }
};

// Filtrado local de búsqueda texto (sobre los datos ya filtrados por API)
const filteredEstudiantes = computed(() => {
   if (!searchQuery.value) return estudiantes.value;
   const q = searchQuery.value.toLowerCase();
   return estudiantes.value.filter(s => 
      s.nombre?.toLowerCase().includes(q) || 
      s.numero_documento?.toLowerCase().includes(q) ||
      s.email?.toLowerCase().includes(q)
   );
});

const getGrupoLabel = (grupoId) => {
    const g = grupos.value.find(gr => gr.id === grupoId);
    if (!g) return 'Grupo ' + grupoId;
    return g.sede?.nombre ? `${g.nombre} — ${g.sede.nombre}` : g.nombre;
};

// Carga de datos
const fetchEstudiantes = async (filters = {}) => {
    loading.value = true;
    try {
        await usuariosStore.fetchUsuariosGlobal({ 
            rol: 'estudiante', 
            ...filters 
        });
    } finally {
        loading.value = false;
    }
};

const fetchRoles = async () => {
    try {
        const { data } = await api.get('/roles/');
        const rolEst = data.find(r => r.nombre === 'estudiante');
        if (rolEst) rolEstudianteId.value = rolEst.id;
    } catch (e) {
        console.error('Error cargando roles', e);
    }
};

// Modal actions
const openModal = (est = null) => {
    generatedPassword.value = '';
    passwordActionDone.value = false;
    modal.value.isEdit = !!est;
    if (est) {
        modal.value.data = {
            id: est.id,
            nombre: est.nombre || '',
            email: est.email || '',
            tipo_documento: est.tipo_documento || 'TI',
            numero_documento: est.numero_documento || '',
            grupo_id: est.grupo_id || null,
            password: '',
            activo: est.activo !== false
        };
    } else {
        modal.value.data = {
            id: null,
            nombre: '',
            email: '',
            tipo_documento: 'TI',
            numero_documento: '',
            grupo_id: null,
            password: '',
            activo: true
        };
    }
    modal.value.show = true;
};

const closeModal = () => {
    modal.value.show = false;
    generatedPassword.value = '';
    passwordActionDone.value = false;
};

const saveEstudiante = async () => {
    const payload = { ...modal.value.data };
    const institucionId = authStore.user?.institucion_id;
    if (!institucionId) {
        toast.add({ severity: 'warn', summary: 'Faltan datos', detail: 'No se pudo determinar la institución', life: 4000 });
        return;
    }
    payload.institucion_id = institucionId;
    payload.rol_id = rolEstudianteId.value;

    if (!payload.rol_id) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se encontró el rol de estudiante', life: 4000 });
        return;
    }

    if (!modal.value.isEdit && !payload.password) {
        toast.add({ severity: 'warn', summary: 'Contraseña requerida', detail: 'Ingresa una contraseña para el estudiante', life: 4000 });
        return;
    }
    if (!modal.value.isEdit && !PASSWORD_PATTERN.test(payload.password)) {
        toast.add({ severity: 'warn', summary: 'Contraseña inválida', detail: 'Mínimo 8 caracteres, al menos una letra, un número y un carácter especial', life: 5000 });
        return;
    }

    // No enviar password vacío en edición
    if (modal.value.isEdit && !payload.password) {
        delete payload.password;
    }
    // No enviar id en el payload
    delete payload.id;

    modal.value.saving = true;
    try {
        if (modal.value.isEdit) {
            await usuariosStore.updateUser(modal.value.data.id, payload);
            toast.add({ severity: 'success', summary: 'Actualizado', detail: 'Estudiante actualizado', life: 3000 });
        } else {
            await usuariosStore.createUser(payload);
            toast.add({ severity: 'success', summary: 'Creado', detail: 'Estudiante creado exitosamente', life: 3000 });
        }
        closeModal();
        await fetchEstudiantes(buildFilters());
    } catch (e) {
        const detail = e.response?.data?.detail || e.message || 'Error guardando estudiante';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    } finally {
        modal.value.saving = false;
    }
};

const confirmDelete = (est) => {
    confirm.require({
        message: `¿Estás seguro de eliminar al estudiante "${est.nombre}"?`,
        header: 'Confirmar eliminación',
        icon: 'pi pi-exclamation-triangle',
        acceptLabel: 'Eliminar',
        rejectLabel: 'Cancelar',
        acceptProps: { severity: 'danger' },
        accept: async () => {
            try {
                await usuariosStore.deleteUser(est.id);
                toast.add({ severity: 'success', summary: 'Eliminado', detail: 'Estudiante eliminado', life: 3000 });
                await fetchEstudiantes(buildFilters());
            } catch (e) {
                toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el estudiante', life: 5000 });
            }
        }
    });
};

const buildFilters = () => {
    const filters = {};
    if (selectedGrupo.value) {
        filters.grupo_id = selectedGrupo.value;
    } else if (selectedSede.value) {
        filters.sede_id = selectedSede.value;
    }
    return filters;
};

const userInstitutionId = computed(() => authStore.user?.institucion_id);

// Watchers
watch(selectedSede, async (newSedeId) => {
    selectedGrupo.value = null;
    await gruposStore.fetchGrupos(userInstitutionId.value, newSedeId || undefined);
    await fetchEstudiantes(buildFilters());
});

watch(selectedGrupo, () => {
    fetchEstudiantes(buildFilters());
});

onMounted(async () => {
   loading.value = true;
   try {
       await fetchRoles();
       if (isInstitucionAdmin.value) {
           await Promise.all([
               gruposStore.fetchGrupos(userInstitutionId.value),
               sedesStore.fetchSedes(userInstitutionId.value),
               fetchEstudiantes()
           ]);
       } else if (isAdmin.value) {
           await Promise.all([
               gruposStore.fetchGrupos(),
               sedesStore.fetchSedes(),
               fetchEstudiantes()
           ]);
       }
   } finally {
       loading.value = false;
   }
});

const verDetalle = (estudiante) => {
    router.push(`/estudiantes/${estudiante.id}`);
};

const getInitials = (name) => {
   if (!name) return '??';
   return name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
};
</script>

<style scoped>
.font-sans { font-family: 'Inter', sans-serif; }
.animate-in { animation-fill-mode: both; }
.fade-in { animation-name: fadeIn; }
.zoom-in { animation-name: zoomIn; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes zoomIn { from { transform: scale(0.95); } to { transform: scale(1); } }
</style>
