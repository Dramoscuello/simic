<template>
  <g class="svg-piston">
    <!-- Cilindro (Contenedor) -->
    <rect 
      :x="x" :y="y" 
      :width="width" :height="height" 
      fill="none" 
      stroke="#374151" 
      stroke-width="2" 
    />
    
    <!-- Gas (relleno suave abajo) -->
    <rect 
      :x="x" :y="pistonY" 
      :width="width" :height="gasHeight" 
      fill="#DBEAFE" 
      fill-opacity="0.5"
    />
    
    <!-- Partículas de Gas (opcional, aleatorias simples) -->
    <g v-if="particles">
       <circle v-for="i in 10" :key="i" :cx="x + Math.random()*width" :cy="pistonY + Math.random()*gasHeight" r="1.5" fill="#3B82F6" />
    </g>

    <!-- Émbolo (Pistón Móvil) -->
    <rect 
      :x="x" :y="pistonY - pistonThick" 
      :width="width" :height="pistonThick" 
      fill="#9CA3AF" 
      stroke="#374151" 
      stroke-width="1.5"
    />
    
    <!-- Vástago (Palito arriba) -->
    <line 
      :x1="x + width/2" :y1="pistonY - pistonThick" 
      :x2="x + width/2" :y2="pistonY - pistonThick - 20" 
      stroke="#374151" stroke-width="2" 
    />
    
    <!-- Peso sobre el pistón (W) -->
    <rect 
      v-if="weight"
      :x="x + width/2 - 10" :y="pistonY - pistonThick - 20 - 10" 
      width="20" height="10" 
      fill="#1F2937" 
    />

    <text v-if="label" :x="x + width/2" :y="y + height + 15" text-anchor="middle" font-size="12">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  width: { type: Number, default: 60 },
  height: { type: Number, default: 100 },
  compression: { type: Number, default: 0.5 }, // 0 (lleno) a 1 (vacío) -> Posición del pistón (0 a 1)
  label: { type: String, default: '' },
  particles: { type: Boolean, default: true },
  weight: { type: Boolean, default: false } // ¿Tiene una pesa encima?
});

const pistonThick = 10;
// Compression 0 = Arriba de todo (y)
// Compression 1 = Abajo de todo (y + height)
// Invertimos lógica: volume (0 a 1). 1 = Lleno de gas. 0.5 = Mitad.
// Llamémoslo "volume" internamente para claridad.
// Si compression es 0.5 -> pistón a la mitad.
const gasHeight = computed(() => props.height * props.compression); 
const pistonY = computed(() => props.y + props.height - gasHeight.value);
</script>
