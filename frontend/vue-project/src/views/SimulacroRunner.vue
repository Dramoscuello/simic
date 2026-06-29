<template>
  <!-- Loading State -->
  <div v-if="loading" class="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
    <div class="flex flex-col items-center gap-4">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      <p class="text-slate-500 dark:text-slate-400 font-medium">Cargando simulacro...</p>
    </div>
  </div>

  <!-- Not Found State -->
  <div v-else-if="!simulacro" class="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-900 p-4">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 p-12 text-center max-w-md">
      <div class="w-20 h-20 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-6">
        <span class="material-symbols-outlined text-slate-400 dark:text-slate-500 text-4xl">search_off</span>
      </div>
      <h1 class="text-2xl font-bold text-slate-800 dark:text-white mb-2">Simulacro no encontrado</h1>
      <p class="text-slate-500 dark:text-slate-400 mb-6">El simulacro que buscas no existe o no está disponible.</p>
      <router-link to="/simulacros" class="inline-flex items-center gap-2 bg-primary hover:bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors">
        <span class="material-symbols-outlined text-[18px]">arrow_back</span>
        Volver al listado
      </router-link>
    </div>
  </div>

  <!-- Main Exam View -->
  <div v-else class="font-sans bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-gray-100 min-h-screen flex flex-col transition-colors duration-300">
    <!-- Sticky Header -->
    <header class="sticky top-0 z-50 w-full bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm transition-colors duration-300">
      <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        <!-- Left: Logo & Context -->
        <div class="flex items-center gap-4 sm:gap-6">
          <!-- Back Button -->
          <button 
            @click="isReviewMode ? handleBackReview() : goBack()" 
            class="flex items-center justify-center p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Volver"
          >
            <span class="material-symbols-outlined text-[24px]">arrow_back</span>
          </button>

          <!-- Logo -->
          <div class="flex items-center gap-2">
            <div class="size-8 flex items-center justify-center overflow-hidden">
              <img src="@/assets/logo.png" alt="SIMIC" class="w-7 h-7 object-contain" />
            </div>
            <h1 class="text-xl font-bold tracking-tight hidden sm:block text-slate-800 dark:text-white">SIMIC</h1>
          </div>
          <!-- Divider -->
          <div class="h-6 w-px bg-slate-200 dark:bg-slate-700 hidden md:block"></div>
          <!-- Exam Title & Subject Badge -->
          <div class="hidden sm:flex items-center gap-3">
            <span :class="getAreaBadgeClass(meta.area)" class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
              {{ getAreaLabel(meta.area) }}
            </span>
            <h2 class="text-slate-700 dark:text-slate-300 text-sm font-medium truncate max-w-[200px] lg:max-w-[400px]">
              {{ simulacro.titulo }}
            </h2>
          </div>
        </div>
        
        <!-- Center: Timer or Status -->
        <div v-if="isStudent && !isReviewMode" class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 hidden lg:flex items-center gap-2 bg-slate-50 dark:bg-slate-900 px-4 py-1.5 rounded-full border border-slate-200 dark:border-slate-700">
          <span class="material-symbols-outlined text-primary animate-pulse text-xl">timer</span>
          <span class="font-mono text-lg font-bold tabular-nums text-slate-900 dark:text-white">{{ formattedTime }}</span>
        </div>
        <div v-else class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 hidden lg:flex items-center gap-2 px-4 py-1.5 rounded-full"
             :class="isReviewMode ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-100 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300' : 'bg-amber-50 dark:bg-amber-900/30 border-amber-100 dark:border-amber-800 text-amber-700 dark:text-amber-300'">
           <span class="material-symbols-outlined text-[20px]">{{ isReviewMode ? 'fact_check' : 'visibility' }}</span>
           <span class="text-sm font-bold uppercase tracking-wide">
             {{ isReviewMode ? (studentNameReview ? `Revisando: ${studentNameReview}` : 'Revisión de resultados') : 'Vista previa' }}
           </span>
        </div>
        
        <!-- Right: Progress & Profile -->
        <div class="flex items-center gap-6">
          <div class="flex flex-col items-end hidden sm:flex">
            <span class="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wide">Progreso</span>
            <span class="text-sm font-bold text-slate-800 dark:text-slate-200">Pregunta {{ currentQuestionIndex + 1 }} de {{ totalQuestions }}</span>
          </div>
          <div class="flex items-center gap-3 pl-6 border-l border-slate-200 dark:border-slate-700">
            <div class="text-right hidden sm:block">
              <p class="text-sm font-semibold text-slate-900 dark:text-white leading-none">{{ userName }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">{{ userRole }}</p>
            </div>
            <div class="size-9 rounded-full bg-primary flex items-center justify-center text-white font-bold text-sm border-2 border-white dark:border-slate-700 shadow-sm">
              {{ userInitials }}
            </div>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Main Content Layout -->
    <div class="flex-1 flex w-full max-w-[1440px] mx-auto relative">
      <main class="flex-1 px-4 sm:px-6 py-8 pb-32 w-full flex justify-center">
        <div class="w-full flex gap-6 max-w-[1600px]"> <!-- Wrapper Flex -->
          
          <!-- LEFT COLUMN: Sticky Context (Desktop) - Condicional inteligente -->
          <div v-if="shouldShowSplitView" class="hidden xl:block w-[45%] flex-shrink-0">
             <div class="sticky top-24 max-h-[calc(100vh-180px)] overflow-y-auto bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 custom-scrollbar transition-colors duration-300">
                <!-- Header Texto -->
                <div v-if="currentQuestion.titulo_texto || currentQuestion.autor_texto" class="border-b border-slate-200 dark:border-slate-700 pb-3 mb-4">
                   <h4 v-if="currentQuestion.titulo_texto" class="text-lg font-bold text-slate-800 dark:text-white leading-tight mb-1">
                     {{ currentQuestion.titulo_texto }}
                   </h4>
                   <p v-if="currentQuestion.autor_texto || currentQuestion.fuente_texto" class="text-sm text-slate-500 dark:text-slate-400 italic">
                      <span v-if="currentQuestion.autor_texto">{{ currentQuestion.autor_texto }}</span>
                      <span v-if="currentQuestion.autor_texto && currentQuestion.fuente_texto" class="mx-1">|</span>
                      <span v-if="currentQuestion.fuente_texto">{{ currentQuestion.fuente_texto }}</span>
                   </p>
                </div>

                <div class="space-y-3">
                  <h4 v-if="!currentQuestion.titulo_texto" class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Contexto</h4>
                  <div class="text-slate-700 dark:text-slate-300 text-base leading-relaxed whitespace-pre-line font-serif" v-html="renderMath(currentQuestion.contexto)"></div>
                </div>
                
                <div v-if="currentQuestion.tiene_grafico" class="w-full pt-4 mt-4 border-t border-slate-200/60 dark:border-slate-700 relative group/chart">
                  <div
                    class="relative overflow-hidden rounded-lg"
                    ref="graficoContextRef"
                    :class="{ 'svg-zoom-wrapper': canUseHoverZoom }"
                    :style="getZoomWrapperStyle('context')"
                    @mouseenter="handleZoomMouseEnter('context')"
                    @mouseleave="handleZoomMouseLeave('context')"
                    @mousemove="handleZoomMouseMove($event, 'context')"
                  >
                    <GraficoRenderer 
                      :tipo="currentQuestion.tipo_grafico" 
                      :config="currentQuestion.configuracion_grafico" 
                      :dark-mode="isDarkModeActive"
                      class="w-full"
                      :class="getZoomTargetClass('context')"
                    />
                  </div>
                  <!-- Botón Optimizar (SuperAdmin) -->
                  <button 
                    v-if="isSuperAdmin"
                    @click="openGraficoModal(currentQuestion, 'context')"
                    class="absolute top-2 right-2 opacity-0 group-hover/chart:opacity-100 transition-opacity bg-white dark:bg-slate-800 text-slate-500 hover:text-primary shadow-sm border border-slate-200 dark:border-slate-600 rounded p-1.5 z-10"
                    title="Optimizar gráfico con IA"
                  >
                    <span class="material-symbols-outlined text-[18px]">auto_fix_high</span>
                  </button>
                </div>
             </div>
          </div>

          <!-- CENTER/RIGHT COLUMN: Question -->
          <div class="flex-1 flex flex-col gap-6 min-w-0"> <!-- min-w-0 prevents flex overflow -->
            <!-- Question Card -->
            <article v-if="currentQuestion" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden transition-colors duration-300">
              <!-- Card Header / Meta -->
              <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex flex-wrap items-center gap-3 bg-slate-50/50 dark:bg-slate-700/30">
                <span class="flex items-center justify-center size-8 rounded-lg bg-slate-900 dark:bg-slate-700 text-white font-bold text-sm shadow-sm">
                  {{ currentQuestionIndex + 1 }}
                </span>
                <div class="flex flex-wrap gap-2">
                  <span v-if="currentQuestion.competencia" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-medium border border-slate-200 dark:border-slate-600">
                    <span class="material-symbols-outlined text-[14px]">calculate</span>
                    {{ currentQuestion.competencia }}
                  </span>
                  <span v-if="currentQuestion.componente" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-medium border border-slate-200 dark:border-slate-600">
                    <span class="material-symbols-outlined text-[14px]">category</span>
                    {{ currentQuestion.componente }}
                  </span>
                </div>
                <div class="ml-auto flex gap-2">
                  <!-- Botón Marcar para Revisión (Solo Admin) -->
                  <button 
                    v-if="canManageReviews"
                    @click="openReviewModal(currentQuestion)"
                    :class="questionHasReview(currentQuestion.id) ? 'text-amber-500' : 'text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300'"
                    class="transition-colors relative"
                    title="Marcar para revisión"
                  >
                    <span class="material-symbols-outlined text-xl" :class="{ 'filled': questionHasReview(currentQuestion.id) }">flag</span>
                    <span v-if="getReviewCount(currentQuestion.id) > 0" class="absolute -top-1 -right-1 bg-amber-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">{{ getReviewCount(currentQuestion.id) }}</span>
                  </button>
                  <!-- Estudiante ve bandera solo como indicador visual si quiere marcar para sí mismo -->
                  <button 
                    v-else-if="isStudent"
                    @click="toggleFlag(currentQuestion.id)"
                    :class="flaggedQuestions.has(currentQuestion.id) ? 'text-orange-500' : 'text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300'"
                    class="transition-colors"
                    title="Marcar para revisar después"
                  >
                    <span class="material-symbols-outlined text-xl" :class="{ 'filled': flaggedQuestions.has(currentQuestion.id) }">flag</span>
                  </button>
                </div>
              </div>
              
              <!-- Question Content -->
              <div class="p-6 md:p-8 space-y-8">
                <!-- Context Section (MOBILE or STACKED Desktop) -->
                <!-- Se muestra si hay contexto Y (es móvil O no amerita split view) -->
                <div v-if="currentQuestion.contexto" :class="{ 'xl:hidden': shouldShowSplitView }" class="bg-slate-50 dark:bg-slate-700/30 rounded-lg p-6 border border-slate-200/60 dark:border-slate-700 space-y-4">
                  <!-- Header Texto Reference -->
                  <div v-if="currentQuestion.titulo_texto || currentQuestion.autor_texto" class="border-b border-slate-200 dark:border-slate-600 pb-3 mb-2">
                     <h4 v-if="currentQuestion.titulo_texto" class="text-base font-bold text-slate-800 dark:text-white leading-tight mb-1">
                       {{ currentQuestion.titulo_texto }}
                     </h4>
                     <p v-if="currentQuestion.autor_texto || currentQuestion.fuente_texto" class="text-xs text-slate-500 dark:text-slate-400 italic">
                        <span v-if="currentQuestion.autor_texto">{{ currentQuestion.autor_texto }}</span>
                        <span v-if="currentQuestion.autor_texto && currentQuestion.fuente_texto" class="mx-1">|</span>
                        <span v-if="currentQuestion.fuente_texto">{{ currentQuestion.fuente_texto }}</span>
                     </p>
                  </div>

                  <div class="space-y-3">
                    <h4 v-if="!currentQuestion.titulo_texto" class="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Contexto</h4>
                    <div class="text-slate-700 dark:text-slate-300 text-base leading-relaxed whitespace-pre-line font-serif" v-html="renderMath(currentQuestion.contexto)"></div>
                  </div>
                  
                  <!-- Figure/Chart -->
                  <div v-if="currentQuestion.tiene_grafico" class="w-full pt-4 border-t border-slate-200/60 dark:border-slate-600 relative group/chart">
                    <div
                      class="relative overflow-hidden rounded-lg"
                      ref="graficoQuestionRef"
                      :class="{ 'svg-zoom-wrapper': canUseHoverZoom }"
                      :style="getZoomWrapperStyle('question')"
                      @mouseenter="handleZoomMouseEnter('question')"
                      @mouseleave="handleZoomMouseLeave('question')"
                      @mousemove="handleZoomMouseMove($event, 'question')"
                    >
                        <GraficoRenderer 
                        :tipo="currentQuestion.tipo_grafico" 
                        :config="currentQuestion.configuracion_grafico" 
                        :dark-mode="isDarkModeActive"
                        class="w-full max-w-2xl mx-auto"
                        :class="getZoomTargetClass('question')"
                        />
                    </div>
                    <!-- Botón Optimizar (SuperAdmin) -->
                    <button 
                      v-if="isSuperAdmin"
                      @click="openGraficoModal(currentQuestion, 'question')"
                      class="absolute top-2 right-2 opacity-0 group-hover/chart:opacity-100 transition-opacity bg-white dark:bg-slate-800 text-slate-500 hover:text-primary shadow-sm border border-slate-200 dark:border-slate-600 rounded p-1.5 z-10"
                    title="Optimizar gráfico con IA"
                    >
                      <span class="material-symbols-outlined text-[18px]">auto_fix_high</span>
                    </button>
                  </div>
                </div>
                
                <!-- Question Stem -->
                <div class="space-y-4">
                  <h3 class="text-lg md:text-xl font-medium text-slate-900 dark:text-gray-100 leading-snug" v-html="renderMath(currentQuestion.enunciado)">
                  </h3>
                </div>
                
                <!-- Answer Options -->
                <div class="grid gap-3">
                  <label 
                    v-for="opcion in currentQuestion.opciones" 
                    :key="opcion.id"
                    class="group relative flex items-start gap-4 p-4 rounded-lg border-2 transition-all"
                    :class="[
                      isReviewMode 
                        ? getReviewClass(opcion, currentQuestion)
                        : (respuestas[currentQuestion.id] === opcion.id 
                            ? 'border-primary bg-primary/5 dark:bg-primary/10' 
                            : (isStudent ? 'border-slate-200 dark:border-slate-700 hover:border-primary/60 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer' : 'border-slate-200 dark:border-slate-700 opacity-75 cursor-default'))
                    ]"
                  >
                    <input 
                      type="radio" 
                      :name="`question_${currentQuestion.id}`" 
                      :value="opcion.id"
                      :checked="respuestas[currentQuestion.id] === opcion.id"
                      :disabled="!isStudent || isReviewMode"
                      @change="(!isReviewMode && isStudent) && seleccionarRespuesta(opcion.id)"
                      class="sr-only peer" 
                    />
                    <div 
                      class="flex items-center justify-center size-6 shrink-0 rounded-full border mt-0.5 transition-colors"
                      :class="[
                        respuestas[currentQuestion.id] === opcion.id 
                          ? 'bg-primary border-primary text-white' 
                          : 'border-slate-300 dark:border-slate-500 text-transparent group-hover:border-primary/60'
                      ]"
                    >
                      <span class="text-xs font-bold">{{ opcion.id }}</span>
                    </div>
                    <div class="flex-1">
                      <p class="text-base font-medium" :class="respuestas[currentQuestion.id] === opcion.id ? 'text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'" v-html="renderMath(opcion.texto)">
                      </p>
                    </div>
                    <!-- Selection ring -->
                    <div 
                      v-if="respuestas[currentQuestion.id] === opcion.id"
                      class="absolute inset-0 rounded-lg ring-2 ring-primary pointer-events-none"
                    ></div>
                  </label>
                </div>
              </div>
            </article>
          </div>
        </div>
      </main>
      
      <!-- Right Side Panel (Question Map) - Reduced width -->
      <aside class="hidden 2xl:flex flex-col w-[260px] flex-shrink-0 sticky top-16 h-[calc(100vh-64px)] border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-y-auto transition-colors duration-300">
        <div class="p-4">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xs font-bold uppercase text-slate-500 dark:text-slate-400 tracking-wider">Mapa</h3>
            <span class="text-primary text-xs font-medium">{{ answeredCount }}/{{ totalQuestions }}</span>
          </div>
          
          <!-- Grid -->
          <div class="grid grid-cols-4 gap-2 mb-8">
            <button 
              v-for="(q, idx) in preguntas" 
              :key="q.id"
              @click="goToQuestion(idx)"
              class="aspect-square flex items-center justify-center rounded font-bold text-xs transition-all"
              :class="getQuestionButtonClass(idx, q.id)"
            >
              {{ idx + 1 }}
            </button>
          </div>
          
          <!-- Legend -->
          <div v-if="isStudent" class="space-y-3 border-t border-slate-100 dark:border-slate-700 pt-6">
            <div class="flex items-center gap-3">
              <div class="size-3 rounded-full bg-emerald-500"></div>
              <span class="text-sm text-slate-600 dark:text-slate-400">Respondida</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="size-3 rounded-full bg-primary"></div>
              <span class="text-sm text-slate-600 dark:text-slate-400">Actual</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="size-3 rounded-full bg-slate-300 dark:bg-slate-600"></div>
              <span class="text-sm text-slate-600 dark:text-slate-400">Pendiente</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="size-3 rounded-full bg-orange-400 border border-orange-500"></div>
              <span class="text-sm text-slate-600 dark:text-slate-400">Marcada para revisión</span>
            </div>
          </div>
          
          <!-- Info Box -->
          <div v-if="isStudent" class="mt-8 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-900">
            <div class="flex gap-2">
              <span class="material-symbols-outlined text-primary text-xl">info</span>
              <p class="text-xs text-blue-800 dark:text-blue-300 leading-relaxed">
                Recuerda que puedes marcar preguntas para revisar más tarde usando el icono de bandera.
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
    
    <!-- Sticky Footer (Bottom Nav) -->
    <footer class="fixed bottom-0 left-0 right-0 z-40 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 shadow-[0_-4px_16px_rgba(0,0,0,0.05)] transition-colors duration-300">
      <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Tiempo mínimo requerido -->
        <div v-if="isStudent && !isReviewMode && totalTimeSeconds" class="pt-3 pb-2">
          <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 mb-1">
            <span>Debes permanecer al menos {{ minFinishRequiredMinutes }} min antes de finalizar</span>
            <span v-if="!canFinish">Faltan ~{{ minFinishRemainingMinutes }} min</span>
            <span v-else class="text-emerald-600 dark:text-emerald-400">Listo para finalizar</span>
          </div>
          <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              class="h-1.5 bg-amber-500 dark:bg-amber-400 transition-all"
              :style="{ width: `${minFinishProgress}%` }"
            ></div>
          </div>
        </div>

        <div class="h-20 flex items-center justify-between">
        <!-- Prev Button -->
        <button 
          @click="prevQuestion"
          :disabled="currentQuestionIndex === 0"
          class="flex items-center gap-2 px-6 h-11 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span class="material-symbols-outlined">arrow_back</span>
          <span class="hidden sm:inline">Anterior</span>
        </button>
        
        <!-- Mini Progress Indicator -->
        <div class="hidden md:flex flex-col items-center gap-2">
          <div class="flex gap-1.5">
            <div 
              v-for="(q, idx) in Math.min(preguntas.length, 10)" 
              :key="idx"
              class="size-2 rounded-full transition-all"
              :class="[
                idx === currentQuestionIndex ? 'bg-primary ring-2 ring-primary/30' :
                respuestas[preguntas[idx]?.id] ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'
              ]"
            ></div>
            <span v-if="preguntas.length > 10" class="text-xs text-slate-400 ml-1">+{{ preguntas.length - 10 }}</span>
          </div>
          <span class="text-[10px] text-slate-400 font-medium tracking-widest uppercase">Progreso</span>
        </div>
        
        <!-- Next / Finish Button -->
        <button 
          v-if="currentQuestionIndex < totalQuestions - 1"
          @click="nextQuestion"
          class="flex items-center gap-2 px-8 h-11 rounded-lg bg-primary hover:bg-indigo-600 text-white font-bold shadow-lg shadow-primary/30 transition-all hover:shadow-primary/50 hover:-translate-y-0.5 active:translate-y-0"
        >
          <span>Siguiente</span>
          <span class="material-symbols-outlined">arrow_forward</span>
        </button>
        <button 
          v-else
          @click="isReviewMode ? handleBackReview() : (isStudent ? finalizarSimulacro() : goBack())"
          :disabled="isStudent && !isReviewMode && !canFinish"
          class="flex items-center gap-2 px-8 h-11 rounded-lg font-bold shadow-lg transition-all hover:-translate-y-0.5 active:translate-y-0"
          :class="[
            (isStudent && !isReviewMode)
              ? (canFinish ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-500/30' : 'bg-slate-300 dark:bg-slate-600 text-slate-500 dark:text-slate-400 shadow-none cursor-not-allowed')
              : 'bg-slate-800 dark:bg-slate-700 hover:bg-slate-900 dark:hover:bg-slate-600 text-white shadow-slate-500/30'
          ]"
        >
          <span class="material-symbols-outlined">{{ (isStudent && !isReviewMode) ? 'check_circle' : 'logout' }}</span>
          <span>{{ isReviewMode ? 'Salir de revisión' : ((isStudent) ? 'Finalizar' : 'Salir de vista previa') }}</span>
        </button>
      </div>
      </div>
    </footer>
    <!-- MODAL OPTIMIZACIÓN GRÁFICO -->
    <div v-if="showGraficoModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">auto_fix_high</span>
            Optimizar gráfico
          </h3>
          <button @click="closeGraficoModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <span class="material-symbols-outlined text-2xl">close</span>
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
            <div class="bg-white p-6 rounded-lg shadow-sm border border-slate-200 flex justify-center items-center min-h-[300px]" ref="modalGraficoRef">
              <GraficoRenderer 
                v-if="selectedPreguntaGrafico?.configuracion_grafico"
                :config="selectedPreguntaGrafico.configuracion_grafico"
                :tipo="selectedPreguntaGrafico.tipo_grafico"
                :dark-mode="isDarkModeActive"
              />
              <div v-else class="text-slate-400 italic">No hay configuración gráfica disponible</div>
            </div>
            
            <!-- Contexto de la pregunta -->
            <div class="text-sm text-slate-600 dark:text-slate-400">
              <strong>Contexto:</strong> {{ selectedPreguntaGrafico?.contexto?.substring(0, 150) }}...
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
            <span v-if="optimizingGrafico" class="material-symbols-outlined animate-spin text-[18px]">autorenew</span>
            <span v-else class="material-symbols-outlined text-[18px]">auto_fix_high</span>
            {{ optimizingGrafico ? 'Optimizando...' : 'Optimizar ahora' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- MODAL MARCAR PARA REVISIÓN -->
    <div v-if="showReviewModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <span class="material-symbols-outlined text-amber-500">flag</span>
            Marcar para revisión
          </h3>
          <button @click="closeReviewModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <span class="material-symbols-outlined text-2xl">close</span>
          </button>
        </div>
        
        <!-- Content -->
        <div class="p-6 overflow-y-auto flex-1 bg-slate-50 dark:bg-slate-900/50">
          <div class="flex flex-col gap-5">
            <!-- Info de la pregunta -->
            <div class="p-4 bg-slate-100 dark:bg-slate-800 rounded-lg">
              <p class="text-xs text-slate-500 dark:text-slate-400 uppercase font-medium mb-1">Pregunta {{ selectedReviewPregunta?.id }}</p>
              <p class="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">{{ selectedReviewPregunta?.enunciado }}</p>
            </div>
            
            <!-- Revisiones existentes -->
            <div v-if="existingReviews.length > 0" class="space-y-3">
              <h4 class="text-sm font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wide">Revisiones anteriores</h4>
              <div v-for="rev in existingReviews" :key="rev.id" class="p-3 rounded-lg border" :class="rev.resuelto ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800' : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'">
                <div class="flex items-start justify-between gap-2">
                  <div class="flex-1">
                    <p class="text-sm text-slate-700 dark:text-slate-300">{{ rev.revision }}</p>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Por {{ rev.usuario_nombre || 'Usuario' }} • {{ formatDate(rev.created_at) }}</p>
                  </div>
                  <button 
                    v-if="!rev.resuelto"
                    @click="markReviewResolved(rev.id)"
                    class="text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 transition-colors"
                    title="Marcar como resuelto"
                  >
                    <span class="material-symbols-outlined text-[20px]">check_circle</span>
                  </button>
                  <span v-else class="text-emerald-600 dark:text-emerald-400">
                    <span class="material-symbols-outlined text-[20px] filled">check_circle</span>
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Nueva revisión -->
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Nueva nota de revisión</label>
              <textarea 
                v-model="reviewNote"
                placeholder="Describe el problema con esta pregunta (ej: respuesta correcta incorrecta, error en el gráfico, contexto confuso)..."
                class="w-full px-3 py-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm focus:ring-2 focus:ring-amber-400 focus:border-transparent outline-none transition-all resize-y min-h-[100px]"
              ></textarea>
            </div>
          </div>
        </div>
        
        <!-- Footer Actions -->
        <div class="px-6 py-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 flex justify-between gap-3">
          <button 
            @click="closeReviewModal"
            class="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
          >
            Cancelar
          </button>
          <button 
            @click="submitReview"
            :disabled="!reviewNote.trim() || submittingReview"
            class="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="submittingReview" class="material-symbols-outlined animate-spin text-[18px]">autorenew</span>
            <span v-else class="material-symbols-outlined text-[18px]">send</span>
            {{ submittingReview ? 'Guardando...' : 'Guardar revisión' }}
          </button>
        </div>
      </div>
    </div>
    
    <Toast />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onUnmounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useSimulacrosStore } from '../stores/simulacros';
import { useToast } from 'primevue/usetoast';
import Toast from 'primevue/toast';
import html2canvas from 'html2canvas';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import lupaIcon from '../assets/lupa.png';

import api from '../api/axios';
import GraficoRenderer from '../components/graficos/GraficoRenderer.vue';

// Helper de Renderizado Matemático
const renderMath = (text) => {
  if (!text) return '';
  // Detectar LaTeX: bloques $$..$$, \[..\], inline \(..\), $..$
  // Mejorado: Ignora $ seguido de dígito (moneda)
  const regex = /(\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\\)\$(?!\s?\d).*?(?<!\\)\$)/gs;
  
  return text.replace(regex, (match) => {
      try {
          // Limpiar delimitadores
          let formula = match;
          let displayMode = false;
          
          if (formula.startsWith('$$')) { formula = formula.slice(2, -2); displayMode = true; }
          else if (formula.startsWith('\\[')) { formula = formula.slice(2, -2); displayMode = true; }
          else if (formula.startsWith('\\(')) { formula = formula.slice(2, -2); }
          else if (formula.startsWith('$')) { formula = formula.slice(1, -1); }
          
          return katex.renderToString(formula, {
              throwOnError: false,
              displayMode: displayMode,
              output: 'html'
          });
      } catch (e) {
          console.error('Error rendering math:', e);
          return match;
      }
  });
};

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const simulacrosStore = useSimulacrosStore();
const toast = useToast();
const simulacroId = route.params.id;

// Logic for Optimization
const showGraficoModal = ref(false);
const selectedPreguntaGrafico = ref(null);
const modalGraficoRef = ref(null);
const optimizingGrafico = ref(false);
const instruccionesAdicionales = ref('');
const graficoContextRef = ref(null);
const graficoQuestionRef = ref(null);
const isDarkModeActive = ref(false);
const supportsFineHover = ref(false);

const isSvgGraphic = (tipo) => {
  const normalizedType = String(tipo || '').toLowerCase();
  return ['svg_artistico', 'svg_geometrico', 'diagrama_svg'].includes(normalizedType);
};

const zoomState = reactive({
  context: { active: false, x: '50%', y: '50%' },
  question: { active: false, x: '50%', y: '50%' }
});

const resetZoomState = (scope) => {
  zoomState[scope].active = false;
  zoomState[scope].x = '50%';
  zoomState[scope].y = '50%';
};

const getZoomWrapperStyle = (scope) => {
  if (!canUseHoverZoom.value) return undefined;
  return {
    '--zoom-x': zoomState[scope].x,
    '--zoom-y': zoomState[scope].y,
    cursor: `url(${lupaIcon}) 12 12, zoom-in`
  };
};

const getZoomTargetClass = (scope) => ({
  'svg-zoom-target': canUseHoverZoom.value,
  'svg-zoom-target-active': canUseHoverZoom.value && zoomState[scope].active
});

const handleZoomMouseEnter = (scope) => {
  if (!canUseHoverZoom.value) return;
  zoomState[scope].active = true;
};

const handleZoomMouseLeave = (scope) => {
  resetZoomState(scope);
};

const handleZoomMouseMove = (event, scope) => {
  if (!canUseHoverZoom.value) return;

  const rect = event.currentTarget.getBoundingClientRect();
  if (!rect.width || !rect.height) return;

  const x = ((event.clientX - rect.left) / rect.width) * 100;
  const y = ((event.clientY - rect.top) / rect.height) * 100;
  const clampedX = Math.max(0, Math.min(100, x));
  const clampedY = Math.max(0, Math.min(100, y));

  zoomState[scope].x = `${clampedX}%`;
  zoomState[scope].y = `${clampedY}%`;
};

// Logic for Review Modal
const showReviewModal = ref(false);
const selectedReviewPregunta = ref(null);
const reviewNote = ref('');
const submittingReview = ref(false);
const existingReviews = ref([]);
const allReviewsForSimulacro = ref([]);  // Cache de todas las reviews del simulacro

const openGraficoModal = (pregunta, source) => {
  selectedPreguntaGrafico.value = pregunta;
  instruccionesAdicionales.value = ''; // Limpiar
  showGraficoModal.value = true;
};

const closeGraficoModal = () => {
  showGraficoModal.value = false;
  selectedPreguntaGrafico.value = null;
};

const optimizarGrafico = async () => {
  if (!modalGraficoRef.value || !selectedPreguntaGrafico.value) return;
  
  optimizingGrafico.value = true;
  try {
    // 1. Capturar el gráfico renderizado
    const canvas = await html2canvas(modalGraficoRef.value, {
      backgroundColor: '#ffffff',
      scale: 2 // Mejor calidad
    });
    
    const imagenBase64 = canvas.toDataURL('image/png').split(',')[1];
    
    // 2. Llamar al store
    // Nota: optimizarGrafico en el store actualiza el simulacro completo
    await simulacrosStore.optimizarGrafico(
      simulacroId,
      selectedPreguntaGrafico.value.id,
      imagenBase64,
      instruccionesAdicionales.value
    );
    
    toast.add({ 
      severity: 'success', 
      summary: 'Gráfico optimizado', 
      detail: 'El gráfico ha sido corregido exitosamente.',
      life: 3000 
    });
    
    // Recargar localmente para ver cambios
    const response = await api.get(`/simulacros/${simulacroId}`);
    simulacro.value = response.data;
    
    // Parse JSONB
    let content = simulacro.value.contenido;
    if (typeof content === 'string') {
      content = JSON.parse(content);
    }
    preguntas.value = content.preguntas || [];
    
    // Actualizar la pregunta seleccionada también para que el modal se refresque
    const updatedPregunta = preguntas.value.find(p => p.id === selectedPreguntaGrafico.value.id);
    if (updatedPregunta) {
        selectedPreguntaGrafico.value = updatedPregunta;
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

// User info
const userName = computed(() => authStore.user?.nombre || authStore.user?.email || 'Usuario');
const userRole = computed(() => {
  const roleName = authStore.user?.rol?.nombre;
  const map = {
    'admin': 'Super Admin',
    'admin': 'Admin Institucional',
    'estudiante': 'Estudiante'
  };
  return map[roleName] || roleName || 'Estudiante';
});
const userInitials = computed(() => {
  const name = userName.value;
  if (name.includes('@')) return name.charAt(0).toUpperCase();
  const parts = name.split(' ');
  if (parts.length >= 2) return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
  return name.substring(0, 2).toUpperCase();
});

const isStudent = computed(() => userRole.value === 'Estudiante');
const isSuperAdmin = computed(() => userRole.value === 'Super Admin');
const isAdminInstitucional = computed(() => ['Admin Institucional', 'Rector', 'Coordinador'].includes(userRole.value));
const canManageReviews = computed(() => isSuperAdmin.value || isAdminInstitucional.value);
const isReviewMode = computed(() => route.meta.mode === 'review');
const canUseHoverZoom = computed(() => (
  isStudent.value &&
  !isReviewMode.value &&
  supportsFineHover.value &&
  isSvgGraphic(currentQuestion.value?.tipo_grafico)
));
const studentNameReview = ref('');

// State
const loading = ref(true);
const simulacro = ref(null);
const preguntas = ref([]);
const meta = ref({});
const respuestas = reactive({});
const flaggedQuestions = reactive(new Set());
const currentQuestionIndex = ref(0);

// Timer
const timeRemaining = ref(60 * 60); // 60 minutes in seconds
let timerInterval = null;
let heartbeatInterval = null;
let saveTimeout = null;

const intentoActivo = ref(false);
const isSaving = ref(false);
const lastSavedState = ref('');

const formattedTime = computed(() => {
  const hours = Math.floor(timeRemaining.value / 3600);
  const minutes = Math.floor((timeRemaining.value % 3600) / 60);
  const seconds = timeRemaining.value % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
});

const computeTimeRemaining = (fechaInicioIso, durationMin) => {
  if (!durationMin || durationMin <= 0) return 0;
  const start = fechaInicioIso ? new Date(fechaInicioIso) : new Date();
  const end = new Date(start.getTime() + durationMin * 60000);
  const now = new Date();
  return Math.max(0, Math.floor((end.getTime() - now.getTime()) / 1000));
};

const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    if (timeRemaining.value > 0) {
      timeRemaining.value--;
    } else {
      clearInterval(timerInterval);
      alert('¡El tiempo ha terminado!');
      finalizarSimulacro(true);
    }
  }, 1000);
};

// Computed
const totalQuestions = computed(() => preguntas.value.length);
const currentQuestion = computed(() => preguntas.value[currentQuestionIndex.value]);
const answeredCount = computed(() => Object.keys(respuestas).length);
const totalTimeSeconds = computed(() => {
  const duration = simulacro.value?.duracion_minutos || simulacro.value?.tiempo_limite || 60;
  return Math.max(0, Math.floor(duration * 60));
});
const elapsedSeconds = computed(() => {
  if (!totalTimeSeconds.value) return 0;
  return Math.max(0, totalTimeSeconds.value - timeRemaining.value);
});
const minFinishSeconds = computed(() => Math.floor(totalTimeSeconds.value * 0.3));
const canFinish = computed(() => {
  if (!totalTimeSeconds.value) return true;
  return elapsedSeconds.value >= minFinishSeconds.value;
});
const minFinishProgress = computed(() => {
  if (!minFinishSeconds.value) return 100;
  const pct = (elapsedSeconds.value / minFinishSeconds.value) * 100;
  return Math.min(100, Math.max(0, pct));
});
const minFinishRemaining = computed(() => Math.max(0, minFinishSeconds.value - elapsedSeconds.value));
const minFinishRequiredMinutes = computed(() => Math.max(0, Math.ceil(minFinishSeconds.value / 60)));
const minFinishRemainingMinutes = computed(() => Math.max(0, Math.ceil(minFinishRemaining.value / 60)));

const getElapsedSeconds = () => Math.max(0, Math.floor(elapsedSeconds.value));

// Lógica de Split View Inteligente
const shouldShowSplitView = computed(() => {
   const q = currentQuestion.value;
   if (!q || !q.contexto) return false;
   
   // Áreas de lectura intensiva siempre usan Split View para mejor legibilidad
   const splitAreas = ['LECTURA_CRITICA', 'INGLES', 'SOCIALES_CIUDADANAS'];
   const currentArea = meta.value?.area || '';
   
   if (splitAreas.includes(currentArea)) return true;
   
   // Matemáticas y Ciencias:
   // - Si tiene gráfico: Split View (Gráfico a izq, Pregunta a der)
   // - Si tiene título de texto: Split View (Es un texto formal)
   // - Si es largo (> 250 chars): Split View
   if (q.tiene_grafico) return true;
   if (q.titulo_texto) return true;
   if (q.contexto.length > 250) return true;
   
   // Contextos cortos de mate (ej: planteamiento de 2 lineas) van mejor STACKED (arriba de la pregunta)
   return false;
});

// Methods
const getAreaLabel = (area) => {
  const labels = {
    'GLOBAL': 'Global',
    'MATEMATICAS': 'Matemáticas',
    'LECTURA_CRITICA': 'Lectura Crítica',
    'CIENCIAS_NATURALES': 'Ciencias Nat.',
    'SOCIALES_CIUDADANAS': 'Sociales',
    'INGLES': 'Inglés'
  };
  return labels[area] || area || 'Sin área';
};

const getAreaBadgeClass = (area) => {
  const classes = {
    'GLOBAL': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    'MATEMATICAS': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    'LECTURA_CRITICA': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    'CIENCIAS_NATURALES': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    'SOCIALES_CIUDADANAS': 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300',
    'INGLES': 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300'
  };
  return classes[area] || 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300';
};

const getQuestionButtonClass = (idx, questionId) => {
  if (idx === currentQuestionIndex.value) {
    return 'bg-primary text-white shadow-md ring-2 ring-primary ring-offset-2 dark:ring-offset-slate-800';
  }
  if (flaggedQuestions.has(questionId)) {
    return 'bg-orange-100 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 hover:ring-2 ring-orange-400';
  }
  if (respuestas[questionId]) {
    return 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 hover:ring-2 ring-emerald-400';
  }
  return 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600';
};

const seleccionarRespuesta = (opcionId) => {
  respuestas[currentQuestion.value.id] = opcionId;
};

const toggleFlag = (questionId) => {
  if (flaggedQuestions.has(questionId)) {
    flaggedQuestions.delete(questionId);
  } else {
    flaggedQuestions.add(questionId);
  }
};

const goToQuestion = (idx) => {
  currentQuestionIndex.value = idx;
  window.scrollTo(0, 0);
};

const nextQuestion = () => {
  if (currentQuestionIndex.value < totalQuestions.value - 1) {
    currentQuestionIndex.value++;
    window.scrollTo(0, 0);
  }
};

const prevQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--;
    window.scrollTo(0, 0);
  }
};

const goBack = () => {
    // Si NO es modo examen real, volvemos atrás en historial
    if (!isStudent.value || isReviewMode.value) {
        router.back(); 
    } else {
        // En examen real, confirmar salida
        if(confirm("¿Seguro que deseas salir? Perderás el progreso actual.")) {
            saveProgress();
            router.push('/simulacros');
        }
    }
};

const handleBackReview = () => {
    const studentId = route.query.studentId;
    if (studentId) {
        router.push(`/estudiantes/${studentId}`);
    } else {
        router.push('/simulacros');
    }
};

const saveProgress = async () => {
  if (!isStudent.value || isReviewMode.value || !simulacro.value || !intentoActivo.value) return;
  const currentState = JSON.stringify(respuestas);
  if (currentState === lastSavedState.value) return;

  try {
    isSaving.value = true;
    await api.patch(`/simulacros/${simulacroId}/guardar`, {
      respuestas_parciales: respuestas,
      tiempo_empleado: getElapsedSeconds()
    });
    lastSavedState.value = currentState;
  } catch (e) {
    console.warn("Error guardando progreso parcial (reintentaré luego):", e);
  } finally {
    isSaving.value = false;
  }
};

watch(respuestas, () => {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(saveProgress, 3000);
}, { deep: true });

const finalizarSimulacro = async (force = false) => {
  if (isStudent.value && !isReviewMode.value && !canFinish.value && !force) {
    alert(`Debes permanecer al menos el 30% del tiempo antes de finalizar. Faltan ~${minFinishRemainingMinutes.value} min.`);
    return;
  }

  if (!force && Object.keys(respuestas).length < totalQuestions.value) {
    const confirm = window.confirm(`Tienes ${totalQuestions.value - Object.keys(respuestas).length} preguntas sin responder. ¿Seguro que quieres finalizar?`);
    if (!confirm) return;
  }
  
  try {
    loading.value = true;
    
    if (isStudent.value) {
        await api.post(`/simulacros/${simulacroId}/finalizar`, {
            respuestas: respuestas,
            tiempo_empleado: getElapsedSeconds()
        });
        
        router.push(`/simulacros/${simulacroId}/finalizado`);
    } else {
        alert("¡Simulacro finalizado! Respuestas capturadas: " + JSON.stringify(respuestas));
        router.push('/simulacros');
    }
  } catch (error) {
    console.error("Error al finalizar simulacro:", error);
    const msg = error.response?.data?.detail || "Error al enviar el examen. Por favor intenta nuevamente.";
    if (msg.toLowerCase().includes("expirado")) {
        alert("El tiempo del examen ha expirado. Se guardaron las respuestas parciales.");
        router.push(`/simulacros/${simulacroId}/finalizado`);
        return;
    }
    alert(msg);
    loading.value = false;
  }
};

const getReviewClass = (opcion, question) => {
    const opcionId = opcion.id;
    const selected = respuestas[question.id] === opcionId;
    // Asumimos que question.respuesta_correcta está presente en el JSON de preguntas
    const correct = question.respuesta_correcta === opcionId;
    
    if (correct) return 'bg-emerald-100 dark:bg-emerald-900/30 border-emerald-500 text-emerald-900 dark:text-emerald-300 ring-1 ring-emerald-500';
    if (selected && !correct) return 'bg-rose-100 dark:bg-rose-900/30 border-rose-500 text-rose-900 dark:text-rose-300 ring-1 ring-rose-500';
    
    return 'opacity-60 border-slate-200 dark:border-slate-700 grayscale'; 
};

// Lifecycle
onMounted(() => {
  syncDarkModeState();

  if (typeof MutationObserver !== 'undefined') {
    themeClassObserver = new MutationObserver(syncDarkModeState);
    themeClassObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });
  }

  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    hoverMediaQuery = window.matchMedia('(hover: hover) and (pointer: fine)');
    supportsFineHover.value = hoverMediaQuery.matches;

    if (typeof hoverMediaQuery.addEventListener === 'function') {
      hoverMediaQuery.addEventListener('change', handleHoverMediaChange);
    } else if (typeof hoverMediaQuery.addListener === 'function') {
      hoverMediaQuery.addListener(handleHoverMediaChange);
    }
  }
});

onMounted(async () => {
  try {
    const response = await api.get(`/simulacros/${simulacroId}`);
    simulacro.value = response.data;
    
    // Parse JSONB content
    let content = simulacro.value.contenido;
    if (typeof content === 'string') {
      content = JSON.parse(content);
    }
    
    preguntas.value = content.preguntas || [];
    meta.value = content.meta || {};
    
    // Start timer only for students AND NOT REVIEW
    if (isStudent.value && !isReviewMode.value) {
      try {
        const intentoRes = await api.post(`/simulacros/${simulacroId}/iniciar`);
        const intento = intentoRes.data;
        intentoActivo.value = true;

        if (intento.respuestas && Object.keys(intento.respuestas).length > 0) {
          Object.assign(respuestas, intento.respuestas);
          lastSavedState.value = JSON.stringify(respuestas);
          toast.add({ 
            severity: 'info', 
            summary: 'Progreso restaurado', 
            detail: `Has recuperado ${Object.keys(intento.respuestas).length} respuestas guardadas.`,
            life: 4000 
          });
        }

        const duration = simulacro.value.duracion_minutos || simulacro.value.tiempo_limite || 60;
        const remaining = computeTimeRemaining(intento.fecha_inicio, duration);

        if (remaining <= 0) {
          alert('El tiempo del simulacro ha expirado.');
          await finalizarSimulacro(true);
          return;
        }

        timeRemaining.value = remaining;
        startTimer();
        heartbeatInterval = setInterval(saveProgress, 30000);
      } catch (err) {
        intentoActivo.value = false;
        const status = err?.response?.status;
        const message = err?.response?.data?.detail || "No se pudo iniciar el examen.";
        if (status === 409) {
          console.info("Inicio bloqueado:", message);
          try {
            sessionStorage.setItem('simulacros_start_blocked_dialog', JSON.stringify({
              title: 'Simulacro no disponible',
              message
            }));
          } catch (_) {
            // no-op
          }
          router.push('/simulacros');
          return;
        } else {
          console.error("Error iniciando intento:", err);
        }
        const startErrorToast = {
          severity: 'error',
          summary: 'Error al iniciar',
          detail: message,
          life: 4500
        };
        toast.add(startErrorToast);
        try {
          sessionStorage.setItem('simulacros_start_error_toast', JSON.stringify(startErrorToast));
        } catch (_) {
          // no-op: si el storage falla, mantenemos el toast local
        }
        router.push('/simulacros');
        return;
      }
    }
    
    // Load answers if review mode
    if (isReviewMode.value) {
         const studentId = route.query.studentId;
         let url = `/simulacros/${simulacroId}/mi-intento`;
         
         if (studentId) {
             url = `/simulacros/${simulacroId}/intentos/${studentId}`;
         }
         
         const res = await api.get(url);
         const intento = res.data || {};
         const respuestasRaw = intento.respuestas || {};
         const preguntasList = preguntas.value || [];

         const newRespuestas = {};
         const existingIds = new Set(preguntasList.map(p => String(p.id)));
         const rawEntries = Object.entries(respuestasRaw);

         // Modo ÚNICO por intento:
         // - OMR (tiempo_empleado null): claves son índices visuales 1..N
         // - Online (default): claves son IDs reales de pregunta
         let mapByIndex = intento.tiempo_empleado === null;

         // Fallback para históricos atípicos: si no se detectó OMR por metadato,
         // probar cobertura por IDs y usar índice solo si IDs no mapean nada.
         if (!mapByIndex && rawEntries.length > 0) {
             const idCoverage = rawEntries.filter(([key]) => existingIds.has(String(key))).length;
             if (idCoverage === 0) {
                 const indexCoverage = rawEntries.filter(([key]) => {
                     const idx = parseInt(key, 10) - 1;
                     return Number.isInteger(idx) && idx >= 0 && idx < preguntasList.length;
                 }).length;
                 mapByIndex = indexCoverage > 0;
             }
         }

         if (mapByIndex) {
             for (const [key, value] of rawEntries) {
                 const idx = parseInt(key, 10) - 1;
                 if (!Number.isInteger(idx) || idx < 0 || idx >= preguntasList.length) continue;
                 const realQuestionId = preguntasList[idx].id;
                 newRespuestas[realQuestionId] = value;
             }
         } else {
             for (const [key, value] of rawEntries) {
                 if (!existingIds.has(String(key))) continue;
                 newRespuestas[String(key)] = value;
             }
         }

         // Asignar respuestas procesadas
         Object.assign(respuestas, newRespuestas);
         
         // Si hay studentId, intentar obtener nombre (opcional, si quisieramos mostrarlo en el header)
         if (studentId) {
             // Podríamos hacer fetch al usuario, o pasarlo por query param studentName para ahorrar request
             studentNameReview.value = route.query.studentName || 'Estudiante';
         }
    }
    
    // Cargar reviews existentes para el simulacro (si es admin)
    if (canManageReviews.value) {
      try {
        const reviewsRes = await api.get(`/reviews/simulacro/${simulacroId}`);
        allReviewsForSimulacro.value = reviewsRes.data.reviews || [];
      } catch (e) {
        console.error('Error cargando reviews:', e);
      }
    }
    
  } catch (error) {
    console.error("Error cargando simulacro:", error);
  } finally {
    loading.value = false;
  }
});

// ==========================================
// FUNCIONES PARA REVISIONES
// ==========================================

const questionHasReview = (preguntaId) => {
  return allReviewsForSimulacro.value.some(r => r.pregunta_numero === preguntaId && !r.resuelto);
};

const getReviewCount = (preguntaId) => {
  return allReviewsForSimulacro.value.filter(r => r.pregunta_numero === preguntaId && !r.resuelto).length;
};

const openReviewModal = async (pregunta) => {
  selectedReviewPregunta.value = pregunta;
  reviewNote.value = '';
  showReviewModal.value = true;
  
  // Cargar reviews existentes para esta pregunta
  try {
    const res = await api.get(`/reviews/pregunta/${simulacroId}/${pregunta.id}`);
    existingReviews.value = res.data || [];
  } catch (e) {
    console.error('Error cargando reviews de pregunta:', e);
    existingReviews.value = [];
  }
};

const closeReviewModal = () => {
  showReviewModal.value = false;
  selectedReviewPregunta.value = null;
  reviewNote.value = '';
  existingReviews.value = [];
};

const submitReview = async () => {
  if (!reviewNote.value.trim() || !selectedReviewPregunta.value) return;
  
  submittingReview.value = true;
  try {
    await api.post('/reviews/', {
      simulacro_id: parseInt(simulacroId),
      pregunta_numero: selectedReviewPregunta.value.id,
      revision: reviewNote.value.trim()
    });
    
    toast.add({ 
      severity: 'success', 
      summary: 'Revisión guardada', 
      detail: `Pregunta ${selectedReviewPregunta.value.id} marcada para revisión`,
      life: 3000 
    });
    
    // Recargar todas las reviews
    const reviewsRes = await api.get(`/reviews/simulacro/${simulacroId}`);
    allReviewsForSimulacro.value = reviewsRes.data.reviews || [];
    
    closeReviewModal();
    
  } catch (error) {
    console.error('Error guardando revisión:', error);
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: error.response?.data?.detail || 'No se pudo guardar la revisión',
      life: 5000 
    });
  } finally {
    submittingReview.value = false;
  }
};

const markReviewResolved = async (reviewId) => {
  try {
    await api.patch(`/reviews/${reviewId}`, { resuelto: true });
    
    // Actualizar local
    const idx = existingReviews.value.findIndex(r => r.id === reviewId);
    if (idx !== -1) {
      existingReviews.value[idx].resuelto = true;
    }
    
    // Actualizar cache global
    const globalIdx = allReviewsForSimulacro.value.findIndex(r => r.id === reviewId);
    if (globalIdx !== -1) {
      allReviewsForSimulacro.value[globalIdx].resuelto = true;
    }
    
    toast.add({ 
      severity: 'success', 
      summary: 'Revisión resuelta', 
      detail: 'La revisión ha sido marcada como resuelta',
      life: 2000 
    });
    
  } catch (error) {
    console.error('Error resolviendo revisión:', error);
    toast.add({ 
      severity: 'error', 
      summary: 'Error', 
      detail: 'No se pudo marcar como resuelta',
      life: 5000 
    });
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('es-CO', { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const syncDarkModeState = () => {
  isDarkModeActive.value = document.documentElement.classList.contains('dark');
};

const handleHoverMediaChange = (event) => {
  supportsFineHover.value = event.matches;
  if (!event.matches) {
    resetZoomState('context');
    resetZoomState('question');
  }
};

// --- Monitoring Logic ---
let wsMonitor = null;
let reconnectTimer = null;
let themeClassObserver = null;
let hoverMediaQuery = null;

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

const startMonitoring = () => {
    if (!isStudent.value || isReviewMode.value || !authStore.user?.institucion_id) return;
    
    // Función interna para reconectar
    const connect = () => {
        const wsUrl = `${getWsBaseUrl()}/monitoreo/ws/reportar/${authStore.user.institucion_id}`;
        
        console.log("Conectando monitoreo WS...", wsUrl);
        wsMonitor = new WebSocket(wsUrl);
        
        wsMonitor.onopen = () => {
            console.log("Monitoreo activo 🟢");
            if (reconnectTimer) clearTimeout(reconnectTimer); // Limpiar timer si reconectó
        };

        wsMonitor.onclose = () => {
             console.warn("Monitoreo desconectado 🔴. Reconectando en 3s...");
             // Intentar reconectar
             if (reconnectTimer) clearTimeout(reconnectTimer);
             reconnectTimer = setTimeout(connect, 3000);
        };
        
        wsMonitor.onerror = (err) => {
             console.error("Error WS Monitoreo:", err);
             // Onclose se disparará después de error, manejando la reconexión
        };
    };

    connect(); // Iniciar conexión
    
    // Add Listeners
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleBlur);
};

const reportIncident = (type) => {
    if (!wsMonitor || wsMonitor.readyState !== WebSocket.OPEN) return;
    
    // Rate Limiting Simple (Debounce 2s)
    const now = Date.now();
    const last = parseInt(localStorage.getItem('last_incident_time') || '0');
    if (now - last < 2000) return;
    localStorage.setItem('last_incident_time', now.toString());
    
    const payload = {
        tipo: "focus_lost",
        estudiante_id: authStore.user.id,
        estudiante_nombre: userName.value,
        simulacro_id: simulacro.value.id,
        simulacro_titulo: simulacro.value.titulo,
        timestamp: new Date().toISOString()
    };
    
    try {
        wsMonitor.send(JSON.stringify(payload));
    } catch(e) {
        console.error("Error enviando reporte:", e);
    }
    
    toast.add({ 
      severity: 'warn', 
      summary: 'Alerta de Atención', 
      detail: 'El sistema ha detectado que saliste de la pantalla. Esto podría anular tu prueba.',
      life: 5000 
    });
};

const handleVisibilityChange = () => {
    if (document.hidden) {
        reportIncident("visibility_hidden");
    }
};

const handleBlur = () => {
    reportIncident("window_blur");
};

// Clean up
onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
  if (heartbeatInterval) clearInterval(heartbeatInterval);
  if (saveTimeout) clearTimeout(saveTimeout);
  if (reconnectTimer) clearTimeout(reconnectTimer);
  saveProgress();
  
  if (wsMonitor) {
    wsMonitor.onclose = null; // Evitar que intente reconectar al salir
    wsMonitor.close();
  }

  if (themeClassObserver) {
    themeClassObserver.disconnect();
  }

  if (hoverMediaQuery) {
    if (typeof hoverMediaQuery.removeEventListener === 'function') {
      hoverMediaQuery.removeEventListener('change', handleHoverMediaChange);
    } else if (typeof hoverMediaQuery.removeListener === 'function') {
      hoverMediaQuery.removeListener(handleHoverMediaChange);
    }
  }
  
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  window.removeEventListener("blur", handleBlur);
});

// Start monitoring when simulacro is ready
watch(simulacro, (val) => {
    if (val && val.id) {
        startMonitoring();
    }
});

watch(currentQuestionIndex, () => {
  resetZoomState('context');
  resetZoomState('question');
});
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}

.bg-primary {
  background-color: #5a5cf2;
}

.text-primary {
  color: #5a5cf2;
}

.border-primary {
  border-color: #5a5cf2;
}

.ring-primary {
  --tw-ring-color: #5a5cf2;
}

.shadow-primary\/30 {
  --tw-shadow-color: rgba(90, 92, 242, 0.3);
}

.material-symbols-outlined.filled {
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.svg-zoom-wrapper {
  cursor: zoom-in;
}

:deep(.svg-zoom-target svg) {
  transform-origin: var(--zoom-x, 50%) var(--zoom-y, 50%);
  transition: transform 120ms ease-out;
  will-change: transform;
}

:deep(.svg-zoom-target.svg-zoom-target-active svg) {
  transform: scale(1.9);
}
</style>
