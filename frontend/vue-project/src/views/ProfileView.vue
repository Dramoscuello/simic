<template>
  <div class="mx-auto max-w-4xl p-4 sm:p-6 lg:p-8">
    
    <!-- Encabezado -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Mi perfil</h1>
      <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Gestiona tu información personal y credenciales de acceso.</p>
    </div>

    <div class="space-y-6">
      <!-- Tarjeta de Información Personal -->
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div class="p-6 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <h2 class="text-lg font-medium text-slate-900 dark:text-white flex items-center gap-2">
            <span class="material-icons-round text-primary">badge</span>
            Información personal
          </h2>
        </div>
        
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Nombre -->
          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Nombre <span class="text-red-500">*</span></label>
            <InputText 
              v-model="userData.nombre"
              type="text" 
              class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-primary focus:border-primary disabled:opacity-60 disabled:cursor-not-allowed p-2 border"
              :disabled="loading || isProfileReadOnly"
            />
          </div>

          <!-- Email -->
          <div class="space-y-2">
             <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Correo electrónico <span class="text-red-500">*</span></label>
            <InputText 
              v-model="userData.email"
              type="email" 
              class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-primary focus:border-primary disabled:opacity-60 disabled:cursor-not-allowed p-2 border"
              :disabled="loading || isProfileReadOnly"
            />
          </div>

          <!-- Tipo Documento -->
          <div class="space-y-2 flex flex-col">
             <label class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Tipo de documento <span class="text-red-500">*</span></label>
            <Select
                v-model="userData.tipo_documento"
                :options="documentTypes"
                optionLabel="label"
                optionValue="value"
                placeholder="Seleccione tipo"
                class="w-full"
                :pt="{
                    root: { class: 'w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white h-[42px] flex items-center' },
                    trigger: { class: 'w-10 flex items-center justify-center text-slate-500' },
                    panel: { class: 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-lg rounded-lg' },
                    item: { class: 'p-2 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer text-slate-700 dark:text-slate-200' },
                    input: { class: 'p-2 w-full bg-transparent border-0 focus:ring-0 text-slate-900 dark:text-white' }
                }"
                :disabled="loading || isProfileReadOnly"
            />
          </div>

          <!-- Número Documento -->
          <div class="space-y-2">
             <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Número de documento <span class="text-red-500">*</span></label>
            <InputText 
              v-model="userData.numero_documento"
              type="text" 
              class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-primary focus:border-primary disabled:opacity-60 disabled:cursor-not-allowed p-2 border"
              :disabled="loading || isProfileReadOnly"
            />
          </div>
        </div>

        <div v-if="!isProfileReadOnly" class="p-6 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700 flex justify-end">
            <button 
                @click="updateProfile"
                :disabled="loading || !isFormValid"
                class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <span v-if="loading" class="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"></span>
                <span v-else class="material-icons-round text-sm">save</span>
                Guardar cambios
            </button>
        </div>
      </div>

      <!-- Tarjeta de Cambio de Contraseña -->
      <div v-if="canChangePassword" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div class="p-6 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <h2 class="text-lg font-medium text-slate-900 dark:text-white flex items-center gap-2">
            <span class="material-icons-round text-primary">security</span>
            Seguridad y contraseña
          </h2>
        </div>
        
        <div class="p-6 space-y-4 max-w-lg">
          
          <!-- Contraseña Actual -->
          <div class="space-y-2">
             <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Contraseña actual</label>
             <div class="relative">
                 <InputText 
                   v-model="passwordForm.current"
                   :type="showPassword.current ? 'text' : 'password'"
                   class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-primary focus:border-primary pr-10 p-2 border"
                   placeholder="Ingrese su contraseña actual"
                 />
                 <button @click="showPassword.current = !showPassword.current" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                     <span class="material-icons-round text-sm">{{ showPassword.current ? 'visibility_off' : 'visibility' }}</span>
                 </button>
             </div>
          </div>

          <!-- Nueva Contraseña -->
          <div class="space-y-2">
             <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Nueva contraseña</label>
             <div class="relative">
                 <InputText 
                   v-model="passwordForm.new"
                   :type="showPassword.new ? 'text' : 'password'"
                   class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-primary focus:border-primary pr-10 p-2 border"
                   placeholder="Mínimo 8 caracteres, letras y números"
                 />
                 <button @click="showPassword.new = !showPassword.new" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                     <span class="material-icons-round text-sm">{{ showPassword.new ? 'visibility_off' : 'visibility' }}</span>
                 </button>
             </div>
             <!-- Indicadores de Fuerza -->
             <div class="flex gap-2 mt-1">
                 <span :class="{'text-emerald-500': hasMinLength, 'text-slate-400': !hasMinLength}" class="text-xs flex items-center gap-1">
                     <span class="material-icons-round text-[10px]">{{ hasMinLength ? 'check' : 'circle' }}</span> 8+ Caracteres
                 </span>
                 <span :class="{'text-emerald-500': hasMixed, 'text-slate-400': !hasMixed}" class="text-xs flex items-center gap-1">
                     <span class="material-icons-round text-[10px]">{{ hasMixed ? 'check' : 'circle' }}</span> Letras y Números
                 </span>
             </div>
          </div>

          <!-- Confirmar Nueva Contraseña -->
          <div class="space-y-2">
             <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Confirmar nueva contraseña</label>
             <div class="relative">
                 <InputText 
                   v-model="passwordForm.confirm"
                   :type="showPassword.confirm ? 'text' : 'password'"
                   class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-primary focus:border-primary pr-10 p-2 border"
                   :class="{'border-red-300 focus:border-red-500 focus:ring-red-200': !passwordsMatch && passwordForm.confirm}"
                 />
                 <button @click="showPassword.confirm = !showPassword.confirm" class="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                     <span class="material-icons-round text-sm">{{ showPassword.confirm ? 'visibility_off' : 'visibility' }}</span>
                 </button>
             </div>
             <p v-if="!passwordsMatch && passwordForm.confirm" class="text-xs text-red-500 mt-1">Las contraseñas no coinciden.</p>
          </div>

        </div>

        <div class="p-6 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-700 flex justify-end">
            <button 
                @click="changePassword"
                :disabled="pwdLoading || !isPasswordFormValid"
                class="bg-slate-900 dark:bg-white hover:bg-slate-800 dark:hover:bg-slate-100 text-white dark:text-slate-900 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <span v-if="pwdLoading" class="animate-spin h-4 w-4 border-2 border-slate-400 border-t-white dark:border-slate-400 dark:border-t-slate-900 rounded-full"></span>
                <span v-else class="material-icons-round text-sm">lock_reset</span>
                Actualizar contraseña
            </button>
        </div>
      </div>
    
    </div>
    
    <!-- Toast Notification (Basic) -->
    <div v-if="notification.show" :class="notification.type === 'error' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'" class="fixed bottom-4 right-4 p-4 rounded-lg shadow-lg border flex items-center gap-3 animate-in slide-in-from-bottom-4 z-50">
        <span class="material-icons-round">{{ notification.type === 'error' ? 'error' : 'check_circle' }}</span>
        <span class="font-medium text-sm">{{ notification.message }}</span>
        <button @click="notification.show = false" class="ml-2 hover:bg-black/5 rounded-full p-1"><span class="material-icons-round text-sm">close</span></button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import api from '../api/axios';
import InputText from 'primevue/inputtext';
import Select from 'primevue/select';

const authStore = useAuthStore();
const loading = ref(false);
const pwdLoading = ref(false);

const userData = ref({
    nombre: '',
    email: '',
    tipo_documento: '',
    numero_documento: '',
});

const documentTypes = [
    { label: 'Cédula de Ciudadanía', value: 'CC' },
    { label: 'Tarjeta de Identidad', value: 'TI' }
];

const passwordForm = ref({
    current: '',
    new: '',
    confirm: ''
});

const showPassword = ref({
    current: false,
    new: false,
    confirm: false
});

const notification = ref({ show: false, message: '', type: 'success' });

const originalUserData = ref({}); // Para detectar cambios

// --- Carga Inicial ---
onMounted(async () => {
    // Cargar datos frescos del usuario al montar
    try {
        loading.value = true;
        await authStore.fetchUser(); // Asegurar datos actualizados
        if (authStore.user) {
            // Mapeo explicito para asegurar reactividad y limpiar datos extra
            const data = { 
                nombre: authStore.user.nombre || '',
                email: authStore.user.email || '',
                tipo_documento: authStore.user.tipo_documento || 'CC', // Valor por defecto
                numero_documento: authStore.user.numero_documento || ''
            };
            userData.value = { ...data };
            originalUserData.value = { ...data }; // Guardar copia original
        }
    } catch (e) {
        showNotify("Error cargando perfil", "error");
    } finally {
        loading.value = false;
    }
});

// --- Validaciones Perfil ---
const hasChanges = computed(() => {
    return JSON.stringify(userData.value) !== JSON.stringify(originalUserData.value);
});

const isProfileReadOnly = computed(() => {
    return authStore.user?.rol?.nombre === 'estudiante';
});

const canChangePassword = computed(() => !!authStore.user?.id);

const isFormValid = computed(() => {
    return userData.value.nombre && 
           userData.value.email && 
           userData.value.tipo_documento &&
           userData.value.numero_documento &&
           hasChanges.value; // Solo activo si hay cambios
});

// --- Validaciones Password ---
const hasMinLength = computed(() => passwordForm.value.new.length >= 8);
const hasMixed = computed(() => /^(?=.*[A-Za-z])(?=.*\d)/.test(passwordForm.value.new));
const passwordsMatch = computed(() => passwordForm.value.new === passwordForm.value.confirm);

const isPasswordFormValid = computed(() => {
    return passwordForm.value.current && 
           hasMinLength.value && 
           hasMixed.value && 
           passwordsMatch.value;
});

// --- Acciones ---

const updateProfile = async () => {
    if (!isFormValid.value) return;
    loading.value = true;
    try {
        await api.put(`/usuarios/${authStore.user.id}`, {
            nombre: userData.value.nombre,
            email: userData.value.email,
            tipo_documento: userData.value.tipo_documento,
            numero_documento: userData.value.numero_documento
        });
        
        // Actualizar store local
        await authStore.fetchUser();
        originalUserData.value = { ...userData.value }; // Resetear estado de cambios
        showNotify("Perfil actualizado correctamente");
    } catch (e) {
        console.error(e);
        const msg = e.response?.data?.detail || "Error al actualizar perfil";
        showNotify(msg, "error");
    } finally {
        loading.value = false;
    }
};

const changePassword = async () => {
    if (!isPasswordFormValid.value) return;
    pwdLoading.value = true;
    try {
        await api.post('/auth/change-password', {
            current_password: passwordForm.value.current,
            new_password: passwordForm.value.new
        });
        
        showNotify("Contraseña actualizada correctamente");
        
        // Limpiar formulario
        passwordForm.value = { current: '', new: '', confirm: '' };
    } catch (e) {
        console.error(e);
        const msg = e.response?.data?.detail || "Error al cambiar contraseña";
        showNotify(msg, "error");
    } finally {
        pwdLoading.value = false;
    }
};

const showNotify = (msg, type = 'success') => {
    notification.value = { show: true, message: msg, type };
    setTimeout(() => notification.value.show = false, 4000);
};
</script>
