<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-4">
    <div class="max-w-2xl w-full bg-white dark:bg-slate-800 rounded-3xl shadow-xl overflow-hidden border border-slate-100 dark:border-slate-700">
      <!-- Header -->
      <div class="bg-gradient-to-br from-primary to-indigo-700 p-10 text-white relative overflow-hidden">
        <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl"></div>
        <div class="relative z-10 text-center">
          <div class="mx-auto bg-white/20 w-16 h-16 rounded-2xl flex items-center justify-center mb-6 backdrop-blur-sm border border-white/30">
            <span class="material-icons-round text-3xl">menu_book</span>
          </div>
          <h1 class="text-3xl font-bold mb-2 tracking-tight">Instrucciones del examen</h1>
          <p class="text-indigo-100 font-medium">Por favor lee atentamente antes de iniciar</p>
        </div>
      </div>

      <!-- Content -->
      <div class="p-8 space-y-8">
        <div class="grid gap-6">
          <div class="flex gap-4 items-start">
            <div class="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0 mt-1">
              <span class="material-icons-round">timer</span>
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white">Tiempo limitado</h3>
              <p class="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mt-1">
                El examen tiene una duración definida. Un cronómetro en pantalla te indicará el tiempo restante. Si el tiempo termina, el examen se enviará automáticamente.
              </p>
            </div>
          </div>

          <div class="flex gap-4 items-start">
            <div class="w-10 h-10 rounded-full bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0 mt-1">
              <span class="material-icons-round">check_circle</span>
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white">Selección única</h3>
              <p class="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mt-1">
                Cada pregunta tiene solo una respuesta correcta. Asegúrate de seleccionar la opción que consideres más adecuada.
              </p>
            </div>
          </div>

          <div class="flex gap-4 items-start">
            <div class="w-10 h-10 rounded-full bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center justify-center flex-shrink-0 mt-1">
              <span class="material-icons-round">save</span>
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white">Guardado automático</h3>
              <p class="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mt-1">
                Tus respuestas se guardan temporalmente mientras avanzas. Sin embargo, debes presionar "Finalizar" para enviar tu examen.
              </p>
            </div>
          </div>
          
          <div class="flex gap-4 items-start">
            <div class="w-10 h-10 rounded-full bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 flex items-center justify-center flex-shrink-0 mt-1">
              <span class="material-icons-round">wifi</span>
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white">Conexión estable</h3>
              <p class="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mt-1">
                Asegúrate de tener una conexión a internet estable. Evita recargar la página durante el examen.
              </p>
            </div>
          </div>
        </div>

        <div class="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-300 flex gap-3">
          <span class="material-icons-round text-slate-400 dark:text-slate-500">info</span>
          <p>Al hacer clic en "Comenzar examen", aceptas haber leído y entendido estas instrucciones. El tiempo empezará a correr inmediatamente.</p>
        </div>
      </div>

      <!-- Actions -->
      <div class="p-8 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row gap-4 justify-between items-center">
        <router-link 
          to="/simulacros" 
          class="text-slate-500 dark:text-slate-400 font-medium hover:text-slate-800 dark:hover:text-white transition-colors py-2 px-4"
        >
          Cancelar y volver
        </router-link>
        
        <router-link 
          :to="`/simulacros/${route.params.id}/presentar`"
          class="w-full sm:w-auto bg-primary hover:bg-indigo-600 border border-transparent dark:border-indigo-500 text-white font-bold py-3.5 px-8 rounded-xl shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:-webkit-transform-y-0.5 transition-all flex items-center justify-center gap-2 group"
        >
          <span>Comenzar examen</span>
          <span class="material-icons-round group-hover:translate-x-1 transition-transform">arrow_forward</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router';

const route = useRoute();
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}
.bg-primary {
  background-color: #6366f1;
}
</style>
