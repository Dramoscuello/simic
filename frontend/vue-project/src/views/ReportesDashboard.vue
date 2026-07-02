<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 sm:p-6">
    
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Panel de resultados</h2>
      </div>
      
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
      <!-- Estudiantes -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 relative overflow-hidden group">
         <div class="absolute right-0 top-0 w-24 h-24 bg-blue-50 dark:bg-blue-900/20 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
         <p class="text-sm font-medium text-slate-500 dark:text-slate-400 relative z-10">Estudiantes evaluados</p>
         <div class="flex items-end gap-2 mt-2 relative z-10">
            <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ stats.total_estudiantes_activos }}</span>
            <span class="text-xs text-emerald-500 font-medium mb-1 flex items-center">
               <span class="material-icons-round text-[14px]">trending_up</span> Activos
            </span>
         </div>
      </div>

      <!-- Promedio -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 relative overflow-hidden group">
         <div class="absolute right-0 top-0 w-24 h-24 bg-indigo-50 dark:bg-indigo-900/20 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
         <p class="text-sm font-medium text-slate-500 dark:text-slate-400 relative z-10">Promedio global</p>
         <div class="flex items-end gap-2 mt-2 relative z-10">
            <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ stats.promedio_global }}</span>
            <span class="text-xs text-slate-400 font-medium mb-1">/ 100</span>
         </div>
         <div class="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full mt-3 overflow-hidden">
             <div class="bg-indigo-500 h-full rounded-full transition-all duration-1000" :style="{ width: `${stats.promedio_global}%` }"></div>
         </div>
      </div>

      <!-- Simulacros -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 relative overflow-hidden group">
         <div class="absolute right-0 top-0 w-24 h-24 bg-purple-50 dark:bg-purple-900/20 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
         <p class="text-sm font-medium text-slate-500 dark:text-slate-400 relative z-10">Exámenes realizados</p>
         <div class="flex items-end gap-2 mt-2 relative z-10">
            <span class="text-3xl font-bold text-slate-800 dark:text-white">{{ stats.total_simulacros_realizados }}</span>
         </div>
      </div>

      <!-- Alerta -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 relative overflow-hidden group">
         <div class="absolute right-0 top-0 w-24 h-24 bg-amber-50 dark:bg-amber-900/20 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
         <p class="text-sm font-medium text-slate-500 dark:text-slate-400 relative z-10">Áreas de atención</p>
         <div class="flex flex-wrap gap-2 mt-3 relative z-10">
             <span 
                v-for="area in stats.areas_criticas" 
                :key="area"
                class="px-2 py-1 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-xs rounded-md font-bold"
             >
                {{ formatAreaName(area) }}
             </span>
         </div>
      </div>
    </div>

    <!-- MAIN DASHBOARD: 2 COLUMNS -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[500px]">
        
        <!-- COLUMN 1: Reportes Individuales -->
        <ReportSummaryColumn 
            title="Individuales recientes" 
            icon="person" 
            color="blue"
            :items="individuales"
            :loading="loading"
            class="animate-in fade-in slide-in-from-left-4 duration-500 delay-100"
            @view-history="goToHistory('individual')"
        >
            <template #item="{ item }">
                <ReportCard 
                    :title="item.subtitulo"
                    :subtitle="item.titulo"
                    :date="item.fecha"
                    :score="item.puntaje"
                    :tags="item.tags"
                    :fraude="item.fraude"
                    icon="description"
                    color="blue"
                    @click="openReporte(item)"
                />
            </template>
        </ReportSummaryColumn>

        <!-- COLUMN 2: Reportes Grupales -->
        <ReportSummaryColumn 
            title="Diagnósticos grupales" 
            icon="groups" 
            color="emerald"
            :items="grupales"
            :loading="loading"
            class="animate-in fade-in slide-in-from-right-4 duration-500 delay-300"
            @view-history="goToHistory('grupal')"
        >
            <template #item="{ item }">
                <ReportCard 
                    :title="item.titulo"
                    :subtitle="item.subtitulo"
                    :date="item.fecha"
                    :tags="item.tags"
                    icon="analytics"
                    color="emerald"
                    @click="openReporte(item)"
                />
            </template>
        </ReportSummaryColumn>

    </div>

    <!-- Modal Detalle Reporte -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
       <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="showModal = false"></div>
       <div class="relative w-full max-w-4xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-in zoom-in-95 duration-200">
          
          <!-- Modal Header -->
          <div class="bg-indigo-600 dark:bg-indigo-900 text-white p-6 flex justify-between items-center sticky top-0 z-10 shrink-0 shadow-md">
             <div class="flex items-center gap-3 overflow-hidden">
                <div class="p-2 bg-white/20 rounded-lg shrink-0 flex items-center justify-center w-10 h-10">
                    <span v-if="modalLoading" class="animate-spin h-5 w-5 block border-2 border-white/50 border-t-white rounded-full"></span>
                    <span v-else class="material-icons-round text-white block text-xl">description</span>
                </div>
                <div class="min-w-0">
                    <h3 class="font-bold text-lg truncate">{{ modalData?.titulo || 'Cargando reporte...' }}</h3>
                    <p class="text-indigo-200 text-xs truncate">{{ modalData?.subtitulo }}</p>
                </div>
             </div>
             <button @click="showModal = false" class="p-2 hover:bg-white/20 rounded-full transition-colors shrink-0">
                 <span class="material-icons-round text-2xl">close</span>
             </button>
          </div>

          <!-- Modal Body -->
          <div id="reporte-content" class="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-slate-900 prose dark:prose-invert max-w-none">
             <div v-if="modalLoading" class="flex flex-col items-center justify-center py-20 space-y-4">
                 <div class="animate-spin rounded-full h-12 w-12 border-4 border-slate-200 border-t-indigo-600"></div>
                 <p class="text-slate-400">Recuperando informe completo...</p>
             </div>
             
             <!-- ESTADO: FRAUDE -->
             <div v-else-if="modalData && modalData.fraude" class="text-center py-12">
                 <div class="inline-flex p-4 bg-rose-50 dark:bg-rose-900/30 rounded-full mb-4 border-2 border-rose-200 dark:border-rose-800">
                    <span class="material-icons-round text-rose-600 dark:text-rose-400 text-5xl">gavel</span>
                 </div>
                 <h4 class="text-2xl font-bold text-rose-700 dark:text-rose-400 mb-2">PRUEBA ANULADA</h4>
                 <div class="max-w-md mx-auto space-y-2 text-slate-600 dark:text-slate-300">
                     <p>Este reporte no está disponible porque el examen fue sancionado por fraude.</p>
                     <p class="text-sm bg-rose-50 dark:bg-rose-900/10 p-3 rounded-lg border border-rose-100 dark:border-rose-900/50">
                        Nota asignada: <strong>0.0</strong><br>
                        Estado: <strong>Sancionado</strong>
                     </p>
                 </div>
             </div>

             <!-- ESTADO: NUMÉRICO (Grupal) -->
             <div
               v-else-if="modalData && modalData.tipo_contenido === 'numerico' && modalData.data && selectedItem?.tipo_reporte === 'grupal'"
               class="not-prose space-y-6 animate-fade-in"
             >
                 <h3 class="text-2xl font-black text-slate-900 dark:text-white">Reporte grupal numérico</h3>

                 <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                     <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                         <p class="text-xs uppercase tracking-wide text-slate-500">Institución</p>
                         <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ modalData.data.institution_name || 'N/A' }}</p>
                     </div>
                     <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                         <p class="text-xs uppercase tracking-wide text-slate-500">Área</p>
                         <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ modalData.data.area_display || modalData.data.area || 'N/A' }}</p>
                     </div>
                     <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                         <p class="text-xs uppercase tracking-wide text-slate-500">Finalizados</p>
                         <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ modalData.data.students_count || 0 }}</p>
                     </div>
                     <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                         <p class="text-xs uppercase tracking-wide text-slate-500">Rango</p>
                         <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">
                             {{ formatScore100(modalData.data.min_score_100) }} - {{ formatScore100(modalData.data.max_score_100) }}
                         </p>
                     </div>
                     <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                         <p class="text-xs uppercase tracking-wide text-slate-500">Nivel de desempeño</p>
                         <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">
                             {{ modalData.data.performance_level || 'N/A' }}
                             <span v-if="modalData.data.performance_interval" class="text-slate-500 font-medium">
                                 ({{ modalData.data.performance_interval }})
                             </span>
                         </p>
                     </div>
                     <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                         <p class="text-xs uppercase tracking-wide text-slate-500">Fecha de generación</p>
                         <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ modalData.data.generated_at || 'N/A' }}</p>
                     </div>
                 </div>

                 <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 text-center">
                     <h4 class="text-lg font-extrabold text-slate-900 dark:text-white">Reporte general</h4>
                     <div class="relative w-52 h-52 mx-auto mt-5">
                         <div class="absolute inset-0 rounded-full" :style="groupProgressStyle(modalData.data.average_score_100)"></div>
                         <div class="absolute inset-[14px] rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center">
                             <span class="text-5xl font-black text-indigo-600 dark:text-indigo-400">{{ formatScore(modalData.data.average_score_100) }}</span>
                             <span class="text-sm font-bold text-slate-500">/100</span>
                             <span class="text-xs font-bold text-blue-700 dark:text-blue-300 mt-1">
                                 {{ modalData.data.performance_level || 'N/A' }}
                             </span>
                         </div>
                     </div>
                 </div>

                 <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 md:p-5">
                     <h4 class="text-base font-extrabold text-slate-900 dark:text-white mb-3">Detalle por estudiante</h4>
                     <div class="overflow-x-auto">
                         <table class="min-w-full text-sm border-collapse">
                             <thead>
                                 <tr class="bg-indigo-600 text-white">
                                     <th class="px-3 py-2 text-center font-bold w-14">#</th>
                                     <th class="px-3 py-2 text-left font-bold">Estudiante</th>
                                     <th class="px-3 py-2 text-center font-bold w-40">Nota (N/100)</th>
                                 </tr>
                             </thead>
                             <tbody>
                                 <tr
                                     v-for="(student, idx) in (modalData.data.students || [])"
                                     :key="`${student.name}-${idx}`"
                                     class="odd:bg-slate-50 dark:odd:bg-slate-800 even:bg-white dark:even:bg-slate-900 border-b border-slate-100 dark:border-slate-700"
                                 >
                                     <td class="px-3 py-2 text-center font-semibold text-slate-600 dark:text-slate-300">{{ idx + 1 }}</td>
                                     <td class="px-3 py-2 text-slate-900 dark:text-slate-100 font-medium">{{ student.name }}</td>
                                     <td class="px-3 py-2 text-center">
                                         <span class="inline-flex items-center rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-3 py-1 text-xs font-bold">
                                             {{ formatScore100(student.score_100) }}
                                         </span>
                                     </td>
                                 </tr>
                                 <tr v-if="!(modalData.data.students || []).length">
                                     <td colspan="3" class="px-3 py-5 text-center text-slate-500">Sin estudiantes para mostrar.</td>
                                 </tr>
                             </tbody>
                         </table>
                     </div>
                 </div>
             </div>

             <div v-else-if="modalData && modalData.contenido" v-html="renderMarkdown(modalData.contenido)"></div>
             <div v-else class="flex flex-col items-center justify-center py-20 text-slate-400">
                 <span class="material-icons-round text-4xl mb-2">content_paste_off</span>
                 <p>No se pudo cargar el contenido del reporte.</p>
             </div>
          </div>
          
          <!-- Modal Footer -->
          <div v-if="!modalLoading" class="p-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex justify-end gap-2 shrink-0">
              <button
                @click="downloadReport"
                :disabled="modalData?.fraude"
                class="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
              >
                  <span class="material-icons-round text-[18px]">download</span>
                  Descargar PDF
              </button>
              <button @click="showModal = false" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold shadow-md shadow-indigo-500/20 transition-all hover:translate-y-[-1px]">
                  Cerrar
              </button>
          </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/axios';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';
import html2pdf from 'html2pdf.js';

import ReportSummaryColumn from '../components/dashboard/ReportSummaryColumn.vue'; 
import ReportCard from '../components/dashboard/ReportCard.vue';

dayjs.extend(relativeTime);
dayjs.locale('es');

const router = useRouter();
const loading = ref(true);
const stats = ref({
    total_estudiantes_activos: 0,
    promedio_global: 0,
    total_simulacros_realizados: 0
});

const individuales = ref([]);
const grupales = ref([]);

const showModal = ref(false);
const modalData = ref(null);
const modalLoading = ref(false);
const selectedItem = ref(null);

const fetchData = async () => {
    loading.value = true;
    try {
        const res = await api.get('/reportes/dashboard');
        const data = res.data;
        
        stats.value = data.stats;
        individuales.value = data.individuales || [];
        grupales.value = data.grupales || [];
        
    } catch (e) {
        console.error("Error loading dashboard data:", e);
    } finally {
        loading.value = false;
    }
};

const openReporte = async (item) => {
    selectedItem.value = item;
    modalData.value = null;
    showModal.value = true;
    modalLoading.value = true;
    
    try {
        const res = await api.get(`/reportes/detalle/${item.tipo_reporte}/${item.id}`);
        modalData.value = res.data;
    } catch(e) {
        console.error("Error fetching report detail:", e);
        modalData.value = {
            titulo: "Error",
            subtitulo: "No se pudo cargar el reporte",
            contenido: "Ocurrió un error al cargar el detalle del reporte. Intente nuevamente."
        };
    } finally {
        modalLoading.value = false;
    }
};

const goToHistory = (tipo) => {
    router.push({ name: 'reportes-historico', params: { tipo } });
};

const downloadReport = async () => {
    if (!selectedItem.value || !modalData.value || modalData.value.fraude) return;

    const meta = selectedItem.value.metadata || {};
    if (selectedItem.value.tipo_reporte === 'individual') {
        try {
            const url = `/reportes/detalle/individual/${selectedItem.value.id}/pdf`;
            const response = await api.get(url, { responseType: 'blob' });
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = `Informe_IA_${selectedItem.value.id}.pdf`;
            link.click();
            return;
        } catch (e) {
            console.error("Error descargando PDF individual backend", e);
        }
    }

    if (selectedItem.value.tipo_reporte === 'grupal' && meta.simulacro_id) {
        try {
            const url = `/simulacros/${meta.simulacro_id}/reporte-grupal/pdf`;
            const response = await api.get(url, { responseType: 'blob' });
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = `Reporte_Grupal_${modalData.value?.subtitulo || 'Area'}.pdf`;
            link.click();
            return;
        } catch (e) {
            console.error("Error descargando PDF grupal backend", e);
        }
    }

    const element = document.getElementById('reporte-content');
    if (!element) return;
    const opt = {
        margin: 0.5,
        filename: `Reporte_${new Date().toISOString().slice(0,10)}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(element).save();
};

const formatAreaName = (name) => {
    if (!name) return '';
    const map = {
        'MATEMATICAS': 'Matemáticas',
        'LECTURA_CRITICA': 'Lectura Crítica',
        'SOCIALES_CIUDADANAS': 'Sociales',
        'CIENCIAS_NATURALES': 'Ciencias',
        'INGLES': 'Inglés'
    };
    return map[name] || name;
};

const formatScore = (value) => {
    const n = Number(value);
    if (!Number.isFinite(n)) return '0.0';
    return n.toFixed(1);
};

const formatScore100 = (value) => `${formatScore(value)}/100`;

const groupProgressStyle = (value) => {
    const n = Number(value);
    const pct = Number.isFinite(n) ? Math.max(0, Math.min(100, n)) : 0;
    const deg = pct * 3.6;
    return {
        background: `conic-gradient(#4f46e5 0deg ${deg}deg, #e2e8f0 ${deg}deg 360deg)`
    };
};

const renderMarkdown = (text) => {
   if (!text) return '';
   return text
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2 text-slate-800 dark:text-slate-100">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-6 mb-3 text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-700 pb-2">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-6 mb-4 text-slate-900 dark:text-white">$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc marker:text-indigo-500">$1</li>')
      .replace(/\n/gim, '<br />');
};

onMounted(() => {
    fetchData();
});
</script>
