<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-4">
    <div class="max-w-md w-full bg-white dark:bg-slate-800 rounded-3xl shadow-xl overflow-hidden border border-slate-100 dark:border-slate-700 text-center p-12">
      
      <!-- Success Animation -->
      <div class="mb-8 relative flex justify-center">
        <div class="absolute inset-0 bg-emerald-100 dark:bg-emerald-900/30 rounded-full scale-150 animate-pulse opacity-50"></div>
        <div class="relative bg-emerald-500 text-white w-24 h-24 rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/40">
           <span class="material-icons-round text-5xl">check_circle</span>
        </div>
      </div>
      
      <h1 class="text-3xl font-bold text-slate-800 dark:text-white mb-3">¡Simulacro Finalizado!</h1>
      <p class="text-slate-500 dark:text-slate-400 text-lg mb-8 leading-relaxed">
        Tus respuestas han sido enviadas correctamente. Estamos procesando tus resultados.
      </p>
      
      <div class="bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 py-3 px-6 rounded-full inline-flex items-center gap-2 text-sm font-medium animate-bounce mx-auto">
        <span class="material-icons-round text-base">hourglass_empty</span>
        Volviendo al listado en 3 segundos...
      </div>
      
      <div class="mt-8 pt-8 border-t border-slate-100 dark:border-slate-700">
         <p class="text-slate-400 dark:text-slate-500 text-sm">¿No redirige?</p>
         <router-link to="/simulacros" class="text-primary dark:text-primary-400 font-bold hover:underline mt-1 inline-block">
            Haz clic aquí
         </router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(() => {
  setTimeout(() => {
    router.push('/simulacros');
  }, 3000);
});
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
</style>
