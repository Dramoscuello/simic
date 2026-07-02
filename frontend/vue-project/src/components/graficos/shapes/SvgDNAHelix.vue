<template>
  <g class="svg-dna-helix">
    <!-- Doble Helice simplificada con ondas -->
    <path 
      :d="strand1Path" 
      fill="none" 
      stroke="#3B82F6" 
      stroke-width="3"
    />
    <path 
      :d="strand2Path" 
      fill="none" 
      stroke="#60A5FA" 
      stroke-width="3"
    />

    <!-- Peldaños (Bases Nitrogenadas) -->
    <!-- Dibujamos líneas horizontales donde las ondas se cruzan o separan -->
    <line 
      v-for="i in stepsCount" 
      :key="i"
      :x1="getX1(i)" 
      :y1="getY(i)" 
      :x2="getX2(i)" 
      :y2="getY(i)" 
      stroke="#9CA3AF" 
      stroke-width="1.5"
      stroke-linecap="round"
    />
    
    <text v-if="label" :x="x + width/2" :y="y + height + 15" text-anchor="middle" font-size="12">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  width: { type: Number, default: 60 },  // Ancho total de la hélice
  height: { type: Number, default: 200 }, // Largo vertical
  label: { type: String, default: 'ADN' }
});

const loops = 3;
const stepsCount = 12;

// Generar path senoidal vertical
const generateStrand = (offsetPhase) => {
  const points = [];
  const steps = 50;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps; // 0 a 1
    const py = props.y + t * props.height;
    // Onda: x base + amplitud * sin(frecuencia * t + fase)
    const angle = t * loops * 2 * Math.PI + offsetPhase;
    const px = props.x + (props.width/2) + (props.width/2) * Math.sin(angle);
    points.push(`${i===0?'M':'L'} ${px.toFixed(1)} ${py.toFixed(1)}`);
  }
  return points.join(' ');
};

const strand1Path = computed(() => generateStrand(0));
const strand2Path = computed(() => generateStrand(Math.PI)); // Desfase 180 grados

// Calcular posiciones de los peldaños
const getY = (i) => props.y + (i / stepsCount) * props.height;
const getX1 = (i) => {
  const t = i / stepsCount;
  const angle = t * loops * 2 * Math.PI;
  return props.x + (props.width/2) + (props.width/2) * Math.sin(angle) * 0.8; // 0.8 para no tocar el borde exacto
};
const getX2 = (i) => {
  const t = i / stepsCount;
  const angle = t * loops * 2 * Math.PI + Math.PI;
  return props.x + (props.width/2) + (props.width/2) * Math.sin(angle) * 0.8;
};
</script>
