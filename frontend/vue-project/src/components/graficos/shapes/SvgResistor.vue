<template>
  <g class="svg-resistor">
    <!-- Línea de entrada -->
    <line 
      :x1="x1" :y1="y1" 
      :x2="startZigZag.x" :y2="startZigZag.y" 
      stroke="#374151" stroke-width="2" 
    />
    
    <!-- El Zig Zag -->
    <polyline 
      :points="zigZagPoints" 
      fill="none" 
      stroke="#374151" 
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />

    <!-- Línea de salida -->
    <line 
      :x1="endZigZag.x" :y1="endZigZag.y" 
      :x2="x2" :y2="y2" 
      stroke="#374151" stroke-width="2" 
    />
    
    <!-- Etiqueta opcional (R1, 10Ω) -->
    <text 
      v-if="label"
      :x="midX" 
      :y="midY - 15" 
      text-anchor="middle" 
      font-size="12" 
      fill="#374151"
      font-weight="bold"
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
  x2: { type: Number, required: true },
  y2: { type: Number, required: true },
  label: { type: String, default: '' }
});

// Lógica geométrica para dibujar un Resistor entre (x1,y1) y (x2,y2)
const length = computed(() => Math.hypot(props.x2 - props.x1, props.y2 - props.y1));
const angle = computed(() => Math.atan2(props.y2 - props.y1, props.x2 - props.x1));

const midX = computed(() => (props.x1 + props.x2) / 2);
const midY = computed(() => (props.y1 + props.y2) / 2);

// Configuración del zig-zag
const zigZagLength = 40; // Largo total de la parte rizada
const spikes = 6;        // Número de picos
const height = 10;       // Altura de los picos

// Puntos de inicio y fin del zig-zag (centrado en la línea)
const startZigZag = computed(() => {
  const t = (length.value - zigZagLength) / 2 / length.value;
  return {
    x: props.x1 + (props.x2 - props.x1) * t,
    y: props.y1 + (props.y2 - props.y1) * t
  };
});

const endZigZag = computed(() => {
  const t = (length.value + zigZagLength) / 2 / length.value;
  return {
    x: props.x1 + (props.x2 - props.x1) * t,
    y: props.y1 + (props.y2 - props.y1) * t
  };
});

// Generar los puntos del zig-zag
const zigZagPoints = computed(() => {
  const points = [];
  const ux = Math.cos(angle.value);
  const uy = Math.sin(angle.value);
  const vx = -uy; // Vector perpendicular
  const vy = ux;

  // Punto inicial
  points.push(`${startZigZag.value.x},${startZigZag.value.y}`);

  for (let i = 0; i <= spikes; i++) {
    const progress = i / spikes; // 0 a 1
    // Alternar arriba y abajo (0, 1, -1, 1, -1, 0)
    let offset = 0;
    if (i > 0 && i < spikes) {
        offset = (i % 2 === 0) ? -height : height;
    }
    
    // Posición en la línea base
    const bx = startZigZag.value.x + (endZigZag.value.x - startZigZag.value.x) * progress;
    const by = startZigZag.value.y + (endZigZag.value.y - startZigZag.value.y) * progress;
    
    // Aplicar desplazamiento perpendicular
    const px = bx + vx * offset;
    const py = by + vy * offset;
    
    points.push(`${px},${py}`);
  }
  
  return points.join(" ");
});
</script>
