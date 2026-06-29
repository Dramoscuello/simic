<template>
  <g class="svg-pulley">
    <!-- Soporte superior (línea o gancho) -->
    <line :x1="x" :y1="y" :x2="x" :y2="y - radius - 10" stroke="#374151" stroke-width="2" />
    <circle :cx="x" :cy="y - radius - 10" r="3" fill="#374151" />
    
    <!-- Cuerda rodeando la polea (Arco superior) -->
    <!-- Si hay cuerdas colgando, dibujamos lineas tangentes -->
    <line v-if="ropeLeft" :x1="x - radius" :y1="y" :x2="x - radius" :y2="y + ropeLeft" stroke="#1F2937" stroke-width="2" />
    <line v-if="ropeRight" :x1="x + radius" :y1="y" :x2="x + radius" :y2="y + ropeRight" stroke="#1F2937" stroke-width="2" />

    <!-- La Polea (Rueda) -->
    <circle :cx="x" :cy="y" :r="radius" fill="#F3F4F6" stroke="#374151" stroke-width="2" />
    <circle :cx="x" :cy="y" :r="3" fill="#9CA3AF" /> <!-- Eje -->

    <!-- Etiqueta -->
    <text v-if="label" :x="x" :y="y - radius - 15" text-anchor="middle" font-size="12" fill="#374151">{{ label }}</text>
  </g>
</template>

<script setup>
const props = defineProps({
  x: { type: Number, required: true }, // Centro polea
  y: { type: Number, required: true },
  radius: { type: Number, default: 15 },
  ropeLeft: { type: Number, default: 50 }, // Largo cuerda izquierda (0 = no hay)
  ropeRight: { type: Number, default: 50 }, // Largo cuerda derecha
  label: { type: String, default: '' }
});
</script>
