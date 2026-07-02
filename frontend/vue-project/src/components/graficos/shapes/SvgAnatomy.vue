<template>
  <g class="svg-anatomy" :transform="`translate(${x}, ${y}) scale(${scale})`">
    
    <!-- ============================================= -->
    <!-- ZONA PARA PEGAR TUS SVGs DE FLATICON          -->
    <!-- Copia el contenido interno del SVG descagado  -->
    <!-- y pégalo dentro del v-if correspondiente.     -->
    <!-- Aseguraté de ajustar el 'scale' si es gigante -->
    <!-- ============================================= -->

    <!-- CORAZÓN (Heart) -->
    <g v-if="part === 'heart'">
       <!-- Placeholder: Un corazón simple dibujado con código -->
       <path 
         d="M 0 -10 C -20 -30 -40 10 0 30 C 40 10 20 -30 0 -10" 
         fill="#F87171" 
         stroke="#B91C1C"
         stroke-width="2"
       />
       <!-- AQUI PEGARÍAS EL PATH COMPLEJO DE FLATICON -->
       <!-- <path d="M... codigo gigante ..." fill="..." /> -->
    </g>

    <!-- PULMONES (Lungs) -->
    <g v-if="part === 'lungs'">
       <!-- Placeholder: Dos óvalos rosas -->
       <ellipse cx="-15" cy="0" rx="12" ry="20" fill="#FBCFE8" stroke="#DB2777" />
       <ellipse cx="15" cy="0" rx="12" ry="20" fill="#FBCFE8" stroke="#DB2777" />
       <!-- Traquea -->
       <rect x="-3" y="-30" width="6" height="15" fill="#E5E7EB" />
    </g>

    <!-- SISTEMA DIGESTIVO (Digestive) -->
    <g v-if="part === 'digestive'">
       <!-- Placeholder -->
       <path d="M -10 -20 Q 0 0 10 -20 L 10 20 L -10 20 Z" fill="#FEF08A" stroke="#EAB308" />
    </g>

    <text v-if="label" :x="0" :y="40" text-anchor="middle" font-size="12">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true }, // Centro X
  y: { type: Number, required: true }, // Centro Y
  part: { type: String, default: 'heart' }, // 'heart' | 'lungs' | 'digestive'
  width: { type: Number, default: 50 }, // Ancho objetivo aproximado (para calcular escala)
  label: { type: String, default: '' }
});

// Calculamos una escala simple basada en un tamaño base asumido de 50px
// Si pegas un SVG de Flaticon que mide 512px, tendrás que ajustar este divisor.
const scale = computed(() => {
    return props.width / 50; 
});
</script>
