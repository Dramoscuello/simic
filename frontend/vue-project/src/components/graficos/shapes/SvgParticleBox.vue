<template>
  <g class="svg-particle-box">
    <!-- Contenedor -->
    <rect 
      :x="x" :y="y" 
      :width="width" :height="height" 
      fill="none" 
      stroke="#374151" 
      stroke-width="2" 
    />
    
    <!-- Partículas -->
    <circle 
      v-for="(pos, i) in particles" 
      :key="i"
      :cx="pos.cx" 
      :cy="pos.cy" 
      :r="particleSize" 
      :fill="color"
    />
    
    <!-- Etiqueta opcional -->
    <text v-if="label" :x="x + width/2" :y="y - 8" text-anchor="middle" font-size="12" fill="#374151">
      {{ label }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  width: { type: Number, default: 100 },
  height: { type: Number, default: 100 },
  count: { type: Number, default: 20 },
  particleSize: { type: Number, default: 3 },
  color: { type: String, default: '#374151' },
  label: { type: String, default: '' }
});

// Generador Determinístico de Números Pseudo-Aleatorios (LCG simple)
// Esto asegura que las partículas siempre aparezcan en el mismo lugar para la misma pregunta.
const seededRandom = (seed) => {
  const m = 2 ** 35 - 31;
  const a = 185852;
  let s = seed % m;
  return () => {
    s = (s * a) % m;
    return s / m;
  };
};

const particles = computed(() => {
  // Usamos x+y como semilla base para que cajas en distinta posición tengan distinta distribución
  const rng = seededRandom(Math.round(props.x + props.y + props.count));
  const pts = [];
  const padding = props.particleSize + 2;
  
  for (let i = 0; i < props.count; i++) {
    pts.push({
      cx: props.x + padding + (rng() * (props.width - 2 * padding)),
      cy: props.y + padding + (rng() * (props.height - 2 * padding))
    });
  }
  return pts;
});
</script>
