<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6 p-4 sm:p-6">
    
    <!-- Header -->
    <div class="flex flex-col gap-2">
        <button @click="$router.push('/reportes')" class="text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white flex items-center gap-1 w-fit text-sm font-medium transition-colors">
            <span class="material-icons-round text-[16px]">arrow_back</span>
            Volver al Panel
        </button>
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-2">
            <div>
                <h2 class="text-2xl font-bold text-slate-800 dark:text-white capitalize">Histórico de reportes: {{ titleMap[currentTipo] || currentTipo }}</h2>
                <p class="text-slate-500 dark:text-slate-400">Listado completo filtrado.</p>
            </div>
            
            <!-- Filters -->
            <div class="flex items-center gap-3"></div>
        </div>
    </div>

    <!-- Content Grid -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
        <p class="text-slate-500">Cargando histórico...</p>
    </div>
    
    <div v-else-if="items.length === 0" class="bg-white dark:bg-slate-800 rounded-xl p-10 text-center shadow-sm border border-slate-100 dark:border-slate-700">
        <span class="material-icons-round text-5xl text-slate-200 mb-4">history_toggle_off</span>
        <h3 class="text-lg font-bold text-slate-700 dark:text-slate-200">No hay registros</h3>
        <p class="text-slate-500">No se encontraron reportes con los filtros seleccionados.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-in fade-in slide-in-from-bottom-4">
        <ReportCard 
            v-for="item in paginatedItems"
            :key="item.id"
            :title="item.titulo"
            :subtitle="item.subtitulo"
            :date="item.fecha"
            :score="item.puntaje"
            :tags="item.tags"
            :icon="iconMap[currentTipo]"
            :color="colorMap[currentTipo]"
            :fraude="item.fraude"
            @click="openReporte(item)"
        />
    </div>

    <!-- Pagination -->
    <div v-if="items.length > 0" class="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700 mt-6">
        <p class="text-sm text-slate-500 dark:text-slate-400">
            Mostrando <strong>{{ (currentPage - 1) * itemsPerPage + 1 }}</strong> - <strong>{{ Math.min(currentPage * itemsPerPage, items.length) }}</strong> de <strong>{{ items.length }}</strong> reportes
        </p>
        <div class="flex items-center gap-2">
            <button 
                @click="prevPage"
                :disabled="currentPage === 1"
                class="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                Anterior
            </button>
            <span class="text-sm text-slate-400 px-2">
                Página {{ currentPage }} de {{ totalPages }}
            </span>
            <button 
                @click="nextPage"
                :disabled="currentPage >= totalPages"
                class="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                Siguiente
            </button>
        </div>
    </div>

    <!-- Modal Detalle (Copiado de Dashboard) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
       <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="showModal = false"></div>
       <div class="relative w-full max-w-4xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-in zoom-in-95 duration-200">
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
          <div id="reporte-content" class="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-slate-900 prose dark:prose-invert max-w-none">
             <div v-if="modalLoading" class="flex flex-col items-center justify-center py-20 space-y-4">
                 <div class="animate-spin rounded-full h-12 w-12 border-4 border-slate-200 border-t-indigo-600"></div>
                 <p class="text-slate-400">Recuperando informe completo...</p>
             </div>
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

             <!-- ESTADO: GRUPAL BATCH (agrupado multi-área con tabla de estudiantes 5 áreas) -->
             <div
               v-else-if="modalData && selectedItem?.tipo_reporte === 'grupal_batch' && (modalData.areas || grupalBatchDetail?.areas)"
               class="not-prose animate-fade-in text-left"
             >
                 <div class="flex flex-col gap-4">
                     <!-- Summary header institucional -->
                     <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4 border border-emerald-200 dark:border-emerald-800">
                         <div>
                             <span class="text-xs font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                                 {{ (grupalBatchDetail || modalData).institucion_nombre || 'Institución Educativa' }}
                             </span>
                             <h3 class="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                                 {{ (grupalBatchDetail || modalData).subtitulo || (grupalBatchDetail || modalData).titulo }}
                             </h3>
                         </div>
                         <div class="flex items-center gap-2">
                             <div v-if="(grupalBatchDetail || modalData).puntaje_global !== null && (grupalBatchDetail || modalData).puntaje_global !== undefined"
                                 class="rounded-lg bg-emerald-600 text-white px-3.5 py-1.5 text-xs font-bold shadow-sm">
                                 Promedio Global: {{ formatScore((grupalBatchDetail || modalData).puntaje_global) }} / 500
                             </div>
                             <div class="rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 px-3 py-1.5 text-xs font-semibold">
                                 {{ (grupalBatchDetail || modalData).total_estudiantes_completos || 0 }} Estudiantes (5 áreas)
                             </div>
                         </div>
                     </div>

                     <!-- Tab Controls: 'estudiantes' | 'areas' -->
                     <div class="flex border-b border-slate-200 dark:border-slate-700 gap-4 text-sm font-semibold">
                         <button
                             @click="activeGrupalTab = 'estudiantes'"
                             class="pb-2 transition-colors border-b-2"
                             :class="activeGrupalTab === 'estudiantes' ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400' : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400'"
                         >
                             Estudiantes con 5 áreas ({{ (grupalBatchDetail || modalData).total_estudiantes_completos || 0 }})
                         </button>
                         <button
                             @click="activeGrupalTab = 'areas'"
                             class="pb-2 transition-colors border-b-2"
                             :class="activeGrupalTab === 'areas' ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400' : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400'"
                         >
                             Promedios por área
                         </button>
                     </div>

                     <!-- Content 1: Student Table -->
                     <div v-if="activeGrupalTab === 'estudiantes'" class="space-y-4">
                         <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                             <input
                                 v-model="searchStudentQuery"
                                 type="text"
                                 placeholder="Buscar por nombre o documento..."
                                 class="px-3.5 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 outline-none focus:ring-2 focus:ring-emerald-500 w-full sm:w-72"
                             />
                         </div>

                         <div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                             <table class="w-full text-xs text-left">
                                 <thead class="bg-slate-900 text-white uppercase text-[10px] tracking-wider font-bold">
                                     <tr>
                                         <th class="px-3 py-3 text-center w-10">#</th>
                                         <th class="px-3 py-3">N° Documento</th>
                                         <th class="px-3 py-3">Estudiante</th>
                                         <th class="px-3 py-3 text-center">Lect. Crítica</th>
                                         <th class="px-3 py-3 text-center">Matemáticas</th>
                                         <th class="px-3 py-3 text-center">Ciencias Nat.</th>
                                         <th class="px-3 py-3 text-center">Sociales y C.</th>
                                         <th class="px-3 py-3 text-center">Inglés</th>
                                         <th class="px-3 py-3 text-center">Puntaje Global</th>
                                     </tr>
                                 </thead>
                                 <tbody class="divide-y divide-slate-100 dark:divide-slate-700 bg-white dark:bg-slate-800">
                                     <tr
                                         v-for="(st, idx) in filteredBatchEstudiantes"
                                         :key="st.usuario_id || idx"
                                         class="hover:bg-emerald-50/50 dark:hover:bg-emerald-950/20 transition-colors"
                                     >
                                         <td class="px-3 py-2.5 text-center font-bold text-slate-400">{{ idx + 1 }}</td>
                                         <td class="px-3 py-2.5 font-mono text-slate-600 dark:text-slate-400">{{ st.numero_documento }}</td>
                                         <td class="px-3 py-2.5 font-semibold text-slate-900 dark:text-white">{{ st.nombre }}</td>
                                         <td class="px-3 py-2.5 text-center font-medium">{{ formatScore(st.lectura_critica) }}</td>
                                         <td class="px-3 py-2.5 text-center font-medium">{{ formatScore(st.matematicas) }}</td>
                                         <td class="px-3 py-2.5 text-center font-medium">{{ formatScore(st.ciencias_naturales) }}</td>
                                         <td class="px-3 py-2.5 text-center font-medium">{{ formatScore(st.sociales_ciudadanas) }}</td>
                                         <td class="px-3 py-2.5 text-center font-medium">{{ formatScore(st.ingles) }}</td>
                                         <td class="px-3 py-2.5 text-center">
                                             <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                                                 {{ formatScore(st.puntaje_total) }} / 500
                                             </span>
                                         </td>
                                     </tr>
                                     <tr v-if="filteredBatchEstudiantes.length === 0">
                                         <td colspan="9" class="px-4 py-8 text-center text-slate-400">
                                             {{ searchStudentQuery ? 'No se encontraron estudiantes coincidentes.' : 'No hay estudiantes con las 5 áreas completadas registradas en este lote.' }}
                                         </td>
                                     </tr>
                                 </tbody>
                             </table>
                         </div>
                     </div>

                     <!-- Content 2: Per-Area Breakdown -->
                     <div v-else class="space-y-4">
                         <div class="flex flex-wrap gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
                             <button
                                 v-for="area in ((grupalBatchDetail || modalData).areas || [])"
                                 :key="area.area"
                                 @click="activeAreaTab = area.area"
                                 class="px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5"
                                 :class="activeAreaTab === area.area
                                     ? 'bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-sm'
                                     : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                             >
                                 {{ area.display }}
                                 <span v-if="area.average_score_100 !== null && area.average_score_100 !== undefined" class="font-bold">{{ formatScore(area.average_score_100) }}</span>
                             </button>
                         </div>
                         <div v-if="activeGrupalArea" class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
                             <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                                 <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
                                     <p class="text-xs uppercase tracking-wide text-slate-500">Área</p>
                                     <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ activeGrupalArea.display }}</p>
                                 </div>
                                 <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
                                     <p class="text-xs uppercase tracking-wide text-slate-500">Finalizados</p>
                                     <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ activeGrupalArea.students_count || 0 }}</p>
                                 </div>
                                 <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
                                     <p class="text-xs uppercase tracking-wide text-slate-500">Nivel de desempeño</p>
                                     <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ activeGrupalArea.performance_level || 'N/A' }}</p>
                                 </div>
                             </div>
                             <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 text-center">
                                 <h4 class="text-lg font-extrabold text-slate-900 dark:text-white">Promedio grupal del área</h4>
                                 <div class="relative w-36 h-36 mx-auto mt-4">
                                     <div class="absolute inset-0 rounded-full" :style="groupProgressStyle(activeGrupalArea.average_score_100)"></div>
                                     <div class="absolute inset-[10px] rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center">
                                         <span class="text-3xl font-black text-emerald-600 dark:text-emerald-400">{{ formatScore(activeGrupalArea.average_score_100) }}</span>
                                         <span class="text-xs font-bold text-slate-500">/100</span>
                                     </div>
                                 </div>
                             </div>
                         </div>
                     </div>
                 </div>
             </div>

              <!-- ESTADO: INDIVIDUAL BATCH (agrupado multi-área con tabs) -->
              <div
                v-else-if="modalData && selectedItem?.tipo_reporte === 'individual_batch' && (modalData.areas || batchDetail?.areas)"
                class="not-prose animate-fade-in text-left"
              >
                  <div class="flex flex-col gap-4">
                      <!-- Summary header -->
                      <div class="flex flex-wrap items-center justify-between gap-2 bg-violet-50 dark:bg-violet-900/20 rounded-xl p-4 border border-violet-200 dark:border-violet-800">
                          <div>
                              <h3 class="text-lg font-bold text-violet-900 dark:text-violet-100">{{ (batchDetail || modalData).titulo }}</h3>
                              <p class="text-sm text-violet-700 dark:text-violet-300">{{ (batchDetail || modalData).subtitulo }}</p>
                          </div>
                          <div class="flex items-center gap-3">
                              <div v-if="(batchDetail || modalData).puntaje_global !== null && (batchDetail || modalData).puntaje_global !== undefined"
                                  class="rounded-full bg-violet-600 text-white px-4 py-2 text-sm font-bold">
                                  Global: {{ formatScore((batchDetail || modalData).puntaje_global) }} / 500
                              </div>
                          </div>
                      </div>

                      <!-- Area tabs -->
                      <div class="flex flex-wrap gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
                          <button
                              v-for="area in ((batchDetail || modalData).areas || [])"
                              :key="area.area"
                              @click="activeAreaTab = area.area"
                              class="px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5"
                              :class="activeAreaTab === area.area
                                  ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                          >
                              <span v-if="area.fraude" class="material-icons-round text-[14px] text-rose-500">gavel</span>
                              {{ area.display }}
                              <span v-if="area.score !== null && area.score !== undefined" class="font-bold">{{ area.score.toFixed(1) }}</span>
                          </button>
                      </div>

                      <!-- Active tab content -->
                      <div v-if="activeAreaContent" class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
                          <div v-if="activeAreaContent.fraude" class="text-center py-8">
                              <div class="inline-flex p-3 bg-rose-50 dark:bg-rose-900/30 rounded-full mb-3 border-2 border-rose-200 dark:border-rose-800">
                                  <span class="material-icons-round text-rose-600 dark:text-rose-400 text-3xl">gavel</span>
                              </div>
                              <h4 class="text-lg font-bold text-rose-700 dark:text-rose-400 mb-2">PRUEBA ANULADA — {{ activeAreaContent.display }}</h4>
                              <p class="text-sm text-slate-500">Este reporte no está disponible porque el examen fue sancionado por fraude.</p>
                          </div>
                          <div v-else v-html="renderMarkdown(activeAreaContent.contenido || 'Contenido no disponible.')"></div>
                      </div>
                  </div>
              </div>

             <div v-else-if="modalData && modalData.tipo_contenido === 'numerico' && modalData.data" class="space-y-8 animate-fade-in text-center">
                 <div class="flex justify-center">
                     <div class="relative w-48 h-48 rounded-full border-[6px] border-indigo-600 flex flex-col items-center justify-center bg-white dark:bg-slate-800 shadow-xl">
                         <span class="text-5xl font-black text-indigo-600 dark:text-indigo-400">{{ modalData.data.global_score }}</span>
                         <span class="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Puntaje global</span>
                         <span class="absolute -bottom-4 bg-indigo-600 text-white px-3 py-1 rounded-full text-xs font-bold shadow-md">ESCALA 0-500</span>
                     </div>
                 </div>

                 <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                     <div v-for="area in modalData.data.areas" :key="area.area" class="bg-white dark:bg-slate-700 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-600 flex justify-between items-center">
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
                     * El puntaje global es una estimación basada en la ponderación oficial del ICFES.
                 </div>
             </div>

             <div v-else-if="modalData && modalData.contenido" v-html="renderMarkdown(modalData.contenido)"></div>
             <div v-else class="flex flex-col items-center justify-center py-20 text-slate-400">
                 <span class="material-icons-round text-4xl mb-2">content_paste_off</span>
                 <p>No se pudo cargar el contenido del reporte.</p>
             </div>
          </div>
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
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/axios';
import ReportCard from '../components/dashboard/ReportCard.vue';
import Select from 'primevue/select'; // Requires PrimeVue setup in App
import html2pdf from 'html2pdf.js';

const route = useRoute();
const currentTipo = computed(() => route.params.tipo);
const loading = ref(false);
const items = ref([]);
const currentPage = ref(1);
const itemsPerPage = 16;

// Maps
const titleMap = {
    'individual': 'Individuales',
    'grupal': 'Grupales'
};
const iconMap = {
    'individual': 'person',
    'grupal': 'groups'
};
const colorMap = {
    'individual': 'blue',
    'grupal': 'emerald'
};

// Data fetching
const fetchItems = async () => {
    loading.value = true;
    try {
        const params = { limit: 50 };
        const res = await api.get(`/reportes/lista/${currentTipo.value}`, { params });
        items.value = res.data;
    } catch(e) {
        console.error(e);
        items.value = [];
    } finally {
        loading.value = false;
    }
};


// Modal Logic
const showModal = ref(false);
const modalData = ref(null);
const modalLoading = ref(false);
const selectedItem = ref(null);
const batchDetail = ref(null);
const grupalBatchDetail = ref(null);
const activeAreaTab = ref(null);
const activeGrupalTab = ref('estudiantes');
const searchStudentQuery = ref('');

const filteredBatchEstudiantes = computed(() => {
    const list = (grupalBatchDetail.value || modalData.value)?.estudiantes || [];
    if (!searchStudentQuery.value) return list;
    const q = searchStudentQuery.value.toLowerCase().trim();
    return list.filter(s =>
        (s.nombre && s.nombre.toLowerCase().includes(q)) ||
        (s.numero_documento && s.numero_documento.toLowerCase().includes(q))
    );
});

const activeAreaContent = computed(() => {
    const areas = (batchDetail.value || modalData.value)?.areas;
    if (!areas || !activeAreaTab.value) return null;
    return areas.find(a => a.area === activeAreaTab.value) || null;
});

const activeGrupalArea = computed(() => {
    const areas = (grupalBatchDetail.value || modalData.value)?.areas;
    if (!areas || !activeAreaTab.value) return null;
    return areas.find(a => a.area === activeAreaTab.value) || null;
});

const openReporte = async (item) => {
    selectedItem.value = item;
    modalData.value = null;
    batchDetail.value = null;
    grupalBatchDetail.value = null;
    activeAreaTab.value = null;
    activeGrupalTab.value = 'estudiantes';
    searchStudentQuery.value = '';
    showModal.value = true;
    modalLoading.value = true;
    try {
        if (item.tipo_reporte === 'individual_batch') {
            const meta = item.metadata || {};
            const params = new URLSearchParams({ usuario_id: meta.usuario_id });
            if (meta.batch_id) params.append('batch_id', meta.batch_id);
            else params.append('simulacro_id', meta.simulacro_ids?.[0] || '');
            const res = await api.get(`/reportes/detalle/individual-batch?${params.toString()}`);
            batchDetail.value = res.data;
            modalData.value = res.data;
            if (res.data.areas?.length) {
                activeAreaTab.value = res.data.areas[0].area;
            }
        } else if (item.tipo_reporte === 'grupal_batch') {
            const meta = item.metadata || {};
            const params = new URLSearchParams({ batch_id: meta.batch_id });
            const res = await api.get(`/reportes/detalle/grupal-batch?${params.toString()}`);
            grupalBatchDetail.value = res.data;
            modalData.value = res.data;
            if (res.data.areas?.length) {
                activeAreaTab.value = res.data.areas[0].area;
            }
        } else {
            const res = await api.get(`/reportes/detalle/${item.tipo_reporte}/${item.id}`);
            modalData.value = res.data;
        }
    } catch(e) {
        console.error(e);
        modalData.value = { titulo: "Error", contenido: "Error cargando." };
    } finally {
        modalLoading.value = false;
    }
};

const downloadReport = async () => {
    if (!selectedItem.value || !modalData.value || modalData.value.fraude) return;

    const isIndividual = selectedItem.value.tipo_reporte === 'individual' || selectedItem.value.tipo_reporte === 'individual_batch';
    if (isIndividual) {
        const respId = activeAreaContent.value?.respuesta_id || modalData.value?.respuesta_id || selectedItem.value.id;
        if (respId) {
            try {
                const url = `/reportes/detalle/individual/${respId}/pdf`;
                const response = await api.get(url, { responseType: 'blob' });
                const blob = new Blob([response.data], { type: 'application/pdf' });
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                const areaName = activeAreaContent.value?.display || 'Area';
                const studentName = selectedItem.value?.titulo || 'Estudiante';
                link.download = `Reporte_Individual_${studentName}_${areaName}.pdf`.replace(/\s+/g, '_');
                link.click();
                return;
            } catch (e) {
                console.error("Error descargando PDF individual backend", e);
            }
        }
    }

    const meta = selectedItem.value.metadata || {};
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

    if (selectedItem.value.tipo_reporte === 'grupal_batch') {
        const batchMeta = selectedItem.value.metadata || {};
        const bId = batchMeta.batch_id || (grupalBatchDetail.value || modalData.value)?.batch_id;
        if (bId) {
            try {
                const url = `/reportes/grupal-batch/${bId}/pdf`;
                const response = await api.get(url, { responseType: 'blob' });
                const blob = new Blob([response.data], { type: 'application/pdf' });
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = `Reporte_Grupal_Batch_${bId}.pdf`;
                link.click();
                return;
            } catch (e) {
                console.error("Error descargando PDF grupal batch backend", e);
            }
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

watch(currentTipo, () => {
    currentPage.value = 1;
    fetchItems();
});

// Paginación Computed y Métodos
const totalPages = computed(() => Math.ceil(items.value.length / itemsPerPage));

const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return items.value.slice(start, end);
});

const prevPage = () => {
    if (currentPage.value > 1) currentPage.value--;
};

const nextPage = () => {
    if (currentPage.value < totalPages.value) currentPage.value++;
};

onMounted(() => {
    fetchItems();
});
</script>
