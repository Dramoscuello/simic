<template>
  <div class="flex flex-col bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 h-full overflow-hidden">
     <!-- Header -->
     <div class="p-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/50">
         <div class="flex items-center gap-2">
             <div :class="iconBgClass">
                 <span class="material-icons-round text-[20px]">{{ icon }}</span>
             </div>
             <h3 class="font-bold text-slate-800 dark:text-white">{{ title }}</h3>
         </div>
         <span class="text-xs font-medium px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-slate-500">{{ items.length }}</span>
     </div>

     <!-- Content -->
     <div class="flex-1 overflow-y-auto p-4 space-y-3 min-h-[300px]">
         <div v-if="loading" class="flex flex-col items-center justify-center h-full py-10 opacity-50">
             <span class="animate-spin rounded-full h-8 w-8 border-2 border-slate-300 border-t-blue-500"></span>
         </div>
         <div v-else-if="items.length === 0" class="flex flex-col items-center justify-center h-full py-10 text-slate-400">
             <span class="material-icons-round text-4xl mb-2 opacity-20">inbox</span>
             <span class="text-sm">No hay reportes recientes</span>
         </div>
         <template v-else>
             <div v-for="item in items" :key="item.id">
                 <slot name="item" :item="item"></slot>
             </div>
         </template>
     </div>

     <!-- Footer -->
     <div class="p-3 border-t border-slate-100 dark:border-slate-700 bg-slate-50/30 dark:bg-slate-800/30">
         <button 
            @click="$emit('view-history')"
            class="w-full py-2 text-sm font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white transition-colors flex items-center justify-center gap-1 group"
         >
             Ver Histórico
             <span class="material-icons-round text-[16px] group-hover:translate-x-1 transition-transform">arrow_forward</span>
         </button>
     </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
    title: String,
    icon: String,
    color: {
        type: String,
        default: 'blue' 
    },
    items: {
        type: Array,
        default: () => []
    },
    loading: Boolean
});

defineEmits(['view-history']);

// Tailwind CSS no interpolar strings dinámicas completas,
// es mejor mapear clases estáticas si se usa JIT/Purge
const iconBgClass = computed(() => {
    const map = {
        'blue': 'p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
        'indigo': 'p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
        'emerald': 'p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
        'purple': 'p-1.5 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
    };
    return map[props.color] || map['blue'];
});
</script>
