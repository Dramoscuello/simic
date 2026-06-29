<template>
  <g class="svg-spring" :transform="`rotate(${rotation}, ${x1}, ${y1})`">
    <!-- Un resorte es una serie de bucles helicoidales -->
    <path 
      :d="springPath" 
      fill="none" 
      stroke="#4B5563" 
      stroke-width="2"
      stroke-linejoin="round"
    />
    
    <!-- Etiquetas opcionales -->
    <text v-if="label" :x="midX" :y="-width/2 - 5" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(0)">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x1: { type: Number, required: true },
  y1: { type: Number, required: true },
  length: { type: Number, default: 100 }, // Longitud de extensión
  width: { type: Number, default: 20 },   // Ancho del resorte
  rotation: { type: Number, default: 0 }, // Rotación en grados
  coils: { type: Number, default: 8 },    // Número de vueltas
  label: { type: String, default: '' }
});

const midX = computed(() => props.length / 2);

const springPath = computed(() => {
  const l = props.length;
  const w = props.width;
  const n = props.coils;
  
  // Dibujamos horizontalmente desde (0,0) a (length, 0) y luego el <g> rota todo.
  
  let d = `M 0 0 L 10 0 `; // Segmento inicial recto
  
  const step = (l - 20) / n; // Espacio para espirales (quitando segmentos rectos inicio/fin)
  
  for (let i = 0; i < n; i++) {
    const startX = 10 + i * step;
    // ZigZag tipo resorte: Arriba, luego Abajo
    d += `L ${startX + step*0.25} ${-w/2} `;
    d += `L ${startX + step*0.75} ${w/2} `;
  }
  
  d += `L ${l - 10} 0 L ${l} 0`; // Segmento final recto y cierre
  
  return d;
});
</script>
