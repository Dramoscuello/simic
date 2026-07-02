<template>
  <g class="svg-meter">
    <!-- Círculo del instrumento -->
    <circle 
      :cx="x" :cy="y" 
      :r="radius" 
      fill="#F9FAFB" 
      stroke="#374151" 
      stroke-width="2" 
    />
    
    <!-- Símbolo (A, V, G) -->
    <text 
      :x="x" :y="y" 
      text-anchor="middle" 
      dominant-baseline="central" 
      font-size="18" 
      font-weight="bold" 
      fill="#374151"
    >
      {{ type }}
    </text>

    <!-- Aguja (si es analógico visualmente) -->
    <line 
       v-if="reading !== null"
       :x1="x" :y1="y + 10" 
       :x2="needleTip.x" :y2="needleTip.y" 
       stroke="#EF4444" 
       stroke-width="1.5"
    />

    <!-- Conectores laterales (cables) -->
    <line :x1="x - radius" :y1="y" :x2="x - radius - 10" :y2="y" stroke="#374151" stroke-width="2" />
    <line :x1="x + radius" :y1="y" :x2="x + radius + 10" :y2="y" stroke="#374151" stroke-width="2" />
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  type: { type: String, default: 'V' }, // 'V', 'A', 'Ω'
  radius: { type: Number, default: 20 },
  reading: { type: Number, default: null } // 0 a 100% de escala (ángulo)
});

const needleTip = computed(() => {
    // Escala de -45 a +45 grados
    const angle = (props.reading - 50) * 1.8; // map 0..100 to -90..90 approx
    const rad = (angle - 90) * Math.PI / 180; // -90 es arriba
    const len = props.radius * 0.8;
    return {
        x: props.x + len * Math.cos(rad),
        y: props.y + len * Math.sin(rad)
    };
});
</script>
