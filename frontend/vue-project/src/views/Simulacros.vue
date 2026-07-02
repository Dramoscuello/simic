<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6">
    <Toast />
    <ConfirmDialog />
    <Dialog
      v-model:visible="startBlockedDialogVisible"
      modal
      :closable="false"
      :dismissableMask="false"
      :draggable="false"
      class="w-[92vw] max-w-lg"
    >
      <template #header>
        <div class="flex items-center gap-2 text-red-700 dark:text-red-300">
          <span class="material-icons-round">warning</span>
          <span class="font-semibold">{{ startBlockedDialogTitle }}</span>
        </div>
      </template>
      <p class="text-slate-700 dark:text-slate-200 leading-relaxed">
        {{ startBlockedDialogMessage }}
      </p>
      <template #footer>
        <button
          type="button"
          class="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 transition-colors"
          @click="startBlockedDialogVisible = false"
        >
          Entendido
        </button>
      </template>
    </Dialog>
    <!-- Header: Title + Action Button -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Simulacros</h2>
        <p class="text-slate-500 dark:text-slate-400">Gestiona todos los simulacros del sistema</p>
      </div>
      
      <!-- Action Buttons Group -->
      <div class="flex items-center gap-3">
          <router-link 
            v-if="userRole === 'admin' || userRole === 'admin'"
            to="/simulacros/crear"
            class="flex items-center gap-2 bg-gradient-to-r from-primary to-indigo-600 hover:from-indigo-600 hover:to-primary text-white px-5 py-2.5 rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all h-[44px]"
          >
            <span class="material-icons-round text-[20px]">add</span>
            Nuevo simulacro
          </router-link>
      </div>
    </div>

    <!-- Filters Section (Super Admin & Admin Institucion) -->
    <div v-if="userRole === 'admin' || userRole === 'admin'" class="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-100 dark:border-slate-700">
      <div class="flex items-center gap-2 mb-3">
        <span class="material-icons-round text-slate-400 dark:text-slate-500 text-[20px]">filter_list</span>
        <span class="text-sm font-medium text-slate-600 dark:text-slate-300">Filtros avanzados</span>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <!-- Filtro por Sede -->
        <div v-if="userRole === 'admin' && showSedeFilter" class="flex flex-col gap-1">
          <label class="text-xs text-slate-500 dark:text-slate-400">Sede</label>
          <Select 
            v-model="filterSede" 
            :options="sedeOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todas las sedes"
            class="w-56"
            :pt="{
              root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
              trigger: { class: 'text-slate-500 dark:text-slate-400' },
              panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
            }"
            filter
            showClear
          />
        </div>
        <!-- Filtro por Área -->
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-500 dark:text-slate-400">Área</label>
          <Select 
            v-model="filterArea" 
            :options="areaOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todas las áreas"
            class="w-44"
            :pt="{
              root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
              trigger: { class: 'text-slate-500 dark:text-slate-400' },
              panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
            }"
          />
        </div>
        <!-- Filtro por Estado -->
        <div class="flex flex-col gap-1">
          <label class="text-xs text-slate-500 dark:text-slate-400">Estado</label>
          <Select 
            v-model="filterStatus" 
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Todos los estados"
            class="w-40"
            :pt="{
              root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
              trigger: { class: 'text-slate-500 dark:text-slate-400' },
              panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
            }"
          />
        </div>
        <!-- Botón Limpiar Filtros -->
        <div class="flex flex-col gap-1">
          <label class="text-xs text-transparent">.</label>
          <button 
            @click="clearFilters"
            class="flex items-center gap-1 px-3 py-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <span class="material-icons-round text-[18px]">clear_all</span>
            Limpiar
          </button>
        </div>
      </div>
    </div>

    <!-- Filters for Student (Reduced) -->
    <div v-else class="flex flex-wrap items-center gap-3">
      <Select 
        v-model="filterArea" 
        :options="areaOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Todas las áreas"
        class="w-44"
        :pt="{
          root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
          trigger: { class: 'text-slate-500 dark:text-slate-400' },
          panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
          item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
        }"
      />
      <!-- Estado oculto para estudiantes ya que usan tabs -->
    </div>
    
    <!-- Botón Generar/Ver Reporte Grupal (Docente/Admin) -->
    <div 
        v-if="userRole === 'admin' && canGenerateGroupReport" 
        :class="existingGroupReport ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-100 dark:border-emerald-800' : 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-100 dark:border-indigo-800'"
        class="border rounded-xl p-4 flex items-center justify-between mb-4 animate-in fade-in slide-in-from-top-4"
    >
        <div class="flex items-center gap-3">
            <div :class="existingGroupReport ? 'bg-emerald-100 dark:bg-emerald-800 text-emerald-700 dark:text-emerald-300' : 'bg-indigo-100 dark:bg-indigo-800 text-indigo-700 dark:text-indigo-300'" class="p-2 rounded-lg">
                <span class="material-icons-round">{{ existingGroupReport ? 'check_circle' : 'analytics' }}</span>
            </div>
            <div>
                <h4 :class="existingGroupReport ? 'text-emerald-900 dark:text-emerald-100' : 'text-indigo-900 dark:text-indigo-100'" class="font-bold">
                    {{ existingGroupReport ? 'Diagnóstico disponible' : 'Análisis grupal disponible' }}
                </h4>
                <p :class="existingGroupReport ? 'text-emerald-700 dark:text-emerald-300' : 'text-indigo-700 dark:text-indigo-300'" class="text-sm">
                    {{ existingGroupReport ? 'Ya existe un diagnóstico generado para este grupo. Puedes verlo o regenerarlo.' : 'Has filtrado simulacros finalizados. Puedes generar un diagnóstico pedagógico del grupo.' }}
                </p>
            </div>
        </div>
        <button 
            @click="generateGroupReportFromFilter"
            :disabled="groupReportLoading || checkingGroupReport"
            :class="existingGroupReport ? 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-500/20'"
            class="text-white px-5 py-2.5 rounded-lg text-sm font-bold shadow-md transition-all flex items-center gap-2"
        >
            <span v-if="groupReportLoading || checkingGroupReport" class="animate-spin rounded-full h-4 w-4 border-2 border-white/50 border-t-white"></span>
            <span v-else class="material-icons-round">{{ existingGroupReport ? 'visibility' : 'psychology' }}</span>
            {{ existingGroupReport ? 'Ver diagnóstico' : 'Generar diagnóstico' }}
        </button>
    </div>

    <!-- Student Tabs -->
    <div v-if="userRole === 'estudiante'" class="flex gap-2 mb-2 p-1 bg-slate-100/80 dark:bg-slate-800/80 rounded-lg w-fit">
       <button 
         @click="changeTab('pendiente')" 
         class="px-4 py-2 rounded-md text-sm font-medium transition-all"
         :class="activeTab === 'pendiente' ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
       >Por hacer</button>
       <button 
         @click="changeTab('realizado')" 
         class="px-4 py-2 rounded-md text-sm font-medium transition-all"
         :class="activeTab === 'realizado' ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
       >Historial</button>
    </div>
    
    <!-- Stats Cards -->
    <div v-if="!(userRole === 'admin' && !hasFilters)" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Total Simulacros -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Total simulacros</p>
            <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{{ simulacros.length }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-blue-50 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <span class="material-icons-round">quiz</span>
          </div>
        </div>
      </div>
      
      <!-- Card dinámica según filtro de estado -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">{{ statsCardLabel }}</p>
            <p class="text-2xl font-bold mt-1" :class="statsCardTextClass">
                {{ statsCardCount }}
            </p>
          </div>
          <div class="h-10 w-10 rounded-lg flex items-center justify-center" :class="statsCardBgClass">
            <span class="material-icons-round">{{ statsCardIcon }}</span>
          </div>
        </div>
      </div>
      
      <!-- Total Preguntas (filtradas) -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Total preguntas</p>
            <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{{ totalQuestions }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-purple-50 dark:bg-purple-900/40 flex items-center justify-center text-purple-600 dark:text-purple-400">
            <span class="material-icons-round">help_outline</span>
          </div>
        </div>
      </div>
      
      <!-- Filtrados -->
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Mostrando</p>
            <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{{ filteredSimulacros.length }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-amber-50 dark:bg-amber-900/40 flex items-center justify-center text-amber-600 dark:text-amber-400">
            <span class="material-icons-round">filter_list</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
      <p class="text-slate-500 dark:text-slate-400">Cargando simulacros...</p>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="filteredSimulacros.length === 0" class="bg-white dark:bg-slate-800 rounded-2xl p-12 text-center shadow-sm border border-slate-100 dark:border-slate-700">
      <div class="w-20 h-20 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-6">
        <span class="material-icons-round text-slate-400 dark:text-slate-500 text-4xl">quiz</span>
      </div>
      <h3 class="text-xl font-bold text-slate-800 dark:text-white mb-2">No hay simulacros</h3>
      <p class="text-slate-500 dark:text-slate-400 mb-6 max-w-md mx-auto">
        {{ (userRole === 'admin' && !hasFilters) ? 'Utiliza los filtros arriba para buscar simulacros o crea uno nuevo.' : (searchQuery || filterArea || filterStatus ? 'No se encontraron simulacros con los filtros aplicados.' : 'No hay simulacros disponibles en este momento.') }}
      </p>
      <router-link 
        v-if="userRole === 'admin'"
        to="/simulacros/crear"
        class="inline-flex items-center gap-2 bg-primary hover:bg-indigo-600 text-white px-6 py-3 rounded-lg text-sm font-semibold shadow-md transition-all"
      >
        <span class="material-icons-round text-[20px]">add</span>
        Crear primer simulacro
      </router-link>
    </div>
    
    <!-- Simulacros Grid -->
    <div v-else>
         <!-- GROUPED VIEW (Estudiante Historial) -->
         <div v-if="userRole === 'estudiante' && activeTab === 'realizado'" class="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div v-for="group in groupedSimulacros" :key="group.id" class="space-y-4">
                 <div class="flex items-center gap-3 border-b border-slate-200 dark:border-slate-700 pb-2">
                    <span class="material-icons-round text-primary dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 p-2 rounded-lg">{{ group.id === 'untagged' ? 'article' : 'inventory_2' }}</span>
                    <div>
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white leading-none">{{ group.title }}</h3>
                        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">{{ group.items.length }} Simulacros</p>
                    </div>
                 </div>
                 <!-- Paginación interna por grupo si es muy grande, o mostrar todos (historial suele ser corto) -->
                 <!-- Por ahora mantenemos todos en historial agrupado como comportamiento esperado -->
                 <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    <SimulacroCard 
                        v-for="simulacro in group.items" 
                        :key="simulacro.id" 
                        :simulacro="simulacro"
                        :userRole="userRole"
                        :activeTab="activeTab"
                        @edit="openEditModal"
                        @delete="confirmDelete"
                        @exportPdf="handleExportPdf"
                        @generateAnswerSheets="openAnswerSheetsModal"
                        @uploadOMR="openUploadOMRModal"
                        @reset="confirmReset"
                    />
                 </div>
              </div>
         </div>
         
         <!-- FLAT VIEW (Default) -->
         <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <SimulacroCard 
                v-for="simulacro in paginatedSimulacros" 
                :key="simulacro.id" 
                :simulacro="simulacro"
                :userRole="userRole"
                :activeTab="activeTab"
                @edit="openEditModal"
                @delete="confirmDelete"
                @exportPdf="handleExportPdf"
                @generateAnswerSheets="openAnswerSheetsModal"
                @uploadOMR="openUploadOMRModal"
                @reset="confirmReset"
              />
         </div>
    </div>
    
    
    <!-- Pagination -->
    <div v-if="filteredSimulacros.length > 0 && !(userRole === 'estudiante' && activeTab === 'realizado')" class="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700 mt-6">
      <p class="text-sm text-slate-500 dark:text-slate-400">
        Mostrando <strong>{{ (currentPage - 1) * itemsPerPage + 1 }}</strong> - <strong>{{ Math.min(currentPage * itemsPerPage, filteredSimulacros.length) }}</strong> de <strong>{{ filteredSimulacros.length }}</strong> simulacros
      </p>
      <div class="flex items-center gap-2">
        <button 
          @click="prevPage"
          :disabled="currentPage === 1"
          class="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Anterior
        </button>
        <span class="text-sm text-slate-400 px-2">
            Página {{ currentPage }} de {{ totalPages }}
        </span>
        <button 
          @click="nextPage"
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Siguiente
        </button>
      </div>
    </div>
    
    <!-- Modal Editar Simulacro (Admin IE) -->
    <div v-if="editModal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="closeEditModal"></div>
      <div class="relative w-full max-w-md max-h-[90vh] flex flex-col bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
        <!-- Header -->
        <div class="bg-gradient-to-r from-primary to-indigo-600 text-white p-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-white/20 rounded-lg">
                <span class="material-icons-round">settings</span>
              </div>
              <div>
                <h3 class="font-bold text-lg">Configurar simulacro</h3>
                <p class="text-indigo-200 text-sm">{{ editModal.data.titulo }}</p>
              </div>
            </div>
            <button @click="closeEditModal" type="button" class="h-8 w-8 flex items-center justify-center hover:bg-white/20 rounded-full transition-colors">
              <span class="material-icons-round">close</span>
            </button>
          </div>
        </div>
        
        <!-- Body -->
        <form @submit.prevent="saveSimulacroConfig" class="p-6 space-y-5 overflow-y-auto">
          <!-- Selector Estado (Ciclo de Vida) -->
          <div class="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Estado del simulacro</label>
            <div class="grid grid-cols-2 gap-3">
              <label class="cursor-pointer relative">
                <input type="radio" v-model="editModal.data.estado" value="activo" class="peer sr-only">
                <div class="flex items-center justify-center gap-2 p-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-500 dark:text-slate-400 peer-checked:border-emerald-500 peer-checked:bg-emerald-50 peer-checked:dark:bg-emerald-900/20 peer-checked:text-emerald-700 peer-checked:dark:text-emerald-400 transition-all">
                  <span class="material-icons-round text-[18px]">check_circle</span>
                  <span class="font-medium text-sm">Activo</span>
                </div>
              </label>
              <label class="cursor-pointer relative">
                <input type="radio" v-model="editModal.data.estado" value="finalizado" class="peer sr-only">
                <div class="flex items-center justify-center gap-2 p-3 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-500 dark:text-slate-400 peer-checked:border-slate-500 peer-checked:bg-slate-100 peer-checked:dark:bg-slate-600 peer-checked:text-slate-700 peer-checked:dark:text-slate-200 transition-all">
                  <span class="material-icons-round text-[18px]">task_alt</span>
                  <span class="font-medium text-sm">Finalizado</span>
                </div>
              </label>
            </div>
          </div>

          <!-- Switch Visibilidad (Admin IE y Super Admin) -->
          <div class="flex items-center justify-between p-4 bg-white dark:bg-slate-700 rounded-xl border border-slate-200 dark:border-slate-600">
            <div>
              <label class="font-medium text-slate-800 dark:text-white">Visibilidad estudiantes</label>
              <p class="text-xs text-slate-500 dark:text-slate-400">¿Visible en el listado de estudiantes?</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="editModal.data.activo" class="sr-only peer">
              <div class="w-11 h-6 bg-slate-300 dark:bg-slate-600 peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
          
          <!-- Duración -->
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Duración (minutos)</label>
            <input 
              type="number" 
              v-model.number="editModal.data.duracion_minutos"
              min="1"
              max="300"
              class="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent bg-slate-50 dark:bg-slate-700 dark:text-white"
              placeholder="60"
            />
            <p class="text-xs text-slate-400 mt-1">Tiempo límite para completar el simulacro</p>
          </div>
          
          <!-- Fecha Desde -->
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Disponible desde</label>
            <input 
              type="date" 
              v-model="editModal.data.fecha_disponible_desde"
              class="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent bg-slate-50 dark:bg-slate-700 dark:text-white"
            />
          </div>
          
          <!-- Fecha Hasta -->
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Disponible hasta</label>
            <input 
              type="date" 
              v-model="editModal.data.fecha_disponible_hasta"
              class="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent bg-slate-50 dark:bg-slate-700 dark:text-white"
            />
          </div>
          
          <!-- Buttons -->
          <div class="flex gap-3 pt-4">
            <button 
              type="button"
              @click="closeEditModal"
              class="flex-1 py-3 border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-medium rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cancelar
            </button>
            <button 
              type="submit"
              :disabled="editModal.saving"
              class="flex-1 py-3 bg-primary hover:bg-indigo-600 text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <span v-if="editModal.saving" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ editModal.saving ? 'Guardando...' : 'Guardar cambios' }}
            </button>
          </div>
        </form>
      </div>
    </div>
    

    
    <!-- Modal Reporte Genérico (Reutilizable para Individual y Grupal) -->
    <div v-if="showReporteModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4">
       <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="showReporteModal = false"></div>
       <div class="relative w-full max-w-4xl bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-fade-in-up">
          <div class="bg-indigo-600 dark:bg-indigo-900 text-white p-6 flex justify-between items-center sticky top-0 z-10">
             <div class="flex items-center gap-3">
                <div class="p-2 bg-white/20 rounded-lg"><span class="material-icons-round text-white">psychology</span></div>
                <div>
                    <h3 class="font-bold text-lg">{{ currentReporte?.titulo || 'Informe IA' }}</h3>
                    <p class="text-indigo-200 text-xs flex items-center gap-1">
                        <span class="material-icons-round text-[14px]">{{ currentReporte?.es_grupal ? 'groups' : 'person' }}</span>
                        {{ currentReporte?.es_grupal ? 'Análisis de tendencias grupales' : 'Análisis individual' }}
                    </p>
                </div>
             </div>
             <button @click="showReporteModal = false" class="p-2 hover:bg-white/20 rounded-full transition-colors"><span class="material-icons-round text-2xl">close</span></button>
          </div>
          <div class="flex-1 overflow-y-auto p-8 bg-slate-50 dark:bg-slate-900 prose dark:prose-invert max-w-none">
             <div
               v-if="currentReporte?.es_grupal && currentReporte?.tipo_contenido === 'numerico' && currentReporte?.reporte_data"
               class="not-prose space-y-6"
             >
                <h3 class="text-2xl font-black text-slate-900 dark:text-white">Reporte grupal numérico</h3>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                        <p class="text-xs uppercase tracking-wide text-slate-500">Institución</p>
                        <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ currentReporte.reporte_data.institution_name || 'N/A' }}</p>
                    </div>
                    <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                        <p class="text-xs uppercase tracking-wide text-slate-500">Área</p>
                        <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ currentReporte.reporte_data.area_display || currentReporte.reporte_data.area || 'N/A' }}</p>
                    </div>
                    <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                        <p class="text-xs uppercase tracking-wide text-slate-500">Finalizados</p>
                        <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ currentReporte.reporte_data.students_count || 0 }}</p>
                    </div>
                    <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                        <p class="text-xs uppercase tracking-wide text-slate-500">Rango</p>
                        <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">
                            {{ formatScore100(currentReporte.reporte_data.min_score_100) }} - {{ formatScore100(currentReporte.reporte_data.max_score_100) }}
                        </p>
                    </div>
                    <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                        <p class="text-xs uppercase tracking-wide text-slate-500">Nivel de desempeño</p>
                        <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">
                            {{ currentReporte.reporte_data.performance_level || 'N/A' }}
                            <span v-if="currentReporte.reporte_data.performance_interval" class="text-slate-500 font-medium">
                                ({{ currentReporte.reporte_data.performance_interval }})
                            </span>
                        </p>
                    </div>
                    <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
                        <p class="text-xs uppercase tracking-wide text-slate-500">Fecha de generación</p>
                        <p class="text-sm font-bold text-slate-900 dark:text-white mt-1">{{ currentReporte.reporte_data.generated_at || 'N/A' }}</p>
                    </div>
                </div>

                <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 text-center">
                    <h4 class="text-lg font-extrabold text-slate-900 dark:text-white">Reporte general</h4>
                    <div class="relative w-52 h-52 mx-auto mt-5">
                        <div class="absolute inset-0 rounded-full" :style="groupProgressStyle(currentReporte.reporte_data.average_score_100)"></div>
                        <div class="absolute inset-[14px] rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center">
                            <span class="text-5xl font-black text-indigo-600 dark:text-indigo-400">{{ formatScore(currentReporte.reporte_data.average_score_100) }}</span>
                            <span class="text-sm font-bold text-slate-500">/100</span>
                            <span class="text-xs font-bold text-blue-700 dark:text-blue-300 mt-1">
                                {{ currentReporte.reporte_data.performance_level || 'N/A' }}
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
                                    v-for="(student, idx) in (currentReporte.reporte_data.students || [])"
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
                                <tr v-if="!(currentReporte.reporte_data.students || []).length">
                                    <td colspan="3" class="px-3 py-5 text-center text-slate-500">Sin estudiantes para mostrar.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
             </div>
             <div v-else-if="currentReporte?.analisis_ia?.informe_ia" v-html="renderMarkdown(currentReporte.analisis_ia.informe_ia)"></div>
             <div v-else class="flex flex-col items-center justify-center py-12 text-slate-400">
                 <span class="material-icons-round text-4xl mb-2">content_paste_off</span>
                 <p>Contenido vacío</p>
             </div>
          </div>
          <div class="p-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex justify-end gap-2">
             <button
                v-if="currentReporte?.es_grupal"
                @click="downloadGroupReportPdf"
                :disabled="reportPdfLoading || !currentReporte?.simulacro_id"
                class="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
             >
                <span v-if="reportPdfLoading" class="animate-spin rounded-full h-4 w-4 border-2 border-slate-300 border-t-slate-600 dark:border-slate-600 dark:border-t-slate-200"></span>
                <span v-else class="material-icons-round text-[18px]">download</span>
                Descargar PDF
             </button>
             <button
                @click="showReporteModal = false"
                class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold shadow-md shadow-indigo-500/20 transition-all hover:translate-y-[-1px]"
             >
                Cerrar
             </button>
          </div>
       </div>
    </div>

  <!-- Modal de Hojas de Respuestas OMR -->
  <div v-if="showAnswerSheetsModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="bg-gradient-to-r from-purple-500 to-indigo-600 p-6 text-white">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="material-icons-round text-3xl">assignment</span>
            <div>
              <h2 class="text-2xl font-bold">Generar hojas OMR</h2>
              <p class="text-purple-100 text-sm mt-1">{{ selectedSimulacroForOMR?.titulo }}</p>
            </div>
          </div>
          <button @click="showAnswerSheetsModal = false" class="p-2 hover:bg-white/20 rounded-full transition-colors">
            <span class="material-icons-round text-2xl">close</span>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <div class="mb-6">
          <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-3 flex items-center gap-2">
            <span class="material-icons-round">groups</span>
            Seleccionar Grupos
          </h3>
          <p class="text-sm text-slate-600 dark:text-slate-400 mb-4">
            Seleccione los grupos para los cuales desea generar hojas de respuestas personalizadas.
          </p>

          <!-- Loading -->
          <div v-if="loadingGroups" class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-10 w-10 border-4 border-purple-500 border-t-transparent"></div>
          </div>

          <!-- Lista de grupos -->
          <div v-else-if="gruposDisponibles.length > 0" class="space-y-2">
            <label 
              v-for="grupo in gruposDisponibles" 
              :key="grupo.id"
              class="flex items-center gap-3 p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors cursor-pointer"
            >
              <input 
                type="checkbox" 
                :value="grupo.id"
                v-model="gruposSeleccionados"
                class="w-5 h-5 rounded border-slate-300 text-purple-600 focus:ring-purple-500 focus:ring-offset-0 cursor-pointer"
              />
              <div class="flex-1">
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ grupo.nombre }}</span>
                <span class="text-sm text-slate-500 dark:text-slate-400 ml-2">
                  ({{ grupo.estudiantes_count || 0 }} estudiantes)
                </span>
              </div>
            </label>
          </div>

          <!-- No hay grupos -->
          <div v-else class="flex flex-col items-center justify-center py-8 text-center">
            <span class="material-icons-round text-5xl text-slate-300 dark:text-slate-600 mb-3">group_off</span>
            <p class="text-slate-600 dark:text-slate-400">No hay grupos disponibles</p>
          </div>
        </div>

        <!-- Resumen -->
        <div v-if="gruposSeleccionados.length > 0" class="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-purple-900 dark:text-purple-200">
              Total de hojas a generar:
            </span>
            <span class="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {{ totalEstudiantes }}
            </span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-slate-200 dark:border-slate-700 p-6 bg-slate-50 dark:bg-slate-800/50 flex gap-3 justify-end">
        <button 
          @click="showAnswerSheetsModal = false"
          class="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors font-medium"
        >
          Cancelar
        </button>
        <button 
          @click="generateAnswerSheets"
          :disabled="gruposSeleccionados.length === 0"
          class="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <span class="material-icons-round text-[18px]">download</span>
          Generar Hojas
        </button>
      </div>
    </div>
  </div>

  <!-- Modal de Subir Evidencias OMR (Admin IE) -->
  <div v-if="showUploadOMRModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="bg-gradient-to-r from-purple-500 to-indigo-600 p-6 text-white">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="material-icons-round text-3xl">cloud_upload</span>
            <div>
              <h2 class="text-2xl font-bold">Subir evidencias OMR</h2>
              <p class="text-purple-100 text-sm mt-1">{{ selectedSimulacroForUpload?.titulo }}</p>
            </div>
          </div>
          <button 
            @click="closeUploadOMRModal" 
            :disabled="omrUpload.status === 'processing'"
            class="p-2 hover:bg-white/20 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="material-icons-round text-2xl">close</span>
          </button>
        </div>
      </div>

      <!-- Content: UPLOAD STATE -->
      <div v-if="omrUpload.status === 'idle'" class="flex-1 overflow-y-auto p-6">
        <!-- Drag & Drop Zone -->
        <div 
          class="border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer"
          :class="isDragging ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20' : 'border-slate-300 dark:border-slate-600 hover:border-purple-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleFileDrop"
          @click="triggerFileInput"
        >
          <input 
            type="file" 
            ref="fileInputRef" 
            @change="handleFileSelect" 
            multiple 
            accept="image/jpeg,image/png,image/webp,application/pdf"
            class="hidden"
          />
          <span class="material-icons-round text-5xl text-purple-500 mb-3">cloud_upload</span>
          <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
            {{ isDragging ? '¡Suelta los archivos aquí!' : 'Arrastra tus archivos aquí' }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-2">
            o haz clic para seleccionar
          </p>
          <p class="text-xs text-slate-400 dark:text-slate-500">
            Formatos: JPG, PNG, WEBP, PDF (máx. 20 MB c/u)
          </p>
        </div>

        <!-- Lista de Archivos Seleccionados -->
        <div v-if="omrUpload.files.length > 0" class="mt-6">
          <div class="flex items-center justify-between mb-3">
            <h4 class="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <span class="material-icons-round text-[18px]">folder</span>
              Archivos Seleccionados ({{ omrUpload.files.length }})
            </h4>
            <button 
              @click="clearOMRFiles"
              class="text-xs text-red-500 hover:text-red-700 flex items-center gap-1"
            >
              <span class="material-icons-round text-[14px]">delete_sweep</span>
              Limpiar todo
            </button>
          </div>
          <div class="space-y-2 max-h-48 overflow-y-auto pr-2">
            <div 
              v-for="(file, index) in omrUpload.files" 
              :key="index"
              class="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600"
            >
              <div class="flex items-center gap-3">
                <span class="material-icons-round text-slate-400">
                  {{ file.type.includes('pdf') ? 'picture_as_pdf' : 'image' }}
                </span>
                <div>
                  <p class="text-sm font-medium text-slate-700 dark:text-slate-300 truncate max-w-[200px]">{{ file.name }}</p>
                  <p class="text-xs text-slate-500 dark:text-slate-400">{{ formatFileSize(file.size) }}</p>
                </div>
              </div>
              <button 
                @click="removeOMRFile(index)"
                class="p-1 text-slate-400 hover:text-red-500 transition-colors"
              >
                <span class="material-icons-round text-[18px]">close</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Opciones de Procesamiento -->
        <div v-if="omrUpload.files.length > 0" class="mt-6 p-4 bg-slate-50 dark:bg-slate-700/30 rounded-xl border border-slate-200 dark:border-slate-600">
          <h4 class="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <span class="material-icons-round text-[18px]">settings</span>
            Método de procesamiento
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label class="cursor-pointer">
              <input type="radio" v-model="omrUpload.method" value="vision_ai" class="peer sr-only" />
              <div class="p-4 rounded-lg border-2 border-slate-200 dark:border-slate-600 peer-checked:border-purple-500 peer-checked:bg-purple-50 dark:peer-checked:bg-purple-900/20 transition-all">
                <div class="flex items-center gap-2 mb-2">
                  <span class="material-icons-round text-purple-500">psychology</span>
                  <span class="font-semibold text-slate-800 dark:text-slate-200">Visión IA (Claude)</span>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400">Más preciso, detecta marcas difusas</p>
              </div>
            </label>
            <label class="cursor-pointer">
              <input type="radio" v-model="omrUpload.method" value="ocr_tradicional" class="peer sr-only" />
              <div class="p-4 rounded-lg border-2 border-slate-200 dark:border-slate-600 peer-checked:border-purple-500 peer-checked:bg-purple-50 dark:peer-checked:bg-purple-900/20 transition-all">
                <div class="flex items-center gap-2 mb-2">
                  <span class="material-icons-round text-purple-500">document_scanner</span>
                  <span class="font-semibold text-slate-800 dark:text-slate-200">OCR Tradicional</span>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400">Más rápido, requiere marcas claras</p>
              </div>
            </label>
          </div>
        </div>

      </div>

      <!-- Content: PROCESSING STATE -->
      <div v-else-if="omrUpload.status === 'processing'" class="flex-1 overflow-y-auto p-6">
        <div class="text-center mb-8">
          <div class="relative inline-flex items-center justify-center mb-4">
            <div class="animate-spin rounded-full h-16 w-16 border-4 border-purple-200 border-t-purple-500"></div>
            <span class="absolute material-icons-round text-purple-500 text-2xl">document_scanner</span>
          </div>
          <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">Procesando hojas de respuestas</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Esto puede tomar unos minutos...</p>
        </div>

        <!-- Progress Bar -->
        <div class="mb-6">
          <div class="flex justify-between text-sm mb-2">
            <span class="text-slate-600 dark:text-slate-400">Progreso</span>
            <span class="font-semibold text-purple-600 dark:text-purple-400">{{ omrUpload.progress.current }}/{{ omrUpload.progress.total }} ({{ omrUpload.progress.percent }}%)</span>
          </div>
          <div class="h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div 
              class="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300"
              :style="{ width: `${omrUpload.progress.percent}%` }"
            ></div>
          </div>
        </div>

        <!-- Current File -->
        <div class="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4 mb-4">
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-1">Procesando:</p>
          <p class="font-medium text-slate-800 dark:text-slate-200 truncate">{{ omrUpload.currentFile }}</p>
        </div>

        <!-- Partial Results -->
        <div v-if="omrUpload.results.length > 0" class="space-y-2 max-h-48 overflow-y-auto">
          <div 
            v-for="(result, idx) in omrUpload.results.slice(-5)" 
            :key="idx"
            class="flex items-center gap-3 p-3 rounded-lg"
            :class="result.status === 'success' ? 'bg-emerald-50 dark:bg-emerald-900/20' : result.status === 'warning' ? 'bg-amber-50 dark:bg-amber-900/20' : 'bg-red-50 dark:bg-red-900/20'"
          >
            <span class="material-icons-round text-[18px]" :class="result.status === 'success' ? 'text-emerald-500' : result.status === 'warning' ? 'text-amber-500' : 'text-red-500'">
              {{ result.status === 'success' ? 'check_circle' : result.status === 'warning' ? 'warning' : 'error' }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{{ result.filename }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">{{ result.student || result.message }}</p>
            </div>
            <span v-if="result.confidence" class="text-xs font-semibold text-slate-500 dark:text-slate-400">{{ result.confidence }}%</span>
          </div>
        </div>
      </div>

      <!-- Content: COMPLETED STATE -->
      <div v-else-if="omrUpload.status === 'completed'" class="flex-1 overflow-y-auto p-6">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-900/30 mb-4">
            <span class="material-icons-round text-5xl text-emerald-500">check_circle</span>
          </div>
          <h3 class="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">¡Procesamiento Completado!</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">Las respuestas han sido registradas correctamente</p>
        </div>

        <!-- Summary Stats -->
        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="text-center p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl border border-emerald-200 dark:border-emerald-800">
            <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ omrUpload.summary.success }}</p>
            <p class="text-xs text-emerald-700 dark:text-emerald-300">Exitosas</p>
          </div>
          <div class="text-center p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ omrUpload.summary.warnings }}</p>
            <p class="text-xs text-amber-700 dark:text-amber-300">Advertencias</p>
          </div>
          <div class="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800">
            <p class="text-2xl font-bold text-red-600 dark:text-red-400">{{ omrUpload.summary.errors }}</p>
            <p class="text-xs text-red-700 dark:text-red-300">Errores</p>
          </div>
        </div>

        <!-- Detailed Results (only show errors/warnings if any) -->
        <div v-if="omrUpload.summary.warnings > 0 || omrUpload.summary.errors > 0" class="mb-4">
          <h4 class="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <span class="material-icons-round text-[18px]">report</span>
            Requieren atención
          </h4>
          <div class="space-y-2 max-h-40 overflow-y-auto">
            <div 
              v-for="(result, idx) in omrUpload.results.filter(r => r.status !== 'success')" 
              :key="idx"
              class="flex items-center justify-between p-3 rounded-lg"
              :class="result.status === 'warning' ? 'bg-amber-50 dark:bg-amber-900/20' : 'bg-red-50 dark:bg-red-900/20'"
            >
              <div class="flex items-center gap-3">
                <span class="material-icons-round" :class="result.status === 'warning' ? 'text-amber-500' : 'text-red-500'">
                  {{ result.status === 'warning' ? 'warning' : 'error' }}
                </span>
                <div>
                  <p class="text-sm font-medium text-slate-800 dark:text-slate-200">{{ result.filename }}</p>
                  <p class="text-xs text-slate-500 dark:text-slate-400">{{ result.message }}</p>
                </div>
              </div>
              <button 
                v-if="result.status === 'warning'"
                @click="openManualAssignment(result)"
                class="px-3 py-1 text-xs font-medium bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
              >
                Asignar
              </button>
            </div>
          </div>
        </div>

        <!-- Info note -->
        <div v-if="!omrUpload.saved" class="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <div class="flex items-start gap-3">
            <span class="material-icons-round text-amber-500 mt-0.5">warning</span>
            <div>
              <p class="text-sm font-medium text-amber-900 dark:text-amber-200">Revisa los resultados antes de guardar</p>
              <p class="text-xs text-amber-700 dark:text-amber-300">Los datos aún no están guardados. Haz clic en "Guardar" para registrar las respuestas.</p>
            </div>
          </div>
        </div>
        <div v-else class="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
          <div class="flex items-start gap-3">
            <span class="material-icons-round text-emerald-500 mt-0.5">check_circle</span>
            <div>
              <p class="text-sm font-medium text-emerald-900 dark:text-emerald-200">Respuestas guardadas exitosamente</p>
              <p class="text-xs text-emerald-700 dark:text-emerald-300">Los reportes IA se generarán automáticamente. Los estudiantes ya pueden ver sus puntajes.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-slate-200 dark:border-slate-700 p-6 bg-slate-50 dark:bg-slate-800/50 flex gap-3 justify-end">
        <button 
          v-if="omrUpload.status === 'idle'"
          @click="closeUploadOMRModal"
          class="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors font-medium"
        >
          Cancelar
        </button>
        <button 
          v-if="omrUpload.status === 'idle'"
          @click="startOMRProcessing"
          :disabled="omrUpload.files.length === 0"
          class="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <span class="material-icons-round text-[18px]">play_arrow</span>
          Procesar {{ omrUpload.files.length }} Archivo{{ omrUpload.files.length !== 1 ? 's' : '' }}
        </button>
        
        <!-- Botones para estado completado -->
        <template v-if="omrUpload.status === 'completed'">
          <button 
            @click="closeUploadOMRModal"
            class="px-4 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors font-medium"
          >
            Cerrar sin guardar
          </button>
          <button 
            v-if="omrUpload.summary.success > 0 && !omrUpload.saved"
            @click="confirmSaveOMRResults"
            :disabled="omrUpload.saving"
            class="px-6 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-all font-medium flex items-center gap-2 disabled:opacity-50"
          >
            <span v-if="omrUpload.saving" class="material-icons-round text-[18px] animate-spin">refresh</span>
            <span v-else class="material-icons-round text-[18px]">save</span>
            {{ omrUpload.saving ? 'Guardando...' : `Guardar ${omrUpload.summary.success} Resultado${omrUpload.summary.success !== 1 ? 's' : ''}` }}
          </button>
          <button 
            v-if="omrUpload.saved"
            @click="closeUploadOMRModal"
            class="px-6 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all font-medium flex items-center gap-2"
          >
            <span class="material-icons-round text-[18px]">check</span>
            Listo
          </button>
        </template>
      </div>
    </div>
  </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useSimulacrosStore } from '../stores/simulacros';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import ConfirmDialog from 'primevue/confirmdialog';
import Dialog from 'primevue/dialog';
import { useRouter } from 'vue-router';
import Select from 'primevue/select';
import SimulacroCard from '../components/SimulacroCard.vue';
import api from '../api/axios';

const authStore = useAuthStore();
const simulacrosStore = useSimulacrosStore();
const router = useRouter(); 
const toast = useToast();
const confirm = useConfirm(); 

// User Role
const userRole = computed(() => authStore.user?.rol?.nombre || 'guest');

// Data Local (Filtros de UI)
const searchQuery = ref('');
const filterArea = ref(null);
const filterStatus = ref(null);
const filterSede = ref(null);
const activeTab = ref('pendiente');
const currentPage = ref(1);
const itemsPerPage = 10;
const startBlockedDialogVisible = ref(false);
const startBlockedDialogTitle = ref('Cupos agotados');
const startBlockedDialogMessage = ref('No fue posible iniciar el simulacro.');

// Data del Store (Mapeada)
const simulacros = computed(() => simulacrosStore.simulacros);
const loading = computed(() => simulacrosStore.loading);

const hasFilters = computed(() => {
    return filterSede.value || filterStatus.value || filterArea.value;
});

// Opciones para Selects
const areaOptions = [
  { label: 'Todas las áreas', value: null },
  { label: 'Matemáticas', value: 'MATEMATICAS' },
  { label: 'Lectura Crítica', value: 'LECTURA_CRITICA' },
  { label: 'Ciencias Naturales', value: 'CIENCIAS_NATURALES' },
  { label: 'Sociales', value: 'SOCIALES_CIUDADANAS' },
  { label: 'Inglés', value: 'INGLES' }
];

// Opciones de estado (Simulacros Lifecycle) - Ya no existe 'borrador'
const statusOptions = computed(() => {
  return [
    { label: 'Todos los estados', value: null },
    { label: 'Activo', value: 'activo' },
    { label: 'Finalizado', value: 'finalizado' }
  ];
});

// Opciones dinámicas
const sedeOptions = ref([{ label: 'Todas las sedes', value: null }]);

// Mostrar filtro de sede solo si hay más de una sede real
const showSedeFilter = computed(() => sedeOptions.value.length > 2);

// Carga Inicial de Opciones (Sedes)
const loadOptions = async () => {
    if (userRole.value === 'admin') {
        try {
            const res = await api.get('/sedes/');
            const sedes = Array.isArray(res.data) ? res.data : [];
            sedeOptions.value = [
                { label: 'Todas las sedes', value: null },
                ...sedes.map(s => ({ label: s.nombre, value: s.id }))
            ];
            // Si solo existe una sede real, no tiene sentido filtrar
            if (sedes.length <= 1) {
                filterSede.value = null;
            }
        } catch (e) {
            console.error('Error cargando sedes:', e);
        }
    }
};

onMounted(() => {
  try {
    const blockedRaw = sessionStorage.getItem('simulacros_start_blocked_dialog');
    if (blockedRaw) {
      const blockedPayload = JSON.parse(blockedRaw);
      sessionStorage.removeItem('simulacros_start_blocked_dialog');
      startBlockedDialogTitle.value = blockedPayload?.title || 'Cupos agotados';
      startBlockedDialogMessage.value = blockedPayload?.message || 'No fue posible iniciar el simulacro.';
      startBlockedDialogVisible.value = true;
    }

    const raw = sessionStorage.getItem('simulacros_start_error_toast');
    if (!raw) return;
    const payload = JSON.parse(raw);
    sessionStorage.removeItem('simulacros_start_error_toast');
    if (payload?.detail) {
      toast.add({
        severity: payload.severity || 'warn',
        summary: payload.summary || 'No fue posible iniciar',
        detail: payload.detail,
        life: payload.life || 4500
      });
    }
  } catch (_) {
    sessionStorage.removeItem('simulacros_start_error_toast');
  }
});

// Cargar Simulacros
// Cargar Simulacros
const fetchSimulacros = async () => {
    if (userRole.value === 'estudiante') {
        // Cargar según el tab activo (pendiente o realizado)
        await simulacrosStore.fetchSimulacros({ estado: activeTab.value }, true);
    } else if (userRole.value === 'admin') {
        // Admin Institución: Cargar simulacros de su institución, opcionalmente filtrados por sede
        const params = {};
        if (authStore.user?.institucion_id) {
            params.institucion_id = authStore.user.institucion_id;
        }
        if (filterSede.value) params.sede_id = filterSede.value;
        if (filterStatus.value) params.estado = filterStatus.value;
        else params.estado = 'todos';

        await simulacrosStore.fetchSimulacros(params);
    } else {
        // Admin Institución: Cargar todo lo de su institución (normal)
        await simulacrosStore.fetchSimulacros();
    }
};

// Watcher de Sede
watch(filterSede, async () => {
    if (userRole.value === 'admin') {
        await fetchSimulacros(); // Recargar lista
    }
});

// Watcher de otros filtros para Super Admin
watch([filterStatus], async () => {
    if (userRole.value === 'admin') {
        await fetchSimulacros();
    }
});

// Watcher de User Role para inicialización
watch(userRole, async (val) => {
    if (val && val !== 'guest') {
        await Promise.all([
            loadOptions(),
            fetchSimulacros()
        ]);
    }
}, { immediate: true });


// Lógica de Tabs
const changeTab = async (tab) => {
    activeTab.value = tab;
    if (userRole.value === 'estudiante') {
        await simulacrosStore.fetchSimulacros({ estado: tab }, true);
    }
};

// Limpiar filtros y PAGINACIÓN
const clearFilters = () => {
    filterSede.value = null;
    filterArea.value = null;
    filterStatus.value = null;
    searchQuery.value = '';
    currentPage.value = 1; // Resetear página
};

// Resetear página al cambiar filtros
watch([searchQuery, filterArea, filterStatus, filterSede], () => {
    currentPage.value = 1;
});

// Computed FilteredSimulacros
const filteredSimulacros = computed(() => {
  let result = simulacros.value;
  
  // Filtro de búsqueda
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(s => 
      s.titulo?.toLowerCase().includes(query) || 
      s.descripcion?.toLowerCase().includes(query)
    );
  }
  
  if (filterSede.value) {
      result = result.filter(s => s.sede_id === filterSede.value);
  }

  if (filterArea.value) {
    result = result.filter(s => s.area === filterArea.value);
  }

  // Filtro de Estado: SOLO si NO es estudiante (o si estudiante quiere filtrar extra, pero requerimiento dice redundante)
  // Pero dejaremos la lógica por si acaso filterStatus tiene valor (aunque en UI se ocultará)
  if (filterStatus.value) {
    result = result.filter(s => s.estado === filterStatus.value);
  }
  
  return result;
});

// Computed Paginado
const totalPages = computed(() => Math.ceil(filteredSimulacros.value.length / itemsPerPage));

const paginatedSimulacros = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    return filteredSimulacros.value.slice(start, end);
});

// Navegación
const prevPage = () => {
    if (currentPage.value > 1) currentPage.value--;
};

const nextPage = () => {
    if (currentPage.value < totalPages.value) currentPage.value++;
};

// Agrupación para Historial
const groupedSimulacros = computed(() => {
    if (userRole.value !== 'estudiante' || activeTab.value !== 'realizado') return [];
        return [{ id: 'todos', title: 'Simulacros realizados', items: filteredSimulacros.value }];
});


// Markdown Helper (Duplicate from EstudianteDetalle, idealmente mover a utils)
const renderMarkdown = (text) => {
   if (!text) return '';
   return text
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold mt-4 mb-2 text-slate-800 dark:text-slate-100">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-6 mb-3 text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-700 pb-2">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-6 mb-4 text-slate-900 dark:text-white">$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc marker:text-primary">$1</li>')
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

// Stats Helpers (para las tarjetas superiores)
const countByStatus = computed(() => ({
  activo: simulacros.value.filter(s => s.estado === 'activo').length,
  finalizado: simulacros.value.filter(s => s.estado === 'finalizado').length
}));

const statsCardLabel = computed(() => {
  if (userRole.value === 'estudiante' && activeTab.value === 'realizado') return 'Realizados';
  if (!filterStatus.value) return 'Activos';
  const labels = {
    'activo': 'Activos',
    'finalizado': 'Finalizados'
  };
  return labels[filterStatus.value] || 'Activos';
});

const statsCardCount = computed(() => {
  if (userRole.value === 'estudiante' && activeTab.value === 'realizado') return simulacros.value.length;
  if (!filterStatus.value) return countByStatus.value.activo;
  return countByStatus.value[filterStatus.value] || 0;
});

const statsCardIcon = computed(() => {
  if (userRole.value === 'estudiante' && activeTab.value === 'realizado') return 'fact_check';
  if (!filterStatus.value) return 'check_circle';
  const icons = {
    'activo': 'check_circle',
    'finalizado': 'task_alt'
  };
  return icons[filterStatus.value] || 'check_circle';
});

const statsCardTextClass = computed(() => {
  if (userRole.value === 'estudiante' && activeTab.value === 'realizado') return 'text-primary';
  if (!filterStatus.value) return 'text-emerald-600';
  const classes = {
    'activo': 'text-emerald-600',
    'finalizado': 'text-slate-600'
  };
  return classes[filterStatus.value] || 'text-emerald-600';
});

const statsCardBgClass = computed(() => {
  if (userRole.value === 'estudiante' && activeTab.value === 'realizado') return 'bg-indigo-50 text-primary';
  if (!filterStatus.value) return 'bg-emerald-50 text-emerald-600';
  const classes = {
    'activo': 'bg-emerald-50 text-emerald-600',
    'finalizado': 'bg-slate-100 text-slate-600'
  };
  return classes[filterStatus.value] || 'bg-emerald-50 text-emerald-600';
});

const totalQuestions = computed(() => {
  return filteredSimulacros.value.reduce((sum, s) => sum + (s.total_preguntas || 0), 0);
});

// Reporte Grupal Logic
const groupReportLoading = ref(false);
const checkingGroupReport = ref(false);
const existingGroupReport = ref(null);
const showReporteModal = ref(false);
const currentReporte = ref(null);
const reportPdfLoading = ref(false);

const canGenerateGroupReport = computed(() => {
    return (
      userRole.value === 'admin' &&
      filterArea.value &&
      filterStatus.value === 'finalizado' &&
      filteredSimulacros.value.length > 0
    );
});

// Verificar si existe reporte grupal cuando cambian los filtros
const checkExistingGroupReport = async () => {
    if (userRole.value !== 'admin') {
        existingGroupReport.value = null;
        return;
    }

    const sim = filteredSimulacros.value[0];
    if (!sim || !canGenerateGroupReport.value) {
        existingGroupReport.value = null;
        return;
    }
    
    checkingGroupReport.value = true;
    try {
        const res = await api.get(`/simulacros/${sim.id}/reporte-grupal`);
        existingGroupReport.value = res.data.exists ? res.data : null;
    } catch (e) {
        console.error('Error checking group report:', e);
        existingGroupReport.value = null;
    } finally {
        checkingGroupReport.value = false;
    }
};

// Watcher para verificar reporte cuando los filtros cambian
watch([filterArea, filterStatus, filteredSimulacros], () => {
    if (canGenerateGroupReport.value) {
        checkExistingGroupReport();
    } else {
        existingGroupReport.value = null;
    }
}, { immediate: true });

const generateGroupReportFromFilter = async () => {
    if (userRole.value !== 'admin') return;

    const sim = filteredSimulacros.value[0];
    if (!sim) return;
    
    // Si ya existe, solo mostrarlo
    if (existingGroupReport.value) {
        currentReporte.value = {
            analisis_ia: { informe_ia: existingGroupReport.value.informe },
            titulo: `Diagnóstico Grupal: ${sim.titulo}`,
            es_grupal: true,
            simulacro_id: sim.id,
            tipo_contenido: existingGroupReport.value.tipo_contenido || (existingGroupReport.value.data ? 'numerico' : 'markdown'),
            reporte_data: existingGroupReport.value.data || existingGroupReport.value.estadisticas || null
        };
        showReporteModal.value = true;
        return;
    }
    
    // Si no existe, generarlo
    groupReportLoading.value = true;
    try {
        const res = await api.post(`/simulacros/${sim.id}/reporte-grupal`);
        
        currentReporte.value = {
            analisis_ia: { informe_ia: res.data.informe },
            titulo: `Diagnóstico Grupal: ${sim.titulo}`,
            es_grupal: true,
            simulacro_id: sim.id,
            tipo_contenido: res.data.tipo_contenido || (res.data.data ? 'numerico' : 'markdown'),
            reporte_data: res.data.data || res.data.estadisticas || null
        };
        showReporteModal.value = true;
        
        // Marcar como existente ahora
        existingGroupReport.value = res.data;
        
    } catch (e) {
        console.error(e);
        const detailMsg = e?.response?.data?.detail || 'No se pudo generar el reporte grupal';
        toast.add({ severity: 'error', summary: 'Error', detail: detailMsg, life: 4000 });
    } finally {
        groupReportLoading.value = false;
    }
};

const downloadGroupReportPdf = async () => {
    if (!currentReporte.value?.es_grupal || !currentReporte.value?.simulacro_id) return;

    reportPdfLoading.value = true;
    try {
        const url = `/simulacros/${currentReporte.value.simulacro_id}/reporte-grupal/pdf`;
        const response = await api.get(url, { responseType: 'blob' });
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        const title = (currentReporte.value.titulo || 'Diagnostico_Grupal').replace(/\s+/g, '_');
        link.download = `${title}.pdf`;
        link.click();
    } catch (e) {
        const detailMsg = e?.response?.data?.detail || 'No se pudo descargar el reporte grupal en PDF';
        toast.add({ severity: 'error', summary: 'Error', detail: detailMsg, life: 4000 });
    } finally {
        reportPdfLoading.value = false;
    }
};

// Modal Logic
const editModal = ref({
  show: false,
  saving: false,
  data: {
    id: null,
    titulo: '',
    estado: 'activo', 
    activo: true,
    duracion_minutos: 60,
    fecha_disponible_desde: null,
    fecha_disponible_hasta: null
  }
});

const openEditModal = (simulacro) => {
  editModal.value.data = {
    id: simulacro.id,
    titulo: simulacro.titulo,
    estado: simulacro.estado,
    activo: simulacro.activo,
    duracion_minutos: simulacro.duracion_minutos || 60,
    fecha_disponible_desde: simulacro.fecha_disponible_desde || null,
    fecha_disponible_hasta: simulacro.fecha_disponible_hasta || null
  };
  editModal.value.show = true;
};

const closeEditModal = () => {
  editModal.value.show = false;
};

const saveSimulacroConfig = async () => {
  editModal.value.saving = true;
  try {
    await simulacrosStore.updateSimulacro(editModal.value.data.id, {
      activo: editModal.value.data.activo,
      estado: editModal.value.data.estado,
      duracion_minutos: editModal.value.data.duracion_minutos,
      fecha_disponible_desde: editModal.value.data.fecha_disponible_desde,
      fecha_disponible_hasta: editModal.value.data.fecha_disponible_hasta
    });
    
    closeEditModal();
    toast.add({ severity: 'success', summary: 'Actualizado', detail: 'Simulacro actualizado correctamente', life: 3000 });
  } catch (error) {
    console.error('Error actualizando simulacro:', error);
    toast.add({ severity: 'error', summary: 'Error al guardar', detail: error.response?.data?.detail || error.message, life: 5000 });
  } finally {
    editModal.value.saving = false;
  }
};

// Lógica de Eliminación
const confirmDelete = (simulacro) => {
  confirm.require({
    message: `¿Estás seguro de que deseas eliminar el simulacro "${simulacro.titulo}"? Esta acción no se puede deshacer y eliminará:\n• Todas las respuestas de estudiantes\n• Todas las preguntas usadas asociadas`,
    header: 'Confirmar Eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Sí, eliminar',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        await simulacrosStore.deleteSimulacro(simulacro.id);
        toast.add({ 
          severity: 'success', 
          summary: 'Eliminado', 
          detail: `El simulacro "${simulacro.titulo}" ha sido eliminado correctamente.`,
          life: 3000 
        });
      } catch (error) {
        console.error('Error eliminando simulacro:', error);
        toast.add({ 
          severity: 'error', 
          summary: 'Error al eliminar', 
          detail: error.response?.data?.detail || error.message,
          life: 5000 
        });
      }
    }
  });
};

// Lógica de Reset (Reintentar Simulacro)
const confirmReset = (simulacro) => {
  if (userRole.value !== 'admin' || simulacro.estado !== 'finalizado') return;

  confirm.require({
    message: `¿Reintentar el simulacro "${simulacro.titulo}"?\nSe reabrirá el simulacro y se anularán los intentos y reportes asociados para permitir un nuevo intento.`,
    header: 'Confirmar Reintento',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-warning',
    acceptLabel: 'Sí, reintentar',
    rejectLabel: 'Cancelar',
    accept: async () => {
      try {
        const motivo = `Reset manual por ${authStore.user?.email || 'admin'}`;
        await api.post(`/simulacros/${simulacro.id}/reset`, { motivo });
        const idx = simulacrosStore.simulacros.findIndex(s => s.id === simulacro.id);
        if (idx !== -1) {
          simulacrosStore.simulacros.splice(idx, 1, {
            ...simulacrosStore.simulacros[idx],
            estado: 'activo',
            activo: true
          });
        }
        toast.add({
          severity: 'success',
          summary: 'Simulacro reabierto',
          detail: 'Se anuló el histórico y se reactivó el simulacro para nuevos intentos.',
          life: 3500
        });
      } catch (error) {
        console.error('Error reseteando simulacro:', error);
        toast.add({
          severity: 'error',
          summary: 'Error al reintentar',
          detail: error.response?.data?.detail || error.message,
          life: 5000
        });
      }
    }
  });
};

// Lógica de Exportación a PDF (Vía Backend)
const handleExportPdf = async (simulacro) => {
  try {
    toast.add({ 
      severity: 'info', 
      summary: 'Generando PDF', 
      detail: 'Descargando cuadernillo de alta calidad...', 
      life: 3000 
    });

    const response = await api.get(`/simulacros/${simulacro.id}/pdf`, {
      responseType: 'blob'
    });

    // Crear blob y link de descarga
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Obtener nombre del archivo del header o generar uno
    const contentDisposition = response.headers['content-disposition'];
    let filename = `Simulacro_${simulacro.titulo.replace(/\s+/g, '_')}.pdf`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch && filenameMatch.length === 2) {
        filename = filenameMatch[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    toast.add({ 
      severity: 'success', 
      summary: 'Éxito', 
      detail: 'Cuadernillo descargado correctamente', 
      life: 3000 
    });
  } catch (error) {
    console.error('Error descargando PDF:', error);
    
    let mensajeError = 'No se pudo descargar el cuadernillo';
    
    // Intentar leer el blob de error si existe
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text();
        const json = JSON.parse(text);
        if (json.detail) mensajeError = json.detail;
      } catch (e) {
        // Fallback
      }
    } else if (error.response?.data?.detail) {
      mensajeError = error.response.data.detail;
    }
    
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: mensajeError, 
      life: 5000 
    });
  }
};

// ==================== HOJAS DE RESPUESTAS OMR ====================

// Estado para el modal de hojas OMR
const showAnswerSheetsModal = ref(false);
const selectedSimulacroForOMR = ref(null);
const gruposDisponibles = ref([]);
const gruposSeleccionados = ref([]);
const loadingGroups = ref(false);

// Abrir modal de selección de grupos
const openAnswerSheetsModal = async (simulacro) => {
  selectedSimulacroForOMR.value = simulacro;
  showAnswerSheetsModal.value = true;
  gruposSeleccionados.value = [];
  
  // Cargar grupos disponibles
  await loadAvailableGroups();
};

// Cargar grupos disponibles de la institución
const loadAvailableGroups = async () => {
  loadingGroups.value = true;
  
  try {
    // Si es admin, obtener grupos de la institución del simulacro
    // Si es admin, obtener grupos de su institución
    let institucionId = null;
    
    if (userRole.value === 'admin' && selectedSimulacroForOMR.value) {
      institucionId = selectedSimulacroForOMR.value.institucion_id;
    } else if (userRole.value === 'admin') {
      institucionId = authStore.user?.institucion_id;
    }
    
    if (!institucionId) {
      throw new Error('No se pudo determinar la institución');
    }
    
    const response = await api.get(`/grupos/`, {
      params: { institucion_id: institucionId }
    });
    gruposDisponibles.value = Array.isArray(response.data) ? response.data : [];
    
  } catch (error) {
    console.error('Error cargando grupos:', error);
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'No se pudieron cargar los grupos',
      life: 3000
    });
  } finally {
    loadingGroups.value = false;
  }
};

// Generar hojas OMR
const generateAnswerSheets = async () => {
  if (gruposSeleccionados.value.length === 0) {
    toast.add({
      severity: 'warn',
      summary: 'Selección requerida',
      detail: 'Debe seleccionar al menos un grupo',
      life: 3000
    });
    return;
  }
  
  toast.add({
    severity: 'info',
    summary: 'Generando Hojas OMR',
    detail: 'Preparando hojas de respuestas personalizadas...',
    life: 3000
  });
  
  try {
    const response = await api.post(
      `/simulacros/${selectedSimulacroForOMR.value.id}/hojas-respuestas`,
      {
        grupos_ids: gruposSeleccionados.value
      },
      {
        responseType: 'blob'
      }
    );
    
    // Crear enlace de descarga
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Hojas_OMR_${selectedSimulacroForOMR.value.titulo}.pdf`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.add({
      severity: 'success',
      summary: 'Hojas OMR Generadas',
      detail: 'Las hojas de respuestas se han descargado exitosamente',
      life: 3000
    });
    
    // Cerrar modal
    showAnswerSheetsModal.value = false;
    
  } catch (error) {
    console.error('Error generando hojas OMR:', error);
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: error.response?.data?.detail || 'No se pudieron generar las hojas OMR',
      life: 5000
    });
  }
};

// Computed para contar total de estudiantes
const totalEstudiantes = computed(() => {
  return gruposDisponibles.value
    .filter(g => gruposSeleccionados.value.includes(g.id))
    .reduce((sum, grupo) => sum + (grupo.estudiantes_count || 0), 0);
});


// ==================== UPLOAD EVIDENCIAS OMR ====================

// Estado del modal
const showUploadOMRModal = ref(false);
const selectedSimulacroForUpload = ref(null);
const isDragging = ref(false);
const fileInputRef = ref(null);

// Estado de upload y procesamiento
const omrUpload = ref({
  status: 'idle', // 'idle' | 'processing' | 'completed'
  files: [],
  method: 'vision_ai', // 'vision_ai' | 'ocr_tradicional'
  progress: {
    current: 0,
    total: 0,
    percent: 0
  },
  currentFile: '',
  results: [],
  summary: {
    success: 0,
    warnings: 0,
    errors: 0
  },
  saving: false,
  saved: false,
  saveResults: null
});

// Abrir modal de upload OMR
const openUploadOMRModal = (simulacro) => {
  selectedSimulacroForUpload.value = simulacro;
  showUploadOMRModal.value = true;
  resetOMRUpload();
};

// Cerrar modal de upload OMR
const closeUploadOMRModal = () => {
  if (omrUpload.value.status === 'processing') return; // No cerrar durante procesamiento
  showUploadOMRModal.value = false;
  resetOMRUpload();
};

// Resetear estado de upload
const resetOMRUpload = () => {
  omrUpload.value = {
    status: 'idle',
    files: [],
    method: 'vision_ai',
    progress: { current: 0, total: 0, percent: 0 },
    currentFile: '',
    results: [],
    summary: { success: 0, warnings: 0, errors: 0 },
    saving: false,
    saved: false,
    saveResults: null
  };
};

// Trigger para input de archivo
const triggerFileInput = () => {
  fileInputRef.value?.click();
};

// Handler para selección de archivos
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files);
  addFiles(files);
  event.target.value = ''; // Reset input
};

// Handler para drag & drop
const handleFileDrop = (event) => {
  isDragging.value = false;
  const files = Array.from(event.dataTransfer.files);
  addFiles(files);
};

// Agregar archivos validando tipo y tamaño
const addFiles = (newFiles) => {
  const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
  const maxSize = 20 * 1024 * 1024; // 20 MB

  newFiles.forEach(file => {
    if (!validTypes.includes(file.type)) {
      toast.add({
        severity: 'warn',
        summary: 'Formato no válido',
        detail: `${file.name} no es un formato permitido`,
        life: 3000
      });
      return;
    }

    if (file.size > maxSize) {
      toast.add({
        severity: 'warn',
        summary: 'Archivo muy grande',
        detail: `${file.name} excede el límite de 20 MB`,
        life: 3000
      });
      return;
    }

    // Evitar duplicados
    if (!omrUpload.value.files.find(f => f.name === file.name && f.size === file.size)) {
      omrUpload.value.files.push(file);
    }
  });
};

// Remover un archivo de la lista
const removeOMRFile = (index) => {
  omrUpload.value.files.splice(index, 1);
};

// Limpiar todos los archivos
const clearOMRFiles = () => {
  omrUpload.value.files = [];
};

// Formatear tamaño de archivo
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
};

// Iniciar procesamiento OMR
const startOMRProcessing = async () => {
  if (omrUpload.value.files.length === 0) return;

  omrUpload.value.status = 'processing';
  omrUpload.value.progress.total = omrUpload.value.files.length;
  omrUpload.value.progress.current = 0;
  omrUpload.value.progress.percent = 0;
  omrUpload.value.currentFile = 'Preparando archivos...';
  omrUpload.value.results = [];

  try {
    // Crear FormData con los archivos
    const formData = new FormData();
    omrUpload.value.files.forEach((file, index) => {
      formData.append('files', file);
    });

    omrUpload.value.currentFile = 'Enviando al servidor...';
    omrUpload.value.progress.percent = 10;

    // Llamar al endpoint de procesamiento OMR
    const response = await api.post(
      `/simulacros/${selectedSimulacroForUpload.value.id}/procesar-omr`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    console.log('📋 [OMR Processing] Respuesta del servidor:', response.data);

    // Procesar resultados
    const { results, summary } = response.data;

    // Actualizar progreso para cada resultado
    for (let i = 0; i < results.length; i++) {
      const result = results[i];
      omrUpload.value.currentFile = result.filename;
      omrUpload.value.progress.current = i + 1;
      omrUpload.value.progress.percent = Math.round(((i + 1) / results.length) * 100);
      
      // Log detallado de cada resultado en consola
      if (result.data) {
        console.log(`📝 [OMR] ${result.filename}:`, {
          qr_detectado: result.data.qr_detectado,
          estudiante: result.data.qr_datos,
          respuestas: result.data.respuestas,
          confianza: result.data.confianza_general
        });
      }
      
      omrUpload.value.results.push(result);
      
      // Pequeña pausa para visualizar el progreso
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Usar el resumen del backend
    omrUpload.value.summary = {
      success: summary.success,
      warnings: summary.warnings,
      errors: summary.errors
    };

    console.log('✅ [OMR Processing] Resumen:', summary);

  } catch (error) {
    console.error('❌ [OMR Processing] Error:', error);
    
    toast.add({
      severity: 'error',
      summary: 'Error procesando',
      detail: error.response?.data?.detail || 'Error al procesar las hojas OMR',
      life: 5000
    });

    // En caso de error, marcar todos como error
    omrUpload.value.results = omrUpload.value.files.map(file => ({
      filename: file.name,
      status: 'error',
      message: 'Error de comunicación con el servidor'
    }));
    
    omrUpload.value.summary = {
      success: 0,
      warnings: 0,
      errors: omrUpload.value.files.length
    };
  }

  omrUpload.value.status = 'completed';
};

// Abrir modal de asignación manual (placeholder para futura implementación)
const openManualAssignment = (result) => {
  // TODO: Implementar modal de asignación manual
  toast.add({
    severity: 'info',
    summary: 'En desarrollo',
    detail: 'La asignación manual estará disponible próximamente',
    life: 3000
  });
};

// Confirmar y guardar resultados OMR en la base de datos
const confirmSaveOMRResults = async () => {
  if (omrUpload.value.saving) return;
  
  // Filtrar solo resultados exitosos
  const successResults = omrUpload.value.results.filter(r => r.status === 'success');
  
  if (successResults.length === 0) {
    toast.add({
      severity: 'warn',
      summary: 'Sin resultados',
      detail: 'No hay resultados exitosos para guardar',
      life: 3000
    });
    return;
  }

  omrUpload.value.saving = true;

  try {
    console.log('💾 [OMR] Guardando resultados...', successResults);

    const response = await api.post(
      `/simulacros/${selectedSimulacroForUpload.value.id}/guardar-omr`,
      { results: omrUpload.value.results }
    );

    console.log('✅ [OMR] Resultados guardados:', response.data);

    omrUpload.value.saveResults = response.data;
    omrUpload.value.saved = true;

    // Mostrar resumen
    const { summary } = response.data;
    
    if (summary.guardados > 0) {
      toast.add({
        severity: 'success',
        summary: '¡Guardado exitoso!',
        detail: `${summary.guardados} respuesta${summary.guardados !== 1 ? 's' : ''} guardada${summary.guardados !== 1 ? 's' : ''} correctamente`,
        life: 5000
      });
    }
    
    if (summary.omitidos > 0) {
      toast.add({
        severity: 'info',
        summary: 'Registros omitidos',
        detail: `${summary.omitidos} registro${summary.omitidos !== 1 ? 's' : ''} omitido${summary.omitidos !== 1 ? 's' : ''} (ya existían o sin datos)`,
        life: 5000
      });
    }
    
    if (summary.errores > 0) {
      toast.add({
        severity: 'warn',
        summary: 'Algunos errores',
        detail: `${summary.errores} registro${summary.errores !== 1 ? 's' : ''} con error`,
        life: 5000
      });
    }

  } catch (error) {
    console.error('❌ [OMR] Error guardando:', error);
    
    toast.add({
      severity: 'error',
      summary: 'Error al guardar',
      detail: error.response?.data?.detail || 'No se pudieron guardar los resultados',
      life: 5000
    });
  } finally {
    omrUpload.value.saving = false;
  }
};

</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}
.animate-in {
  animation-duration: 300ms;
}
</style>
