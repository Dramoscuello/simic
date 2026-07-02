<template>
  <div class="mx-auto flex w-full max-w-4xl flex-col gap-6">
    <Toast />
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm">
      <router-link to="/simulacros" class="text-slate-500 dark:text-slate-400 hover:text-primary transition-colors flex items-center gap-1">
        <span class="material-icons-round text-[18px]">arrow_back</span>
        Simulacros
      </router-link>
      <span class="material-icons-round text-slate-300 dark:text-slate-600 text-[16px]">chevron_right</span>
      <span class="text-slate-800 dark:text-white font-medium">{{ isEditMode ? 'Editar simulacro' : 'Generar simulacros' }}</span>
    </div>
    
    <!-- Form Card -->
    <form @submit.prevent="isEditMode ? actualizarSimulacro() : requestConfirmation()" class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
      <!-- Form Header -->
      <div class="p-6 border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800">
        <h2 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
          <div class="h-10 w-10 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-primary">
            <span class="material-icons-round">{{ isEditMode ? 'edit' : 'auto_awesome' }}</span>
          </div>
          {{ isEditMode ? 'Editar simulacro' : 'Generar simulacros con IA' }}
        </h2>
        <p class="text-slate-500 dark:text-slate-400 mt-1 ml-[52px]">
          {{ isEditMode ? 'Modifica los datos y selecciona preguntas a regenerar' : 'Selecciona las áreas y el sistema generará automáticamente los simulacros' }}
        </p>
      </div>
      
      <!-- Form Body (bloqueado durante generación) -->
      <div class="p-6 space-y-8" :class="{ 'opacity-50 pointer-events-none': isGenerating }">
        <!-- Basic Info Section -->
        <div>
          <h3 class="text-sm font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span class="material-icons-round text-slate-400 dark:text-slate-500 text-lg">info</span>
            Datos básicos
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Title -->
            <div class="md:col-span-2">
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Nombre base del simulacro <span class="text-rose-500">*</span>
              </label>
              <input 
                v-model="form.titulo" 
                type="text" 
                required 
                class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/40 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                placeholder="Ej: Diagnóstico Febrero 2026"
              />
              <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">Se agregará el nombre del área automáticamente (ej: "Diagnóstico Febrero 2026 - Matemáticas")</p>
            </div>
            
            <!-- Description -->
            <div class="md:col-span-2">
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Descripción
              </label>
              <textarea 
                v-model="form.descripcion" 
                rows="2"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/40 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all resize-none" 
                placeholder="Descripción breve del simulacro (opcional)"
              ></textarea>
            </div>
            
            <!-- Institution (SOLO EN CREACIÓN - Solo SuperAdmin) -->
            <div v-if="!isEditMode && !isAdminIE">
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Institución <span class="text-rose-500">*</span>
              </label>
              <Select 
                v-model="form.institucion_id" 
                :options="instituciones"
                optionLabel="nombre"
                optionValue="id"
                placeholder="Seleccionar institución"
                class="w-full"
                :pt="selectPt"
                filter
                filterPlaceholder="Buscar..."
              />
            </div>

            <!-- Sede (SOLO EN CREACIÓN) -->
            <div v-if="!isEditMode">
              <label v-if="sedeOptions.length > 1" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Sedes
              </label>
              <MultiSelect
                v-if="sedeOptions.length > 1"
                v-model="form.sede_ids"
                :options="sedeOptions"
                optionLabel="nombre"
                optionValue="id"
                placeholder="Seleccionar sedes"
                display="chip"
                class="w-full"
                :pt="selectPt"
              />
              <p v-if="sedeOptions.length > 1" class="text-xs text-slate-400 dark:text-slate-500 mt-1">Selecciona una o varias sedes que presentarán el simulacro</p>
              <p v-else-if="sedeOptions.length === 1" class="text-sm text-slate-600 dark:text-slate-300">
                <span class="font-medium">Sede seleccionada:</span> {{ sedeOptions[0].nombre }}
              </p>
              <p v-else class="text-sm text-slate-500 dark:text-slate-400">
                Selecciona una institución para ver sus sedes.
              </p>
            </div>
            
            <!-- Número de Preguntas (SOLO EN CREACIÓN) -->
            <div v-if="!isEditMode">
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Número de preguntas <span class="text-rose-500">*</span>
              </label>
              <Select
                v-model="form.num_preguntas"
                :options="numPreguntasOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Seleccionar número de preguntas"
                class="w-full"
                :pt="selectPt"
              />
              <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">Opciones permitidas: 10, 20 o 30 preguntas por simulacro</p>
            </div>
            
            <!-- Time Limit -->
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Tiempo límite (minutos)
              </label>
              <input 
                v-model.number="form.tiempo_limite" 
                type="number" 
                min="1"
                @keypress="isNumber($event)"
                class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/40 px-4 py-3 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                placeholder="60"
              />
            </div>
          </div>
        </div>
        
        <!-- SECCIÓN DE DIFICULTAD (SOLO EN CREACIÓN) -->
        <div v-if="!isEditMode && !isAdminIE">
          <h3 class="text-sm font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span class="material-icons-round text-slate-400 dark:text-slate-500 text-lg">tune</span>
            Distribución de dificultad
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Ajusta el porcentaje de preguntas según su nivel de dificultad. La suma debe ser 100%.</p>
          
          <div class="bg-slate-50 dark:bg-slate-700/30 rounded-xl p-5 border border-slate-200 dark:border-slate-600 space-y-5">
            <!-- Barra Fácil -->
            <div class="flex items-center gap-4">
              <div class="w-20 flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Fácil</span>
              </div>
              <input 
                type="range" 
                v-model.number="form.dificultad.facil" 
                min="0" 
                max="100" 
                step="10"
                @input="adjustDificultad('facil')"
                class="flex-1 h-2 bg-slate-200 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <span class="w-12 text-right text-sm font-bold text-emerald-600">{{ form.dificultad.facil }}%</span>
            </div>
            
            <!-- Barra Media -->
            <div class="flex items-center gap-4">
              <div class="w-20 flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-amber-500"></span>
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Media</span>
              </div>
              <input 
                type="range" 
                v-model.number="form.dificultad.medio" 
                min="0" 
                max="100" 
                step="10"
                @input="adjustDificultad('medio')"
                class="flex-1 h-2 bg-slate-200 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <span class="w-12 text-right text-sm font-bold text-amber-600">{{ form.dificultad.medio }}%</span>
            </div>
            
            <!-- Barra Difícil -->
            <div class="flex items-center gap-4">
              <div class="w-20 flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-rose-500"></span>
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Difícil</span>
              </div>
              <input 
                type="range" 
                v-model.number="form.dificultad.dificil" 
                min="0" 
                max="100" 
                step="10"
                @input="adjustDificultad('dificil')"
                class="flex-1 h-2 bg-slate-200 dark:bg-slate-600 rounded-lg appearance-none cursor-pointer accent-rose-500"
              />
              <span class="w-12 text-right text-sm font-bold text-rose-600">{{ form.dificultad.dificil }}%</span>
            </div>
            
            <!-- Indicador de suma -->
            <div class="pt-3 border-t border-slate-200 dark:border-slate-600 flex items-center justify-between">
              <span class="text-xs text-slate-500 dark:text-slate-400">Suma total:</span>
              <span 
                class="text-sm font-bold"
                :class="dificultadTotal === 100 ? 'text-emerald-600' : 'text-rose-600'"
              >
                {{ dificultadTotal }}%
                <span v-if="dificultadTotal !== 100" class="text-rose-500 text-xs">(debe ser 100%)</span>
              </span>
            </div>
          </div>
        </div>
        
        <!-- SECCIÓN MODO EDICIÓN: Lista de Preguntas -->
        <div v-if="isEditMode && simulacroPreguntas.length > 0">
          <h3 class="text-sm font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span class="material-icons-round text-slate-400 dark:text-slate-500 text-lg">quiz</span>
            Preguntas del simulacro
            <span class="text-xs font-normal text-slate-400 dark:text-slate-500">({{ simulacroPreguntas.length }} preguntas)</span>
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Selecciona las preguntas que deseas regenerar con IA</p>
          
          <!-- Contador de seleccionadas -->
          <div v-if="selectedPreguntaIds.length > 0" class="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50">
            <div class="flex items-center gap-2 text-amber-700 dark:text-amber-300">
              <span class="material-icons-round text-[18px]">autorenew</span>
              <span class="text-sm font-medium">{{ selectedPreguntaIds.length }} pregunta(s) seleccionada(s) para regenerar</span>
            </div>
          </div>
          
          <!-- Lista de Preguntas -->
          <div class="max-h-[400px] overflow-y-auto border border-slate-200 dark:border-slate-600 rounded-xl divide-y divide-slate-100 dark:divide-slate-700">
            <label 
              v-for="preg in simulacroPreguntas" 
              :key="preg.id" 
              class="flex items-start gap-3 p-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors"
              :class="{ 'bg-amber-50 dark:bg-amber-900/20': isPreguntaSelected(preg.id) }"
            >
              <input 
                type="checkbox" 
                :checked="isPreguntaSelected(preg.id)"
                @change="togglePregunta(preg.id)"
                class="mt-1 h-5 w-5 rounded border-slate-300 dark:border-slate-600 text-primary focus:ring-primary"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center justify-center h-6 w-6 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold">
                    {{ preg.id }}
                  </span>
                  <span class="text-xs text-slate-400 dark:text-slate-500 uppercase">{{ preg.competencia || 'Sin competencia' }}</span>
                </div>
                <p class="text-sm text-slate-700 dark:text-slate-300 mt-1 line-clamp-2">
                  {{ truncateText(preg.pregunta || preg.enunciado, 100) }}
                </p>
                <!-- Botón Optimizar SVG -->
                <button 
                  type="button"
                  v-if="preg.tiene_grafico || (preg.tipo_grafico && preg.tipo_grafico !== 'null')"
                  @click.stop="openGraficoModal(preg)"
                  class="mt-2 text-xs font-medium text-emerald-600 hover:text-emerald-700 flex items-center gap-1 bg-emerald-50 hover:bg-emerald-100 px-2 py-1 rounded transition-colors w-fit"
                >
                  <span class="material-icons-round text-[14px]">auto_fix_high</span>
                  Ver/Optimizar gráfico
                </button>
              </div>
            </label>
          </div>
          
          <!-- Botones de selección rápida -->
          <div class="flex gap-2 mt-3">
            <button 
              type="button" 
              @click="selectAllPreguntas"
              class="text-xs text-slate-500 dark:text-slate-400 hover:text-primary transition-colors"
            >
              Seleccionar todas
            </button>
            <span class="text-slate-300 dark:text-slate-600">|</span>
            <button 
              type="button" 
              @click="deselectAllPreguntas"
              class="text-xs text-slate-500 dark:text-slate-400 hover:text-primary transition-colors"
            >
              Deseleccionar todas
            </button>
          </div>
        </div>
        <!-- Areas Selection Section (SOLO EN MODO CREACIÓN) -->
        <div v-if="!isEditMode">
          <h3 class="text-sm font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span class="material-icons-round text-slate-400 dark:text-slate-500 text-lg">category</span>
            Áreas a generar
            <span v-if="loadingAreas" class="material-icons-round animate-spin text-primary text-sm">refresh</span>
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Selecciona las áreas para las cuales se generarán simulacros automáticamente</p>
          
          <div class="flex flex-wrap gap-3">
            <button
              v-for="area in areaOptions"
              :key="area.value"
              type="button"
              @click="toggleArea(area.value)"
              class="px-4 py-2.5 rounded-full border-2 font-medium text-sm transition-all duration-200 flex items-center gap-2"
              :class="{
                'border-primary bg-primary text-white shadow-md shadow-primary/25': isAreaSelected(area.value),
                'border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700/40 text-slate-600 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700': !isAreaSelected(area.value)
              }"
            >
              <span class="material-icons-round text-[18px]">
                {{ isAreaSelected(area.value) ? 'check_circle' : 'radio_button_unchecked' }}
              </span>
              {{ area.label }}
            </button>
          </div>
          
          <div v-if="form.areas.length === 0" class="mt-3 text-sm text-amber-600 dark:text-amber-400 flex items-center gap-2">
            <span class="material-icons-round text-[18px]">warning</span>
            Debes seleccionar al menos un área
          </div>
          
          <div v-else class="mt-3 text-sm text-slate-500 dark:text-slate-400">
            <span class="font-medium text-primary">{{ form.areas.length }}</span> área(s) seleccionada(s) 
            → Se generarán <span class="font-medium text-primary">{{ totalSimulacrosGenerados }}</span> simulacro(s)
          </div>
        </div>
        
        <!-- Options Section -->
        <div>
          <h3 class="text-sm font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <span class="material-icons-round text-slate-400 dark:text-slate-500 text-lg">tune</span>
            Opciones
          </h3>
          
          <div class="space-y-4">
            <!-- Active Toggle -->
            <label class="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/30 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
              <div class="flex items-center gap-3">
                <div class="h-10 w-10 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-300">
                  <span class="material-icons-round">visibility</span>
                </div>
                <div>
                  <p class="font-medium text-slate-800 dark:text-slate-100">Activar simulacros al crear</p>
                  <p class="text-sm text-slate-500 dark:text-slate-400">Los estudiantes podrán ver y presentar los simulacros inmediatamente</p>
                </div>
              </div>
              <div class="relative">
                <input type="checkbox" v-model="form.activo" class="sr-only peer" />
                <div class="w-11 h-6 bg-slate-300 dark:bg-slate-600 peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </div>
            </label>


          </div>
        </div>

      </div>
      
      <!-- Progress Section (visible during generation, SOLO EN CREACIÓN) -->
      <div v-if="isGenerating && !isEditMode" class="p-6 border-t border-slate-100 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-indigo-50 dark:from-slate-800 dark:to-indigo-950/40">
        <h3 class="text-sm font-bold text-slate-700 dark:text-slate-200 mb-4 flex items-center gap-2">
          <span class="material-icons-round animate-spin text-primary">autorenew</span>
          Generando simulacros...
        </h3>
        
        <div class="space-y-3">
          <div 
            v-for="(status, area) in generationProgress" 
            :key="area"
            class="flex items-center gap-3 p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700"
          >
            <span 
              class="material-icons-round text-[20px]"
              :class="{
                'text-slate-300': status === 'pending',
                'text-primary animate-spin': status === 'generating',
                'text-amber-500 animate-pulse': status === 'validating',
                'text-emerald-500': status === 'completed',
                'text-rose-500': status === 'error'
              }"
            >
              {{ getStatusIcon(status) }}
            </span>
            <div class="flex-1">
              <p class="font-medium text-slate-700 dark:text-slate-200">{{ getAreaLabel(area) }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">{{ getStatusText(status) }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Form Footer -->
      <div class="p-6 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 flex items-center justify-between">
        <button 
          type="button"
          @click="cancelar"
          :disabled="isGenerating"
          class="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span class="material-icons-round text-[18px]">close</span>
          Cancelar
        </button>
        
          <button 
            type="submit" 
            :disabled="isGenerating || (!isEditMode && (form.areas.length === 0 || !form.institucion_id || !form.titulo || !numPreguntasValido || form.sede_ids.length === 0))"
            class="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-primary to-indigo-600 text-white font-semibold shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isGenerating" class="material-icons-round animate-spin text-[18px]">refresh</span>
            <span v-else class="material-icons-round text-[18px]">{{ isEditMode ? 'save' : 'auto_awesome' }}</span>
            {{ isGenerating ? (isEditMode ? 'Regenerando...' : 'Generando...') : (isEditMode ? 'Actualizar simulacro' : 'Generar simulacros') }}
          </button>
      </div>
    </form>
    <!-- MODAL OPTIMIZACIÓN GRÁFICO -->
    <div v-if="showGraficoModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <span class="material-icons-round text-primary">auto_fix_high</span>
            Optimizar gráfico
          </h3>
          <button @click="closeGraficoModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <span class="material-icons-round text-2xl">close</span>
          </button>
        </div>
        
        <!-- Content -->
        <div class="p-6 overflow-y-auto flex-1 bg-slate-50 dark:bg-slate-900/50">
          <div class="flex flex-col gap-6">
            <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-blue-700 dark:text-blue-300">
              <p class="font-medium mb-1">¿Cómo funciona?</p>
              Capturaremos una imagen del gráfico actual y la enviaremos a una IA experta en diseño para que corrija errores visuales, etiquetas mal ubicadas o proporciones incorrectas.
            </div>

            <!-- Área de renderizado (se captura esto) -->
            <div class="bg-white p-6 rounded-lg shadow-sm border border-slate-200 flex justify-center items-center min-h-[300px]" ref="graficoRef">
              <GraficoRenderer 
                v-if="selectedPreguntaGrafico?.configuracion_grafico"
                :config="selectedPreguntaGrafico.configuracion_grafico"
                :tipo="selectedPreguntaGrafico.tipo_grafico"
              />
              <div v-else class="text-slate-400 italic">No hay configuración gráfica disponible</div>
            </div>
            
            <!-- Contexto de la pregunta -->
            <div class="text-sm text-slate-600 dark:text-slate-400">
              <strong>Contexto:</strong> {{ truncateText(selectedPreguntaGrafico?.contexto, 150) }}
            </div>

            <!-- INSTRUCCIONES ADICIONALES (NUEVO) -->
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Instrucciones adicionales para la IA (opcional)</label>
              <textarea 
                v-model="instruccionesAdicionales"
                placeholder="Ej: Conecta los puntos P, Q, R para formar un triángulo. Asegura que el ángulo en Q sea recto..."
                class="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all resize-y min-h-[80px]"
              ></textarea>
              <p class="text-xs text-slate-500">Usa esto si la IA no entiende qué dibujar (ej: conectar puntos faltantes).</p>
            </div>
          </div>
        </div>
        
        <!-- Footer Actions -->
        <div class="px-6 py-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3">
          <button 
            @click="closeGraficoModal"
            class="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          >
            Cancelar
          </button>
          <button 
            @click="optimizarGrafico"
            :disabled="optimizingGrafico"
            class="px-4 py-2 rounded-lg bg-primary hover:bg-indigo-600 text-white font-medium transition-colors flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            <span v-if="optimizingGrafico" class="material-icons-round animate-spin text-[18px]">autorenew</span>
            <span v-else class="material-icons-round text-[18px]">auto_fix_high</span>
            {{ optimizingGrafico ? 'Optimizando...' : 'Optimizar ahora' }}
          </button>
        </div>
    </div>
  </div>

    
    <!-- MODAL DE CONFIRMACIÓN DE PEDIDO -->
    <div v-if="showConfirmModal" class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden transform transition-all scale-100">
        <!-- Header -->
        <div class="p-6 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800 border-b border-slate-100 dark:border-slate-700">
          <h3 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <span class="material-icons-round text-primary">receipt_long</span>
            Confirmar pedido de generación
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Por favor verifica los detalles antes de continuar.</p>
        </div>
        
        <!-- Content -->
        <div class="p-6 space-y-4">
          <!-- Resumen Principal -->
          <div class="bg-slate-50 dark:bg-slate-700/30 rounded-xl p-4 border border-slate-200 dark:border-slate-600 space-y-3">
            <div class="flex justify-between items-start">
              <span class="text-sm text-slate-500 dark:text-slate-400 font-medium">Nombre del simulacro:</span>
              <span class="text-sm font-bold text-slate-800 dark:text-slate-100 text-right">{{ form.titulo }}</span>
            </div>
            
            <div class="flex justify-between items-start">
              <span class="text-sm text-slate-500 dark:text-slate-400 font-medium">Áreas seleccionadas:</span>
              <div class="text-right">
                <span class="block text-sm font-bold text-primary">{{ form.areas.length }} Áreas</span>
                <span class="text-xs text-slate-400 dark:text-slate-500 block max-w-[200px] truncate">
                  {{ form.areas.map(a => getAreaLabel(a)).join(', ') }}
                </span>
              </div>
            </div>
            
            <div class="pt-3 border-t border-slate-200 dark:border-slate-600 flex justify-between items-center">
              <span class="text-sm text-slate-500 dark:text-slate-400 font-medium">Volumen total:</span>
               <span class="inline-flex items-center gap-1 bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs font-bold">
                 {{ totalSimulacrosGenerados }} simulacros × {{ form.num_preguntas }} preguntas
               </span>
            </div>


          </div>
          
          <!-- Configuración -->
          <div class="grid grid-cols-2 gap-3 text-sm">
             <div class="p-3 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-600 rounded-lg">
                <p class="text-slate-400 dark:text-slate-500 text-xs mb-1">Dificultad</p>
                <div class="flex gap-1 h-2 rounded-full overflow-hidden w-full mb-1">
                  <div class="bg-emerald-500" :style="{ width: form.dificultad.facil + '%' }"></div>
                  <div class="bg-amber-500" :style="{ width: form.dificultad.medio + '%' }"></div>
                  <div class="bg-rose-500" :style="{ width: form.dificultad.dificil + '%' }"></div>
                </div>
                <p class="text-xs font-medium text-slate-600 dark:text-slate-300">
                  {{ form.dificultad.facil }}% / {{ form.dificultad.medio }}% / {{ form.dificultad.dificil }}%
                </p>
             </div>
             <div class="p-3 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-600 rounded-lg">
                <p class="text-slate-400 dark:text-slate-500 text-xs mb-1">Límite de tiempo</p>
                <p class="font-medium text-slate-700 dark:text-slate-300">{{ form.tiempo_limite }} min</p>
             </div>
          </div>
          
          <!-- Alerta de Irreversibilidad -->
          <div class="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300 rounded-lg text-sm border border-amber-100 dark:border-amber-800/50">
            <span class="material-icons-round text-amber-600 dark:text-amber-400 mt-0.5">warning</span>
            <p>
              Esta acción es <strong>irreversible</strong> y comenzará el proceso de generación con IA inmediatamente.
            </p>
          </div>
          
        </div>
        
        <!-- Footer -->
        <div class="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 flex justify-end gap-3">
          <button 
            type="button" 
            @click="showConfirmModal = false"
            class="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors"
          >
            Cancelar
          </button>
          <button 
            type="button" 
            @click="confirmarYGenerar"
            class="px-5 py-2 rounded-lg bg-gradient-to-r from-primary to-indigo-600 text-white font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2"
          >
            <span>Confirmar y Generar</span>
            <span class="material-icons-round text-sm">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useSimulacrosStore } from '../stores/simulacros';
import { useInstitucionesStore } from '../stores/instituciones';
import { useRouter, useRoute } from 'vue-router';
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import Select from 'primevue/select';
import MultiSelect from 'primevue/multiselect';
import api from '../api/axios';

const authStore = useAuthStore();
const simulacrosStore = useSimulacrosStore();
const institucionesStore = useInstitucionesStore();
const router = useRouter();
const route = useRoute();
const toast = useToast();

// Modo edición - detectar por ruta
const simulacroId = computed(() => route.params.id ? parseInt(route.params.id) : null);
const isEditMode = computed(() => !!simulacroId.value);
const isAdminIE = computed(() => ['admin'].includes(authStore.user?.rol?.nombre));
const isSuperAdmin = computed(() => authStore.user?.rol?.nombre === 'admin');

// Form state
const loading = ref(false);
const isGenerating = ref(false);
const instituciones = ref([]);
const sedeOptions = ref([]);

// Estado para modo edición
const simulacroPreguntas = ref([]);  // Lista de preguntas del simulacro
const selectedPreguntaIds = ref([]);  // IDs de preguntas seleccionadas para regenerar

// Progress tracking for each area
const generationProgress = reactive({});

const form = reactive({
  titulo: '',
  descripcion: '',
  areas: [], // Ahora es un array de áreas seleccionadas
  institucion_id: null,
  sede_ids: [], // Sedes seleccionadas para generar los simulacros
  num_preguntas: 30, // Número de preguntas a generar
  tiempo_limite: 60,
  activo: false,
  dificultad: {
    facil: 30,
    medio: 40,
    dificil: 30
  }
});

const showConfirmModal = ref(false);
const DEFAULT_DIFICULTAD = Object.freeze({ facil: 30, medio: 40, dificil: 30 });
const numPreguntasOptions = [
  { label: '10 preguntas', value: 10 },
  { label: '20 preguntas', value: 20 },
  { label: '30 preguntas', value: 30 }
];
const selectPt = {
  root: {
    class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/40 text-slate-800 dark:text-white'
  },
  label: {
    class: 'text-slate-800 dark:text-white'
  },
  trigger: {
    class: 'text-slate-500 dark:text-slate-300'
  },
  panel: {
    class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600'
  },
  item: {
    class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600'
  },
  filterInput: {
    class: 'w-full p-2 border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-white rounded-md'
  }
};
const allowedNumPreguntas = new Set(numPreguntasOptions.map(option => option.value));
const numPreguntasValido = computed(() => allowedNumPreguntas.has(form.num_preguntas));

const totalSimulacrosGenerados = computed(() => {
  const sedesCount = form.sede_ids?.length || (sedeOptions.value.length === 1 ? 1 : 0);
  return form.areas.length * sedesCount;
});

const aplicarDificultadPorDefectoAdmin = () => {
  if (!isAdminIE.value) return;
  form.dificultad.facil = DEFAULT_DIFICULTAD.facil;
  form.dificultad.medio = DEFAULT_DIFICULTAD.medio;
  form.dificultad.dificil = DEFAULT_DIFICULTAD.dificil;
};

const requestConfirmation = () => {
    if (!numPreguntasValido.value) {
        toast.add({ severity: 'warn', summary: 'Número inválido', detail: 'Solo se permiten 10, 20 o 30 preguntas.', life: 4000 });
        return;
    }

    aplicarDificultadPorDefectoAdmin();

    // Validaciones basicas antes de abrir modal (duplicadas de generarSimulacros pero necesarias aqui)
    if (form.areas.length === 0) {
        toast.add({ severity: 'warn', summary: 'Selecciona áreas', detail: 'Debes seleccionar al menos un área', life: 4000 });
        return;
    }
    if (!form.institucion_id || !form.titulo.trim()) {
        toast.add({ severity: 'warn', summary: 'Faltan datos', detail: 'Por favor completa todos los campos requeridos', life: 4000 });
        return;
    }
    if (!form.sede_ids || form.sede_ids.length === 0) {
        toast.add({ severity: 'warn', summary: 'Sede requerida', detail: 'Por favor selecciona al menos una sede', life: 4000 });
        return;
    }
    
    showConfirmModal.value = true;
};

const confirmarYGenerar = () => {
    showConfirmModal.value = false;
    generarSimulacros();
};

const isNumber = (evt) => {
    evt = (evt) ? evt : window.event;
    var charCode = (evt.which) ? evt.which : evt.keyCode;
    if ((charCode > 31 && (charCode < 48 || charCode > 57))) {
        evt.preventDefault();
    } else {
        return true;
    }
};

// Computed para la suma de dificultades
const dificultadTotal = computed(() => {
  return form.dificultad.facil + form.dificultad.medio + form.dificultad.dificil;
});

// Helper para redondear a múltiplos de 10
const roundTo10 = (value) => Math.round(value / 10) * 10;

// Función para auto-balancear dificultades (siempre múltiplos de 10)
const adjustDificultad = (changedField) => {
  const currentValue = form.dificultad[changedField];
  const remaining = 100 - currentValue;
  
  // Obtener los otros dos campos
  const fields = ['facil', 'medio', 'dificil'];
  const otherFields = fields.filter(f => f !== changedField);
  
  // Calcular la proporción actual de los otros campos
  const other1 = form.dificultad[otherFields[0]];
  const other2 = form.dificultad[otherFields[1]];
  const otherTotal = other1 + other2;
  
  if (remaining === 0) {
    // Si el slider actual es 100, los otros deben ser 0
    form.dificultad[otherFields[0]] = 0;
    form.dificultad[otherFields[1]] = 0;
    return;
  }
  
  if (otherTotal === 0) {
    // Si ambos otros son 0, dividir equitativamente el restante
    const half = roundTo10(remaining / 2);
    form.dificultad[otherFields[0]] = half;
    form.dificultad[otherFields[1]] = remaining - half;
    return;
  }
  
  // Distribuir proporcionalmente y redondear a 10
  const ratio = other1 / otherTotal;
  let newValue1 = roundTo10(remaining * ratio);
  let newValue2 = remaining - newValue1;
  
  // Asegurar que ambos sean >= 0
  if (newValue1 < 0) {
    newValue1 = 0;
    newValue2 = remaining;
  }
  if (newValue2 < 0) {
    newValue2 = 0;
    newValue1 = remaining;
  }
  
  // Asegurar que newValue2 sea múltiplo de 10 también
  newValue2 = roundTo10(newValue2);
  
  // Si la suma no es exacta, ajustar
  const sum = currentValue + newValue1 + newValue2;
  if (sum !== 100) {
    const diff = 100 - sum;
    // Preferir ajustar el segundo campo
    if (newValue2 + diff >= 0 && newValue2 + diff <= 100 - currentValue - newValue1) {
      newValue2 = roundTo10(newValue2 + diff);
    } else {
      newValue1 = roundTo10(newValue1 + diff);
    }
  }
  
  form.dificultad[otherFields[0]] = Math.max(0, Math.min(100, newValue1));
  form.dificultad[otherFields[1]] = Math.max(0, Math.min(100, newValue2));
};

// Optimización de Gráficos
import html2canvas from 'html2canvas';
import { defineAsyncComponent } from 'vue';
const GraficoRenderer = defineAsyncComponent(() => import('../components/graficos/GraficoRenderer.vue'));
const showGraficoModal = ref(false);
const selectedPreguntaGrafico = ref(null);
const graficoRef = ref(null);
const optimizingGrafico = ref(false);
const instruccionesAdicionales = ref('');

const openGraficoModal = (pregunta) => {
  selectedPreguntaGrafico.value = pregunta;
  instruccionesAdicionales.value = ''; // Limpiar instrucciones previas
  showGraficoModal.value = true;
};

const closeGraficoModal = () => {
  showGraficoModal.value = false;
  selectedPreguntaGrafico.value = null;
};

const optimizarGrafico = async () => {
  if (!graficoRef.value || !selectedPreguntaGrafico.value) return;
  
  optimizingGrafico.value = true;
  try {
    // 1. Capturar el gráfico renderizado (Estrategia Híbrida)
    let imagenBase64 = '';
    
    // Buscar si hay un SVG dentro del contenedor
    const svgElement = graficoRef.value.querySelector('svg');
    
    if (svgElement) {
      // Estrategia Nativa para SVG (Más robusta para svg_artistico)
      const serializer = new XMLSerializer();
      let source = serializer.serializeToString(svgElement);
      
      // Asegurar namespace
      if(!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
      }
      
      const svgBlob = new Blob([source], {type: "image/svg+xml;charset=utf-8"});
      const url = URL.createObjectURL(svgBlob);
      
      // Convertir SVG a PNG mediante Canvas
      const img = new Image();
      await new Promise((resolve, reject) => {
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = svgElement.getBoundingClientRect().width * 2 || 800;
          canvas.height = svgElement.getBoundingClientRect().height * 2 || 600;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = "#FFFFFF"; // Fondo blanco
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          imagenBase64 = canvas.toDataURL('image/png').split(',')[1];
          URL.revokeObjectURL(url);
          resolve();
        };
        img.onerror = reject;
        img.src = url;
      });
      
    } else {
      // Fallback para Chart.js o HTML normal
      const canvas = await html2canvas(graficoRef.value, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true, // Importante para recursos externos
        logging: false
      });
      imagenBase64 = canvas.toDataURL('image/png').split(',')[1];
    }
    
    // 2. Llamar al store
    const result = await simulacrosStore.optimizarGrafico(
      route.params.id,
      selectedPreguntaGrafico.value.id,
      imagenBase64,
      instruccionesAdicionales.value // Pasar el texto al store
    );
    
    toast.add({ 
      severity: 'success', 
      summary: 'Gráfico optimizado', 
      detail: 'El gráfico ha sido corregido exitosamente.',
      life: 3000 
    });
    
    // Actualizar la pregunta localmente
    const index = simulacroPreguntas.value.findIndex(p => p.id === selectedPreguntaGrafico.value.id);
    if (index !== -1) {
      // El store ya recarga el simulacro, pero aseguramos la reactividad
      await cargarSimulacro(route.params.id);
      // Actualizar la seleccionada también
      selectedPreguntaGrafico.value = simulacroPreguntas.value[index];
    }
    
  } catch (error) {
    console.error('Error optimizando gráfico:', error);
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: 'No se pudo optimizar el gráfico.',
      life: 5000 
    });
  } finally {
    optimizingGrafico.value = false;
  }
};

// Opciones de áreas
const areaOptions = [
  { label: 'Matemáticas', value: 'MATEMATICAS', icon: 'calculate' },
  { label: 'Lectura Crítica', value: 'LECTURA_CRITICA', icon: 'menu_book' },
  { label: 'Ciencias Naturales', value: 'CIENCIAS_NATURALES', icon: 'science' },
  { label: 'Sociales y Ciudadanas', value: 'SOCIALES_CIUDADANAS', icon: 'public' },
  { label: 'Inglés', value: 'INGLES', icon: 'translate' }
];

// Métodos para manejo de áreas
const isAreaSelected = (areaValue) => form.areas.includes(areaValue);

const toggleArea = (areaValue) => {
  const index = form.areas.indexOf(areaValue);
  if (index > -1) {
    form.areas.splice(index, 1);
  } else {
    form.areas.push(areaValue);
  }
};

const getAreaLabel = (areaValue) => {
  const area = areaOptions.find(a => a.value === areaValue);
  return area ? area.label : areaValue;
};

// Métodos para el progreso de generación
const getStatusIcon = (status) => {
  const icons = {
    'pending': 'schedule',
    'generating': 'autorenew',
    'validating': 'verified',
    'completed': 'check_circle',
    'error': 'error'
  };
  return icons[status] || 'help';
};

const getStatusText = (status) => {
  const texts = {
    'pending': 'En cola...',
    'generating': 'Generando con IA...',
    'validating': 'Validando calidad...',
    'completed': 'Completado',
    'error': 'Error en generación'
  };
  return texts[status] || status;
};

// Método para cancelar
const cancelar = () => {
  if (!isGenerating.value) {
    router.push('/simulacros');
  }
};

// Método principal de generación - ASÍNCRONO con polling
const generarSimulacros = async () => {
  if (!numPreguntasValido.value) {
    toast.add({ severity: 'warn', summary: 'Número inválido', detail: 'Solo se permiten 10, 20 o 30 preguntas.', life: 4000 });
    return;
  }

  aplicarDificultadPorDefectoAdmin();

  // Validaciones
  if (form.areas.length === 0) {
    toast.add({ severity: 'warn', summary: 'Selecciona áreas', detail: 'Debes seleccionar al menos un área', life: 4000 });
    return;
  }
  
  if (!form.institucion_id) {
    toast.add({ severity: 'warn', summary: 'Faltan datos', detail: 'Debes seleccionar una institución', life: 4000 });
    return;
  }

  if (!form.titulo.trim()) {
    toast.add({ severity: 'warn', summary: 'Faltan datos', detail: 'Debes ingresar un nombre para el simulacro', life: 4000 });
    return;
  }
  
  loading.value = true;
  isGenerating.value = true;
  
  // Inicializar progreso - todos como "pending"
  form.areas.forEach(area => {
    generationProgress[area] = 'pending';
  });

  const dificultadPayload = isAdminIE.value
    ? { ...DEFAULT_DIFICULTAD }
    : {
        facil: form.dificultad.facil,
        medio: form.dificultad.medio,
        dificil: form.dificultad.dificil
      };
  
  try {
    // 1. Encolar job asíncrono
    const asyncResponse = await simulacrosStore.generateSimulacrosAsync({
      nombre_base: form.titulo,
      institucion_id: form.institucion_id,
      sede_ids: form.sede_ids,
      areas: form.areas,
      num_preguntas: form.num_preguntas,
      duracion_minutos: form.tiempo_limite,
      activar: form.activo,
      dificultad: dificultadPayload
    });
    
    const jobId = asyncResponse.job_id;
    console.log(`Job encolado: ${jobId}`);
    
    toast.add({ 
      severity: 'info', 
      summary: 'Generación iniciada', 
      detail: `Job ${jobId} - Puedes cerrar esta ventana, la generación continuará en el servidor.`,
      life: 5000 
    });
    
    // 2. Polling para actualizar progreso
    const finalStatus = await simulacrosStore.pollJobUntilComplete(
      jobId,
      (status) => {
        // Callback de progreso - actualizar UI
        if (status.progress) {
          Object.keys(status.progress).forEach(area => {
            generationProgress[area] = status.progress[area];
          });
        }
      },
      3000 // Polling cada 3 segundos
    );
    
    // 3. Mostrar resultado final
    if (finalStatus.status === 'completed') {
      const resultadosCompletados = (finalStatus.results || []).filter(r => r.status === 'completed').length;
      const resultadosTotales = (finalStatus.results || []).length;
      if (finalStatus.errores > 0) {
        const erroresDetalle = finalStatus.results
          .filter(r => r.status === 'error')
          .map(r => `${getAreaLabel(r.area)}: ${r.error}`)
          .join('\n');
        
        toast.add({ 
          severity: 'warn', 
          summary: `${resultadosCompletados}/${resultadosTotales} generados`, 
          detail: `Errores:\n${erroresDetalle}`, 
          life: 10000 
        });
      } else {
        toast.add({ 
          severity: 'success', 
          summary: 'Simulacros generados', 
          detail: `Se generaron ${resultadosCompletados} simulacro(s) exitosamente`, 
          life: 5000 
        });
      }
    } else {
      toast.add({ 
        severity: 'error', 
        summary: 'Error en generación', 
        detail: finalStatus.error || 'Error desconocido', 
        life: 10000 
      });
    }
    
  } catch (error) {
    console.error("Error en generación asíncrona:", error);
    
    // Marcar todos como error
    form.areas.forEach(area => {
      generationProgress[area] = 'error';
    });
    
    toast.add({ 
      severity: 'error', 
      summary: 'Error al generar', 
      detail: error.response?.data?.detail || error.message, 
      life: 5000 
    });
  }
  
  loading.value = false;
  isGenerating.value = false;
  
  // Redirigir después de mostrar el resultado
  setTimeout(() => {
    router.push('/simulacros');
  }, 2500);
};

// Cargar datos al montar
const cargarInstituciones = async () => {
  try {
    const insts = await simulacrosStore.fetchInstituciones();
    instituciones.value = insts;
  } catch (e) {
    console.error("Error cargando instituciones", e);
  }
};

const cargarSedes = async (institucionId) => {
  if (!institucionId) {
    sedeOptions.value = [];
    form.sede_ids = [];
    return;
  }
  try {
    const res = await api.get('/sedes/', { params: { institucion_id: institucionId } });
    const sedes = Array.isArray(res.data) ? res.data : [];
    sedeOptions.value = sedes.map(s => ({ nombre: s.nombre, id: s.id }));
    if (sedes.length === 1) {
      form.sede_ids = [sedes[0].id];
    } else {
      const selectedValid = (form.sede_ids || []).filter(id => sedes.some(s => s.id === id));
      form.sede_ids = selectedValid.length ? selectedValid : [];
    }
  } catch (e) {
    console.error('Error cargando sedes', e);
    sedeOptions.value = [];
    form.sede_ids = [];
  }
};

onMounted(async () => {
  if (isEditMode.value) {
    // En modo edición cargamos el simulacro
    await cargarSimulacro();
  } else {
    // MODO CREACIÓN
    // Si es Usuario Institución, pre-cargar sus datos
    if (isAdminIE.value && authStore.user?.institucion_id) {
       form.institucion_id = authStore.user.institucion_id;
       // Cargar datos de la institución
       await institucionesStore.fetchInstitucion(form.institucion_id);
       // Cargar sedes de la institución
       await cargarSedes(form.institucion_id);
    } else {
       // Si es SuperAdmin, cargar lista de instituciones
       await cargarInstituciones();
    }
  }
});

// Recargar sedes cuando cambie la institución seleccionada
watch(() => form.institucion_id, async (newId) => {
  if (!isEditMode.value) {
    await cargarSedes(newId);
  }
});

watch(isAdminIE, () => {
  aplicarDificultadPorDefectoAdmin();
}, { immediate: true });

// ==========================================
// FUNCIONES MODO EDICIÓN
// ==========================================

// Truncar texto para mostrar preview de preguntas
const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
};

// Manejo de selección de preguntas
const isPreguntaSelected = (pregId) => selectedPreguntaIds.value.includes(pregId);

const togglePregunta = (pregId) => {
  const index = selectedPreguntaIds.value.indexOf(pregId);
  if (index > -1) {
    selectedPreguntaIds.value.splice(index, 1);
  } else {
    selectedPreguntaIds.value.push(pregId);
  }
};

const selectAllPreguntas = () => {
  selectedPreguntaIds.value = simulacroPreguntas.value.map(p => p.id);
};

const deselectAllPreguntas = () => {
  selectedPreguntaIds.value = [];
};

// Cargar datos del simulacro en modo edición
const cargarSimulacro = async () => {
  if (!simulacroId.value) return;
  
  loading.value = true;
  try {
    const simulacro = await simulacrosStore.fetchSimulacro(simulacroId.value);
    
    if (simulacro) {
      // Cargar datos del formulario
      form.titulo = simulacro.titulo || '';
      form.descripcion = simulacro.descripcion || '';
      form.tiempo_limite = simulacro.duracion_minutos || 60;
      form.activo = simulacro.activo || false;
      form.institucion_id = simulacro.institucion_id;
      
      // Cargar preguntas del contenido
      const contenido = simulacro.contenido || {};
      simulacroPreguntas.value = contenido.preguntas || [];
      
      console.log(`Simulacro ${simulacroId.value} cargado: ${simulacroPreguntas.value.length} preguntas`);
    }
  } catch (e) {
    console.error("Error cargando simulacro:", e);
    toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo cargar el simulacro', life: 5000 });
    router.push('/simulacros');
  } finally {
    loading.value = false;
  }
};

// Función para actualizar el simulacro (modo edición)
const actualizarSimulacro = async () => {
  if (!simulacroId.value) return;
  
  isGenerating.value = true;
  
  try {
    // ========================================
    // PASO 1: Siempre actualizar metadatos
    // ========================================
    await simulacrosStore.updateSimulacro(simulacroId.value, {
      activo: form.activo,
      titulo: form.titulo,
      descripcion: form.descripcion,
      duracion_minutos: form.tiempo_limite
    });
    
    toast.add({ 
      severity: 'success', 
      summary: 'Metadatos actualizados', 
      detail: 'Los datos del simulacro han sido guardados',
      life: 2000 
    });
    
    // ========================================
    // PASO 2: Regenerar preguntas si hay seleccionadas
    // ========================================
    if (selectedPreguntaIds.value.length > 0) {
      toast.add({ 
        severity: 'info', 
        summary: 'Regenerando', 
        detail: `Regenerando ${selectedPreguntaIds.value.length} pregunta(s) con IA...`, 
        life: 10000 
      });
      
      const payload = {
        pregunta_ids: selectedPreguntaIds.value
      };
      
      const result = await simulacrosStore.regenerarPreguntas(simulacroId.value, payload);
      
      if (result.success) {
        toast.add({ 
          severity: 'success', 
          summary: 'Preguntas regeneradas', 
          detail: result.mensaje, 
          life: 5000 
        });
        
        if (result.errores && result.errores.length > 0) {
          toast.add({ 
            severity: 'warn', 
            summary: 'Advertencias', 
            detail: result.errores.join(', '), 
            life: 8000 
          });
        }
      }
    }
    
    // Redirigir después de éxito
    setTimeout(() => {
      router.push('/simulacros');
    }, 1500);
    
  } catch (error) {
    console.error("Error actualizando simulacro:", error);
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || error.message, 
      life: 8000 
    });
  } finally {
    isGenerating.value = false;
  }
};

// Watch para cargar simulacro cuando cambie el ID (modo edición)
watch(simulacroId, async (newId) => {
  if (newId) {
    await cargarSimulacro();
  }
}, { immediate: true });
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}

.bg-primary {
  background-color: #6366f1;
}

.text-primary {
  color: #6366f1;
}

.border-primary {
  border-color: #6366f1;
}

.focus\:border-primary:focus {
  border-color: #6366f1;
}

.peer-checked\:bg-primary:checked ~ div {
  background-color: #6366f1;
}

.shadow-primary\/25 {
  --tw-shadow-color: rgb(99 102 241 / 0.25);
}
</style>
