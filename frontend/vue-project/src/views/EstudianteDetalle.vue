<template>
  <div class="mx-auto w-full max-w-7xl flex flex-col gap-8 pb-12 relative animate-fade-in">
    
    <!-- Back & Header -->
    <div class="space-y-6">
       <button @click="router.push('/estudiantes')" class="flex items-center text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors">
          <span class="material-icons-round mr-1">arrow_back</span> Volver a lista
       </button>
       
       <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-8 flex flex-col md:flex-row gap-8 items-start md:items-center">
          <div v-if="loadingStudent" class="animate-pulse flex items-center gap-6 w-full">
             <div class="w-24 h-24 rounded-full bg-slate-200 dark:bg-slate-700"></div>
             <div class="space-y-3 flex-1">
                <div class="h-8 w-1/3 bg-slate-200 dark:bg-slate-700 rounded"></div>
                <div class="h-4 w-1/4 bg-slate-200 dark:bg-slate-700 rounded"></div>
             </div>
          </div>
          <div v-else class="flex items-center gap-6 w-full">
             <div class="w-24 h-24 rounded-full bg-primary/10 dark:bg-primary/20 text-primary dark:text-primary-400 flex items-center justify-center font-bold text-3xl border-4 border-white dark:border-slate-800 shadow-lg">
                {{ getInitials(estudiante?.nombre) }}
             </div>
             <div>
                <h1 class="text-3xl font-bold text-slate-900 dark:text-white">{{ estudiante?.nombre }}</h1>
                <div class="flex flex-wrap gap-4 mt-2 text-slate-500 dark:text-slate-400">
                   <span class="flex items-center gap-1"><span class="material-icons-round text-base">badge</span> {{ estudiante?.numero_documento }}</span>
                   <span class="flex items-center gap-1"><span class="material-icons-round text-base">email</span> {{ estudiante?.email }}</span>
                </div>
             </div>
             
             <div class="ml-auto flex gap-4 text-center">
                  <div class="px-6 py-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-100 dark:border-slate-600">
                      <div class="text-2xl font-bold text-slate-800 dark:text-white">{{ historial.length }}</div>
                      <div class="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Simulacros</div>
                  </div>
                  <div class="px-6 py-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-100 dark:border-slate-600">
                      <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ promedioScore }}%</div>
                      <div class="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Promedio</div>
                  </div>
             </div>
          </div>
       </div>
    </div>

    <!-- Filters & Content -->
    <div class="flex flex-col lg:flex-row gap-8">
       
       <!-- Sidebar Filters -->
       <div class="w-full lg:w-64 flex-shrink-0 space-y-6">
          <div>
            <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Buscar simulacro</label>
            <div class="relative">
               <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                  <span class="material-icons-round text-base">search</span>
               </span>
               <input 
                  v-model="filters.search" 
                  type="text" 
                  placeholder="Nombre..." 
                  class="pl-9 w-full rounded-lg border-slate-200 dark:border-slate-600 dark:bg-slate-800 dark:text-white text-sm focus:ring-primary focus:border-primary placeholder-slate-400 dark:placeholder-slate-500" 
               />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Ordenar por</label>
            <Select 
              v-model="filters.sort" 
              :options="sortOptions"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              :pt="{
                  root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
                  trigger: { class: 'text-slate-500 dark:text-slate-400' },
                  panel: { class: 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600' },
                  item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-700' }
              }"
            />
          </div>
          
          <div>
             <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Área</label>
             <Select 
               v-model="filters.area" 
               :options="areasConTodas"
               optionLabel="label"
               optionValue="value"
               placeholder="Todas"
               class="w-full"
               :pt="{
                  root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
                  trigger: { class: 'text-slate-500 dark:text-slate-400' },
                  panel: { class: 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600' },
                  item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-700' }
               }"
             />
          </div>
       </div>

       <!-- Results List -->
       <div class="flex-1 space-y-4">
          <div v-if="loadingHistorial" class="py-12 flex justify-center">
             <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
          </div>
          
          <div v-else-if="filteredHistorial.length === 0" class="bg-white dark:bg-slate-800 rounded-xl p-12 text-center border border-slate-200 dark:border-slate-700 border-dashed">
             <div class="inline-flex p-4 bg-slate-50 dark:bg-slate-700/50 rounded-full mb-4">
                <span class="material-icons-round text-slate-400 dark:text-slate-500 text-4xl">inventory_2</span>
             </div>
             <h3 class="text-lg font-bold text-slate-800 dark:text-white">No se encontraron resultados</h3>
             <p class="text-slate-500 dark:text-slate-400">Prueba ajustando los filtros de búsqueda.</p>
          </div>
          
          <div v-else class="space-y-4">
             <div 
               v-for="intento in filteredHistorial" 
               :key="intento.id"
               class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col sm:flex-row gap-6 items-start sm:items-center"
               :class="intento.fraude ? 'border-l-4 border-l-rose-500 border border-rose-200 dark:border-rose-800/50 bg-rose-50/50 dark:bg-rose-900/10' : 'border border-slate-200 dark:border-slate-700'"
             >
                <!-- Score Circle -->
                <div class="relative flex-shrink-0">
                   <div v-if="intento.fraude" class="w-16 h-16 rounded-full flex flex-col items-center justify-center border-4 border-rose-500 bg-rose-100 dark:bg-rose-900/50 animate-pulse">
                      <span class="material-icons-round text-rose-600 dark:text-rose-400 text-2xl">gavel</span>
                   </div>
                   <div v-else class="w-16 h-16 rounded-full flex items-center justify-center border-4 font-bold text-xl"
                        :class="getScoreColor(intento.puntaje_total)">
                      {{ Math.round(intento.puntaje_total) }}
                   </div>
                </div>
                
                <!-- Info -->
                <div class="flex-1">
                   <div class="flex items-center gap-2 mb-1">
                      <h3 class="font-bold text-lg" :class="intento.fraude ? 'text-rose-700 dark:text-rose-400' : 'text-slate-900 dark:text-white'">{{ intento.simulacro_nombre || `Simulacro #${intento.simulacro_id}` }}</h3>
                      <span v-if="intento.simulacro_area" class="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{{ intento.simulacro_area }}</span>
                      <span v-if="intento.fraude" class="px-2 py-0.5 rounded text-xs font-bold bg-rose-500 text-white flex items-center gap-1 animate-pulse">
                        <span class="material-icons-round text-[12px]">warning</span>
                        SANCIONADO
                      </span>
                   </div>
                   <p class="text-sm flex items-center gap-2 flex-wrap" :class="intento.fraude ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500 dark:text-slate-400'">
                      <span class="material-icons-round text-base">calendar_today</span> {{ formatDate(intento.created_at) }}
                      <template v-if="!intento.fraude">
                        <span class="mx-1">•</span>
                        <span>{{ intento.total_correctas }} ✅</span>
                        <span>{{ intento.total_incorrectas }} ❌</span>
                      </template>
                      <template v-else>
                        <span class="mx-1">•</span>
                        <span class="font-semibold">Nota: 0.0 (Anulado)</span>
                      </template>
                   </p>
                </div>
                
                <!-- Actions -->
                <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                   <button 
                      v-if="!intento.fraude"
                      @click="verReporte(intento)" 
                      class="flex items-center justify-center gap-2 px-4 py-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 rounded-lg text-sm font-bold transition-colors"
                   >
                      <span class="material-icons-round text-[18px]">psychology</span> Análisis IA
                   </button>
                   <button 
                      v-if="intento.fraude"
                      disabled
                      class="flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 rounded-lg text-sm font-medium cursor-not-allowed"
                   >
                      <span class="material-icons-round text-[18px]">block</span> No disponible
                   </button>
                   <button 
                      @click="verRespuestas(intento)" 
                      class="flex items-center justify-center gap-2 px-4 py-2 border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg text-sm font-bold transition-colors"
                   >
                      <span class="material-icons-round text-[18px]">visibility</span> Ver respuestas
                   </button>
                </div>
             </div>
          </div>
       </div>
    </div>

    <!-- Modal Reporte -->
    <div v-if="selectedReporte" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
       <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="selectedReporte = null"></div>
       <div class="relative w-full max-w-4xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-fade-in-up">
          <div class="bg-slate-900 dark:bg-slate-900 text-white p-6 flex justify-between items-center sticky top-0 z-10 border-b border-white/10">
             <div class="flex items-center gap-3">
                <div class="p-2 bg-indigo-500 rounded-lg"><span class="material-icons-round text-white">psychology</span></div>
                <div><h3 class="font-bold text-lg">Informe de análisis IA</h3><p class="text-indigo-200 text-xs">Generado automáticamente por Groq LLM</p></div>
             </div>
             <div class="flex gap-2">
                <button @click="downloadPDF" class="p-2 hover:bg-slate-800 rounded-full transition-colors" title="Descargar PDF"><span class="material-icons-round text-white">download</span></button>
                <button @click="selectedReporte = null" class="p-2 hover:bg-slate-800 rounded-full transition-colors"><span class="material-icons-round text-2xl">close</span></button>
             </div>
          </div>
          <div id="reporte-content" class="flex-1 overflow-y-auto p-8 bg-slate-50 dark:bg-slate-900">
             
             <!-- ESTADO: FRAUDE DETECTADO -->
             <div v-if="selectedReporte.fraude" class="text-center py-12">
                 <div class="inline-flex p-4 bg-rose-50 dark:bg-rose-900/30 rounded-full mb-4 border-2 border-rose-200 dark:border-rose-800">
                    <span class="material-icons-round text-rose-600 dark:text-rose-400 text-5xl">gavel</span>
                 </div>
                 <h4 class="text-2xl font-bold text-rose-700 dark:text-rose-400 mb-2">PRUEBA ANULADA</h4>
                 <div class="max-w-md mx-auto space-y-2 text-slate-600 dark:text-slate-300">
                     <p>Este simulacro fue sancionado por detección de fraude.</p>
                     <p class="text-sm bg-rose-50 dark:bg-rose-900/10 p-3 rounded-lg border border-rose-100 dark:border-rose-900/50">
                        Nota asignada: <strong>0.0</strong><br>
                        Informes generados: <strong>anulados</strong>
                     </p>
                 </div>
             </div>

             <!-- ESTADO: REPORTE NUMÉRICO -->
             <div v-else-if="selectedReporte.tipo === 'numerico'" class="space-y-8 animate-fade-in text-center">
                 
                 <!-- Global Score Circle -->
                 <div class="flex justify-center">
                     <div class="relative w-48 h-48 rounded-full border-[6px] border-indigo-600 flex flex-col items-center justify-center bg-white dark:bg-slate-800 shadow-xl">
                         <span class="text-5xl font-black text-indigo-600 dark:text-indigo-400">{{ selectedReporte.data.global_score }}</span>
                         <span class="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Puntaje global</span>
                         <span class="absolute -bottom-4 bg-indigo-600 text-white px-3 py-1 rounded-full text-xs font-bold shadow-md">ESCALA 0-500</span>
                     </div>
                 </div>

                 <!-- Areas Grid -->
                 <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                     <div v-for="area in selectedReporte.data.areas" :key="area.area" class="bg-white dark:bg-slate-700 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-600 flex justify-between items-center">
                         <div>
                             <h5 class="font-bold text-slate-800 dark:text-white capitalize">{{ area.area.replace('_', ' ').toLowerCase() }}</h5>
                             <p class="text-sm text-indigo-500 font-medium">Nivel de desempeño: {{ area.nivel }}</p>
                         </div>
                         <div class="text-right">
                             <div class="text-2xl font-bold text-slate-700 dark:text-slate-200">{{ area.puntaje }}</div>
                             <div class="text-[10px] text-slate-400 uppercase">Puntos</div>
                         </div>
                     </div>
                 </div>
                 
                 <div class="text-xs text-slate-500 max-w-lg mx-auto italic">
                     * El puntaje global es una estimación basada en la ponderación oficial del ICFES: (Mat*3 + Lec*3 + Soc*3 + Cie*3 + Ing*1)/13 * 5.
                 </div>
             </div>

             <!-- ESTADO: SIN INFORME IA -->
             <div v-else-if="!selectedReporte.analisis_ia" class="text-center py-12">
                <div class="inline-flex p-3 bg-amber-50 dark:bg-amber-900/30 rounded-full mb-4">
                     <span class="material-icons-round text-amber-500 text-4xl">hourglass_disabled</span>
                </div>
                <h4 class="text-slate-800 dark:text-white font-bold mb-2">Informe IA no disponible</h4>
                <p class="text-slate-500 dark:text-slate-400">
                  Este intento no tiene informe IA. Es posible que el estudiante no haya culminado el examen o que el intento se haya cerrado por tiempo.
                </p>
             </div>
             
             <!-- ESTADO: INFORME DISPONIBLE -->
             <div v-else class="space-y-8 animate-fade-in">
                <div class="bg-white dark:bg-slate-800 p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 prose dark:prose-invert max-w-none">
                   <div v-html="renderMarkdown(selectedReporte.analisis_ia.informe_ia)"></div>
                </div>
             </div>
          </div>
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api/axios';
import html2pdf from 'html2pdf.js';
import Select from 'primevue/select';

const route = useRoute();
const router = useRouter();
const studentId = route.params.id;

const estudiante = ref(null);
const historial = ref([]);
const simulacrosMeta = ref({});
const loadingStudent = ref(true);
const loadingHistorial = ref(true);
const selectedReporte = ref(null);

const filters = ref({
   search: '',
   sort: 'recent',
   area: null
});

const sortOptions = [
  { label: 'Más reciente', value: 'recent' },
  { label: 'Más antiguo', value: 'oldest' },
  { label: 'Mayor puntaje', value: 'score_desc' },
  { label: 'Menor puntaje', value: 'score_asc' }
];

const availableAreas = computed(() => {
   const areas = new Set();
   historial.value.forEach(h => {
      if (h.simulacro_area) areas.add(h.simulacro_area);
   });
   return Array.from(areas).sort();
});

const areasConTodas = computed(() => [
  { label: 'Todas', value: null },
  ...availableAreas.value.map(a => ({ label: a, value: a }))
]);

const promedioScore = computed(() => {
   if (historial.value.length === 0) return 0;
   const sum = historial.value.reduce((acc, curr) => acc + (curr.puntaje_total || 0), 0);
   return Math.round(sum / historial.value.length);
});

const filteredHistorial = computed(() => {
   let res = [...historial.value];
   
   if (filters.value.search) {
      const q = filters.value.search.toLowerCase();
      res = res.filter(h => (h.simulacro_nombre || '').toLowerCase().includes(q));
   }
   
   if (filters.value.area) {
      res = res.filter(h => h.simulacro_area === filters.value.area);
   }
   
   res.sort((a, b) => {
      if (filters.value.sort === 'recent') return new Date(b.created_at) - new Date(a.created_at);
      if (filters.value.sort === 'oldest') return new Date(a.created_at) - new Date(b.created_at);
      if (filters.value.sort === 'score_desc') return b.puntaje_total - a.puntaje_total;
      if (filters.value.sort === 'score_asc') return a.puntaje_total - b.puntaje_total;
      return 0;
   });
   
   return res;
});

const initData = async () => {
   try {
      const resUser = await api.get(`/usuarios/${studentId}`);
      estudiante.value = resUser.data;
      loadingStudent.value = false;
      
      const resSims = await api.get('/simulacros/');
      resSims.data.forEach(s => {
         simulacrosMeta.value[s.id] = { 
             nombre: s.titulo, 
             area: s.area
         };
      });
      
      const resHist = await api.get(`/usuarios/${studentId}/intentos`);
      
      historial.value = resHist.data.map(intento => ({
         ...intento,
         simulacro_nombre: simulacrosMeta.value[intento.simulacro_id]?.nombre || 'Simulacro Desconocido',
         simulacro_area: simulacrosMeta.value[intento.simulacro_id]?.area || ''
      }));
      
      loadingHistorial.value = false;
      
   } catch (e) {
      console.error(e);
   }
};

const verRespuestas = (intento) => {
   router.push({
      path: `/simulacros/${intento.simulacro_id}/revision`,
      query: { 
          studentId: estudiante.value.id,
          studentName: estudiante.value.nombre 
      }
   });
};

const verReporte = (intento) => {
   selectedReporte.value = intento;
};

const getInitials = (name) => name ? name.split(' ').map(n=>n[0]).slice(0,2).join('').toUpperCase() : '??';
const formatDate = (dateStr) => new Date(dateStr).toLocaleDateString('es-CO', {day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit'});
const getScoreColor = (sc) => {
    if(sc >= 80) return 'border-emerald-500 text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 dark:text-emerald-400';
    if(sc >= 60) return 'border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/30 dark:text-blue-400';
    if(sc >= 40) return 'border-orange-500 text-orange-600 bg-orange-50 dark:bg-orange-900/30 dark:text-orange-400';
    return 'border-rose-500 text-rose-600 bg-rose-50 dark:bg-rose-900/30 dark:text-rose-400';
};
const renderMarkdown = (text) => {
   if (!text) return '';
   let html = text
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2 text-slate-800 dark:text-slate-100">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-6 mb-3 text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-700 pb-2">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-6 mb-4 text-slate-900 dark:text-white">$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc marker:text-primary">$1</li>')
      .replace(/\n/gim, '<br />');
   return html;
};

const downloadPDF = async () => {
    const exportHtmlFallback = () => {
       const element = document.getElementById('reporte-content');
       if (!element) return;
       const opt = {
          margin: 0.5,
          filename: `Reporte_${estudiante.value?.nombre}_${new Date().toISOString().slice(0,10)}.pdf`,
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2 },
          jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
       };
       html2pdf().set(opt).from(element).save();
    };

    if (selectedReporte.value?.id) {
       try {
          const url = `/reportes/detalle/individual/${selectedReporte.value.id}/pdf`;
          const response = await api.get(url, { responseType: 'blob' });
          const blob = new Blob([response.data], { type: 'application/pdf' });
          const link = document.createElement('a');
          link.href = window.URL.createObjectURL(blob);
          link.download = `Informe_IA_${estudiante.value?.nombre || 'Estudiante'}.pdf`;
          link.click();
          return;
       } catch (e) {
          console.error("Error descargando PDF individual backend", e);
          exportHtmlFallback();
          return;
       }
    }

    exportHtmlFallback();
};

onMounted(() => {
   initData();
});
</script>

<style scoped>
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
.animate-fade-in { animation: fade-in 0.5s ease-out; }
.font-sans { font-family: 'Inter', sans-serif; }
</style>
