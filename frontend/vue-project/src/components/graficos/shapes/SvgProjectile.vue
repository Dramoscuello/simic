<template>
  <g class="svg-projectile">
    <!-- Ejes (opcional) -->
    <line v-if="showAxes" :x1="x1" :y1="y1" :x2="x2 + 20" :y2="y1" stroke="#374151" stroke-width="1" /> <!-- X -->
    <line v-if="showAxes" :x1="x1" :y1="y1" :x2="x1" :y2="peakY - 20" stroke="#374151" stroke-width="1" /> <!-- Y -->

    <!-- Trayectoria Parabólica -->
    <path 
      :d="parabolaPath" 
      fill="none" 
      stroke="#6B7280" 
      stroke-width="1.5" 
      stroke-dasharray="4 2" 
    />

    <!-- Proyectil en posición específica (t=0, t=mid, t=end?) -->
    <!-- Dibujamos 3 puntos clave: inicio, pico, fin -->
    <circle :cx="x1" :cy="y1" r="3" fill="#1F2937" />
    <circle :cx="midX" :cy="peakY" r="3" fill="#1F2937" />
    <circle :cx="x2" :cy="y1" r="3" fill="#1F2937" />
    
    <!-- Vector Velocidad Inicial -->
    <g v-if="v0">
       <line :x1="x1" :y1="y1" :x2="x1 + 30" :y2="y1 - 30" stroke="#EF4444" stroke-width="2" marker-end="url(#arrowhead-red)" />
       <text :x="x1 + 35" :y="y1 - 35" fill="#EF4444" font-size="12">v0</text>
    </g>

    <text v-if="label" :x="midX" :y="peakY - 10" text-anchor="middle" font-size="12">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x1: { type: Number, required: true }, // Inicio (suelo)
  y1: { type: Number, required: true },
  x2: { type: Number, required: true }, // Fin (suelo)
  peakHeight: { type: Number, default: 50 }, // Altura máxima (h)
  showAxes: { type: Boolean, default: true },
  v0: { type: Boolean, default: true },
  label: { type: String, default: '' }
});

const midX = computed(() => (props.x1 + props.x2) / 2);
const peakY = computed(() => props.y1 - props.peakHeight);

const parabolaPath = computed(() => {
  // Curva cuadrática Bezier desde P1 a P2 usando un punto de control
  // Para una parábola perfecta, el punto de control de una Quadratic Bezier debe estar en (midX, peakY * 2 - startY) math magic?
  // Simplificación: Q ControlPoint EndPoint.
  // El control point debe estar al doble de la altura para que la curva pase por peakHeight a la mitad.
  const cpY = props.y1 - 2 * props.peakHeight;
  
  return `M ${props.x1} ${props.y1} Q ${midX.value} ${cpY} ${props.x2} ${props.y1}`;
});
</script>
