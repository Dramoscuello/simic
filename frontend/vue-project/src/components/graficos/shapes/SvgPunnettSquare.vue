<template>
  <g class="svg-punnett">
    <!-- Tabla 2x2 grid -->
    <!-- Líneas horizontales -->
    <line :x1="x" :y1="y" :x2="x + size" :y2="y" stroke="#374151" stroke-width="2" />
    <line :x1="x" :y1="y + size/2" :x2="x + size" :y2="y + size/2" stroke="#374151" stroke-width="1" />
    <line :x1="x" :y1="y + size" :x2="x + size" :y2="y + size" stroke="#374151" stroke-width="2" />

    <!-- Líneas verticales -->
    <line :x1="x" :y1="y" :x2="x" :y2="y + size" stroke="#374151" stroke-width="2" />
    <line :x1="x + size/2" :y1="y" :x2="x + size/2" :y2="y + size" stroke="#374151" stroke-width="1" />
    <line :x1="x + size" :y1="y" :x2="x + size" :y2="y + size" stroke="#374151" stroke-width="2" />

    <!-- Headers (Padres) -->
    <!-- Padre 1 (Arriba) -->
    <text :x="x + size*0.25" :y="y - 10" text-anchor="middle" font-weight="bold">{{ p1[0] }}</text>
    <text :x="x + size*0.75" :y="y - 10" text-anchor="middle" font-weight="bold">{{ p1[1] }}</text>

    <!-- Padre 2 (Izquierda) -->
    <text :x="x - 15" :y="y + size*0.25 + 5" text-anchor="middle" font-weight="bold">{{ p2[0] }}</text>
    <text :x="x - 15" :y="y + size*0.75 + 5" text-anchor="middle" font-weight="bold">{{ p2[1] }}</text>

    <!-- Cruces (Hijos) -->
    <text :x="x + size*0.25" :y="y + size*0.25 + 5" text-anchor="middle" fill="#4B5563">{{ combine(p1[0], p2[0]) }}</text>
    <text :x="x + size*0.75" :y="y + size*0.25 + 5" text-anchor="middle" fill="#4B5563">{{ combine(p1[1], p2[0]) }}</text>
    <text :x="x + size*0.25" :y="y + size*0.75 + 5" text-anchor="middle" fill="#4B5563">{{ combine(p1[0], p2[1]) }}</text>
    <text :x="x + size*0.75" :y="y + size*0.75 + 5" text-anchor="middle" fill="#4B5563">{{ combine(p1[1], p2[1]) }}</text>
  </g>
</template>

<script setup>
const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  size: { type: Number, default: 120 },
  p1: { type: String, default: 'Aa' }, // Alelos Padre 1 (Horizontal)
  p2: { type: String, default: 'Aa' }  // Alelos Padre 2 (Vertical)
});

// Combinar alelos (Ej: 'a' + 'A' -> 'Aa')
const combine = (a, b) => {
  // Convención: Mayúscula primero
  const first = (a === a.toUpperCase() || b === b.toLowerCase()) ? a : b;
  const second = (first === a) ? b : a;
  // Si ambos son upper o ambos lower, el orden no importa tanto, pero intentamos mantener orden alfabético si son letras distintas?
  // Para Mendelianos simples (misma letra) basta poner mayúscula primero.
  if (a.toUpperCase() === b.toUpperCase()) {
      return (a < b) ? a + b : b + a; // Alphabetic sort is simpler for generic
  }
  return (a.toUpperCase() === a) ? a + b : b + a;
};
</script>
