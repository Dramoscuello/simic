<template>
  <div class="font-sans bg-slate-50 min-h-screen">
    <!-- Header -->
    <div class="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between sticky top-0 z-10 shadow-sm">
      <div class="flex items-center gap-4">
        <button @click="$router.push('/admin/dashboard')" class="text-slate-400 hover:text-slate-600 transition-colors">
          <span class="material-icons-round">arrow_back</span>
        </button>
        <div>
          <h1 class="text-xl font-bold text-slate-800 flex items-center gap-2">
            <span class="material-icons-round text-rose-500">policy</span>
            Sala de inspección
          </h1>
          <p class="text-sm text-slate-500">Monitoreo antifraude en tiempo real</p>
        </div>
      </div>
      
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-xs font-bold uppercase tracking-wider border border-green-200 animate-pulse">
          <span class="w-2 h-2 rounded-full bg-green-500"></span>
          En Vivo
        </div>
        <button 
          @click="clearLogs"
          class="text-slate-500 text-sm font-medium hover:text-rose-600 transition-colors flex items-center gap-1"
        >
          <span class="material-icons-round text-[18px]">delete_sweep</span>
          Limpiar todo
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="p-8 max-w-7xl mx-auto">
      
      <!-- Stats Summary -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div class="p-3 bg-rose-50 text-rose-600 rounded-lg">
            <span class="material-icons-round text-2xl">warning</span>
          </div>
          <div>
            <h3 class="text-2xl font-bold text-slate-800">{{ totalIncidents }}</h3>
            <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Alertas totales</p>
          </div>
        </div>
        
        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div class="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <span class="material-icons-round text-2xl">group_off</span>
          </div>
          <div>
            <h3 class="text-2xl font-bold text-slate-800">{{ activeStudentsCount }}</h3>
            <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Estudiantes sospechosos</p>
          </div>
        </div>
        
         <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div class="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <span class="material-icons-round text-2xl">assignment_turned_in</span>
          </div>
          <div>
            <h3 class="text-2xl font-bold text-slate-800">{{ finishedCount }}</h3>
            <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Finalizados (Pend. Acción)</p>
          </div>
        </div>

        <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
          <div class="p-3 bg-slate-50 text-slate-600 rounded-lg">
            <span class="material-icons-round text-2xl">gavel</span>
          </div>
          <div>
            <h3 class="text-2xl font-bold text-slate-800">{{ sanctionedCount }}</h3>
            <p class="text-xs text-slate-500 uppercase font-bold tracking-wider">Sancionados</p>
          </div>
        </div>
      </div>

      <!-- Live Feed Cards -->
      <div v-if="Object.keys(studentsMap).length === 0" class="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400 flex flex-col items-center">
          <span class="material-icons-round text-6xl mb-4 text-slate-200">security</span>
           <h3 class="text-lg font-bold text-slate-600">Sala tranquila</h3>
          <p>No se han detectado incidentes ni finalizaciones recientes.</p>
          <p class="text-xs mt-2 font-mono">Estado WS: {{ connectionStatus }}</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <transition-group name="card">
            <div 
              v-for="student in sortedStudents" 
              :key="student.studentId"
              class="bg-white rounded-xl shadow-sm border transition-all duration-300 relative overflow-hidden group"
              :class="getStatusBorderClass(student)"
            >
                <!-- Status Banner -->
                <div class="absolute top-0 left-0 right-0 h-1.5" :class="getStatusColorClass(student)"></div>
                
                <div class="p-6">
                    <!-- Header -->
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex items-center gap-3">
                             <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-sm" :class="getStatusColorClass(student)">
                                {{ getInitials(student.studentName) }}
                            </div>
                            <div>
                                <h3 class="font-bold text-slate-800 leading-tight">{{ student.studentName }}</h3>
                                <p class="text-xs text-slate-500">{{ student.simulacroTitle }}</p>
                            </div>
                        </div>
                        
                        <!-- Badge Estado -->
                        <span class="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wide border" :class="getStatusBadgeClass(student)">
                            {{ getStatusLabel(student) }}
                        </span>
                    </div>
                    
                    <!-- Metrics -->
                    <div class="flex items-center gap-4 mb-6 p-3 bg-slate-50 rounded-lg border border-slate-100">
                        <div class="text-center flex-1 border-r border-slate-200">
                            <span class="block text-2xl font-bold text-rose-600">{{ student.incidentCount || 0 }}</span>
                            <span class="text-[10px] uppercase text-slate-400 font-bold">Alertas foco</span>
                        </div>
                        <div class="text-center flex-1">
                             <span class="block text-2xl font-bold text-slate-700">
                                 {{ student.puntaje !== null ? Math.round(student.puntaje) : '--' }}
                             </span>
                             <span class="text-[10px] uppercase text-slate-400 font-bold">Puntaje</span>
                        </div>
                    </div>
                    
                    <!-- Info Text -->
                    <div class="space-y-2 mb-6 text-sm">
                        <div v-if="student.lastIncident" class="flex items-center gap-2 text-rose-600 bg-rose-50 px-2 py-1 rounded-md">
                            <span class="material-icons-round text-sm">schedule</span>
                            <span class="text-xs font-medium">Última alerta: {{ formatTime(student.lastIncident) }}</span>
                        </div>
                         <div v-if="student.fraude" class="flex items-center gap-2 text-red-700 bg-red-100 px-2 py-1 rounded-md border border-red-200">
                            <span class="material-icons-round text-sm">gavel</span>
                            <span class="text-xs font-bold">FRAUDE CONFIRMADO</span>
                        </div>
                    </div>
                    
                    <!-- Actions Footer -->
                    <div class="flex gap-2 mt-auto">
                        <button 
                            @click="removeStudent(student.studentId)"
                            class="flex-1 py-2 rounded-lg text-xs font-bold text-slate-500 hover:bg-slate-50 border border-slate-200 transition-colors"
                        >
                            Ocultar
                        </button>
                        
                        <button 
                            v-if="!student.fraude"
                            @click="openSanctionModal(student)"
                            :disabled="student.status !== 'finalizado' || student.sanctioning"
                            class="flex-1 py-2 rounded-lg text-xs font-bold text-white transition-all shadow-sm flex items-center justify-center gap-1"
                            :class="student.status === 'finalizado' ? 'bg-rose-600 hover:bg-rose-700 border-rose-700 shadow-rose-200' : 'bg-slate-300 cursor-not-allowed'"
                            :title="student.status !== 'finalizado' ? 'Espera a que termine el examen' : 'Sancionar estudiante'"
                        >
                            <span v-if="student.sanctioning" class="material-icons-round animate-spin text-sm">autorenew</span>
                            <span v-else class="material-icons-round text-sm">gavel</span>
                            Sancionar
                        </button>
                        
                         <button 
                            v-else
                            disabled
                            class="flex-1 py-2 rounded-lg text-xs font-bold bg-slate-100 text-slate-400 border border-slate-200 cursor-default"
                        >
                            Sancionado
                        </button>
                    </div>
                </div>
            </div>
          </transition-group>
      </div>
    </div>
    <!-- Sanction Modal -->
    <div v-if="showSanctionModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="closeSanctionModal"></div>
        
        <!-- Modal Content -->
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100">
            <!-- Header -->
            <div class="bg-rose-50 px-6 py-4 border-b border-rose-100 flex items-center gap-3">
                <div class="p-2 bg-rose-100 rounded-full text-rose-600">
                    <span class="material-icons-round text-xl">gavel</span>
                </div>
                <h3 class="text-lg font-bold text-rose-900">Confirmar sanción</h3>
            </div>
            
            <!-- Body -->
            <div class="p-6">
                <p class="text-slate-600 mb-4">
                    Estás a punto de sancionar por <strong>FRAUDE</strong> al estudiante:
                </p>
                
                <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-6 flex items-center gap-4">
                    <div class="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-500 text-lg">
                         {{ getInitials(studentToSanction?.studentName) }}
                    </div>
                    <div>
                        <h4 class="font-bold text-slate-800">{{ studentToSanction?.studentName }}</h4>
                        <p class="text-sm text-slate-500">{{ studentToSanction?.incidentCount }} alertas detectadas</p>
                    </div>
                </div>
                
                <div class="space-y-3 text-sm text-slate-600 bg-rose-50/50 p-4 rounded-lg border border-rose-100">
                    <p class="flex items-start gap-2">
                        <span class="material-icons-round text-rose-500 text-base mt-0.5">check_circle</span>
                        <span>Se anulará el simulacro actual.</span>
                    </p>
                    <p class="flex items-start gap-2">
                        <span class="material-icons-round text-rose-500 text-base mt-0.5">check_circle</span>
                        <span>La calificación final será <strong>0.0</strong>.</span>
                    </p>
                    <p class="flex items-start gap-2">
                        <span class="material-icons-round text-rose-500 text-base mt-0.5">check_circle</span>
                        <span>Se eliminarán los informes asociados.</span>
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-3">
                <button 
                    @click="closeSanctionModal"
                    class="px-4 py-2 text-sm font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-200/50 rounded-lg transition-colors"
                >
                    Cancelar
                </button>
                <button 
                    @click="confirmSanction"
                    :disabled="isProcessing"
                    class="px-4 py-2 text-sm font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow-lg shadow-rose-200 flex items-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                >
                    <span v-if="isProcessing" class="material-icons-round animate-spin text-sm">autorenew</span>
                    <span v-else class="material-icons-round text-sm">gavel</span>
                    Confirmar Sanción
                </button>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useAuthStore } from '../../stores/auth';
import api from '../../api/axios';
import { useToast } from 'primevue/usetoast';

const authStore = useAuthStore();
const toast = useToast();

// Structure: { studentId: { ...data } }
const studentsMap = ref({});
const connectionStatus = ref('Desconectado');
let ws = null;

// Modal State
const showSanctionModal = ref(false);
const studentToSanction = ref(null);
const isProcessing = ref(false);

const STORAGE_KEY = 'inspeccion_logs_map_v2'; // Changed key version

onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      studentsMap.value = JSON.parse(saved);
    } catch(e) { console.error("Error loading logs", e); }
  }
  connectWS();
});

watch(studentsMap, (newVal) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newVal));
}, { deep: true });

// --- Computed ---
const sortedStudents = computed(() => {
    return Object.values(studentsMap.value).sort((a, b) => {
        // Priorizar: Finalizados no sancionados > En curso > Sancionados > Fecha
        if (a.fraude && !b.fraude) return 1;
        if (!a.fraude && b.fraude) return -1;
        
        if (a.status === 'finalizado' && b.status !== 'finalizado') return -1;
        if (a.status !== 'finalizado' && b.status === 'finalizado') return 1;
        
        return new Date(b.lastUpdate) - new Date(a.lastUpdate);
    });
});

const totalIncidents = computed(() => {
    return Object.values(studentsMap.value).reduce((sum, s) => sum + (s.incidentCount || 0), 0);
});
const activeStudentsCount = computed(() => {
    return Object.values(studentsMap.value).filter(s => s.status === 'en_curso' && s.incidentCount > 0).length;
});
const finishedCount = computed(() => {
    return Object.values(studentsMap.value).filter(s => s.status === 'finalizado' && !s.fraude).length;
});
const sanctionedCount = computed(() => {
     return Object.values(studentsMap.value).filter(s => s.fraude).length;
});

// --- WebSocket ---
const getWsBaseUrl = () => {
  const rawBase = import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_URL || window.location.origin;
  try {
    const parsed = new URL(rawBase, window.location.origin);
    const wsProtocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
    const isFrontendDevPort = parsed.port === '5173' || parsed.port === '5174';
    if (isFrontendDevPort && !import.meta.env.VITE_WS_URL && !import.meta.env.VITE_API_URL) {
      return `${wsProtocol}//${window.location.hostname}:8000`;
    }
    return `${wsProtocol}//${parsed.host}`;
  } catch (_) {
    const fallbackProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${fallbackProtocol}//${window.location.hostname}:8000`;
  }
};

const connectWS = () => {
  if (!authStore.user?.institucion_id) return;
  const wsUrl = `${getWsBaseUrl()}/monitoreo/ws/alertas/${authStore.user.institucion_id}`;
  
  ws = new WebSocket(wsUrl);
  
  ws.onopen = () => { connectionStatus.value = 'Conectado 🟢'; };
  ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.evento === 'fraude_detectado') handleFraudAlert(payload);
        if (payload.evento === 'simulacro_finalizado') handleSimulacroEnd(payload);
      } catch (e) { console.error(e); }
  };
  ws.onclose = () => { connectionStatus.value = 'Desconectado 🔴'; };
};

const handleFraudAlert = (payload) => {
    const data = payload.data;
    const sid = data.estudiante_id;
    
    // Si no existe, crear entry
    if (!studentsMap.value[sid]) {
        studentsMap.value[sid] = {
            studentId: sid,
            studentName: data.estudiante_nombre,
            simulacroId: data.simulacro_id,
            simulacroTitle: data.simulacro_titulo,
            status: 'en_curso',
            incidentCount: 0,
            lastIncident: null,
            fraude: false,
            respuestaId: null, // No lo tenemos aún
            puntaje: null,
            lastUpdate: new Date().toISOString()
        };
    }
    
    // Actualizar entry
    const student = studentsMap.value[sid];
    student.incidentCount++;
    student.lastIncident = payload.server_time;
    student.lastUpdate = new Date().toISOString();
    
    // Play sound?
};

const handleSimulacroEnd = (payload) => {
    const data = payload.data;
    const sid = data.estudiante_id;
    
    if (!studentsMap.value[sid]) {
         studentsMap.value[sid] = {
            studentId: sid,
            studentName: data.estudiante_nombre,
            simulacroId: data.simulacro_id,
            simulacroTitle: "Simulacro", 
            status: 'finalizado',
            incidentCount: 0,
            lastIncident: null,
            fraude: data.fraude,
            respuestaId: data.respuesta_id,
            puntaje: data.puntaje,
            lastUpdate: new Date().toISOString()
        };
    } else {
        const student = studentsMap.value[sid];
        student.status = 'finalizado';
        student.respuestaId = data.respuesta_id;
        student.puntaje = data.puntaje;
        student.fraude = data.fraude;
        student.lastUpdate = new Date().toISOString();
    }
    
    toast.add({ severity: 'info', summary: 'Simulacro Finalizado', detail: `${data.estudiante_nombre} ha terminado.`, life: 3000 });
};

// --- Actions ---
const clearLogs = () => {
    if(confirm("¿Borrar todo?")) {
        studentsMap.value = {};
        localStorage.removeItem(STORAGE_KEY);
    }
};

const removeStudent = (sid) => {
    delete studentsMap.value[sid];
};

const openSanctionModal = (student) => {
    studentToSanction.value = student;
    showSanctionModal.value = true;
};

const closeSanctionModal = () => {
    showSanctionModal.value = false;
    studentToSanction.value = null;
};

const confirmSanction = async () => {
    const student = studentToSanction.value;
    if (!student || !student.respuestaId) return;

    isProcessing.value = true;
    student.sanctioning = true;
    
    try {
        await api.put(`/monitoreo/respuestas/${student.respuestaId}/fraude`, {
          confirmado: true,
          motivo: `Sanción manual desde sala de inspección. ${student.incidentCount} alertas.`
        });
        
        student.fraude = true;
        student.puntaje = 0;
        toast.add({ severity: 'success', summary: 'Sancionado', detail: 'El estudiante ha sido sancionado correctamente.' });
        closeSanctionModal();
    } catch (e) {
        console.error(e);
        toast.add({ severity: 'error', summary: 'Error', detail: 'Falló la sanción en servidor' });
    } finally {
        isProcessing.value = false;
        student.sanctioning = false;
    }
};

// --- Helpers ---
const getInitials = (name) => name ? name.substring(0,2).toUpperCase() : '??';
const formatTime = (iso) => iso ? new Date(iso).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : '';

const getStatusBorderClass = (s) => {
    if (s.fraude) return 'border-red-200 shadow-red-50';
    if (s.status === 'finalizado') return 'border-emerald-200 shadow-emerald-50';
    if (s.incidentCount > 3) return 'border-rose-300 shadow-rose-50';
    return 'border-slate-200';
};
const getStatusColorClass = (s) => {
    if (s.fraude) return 'bg-red-500';
    if (s.status === 'finalizado') return 'bg-emerald-500';
    if (s.incidentCount > 0) return 'bg-rose-500';
    return 'bg-slate-400';
};
const getStatusBadgeClass = (s) => {
    if (s.fraude) return 'bg-red-50 text-red-700 border-red-200';
    if (s.status === 'finalizado') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    return 'bg-amber-50 text-amber-700 border-amber-200';
};
const getStatusLabel = (s) => {
    if (s.fraude) return 'SANCIONADO';
    if (s.status === 'finalizado') return 'FINALIZADO';
    if (s.status === 'en_curso') return 'EN CURSO';
    return s.status;
};

onUnmounted(() => { if(ws) ws.close(); });
</script>

<style scoped>
.card-move,
.card-enter-active,
.card-leave-active {
  transition: all 0.5s ease;
}
.card-enter-from,
.card-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
.card-leave-active {
  position: absolute;
}
</style>
