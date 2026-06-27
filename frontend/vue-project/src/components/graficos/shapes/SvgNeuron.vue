<template>
  <g class="svg-neuron">
    <!-- Axón (Línea larga) -->
    <path 
      :d="`M ${x} ${y} Q ${x + length*0.3} ${y + 20} ${x + length} ${y}`" 
      fill="none" 
      stroke="#F59E0B" 
      stroke-width="4"
    />
    
    <!-- Vaina de Mielina (Segmentos sobre el axón) -->
    <rect :x="x + length*0.2" :y="y - 3" width="20" height="8" rx="2" fill="#FEF3C7" stroke="#D97706" transform="rotate(5)" />
    <rect :x="x + length*0.4" :y="y + 2" width="20" height="8" rx="2" fill="#FEF3C7" stroke="#D97706" transform="rotate(-2)" />
    <rect :x="x + length*0.6" :y="y - 1" width="20" height="8" rx="2" fill="#FEF3C7" stroke="#D97706" />

    <!-- Soma (Cuerpo celular - Estrella irregular) -->
    <path 
      :d="somaPath" 
      fill="#FBBF24" 
      stroke="#D97706" 
      stroke-width="2"
    />
    
    <!-- Núcleo -->
    <circle :cx="x" :cy="y" r="8" fill="#FFFBEB" stroke="#D97706" />

    <!-- Dendritas (Líneas radiantes) -->
    <g stroke="#D97706" stroke-width="1.5" fill="none">
        <path :d="`M ${x-15} ${y-10} l -10 -15 l -5 5 m 5 -5 l 5 -5`" />
        <path :d="`M ${x-15} ${y+10} l -15 10 l -2 8`" />
        <path :d="`M ${x} ${y-18} l 0 -20 l 5 -5 m -5 5 l -5 -5`" />
    </g>

    <!-- Terminal Axónico (Ramificaciones finales) -->
    <g :transform="`translate(${x + length}, ${y})`" stroke="#D97706" stroke-width="1.5">
       <path d="M 0 0 l 10 -10" />
       <path d="M 0 0 l 12 0" />
       <path d="M 0 0 l 10 10" />
       <circle cx="10" cy="-10" r="2" fill="#D97706" />
       <circle cx="12" cy="0" r="2" fill="#D97706" />
       <circle cx="10" cy="10" r="2" fill="#D97706" />
    </g>

    <text v-if="label" :x="x" :y="y + 40" text-anchor="middle" font-size="12" fill="#374151">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  length: { type: Number, default: 150 }, // Largo del axón hacia la derecha
  label: { type: String, default: '' }
});

const somaPath = computed(() => {
  // Forma de estrella suavizada centrada en x,y
  return `
    M ${props.x-20} ${props.y} 
    Q ${props.x-10} ${props.y-10} ${props.x} ${props.y-20}
    Q ${props.x+10} ${props.y-10} ${props.x+15} ${props.y-5}
    L ${props.x} ${props.y} Z
  `.replace('L', '').replace('Z', '') + 
  ` C ${props.x+20} ${props.y} ${props.x+10} ${props.y+20} ${props.x} ${props.y+20}
    Q ${props.x-10} ${props.y+10} ${props.x-20} ${props.y} Z`; 
    // Simplified logic: drawing a blob
});
</script>
