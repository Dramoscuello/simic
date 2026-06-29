<template>
  <g :transform="transformString">
    <!-- Bloque Principal -->
    <rect 
      :x="-width/2" 
      :y="-height/2" 
      :width="width" 
      :height="height" 
      fill="#E5E7EB" 
      stroke="#374151" 
      stroke-width="2"
    />
    
    <!-- Centro de Masa (Punto) -->
    <circle 
      v-if="showCM" 
      cx="0" 
      cy="0" 
      r="3" 
      fill="#374151" 
    />

    <!-- Etiqueta (m, M, 5kg) -->
    <text 
      v-if="label" 
      x="0" 
      y="5" 
      text-anchor="middle" 
      font-weight="bold" 
      font-size="14" 
      fill="#1F2937"
    >
      {{ label }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true }, // Centro X
  y: { type: Number, required: true }, // Centro Y
  width: { type: Number, default: 50 },
  height: { type: Number, default: 50 },
  rotation: { type: Number, default: 0 }, // Grados
  label: { type: String, default: '' },
  showCM: { type: Boolean, default: true } // Mostrar Centro de Masa
});

const transformString = computed(() => {
  return `translate(${props.x}, ${props.y}) rotate(${props.rotation})`;
});
</script>
