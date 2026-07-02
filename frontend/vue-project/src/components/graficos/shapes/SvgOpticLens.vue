<template>
  <g class="svg-optic-lens">
    <!-- Lente Convexa ( ) -->
    <path 
      v-if="type === 'convex'"
      :d="convexPath" 
      fill="#DBEAFE" 
      fill-opacity="0.4"
      stroke="#3B82F6" 
      stroke-width="1.5" 
    />

    <!-- Lente Cóncava )( -->
    <path 
      v-else
      :d="concavePath" 
      fill="#DBEAFE" 
      fill-opacity="0.4"
      stroke="#3B82F6" 
      stroke-width="1.5" 
    />

    <!-- Eje Óptico (Línea central punteada) -->
    <line 
      :x1="cx - width" 
      :y1="cy" 
      :x2="cx + width" 
      :y2="cy" 
      stroke="#9CA3AF" 
      stroke-width="1" 
      stroke-dasharray="4 2"
    />

    <!-- Focos (F y F') -->
    <circle :cx="cx - focalLength" :cy="cy" r="2" fill="#374151" />
    <text :x="cx - focalLength" :y="cy + 15" font-size="10" text-anchor="middle">F</text>
    
    <circle :cx="cx + focalLength" :cy="cy" r="2" fill="#374151" />
    <text :x="cx + focalLength" :y="cy + 15" font-size="10" text-anchor="middle">F'</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  cx: { type: Number, required: true },
  cy: { type: Number, required: true },
  height: { type: Number, default: 80 },  // Altura total de la lente
  width: { type: Number, default: 20 },   // Grosor máximo
  type: { type: String, default: 'convex' }, // 'convex' | 'concave'
  focalLength: { type: Number, default: 40 }
});

const convexPath = computed(() => {
  // Arco cuadrático para simular curvatura
  // Start Top
  const topY = props.cy - props.height/2;
  const bottomY = props.cy + props.height/2;
  
  return `
    M ${props.cx} ${topY}
    Q ${props.cx + props.width} ${props.cy} ${props.cx} ${bottomY}
    Q ${props.cx - props.width} ${props.cy} ${props.cx} ${topY}
    Z
  `;
});

const concavePath = computed(() => {
  const topY = props.cy - props.height/2;
  const bottomY = props.cy + props.height/2;
  const w = props.width / 2; // Semiancho
  
  return `
    M ${props.cx - w} ${topY}
    L ${props.cx + w} ${topY}
    Q ${props.cx} ${props.cy} ${props.cx + w} ${bottomY}
    L ${props.cx - w} ${bottomY}
    Q ${props.cx} ${props.cy} ${props.cx - w} ${topY}
    Z
  `;
});
</script>
