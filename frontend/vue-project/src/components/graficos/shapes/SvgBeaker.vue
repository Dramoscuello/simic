<template>
  <g class="svg-beaker">
    <!-- Líquido -->
    <path 
      :d="liquidPath" 
      :fill="liquidColor" 
      fill-opacity="0.5"
    />
    
    <!-- Contorno del Vaso -->
    <path 
      :d="beakerPath" 
      fill="none" 
      stroke="#374151" 
      stroke-width="2"
      stroke-linejoin="round"
    />

    <!-- Graduación (Marcas) -->
    <g v-if="showGraduation">
      <line 
        v-for="i in 5" 
        :key="i"
        :x1="x + width - 15" 
        :y1="y + height - (i * height * 0.15)" 
        :x2="x + width" 
        :y2="y + height - (i * height * 0.15)" 
        stroke="#9CA3AF" 
        stroke-width="1.5" 
      />
    </g>

    <!-- Etiqueta debajo -->
    <text v-if="label" :x="x + width/2" :y="y + height + 20" text-anchor="middle" font-size="12" fill="#374151">
      {{ label }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  width: { type: Number, default: 60 },
  height: { type: Number, default: 80 },
  level: { type: Number, default: 50 }, // 0 a 100
  color: { type: String, default: 'blue' },
  showGraduation: { type: Boolean, default: true },
  label: { type: String, default: '' }
});

const liquidColor = computed(() => {
  if (props.color === 'red') return '#FCA5A5';
  if (props.color === 'green') return '#86EFAC';
  return '#93C5FD'; // Blue default
});

// Dibujar contorno del vaso (U con borde superior abierto)
const beakerPath = computed(() => {
  const w = props.width;
  const h = props.height;
  const r = 10; // Radio esquina inferior
  return `
    M ${props.x} ${props.y} 
    v ${h - r} 
    a ${r} ${r} 0 0 0 ${r} ${r} 
    h ${w - 2*r} 
    a ${r} ${r} 0 0 0 ${r} -${r} 
    v -${h - r}
  `;
});

// Dibujar el líquido
const liquidPath = computed(() => {
  const w = props.width;
  const h = props.height;
  const r = 10;
  // Calcular altura del líquido en px desde abajo
  const liquidH = (props.level / 100) * h;
  // Coordenada Y superior del líquido
  const liquidY = props.y + h - liquidH;

  return `
    M ${props.x} ${liquidY}
    v ${liquidH - r} 
    a ${r} ${r} 0 0 0 ${r} ${r} 
    h ${w - 2*r} 
    a ${r} ${r} 0 0 0 ${r} -${r} 
    v -${liquidH - r}
    Z
  `;
});
</script>
