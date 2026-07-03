<template>
  <g class="svg-wave">
    <path 
      :d="wavePath" 
      fill="none" 
      :stroke="color" 
      stroke-width="2"
    />
    
    <!-- Línea de equilibrio -->
    <line 
      :x1="x1" :y1="y1" 
      :x2="x2" :y2="y2" 
      stroke="#9CA3AF" 
      stroke-width="1"
      stroke-dasharray="4 2"
    />
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x1: { type: Number, required: true },
  y1: { type: Number, required: true },
  x2: { type: Number, required: true },
  y2: { type: Number, required: true },
  amplitude: { type: Number, default: 20 },
  wavelength: { type: Number, default: 40 }, // Lambda (longitud de onda) en px
  color: { type: String, default: '#3B82F6' },
  phase: { type: Number, default: 0 } // Desfase en radianes
});

const wavePath = computed(() => {
  const steps = 100; // Resolución
  const dx = props.x2 - props.x1;
  const dy = props.y2 - props.y1;
  const length = Math.hypot(dx, dy);
  const angle = Math.atan2(dy, dx);
  
  const points = [];
  
  for (let i = 0; i <= steps; i++) {
    const t = i / steps; // 0 a 1
    const dist = t * length; // Distancia recorrida en el eje
    
    // Cálculo de la onda sinusoidal pura
    const waveY = props.amplitude * Math.sin((2 * Math.PI * dist / props.wavelength) + props.phase);
    
    // Transformar al plano rotado
    // Coordenada base en la línea
    const bx = props.x1 + dx * t;
    const by = props.y1 + dy * t;
    
    // Vector perpendicular (-sin, cos)
    const px = bx - Math.sin(angle) * waveY;
    const py = by + Math.cos(angle) * waveY;
    
    // Comando SVG
    const cmd = i === 0 ? 'M' : 'L';
    points.push(`${cmd} ${px.toFixed(2)} ${py.toFixed(2)}`);
  }
  
  return points.join(' ');
});
</script>
