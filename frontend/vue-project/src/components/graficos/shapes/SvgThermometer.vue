<template>
  <g class="svg-thermometer">
    <!-- Tubo de vidrio (fondo blanco) -->
    <rect 
      :x="x - width/2" 
      :y="y" 
      :width="width" 
      :height="height" 
      rx="width/2" 
      fill="white" 
      stroke="#374151" 
      stroke-width="1.5"
    />
    
    <!-- Columna de Mercurio/Alcohol (Rojo) -->
    <rect 
      :x="x - width/4" 
      :y="liquidY" 
      :width="width/2" 
      :height="liquidHeight" 
      fill="#EF4444"
    />
    
    <!-- Bulbo inferior (Círculo rojo) -->
    <circle 
      :cx="x" 
      :cy="y + height" 
      :r="width" 
      fill="#EF4444" 
      stroke="#EF4444"
    />
    <circle 
      :cx="x" 
      :cy="y + height" 
      :r="width" 
      fill="none" 
      stroke="#374151"
      stroke-width="1.5"
    />

    <!-- Marcas de Graduación -->
    <g>
      <line v-for="i in 5" :key="i" 
        :x1="x + width/2" :y1="y + height - i*(height/6) - 10" 
        :x2="x + width" :y2="y + height - i*(height/6) - 10" 
        stroke="#374151" stroke-width="1" />
    </g>

    <!-- Valor numérico -->
    <text v-if="label" :x="x + width + 5" :y="liquidY + 5" font-size="12" fill="#374151">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  width: { type: Number, default: 10 },
  height: { type: Number, default: 100 },
  temperature: { type: Number, default: 50 }, // 0 a 100%
  label: { type: String, default: '' }
});

const liquidHeight = computed(() => (props.temperature / 100) * props.height);
const liquidY = computed(() => props.y + props.height - liquidHeight.value);
</script>
