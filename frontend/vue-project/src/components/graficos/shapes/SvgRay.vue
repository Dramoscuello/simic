<template>
  <g class="svg-ray">
    <!-- Línea principal -->
    <line 
      :x1="x1" :y1="y1" 
      :x2="x2" :y2="y2" 
      stroke="#F59E0B" 
      stroke-width="1.5" 
    />
    
    <!-- Flecha direccional en el medio -->
    <path 
      :d="arrowHeadPath" 
      fill="#F59E0B"
    />
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x1: { type: Number, required: true },
  y1: { type: Number, required: true },
  x2: { type: Number, required: true },
  y2: { type: Number, required: true }
});

const arrowHeadPath = computed(() => {
  // Calcular punto medio
  const mx = (props.x1 + props.x2) / 2;
  const my = (props.y1 + props.y2) / 2;
  
  // Calcular ángulo
  const angle = Math.atan2(props.y2 - props.y1, props.x2 - props.x1);
  
  // Tamaño flecha
  const size = 6;
  
  // Vértices del triángulo (rotados)
  const tipX = mx + Math.cos(angle) * size;
  const tipY = my + Math.sin(angle) * size;
  
  const base1X = mx + Math.cos(angle + 2.5) * size;
  const base1Y = my + Math.sin(angle + 2.5) * size;
  
  const base2X = mx + Math.cos(angle - 2.5) * size;
  const base2Y = my + Math.sin(angle - 2.5) * size;
  
  return `M ${tipX} ${tipY} L ${base1X} ${base1Y} L ${base2X} ${base2Y} Z`;
});
</script>
