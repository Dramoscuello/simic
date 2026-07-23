<template>
  <g class="svg-force-vector">
    <!-- El vector en sí -->
    <line 
      :x1="x1" :y1="y1" 
      :x2="x2" :y2="y2" 
      :stroke="color" 
      stroke-width="2.5" 
      :marker-end="`url(#arrowhead-${colorName})`"
    />
    
    <!-- Etiqueta Inteligente -->
    <text 
      v-if="label"
      :x="labelPos.x" 
      :y="labelPos.y" 
      :fill="color"
      font-weight="bold"
      font-size="14"
      text-anchor="middle"
      dominant-baseline="middle"
    >
      {{ label }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x1: { type: Number, required: true },
  y1: { type: Number, required: true },
  x2: { type: Number, required: true }, // Punta
  y2: { type: Number, required: true }, // Punta
  label: { type: String, default: '' },
  color: { type: String, default: 'red' } // 'red', 'blue', 'black'
});

const colorName = computed(() => {
    if (props.color === '#EF4444' || props.color === 'red') return 'red';
    if (props.color === '#3B82F6' || props.color === 'blue') return 'blue';
    return ''; // default gray/black
});

// Calcula dónde poner la etiqueta para que no tape la flecha
// (La pone un poco más allá de la punta o al lado)
const labelPos = computed(() => {
  const dx = props.x2 - props.x1;
  const dy = props.y2 - props.y1;
  const len = Math.hypot(dx, dy);
  
  if (len === 0) return { x: props.x2, y: props.y2 };

  // Offset perpendicular de 15px
  const perpX = -dy / len * 15;
  const perpY = dx / len * 15;
  
  // Punto medio
  const midX = (props.x1 + props.x2) / 2;
  const midY = (props.y1 + props.y2) / 2;
  
  return { 
    x: midX + perpX, 
    y: midY + perpY 
  };
});
</script>
