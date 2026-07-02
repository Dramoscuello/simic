<template>
  <div 
     class="bg-white dark:bg-slate-700/30 border border-slate-100 dark:border-slate-600 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer group relative overflow-hidden"
     :class="borderLeftClass"
     @click="$emit('click')"
  >
     <div class="flex justify-between items-start mb-2 pl-1">
         <div class="flex items-center gap-2">
             <span v-if="fraude" class="material-icons-round text-rose-500 animate-pulse text-[18px]">gavel</span>
             <span v-else class="material-icons-round text-slate-400 group-hover:text-primary transition-colors text-[18px]">{{ icon }}</span>
             
             <span v-if="fraude" class="text-xs font-bold text-rose-600 bg-rose-100 px-1.5 rounded dark:text-rose-300 dark:bg-rose-900/50">FRAUDE</span>
             <span v-else class="text-xs font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider">{{ badge || (tags && tags[0]) || 'Reporte' }}</span>
         </div>
         <span class="text-[10px] text-slate-400 whitespace-nowrap">{{ formatDate(date) }}</span>
     </div>

     <div class="pl-1">
         <h4 class="font-bold text-slate-700 dark:text-slate-200 text-sm leading-tight group-hover:text-primary transition-colors mb-1">{{ title }}</h4>
         <p class="text-xs text-slate-500 dark:text-slate-400 mb-2 line-clamp-1">{{ subtitle }}</p>
         
         <div class="flex items-center gap-2 mt-auto">
             <span v-if="score !== undefined && score !== null" :class="getScoreClass(score)" class="text-xs font-bold px-1.5 py-0.5 rounded">
                 {{ score.toFixed(1) }}%
             </span>
             <div class="flex gap-1 flex-wrap">
                 <span v-for="tag in (tags ? tags.slice(1) : [])" :key="tag" class="text-[10px] px-1.5 py-0.5 bg-slate-100 dark:bg-slate-600/50 text-slate-500 dark:text-slate-300 rounded">
                     {{ tag }}
                 </span>
             </div>
         </div>
     </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/es';
dayjs.extend(relativeTime);
dayjs.locale('es');

const props = defineProps({
    title: String,
    subtitle: String,
    date: [String, Date],
    score: Number,
    tags: Array,
    badge: String,
    icon: String,
    fraude: Boolean, // Nueva prop
    color: {
        type: String,
        default: 'indigo'
    }
});

defineEmits(['click']);

const formatDate = (date) => {
    if (!date) return '';
    return dayjs(date).fromNow();
};

const borderLeftClass = computed(() => {
    if (props.fraude) return 'border-l-4 border-l-rose-500 bg-rose-50/50 dark:bg-rose-900/10'; // Rojo si es Fraude
    
    const map = {
        'blue': 'border-l-4 border-l-blue-500',

        'indigo': 'border-l-4 border-l-indigo-500',
        'emerald': 'border-l-4 border-l-emerald-500',
        'purple': 'border-l-4 border-l-purple-500'
    };
    return map[props.color] || 'border-l-4 border-l-slate-300';
});

const getScoreClass = (s) => {
    if (s >= 80) return 'text-emerald-700 bg-emerald-100 dark:bg-emerald-900/40 dark:text-emerald-300';
    if (s >= 60) return 'text-amber-700 bg-amber-100 dark:bg-amber-900/40 dark:text-amber-300';
    return 'text-red-700 bg-red-100 dark:bg-red-900/40 dark:text-red-300';
};
</script>
