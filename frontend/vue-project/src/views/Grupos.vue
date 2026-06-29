<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-6">
    
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800">Grupos</h2>
        <p class="text-slate-500">Gestiona los grupos académicos y asigna estudiantes</p>
      </div>
      <button 
        v-if="isInstitucionAdmin"
        @click="openModal()"
        class="relative z-50 flex items-center justify-center gap-2 bg-primary hover:bg-indigo-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shadow-sm"
      >
        <span class="material-icons-round text-[20px]">add</span>
        Nuevo grupo (+)
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="grupos.length === 0" class="flex flex-col items-center justify-center py-16 bg-white rounded-2xl border border-dashed border-slate-300">
      <div class="h-16 w-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
        <span class="material-icons-round text-3xl text-slate-400">class</span>
      </div>
      <h3 class="text-lg font-medium text-slate-900 mb-1">No hay grupos creados</h3>
      <p class="text-slate-500 text-sm mb-6 text-center max-w-sm">Crea grupos (ej. 11-A, 11-B) para organizar a tus estudiantes y comparar resultados.</p>
      <button 
        @click="openModal()"
        class="px-4 py-2 bg-primary hover:bg-indigo-600 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
      >
        Crear primer grupo
      </button>
    </div>

    <!-- Grupos Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="grupo in grupos" 
        :key="grupo.id"
        class="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col"
      >
        <div class="p-5 flex items-start justify-between border-b border-slate-50">
          <div class="flex items-center gap-3">
            <div class="h-10 w-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-lg">
              {{ grupo.nombre.substring(0, 2).toUpperCase() }}
            </div>
            <div>
              <h3 class="font-bold text-slate-800 text-lg">{{ grupo.nombre }}</h3>
              <p class="text-xs text-slate-400">{{ grupo.sede?.nombre || 'Sin sede' }}</p>
            </div>
          </div>
          <div v-if="isInstitucionAdmin" class="flex items-center gap-1">
            <button 
              @click="openModal(grupo)"
              class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              title="Editar nombre"
            >
              <span class="material-icons-round text-[20px]">edit</span>
            </button>
            <button 
              @click="confirmDelete(grupo)"
              class="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
              title="Eliminar grupo"
            >
              <span class="material-icons-round text-[20px]">delete</span>
            </button>
          </div>
        </div>
        
        <div class="p-5 flex-1 flex flex-col justify-end gap-4">
             <!-- Stats Placeholder (To be implemented with computed or backend count) -->
             <!-- <div class="flex items-center gap-2 text-sm text-slate-600">
                <span class="material-icons-round text-[18px] text-slate-400">groups</span>
                <span>XX Estudiantes</span>
             </div> -->
             
             <button 
                @click="openStudentsModal(grupo)"
                class="w-full py-2.5 px-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-medium rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
             >
                <span class="material-icons-round text-[18px]">manage_accounts</span>
                Gestionar estudiantes
             </button>
        </div>
      </div>
    </div>

    <!-- Modal Crear/Editar Grupo -->
    <div v-if="modal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h3 class="text-lg font-bold text-slate-800">{{ modal.isEdit ? 'Editar grupo' : 'Nuevo grupo' }}</h3>
            <button @click="closeModal" class="text-slate-400 hover:text-slate-600 transition-colors">
                <span class="material-icons-round">close</span>
            </button>
        </div>
        
        <form @submit.prevent="saveGrupo" class="p-6 space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Nombre del grupo</label>
                <input 
                    v-model="modal.data.nombre" 
                    type="text" 
                    required
                    placeholder="Ej: 11-A" 
                    class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
            </div>

            <div v-if="sedes.length > 1">
                <label class="block text-sm font-medium text-slate-700 mb-1">Sede <span class="text-rose-500">*</span></label>
                <Select
                    v-model="modal.data.sede_id"
                    :options="sedes"
                    optionLabel="nombre"
                    optionValue="id"
                    placeholder="Selecciona una sede"
                    class="w-full"
                />
            </div>
            
            <div class="flex justify-end gap-3 pt-2">
                <button type="button" @click="closeModal" class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-medium transition-colors">
                    Cancelar
                </button>
                <button type="submit" :disabled="modal.saving" class="px-4 py-2 bg-primary hover:bg-indigo-600 text-white rounded-lg font-medium shadow-sm transition-all disabled:opacity-50">
                    {{ modal.saving ? 'Guardando...' : 'Guardar' }}
                </button>
            </div>
        </form>
      </div>
    </div>

    <!-- Modal Gestionar Estudiantes -->
    <div v-if="studentsModal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white w-full max-w-4xl h-[80vh] rounded-2xl shadow-xl overflow-hidden flex flex-col animate-in fade-in zoom-in duration-200">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <div>
                <h3 class="text-lg font-bold text-slate-800">Estudiantes en {{ studentsModal.grupo.nombre }}</h3>
                <p class="text-xs text-slate-500">Asigna o remueve estudiantes de este grupo</p>
            </div>
            <button @click="closeStudentsModal" class="text-slate-400 hover:text-slate-600 transition-colors">
                <span class="material-icons-round">close</span>
            </button>
        </div>

        <div class="flex-1 flex overflow-hidden">
            <!-- Columna Izquierda: Estudiantes del Grupo -->
            <div class="flex-1 border-r border-slate-100 flex flex-col p-4 bg-white">
                <h4 class="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                    <span class="material-icons-round text-emerald-500 text-sm">check_circle</span>
                    Asignados ({{ groupUsers.length }})
                </h4>
                <div class="flex-1 overflow-y-auto space-y-2">
                    <div v-if="loadingUsers" class="flex justify-center py-4">
                        <span class="animate-spin h-5 w-5 border-b-2 border-primary rounded-full"></span>
                    </div>
                    <div v-else-if="groupUsers.length === 0" class="text-center py-8 text-slate-400 text-sm">
                        No hay estudiantes asignados
                    </div>
                    <div 
                        v-for="user in groupUsers" 
                        :key="user.id"
                        class="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:border-slate-200 bg-slate-50/50 transition-colors"
                    >
                        <div class="flex items-center gap-3">
                            <div class="h-8 w-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">
                                {{ user.nombre.charAt(0).toUpperCase() }}
                            </div>
                            <div>
                                <p class="text-sm font-medium text-slate-800">{{ user.nombre }}</p>
                                <p class="text-[10px] text-slate-400">{{ user.email }}</p>
                            </div>
                        </div>
                        <button 
                            @click="removeUserFromGroup(user)"
                            class="text-rose-400 hover:text-rose-600 hover:bg-rose-50 p-1.5 rounded-md transition-colors"
                            title="Quitar del grupo"
                        >
                            <span class="material-icons-round text-[18px]">remove_circle_outline</span>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Columna Derecha: Estudiantes Disponibles -->
            <div class="flex-1 flex flex-col p-4 bg-slate-50/30">
                <h4 class="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                    <span class="material-icons-round text-slate-400 text-sm">person_add</span>
                    Disponibles (Sin Grupo)
                </h4>
                <!-- Buscador -->
                <div class="mb-3 relative">
                     <span class="material-icons-round absolute left-3 top-2.5 text-slate-400 text-[18px]">search</span>
                     <input 
                        v-model="searchQuery"
                        type="text"
                        placeholder="Buscar estudiante..."
                        class="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:ring-1 focus:ring-primary outline-none"
                     />
                </div>
                
                <div class="flex-1 overflow-y-auto space-y-2">
                    <div v-if="loadingUsers" class="flex justify-center py-4">
                         <span class="animate-spin h-5 w-5 border-b-2 border-slate-400 rounded-full"></span>
                    </div>
                    <div v-else-if="filteredAvailableUsers.length === 0" class="text-center py-8 text-slate-400 text-sm">
                        No hay estudiantes disponibles
                    </div>
                    <div 
                        v-for="user in filteredAvailableUsers" 
                        :key="user.id"
                        class="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:border-primary/30 transition-colors cursor-pointer group"
                        @click="addUserToGroup(user)"
                    >
                        <div class="flex items-center gap-3">
                            <div class="h-8 w-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center text-xs font-bold group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                                {{ user.nombre.charAt(0).toUpperCase() }}
                            </div>
                            <div>
                                <p class="text-sm font-medium text-slate-800">{{ user.nombre }}</p>
                                <p class="text-[10px] text-slate-400">{{ user.numero_documento }}</p>
                            </div>
                        </div>
                        <span class="material-icons-round text-slate-300 group-hover:text-primary transition-colors">add_circle_outline</span>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useGruposStore } from '../stores/grupos';
import { useUsuariosStore } from '../stores/usuarios';
import { useSedesStore } from '../stores/sedes';
import { useAuthStore } from '../stores/auth';
import Select from 'primevue/select';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';

const gruposStore = useGruposStore();
const usuariosStore = useUsuariosStore();
const sedesStore = useSedesStore();
const authStore = useAuthStore();
const toast = useToast();
const confirm = useConfirm();

const loading = ref(false);
const grupos = computed(() => gruposStore.grupos);
const sedes = computed(() => sedesStore.sedes);
const userInstitutionId = computed(() => authStore.user?.institucion_id);
const isInstitucionAdmin = computed(() => authStore.user?.rol?.nombre === 'admin');

// Datos del Modal Grupo
const modal = ref({
    show: false,
    isEdit: false,
    saving: false,
    data: { id: null, nombre: '', institucion_id: null, sede_id: null }
});

// Datos del Modal Estudiantes
const studentsModal = ref({
    show: false,
    grupo: null
});
const loadingUsers = ref(false);
const groupUsers = ref([]);
const availableUsers = ref([]);
const searchQuery = ref('');

// Computed fitrada localmente para disponibles
const filteredAvailableUsers = computed(() => {
    if (!searchQuery.value) return availableUsers.value;
    const q = searchQuery.value.toLowerCase();
    return availableUsers.value.filter(u => 
        u.nombre.toLowerCase().includes(q) || 
        u.numero_documento.includes(q) ||
        u.email?.toLowerCase().includes(q)
    );
});

onMounted(async () => {
    loading.value = true;
    try {
        if (isInstitucionAdmin.value) {
            await Promise.all([
                gruposStore.fetchGrupos(userInstitutionId.value),
                sedesStore.fetchSedes(userInstitutionId.value)
            ]);
        } else if (authStore.user?.rol?.nombre === 'admin') {
            await Promise.all([
                gruposStore.fetchGrupos(),
                sedesStore.fetchSedes()
            ]);
        }
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Error cargando grupos', life: 3000 });
    } finally {
        loading.value = false;
    }
});

const getDefaultSedeId = () => {
    return sedes.value.length === 1 ? sedes.value[0].id : null;
};

// --- Actions Grupos ---
const openModal = (grupo = null) => {
    if (grupo) {
        modal.value.isEdit = true;
        modal.value.data = { ...grupo };
    } else {
        modal.value.isEdit = false;
        modal.value.data = {
            nombre: '',
            institucion_id: userInstitutionId.value,
            sede_id: getDefaultSedeId()
        };
    }
    modal.value.show = true;
};

const closeModal = () => {
    modal.value.show = false;
};

const saveGrupo = async () => {
    if (sedes.value.length > 1 && !modal.value.data.sede_id) {
        toast.add({ severity: 'warn', summary: 'Sede requerida', detail: 'Selecciona una sede para el grupo', life: 4000 });
        return;
    }

    modal.value.saving = true;
    try {
        if (modal.value.isEdit) {
            const payload = { nombre: modal.value.data.nombre };
            if (sedes.value.length > 1) {
                payload.sede_id = modal.value.data.sede_id;
            }
            await gruposStore.updateGrupo(modal.value.data.id, payload);
            toast.add({ severity: 'success', summary: 'Actualizado', detail: 'Grupo actualizado', life: 3000 });
        } else {
            if (!modal.value.data.institucion_id) modal.value.data.institucion_id = userInstitutionId.value;
            await gruposStore.createGrupo(modal.value.data);
            toast.add({ severity: 'success', summary: 'Creado', detail: 'Grupo creado exitosamente', life: 3000 });
        }
        closeModal();
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: e.response?.data?.detail || e.message, life: 5000 });
    } finally {
        modal.value.saving = false;
    }
};

const confirmDelete = (grupo) => {
    confirm.require({
        message: `¿Estás seguro de eliminar el grupo "${grupo.nombre}"?`,
        header: 'Confirmar eliminación',
        icon: 'pi pi-exclamation-triangle',
        acceptLabel: 'Eliminar',
        rejectLabel: 'Cancelar',
        acceptProps: { severity: 'danger' },
        accept: async () => {
            try {
                await gruposStore.deleteGrupo(grupo.id);
                toast.add({ severity: 'success', summary: 'Eliminado', detail: 'Grupo eliminado', life: 3000 });
            } catch (e) {
                toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el grupo', life: 5000 });
            }
        }
    });
};

// --- Actions Estudiantes ---
const openStudentsModal = async (grupo) => {
    studentsModal.value.grupo = grupo;
    studentsModal.value.show = true;
    loadingUsers.value = true;
    try {
        // Cargar usuarios del grupo
        // Cargar usuarios sin grupo
        // Nota: Esto debería optimizarse en backend, pero:
        const [usersInGroup, usersAvailable] = await Promise.all([
             usuariosStore.fetchUsuariosGlobal({ grupo_id: grupo.id, rol: 'estudiante' }), // Modificado para pasar params
             // Para disponibles, cargamos TODOS los estudiantes de la inst y filtramos los que no tienen grupo
             // O usamos el nuevo param 'sin_grupo=true' en endpoint
             usuariosStore.fetchUsuariosGlobal({ sin_grupo: true, rol: 'estudiante' })
        ]);
        
        // Pinia fetchUsuariosGlobal sobrescribe 'usuarios', así que cuidado con llamadas paralelas que tocan el mismo state
        // Mejor hacer llamadas API directas aquí o usar actions que retornen data sin mutar state global único
        // Ups, usuariosStore.fetchUsuariosGlobal muta 'this.usuarios'. Eso es un problema si llamo dos veces paralelo.
        // Solución: Usar los retornos de las funciones que modificamos en el store, y no depender del state reactivo para estas listas temporales
        
        // Voy a asumir que modify en store devuelve response.data (verifiqué en store, sí retorna)
        groupUsers.value = usersInGroup; // usersInGroup es la data retornada
        availableUsers.value = usersAvailable;
        
    } catch (e) {
         toast.add({ severity: 'error', summary: 'Error', detail: 'Error cargando estudiantes', life: 3000 });
    } finally {
        loadingUsers.value = false;
    }
};

const closeStudentsModal = () => {
    studentsModal.value.show = false;
    groupUsers.value = [];
    availableUsers.value = [];
};

const addUserToGroup = async (user) => {
    // Optimistic UI updates could be nice, but simple async await is safer
    try {
        await usuariosStore.updateUser(user.id, { grupo_id: studentsModal.value.grupo.id });
        
        // Mover de available a group
        availableUsers.value = availableUsers.value.filter(u => u.id !== user.id);
        groupUsers.value.push({ ...user, grupo_id: studentsModal.value.grupo.id });
        
        toast.add({ severity: 'success', summary: 'Asignado', detail: `${user.nombre} agregado al grupo`, life: 2000 });
    } catch (e) {
         toast.add({ severity: 'error', summary: 'Error', detail: 'Falló la asignación', life: 3000 });
    }
};

const removeUserFromGroup = async (user) => {
    try {
        await usuariosStore.updateUser(user.id, { grupo_id: null }); // Unassign
        
        // Mover de group a available
        groupUsers.value = groupUsers.value.filter(u => u.id !== user.id);
        availableUsers.value.push({ ...user, grupo_id: null });
        
         toast.add({ severity: 'info', summary: 'Removido', detail: `${user.nombre} quitado del grupo`, life: 2000 });
    } catch (e) {
         toast.add({ severity: 'error', summary: 'Error', detail: 'Falló al quitar estudiante', life: 3000 });
    }
};

</script>

<style scoped>
.animate-in {
    animation-fill-mode: both;
}
.fade-in {
    animation-name: fadeIn;
}
.zoom-in {
    animation-name: zoomIn;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes zoomIn {
    from { transform: scale(0.95); }
    to { transform: scale(1); }
}
</style>
