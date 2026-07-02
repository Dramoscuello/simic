<template>
  <g class="svg-cell">
    <!-- Célula Vegetal (Pared Celular - Rectangular) -->
    <rect 
      v-if="type === 'plant'"
      :x="x - radius" :y="y - radius" 
      :width="radius * 2" :height="radius * 2" 
      rx="10" ry="10"
      fill="#ECFCCB" 
      stroke="#65A30D" 
      stroke-width="4"
    />
    
    <!-- Célula Animal / Membrana Interna (Redonda) -->
    <circle 
      :cx="x" :cy="y" 
      :r="type === 'plant' ? radius - 5 : radius" 
      :fill="type === 'plant' ? '#F7FEE7' : '#FEF2F2'" 
      :stroke="type === 'plant' ? '#84CC16' : '#F87171'" 
      stroke-width="2"
    />

    <!-- Núcleo (Siempre presente) -->
    <circle 
      :cx="x" :cy="y" 
      :r="radius * 0.25" 
      fill="#E5E7EB" 
      stroke="#374151"
    />
    <circle :cx="x" :cy="y" :r="radius * 0.08" fill="#374151" /> <!-- Nucleolo -->
    
    <!-- Mitocondria (Ovalo con rayitas) -->
    <g transform="translate(20, 20)">
      <ellipse :cx="x + radius*0.4" :cy="y - radius*0.4" rx="10" ry="6" fill="#FCA5A5" stroke="#B91C1C" transform="rotate(45)" />
    </g>

    <!-- Cloroplasto (Solo vegetal) -->
    <g v-if="type === 'plant'" transform="translate(-20, 20)">
      <ellipse :cx="x - radius*0.4" :cy="y - radius*0.4" rx="10" ry="6" fill="#86EFAC" stroke="#15803D" transform="rotate(-45)" />
    </g>

    <!-- Vacuola (Solo vegetal - Grande) -->
    <path 
      v-if="type === 'plant'"
      :d="`M ${x-15} ${y+15} q 15 15 30 0 t 10 -20`"
      fill="#BFDBFE" stroke="#3B82F6"
      opacity="0.6"
    />

    <!-- Etiqueta -->
    <text v-if="label" :x="x" :y="y + radius + 20" text-anchor="middle" font-size="12" fill="#374151">
      {{ label }}
    </text>
  </g>
</template>

<script setup>
const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  radius: { type: Number, default: 60 },
  type: { type: String, default: 'animal' }, // 'animal' | 'plant'
  label: { type: String, default: '' }
});
</script>
