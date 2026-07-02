<template>
  <g class="svg-lab-container">
    
    <!-- LÍQUIDO -->
    <path 
      :d="liquidPath" 
      :fill="liquidColor" 
      fill-opacity="0.5"
    />

    <!-- CONTORNO (VIDRIO) -->
    <path 
      :d="glassPath" 
      fill="none" 
      stroke="#374151" 
      stroke-width="2"
      stroke-linejoin="round"
    />

    <!-- GRADUACIÓN -->
    <g v-if="showGraduation" stroke="#9CA3AF" stroke-width="1.5">
       <!-- Dibujar rayitas según la altura del contenedor -->
       <line v-for="i in 5" :key="i"
          :x1="gradX - 10" 
          :y1="y + height - (i * height * 0.15)" 
          :x2="gradX" 
          :y2="y + height - (i * height * 0.15)" 
       />
    </g>

    <text v-if="label" :x="x" :y="y + height + 20" text-anchor="middle" font-size="12" fill="#374151">{{ label }}</text>
  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, required: true },
  y: { type: Number, required: true },
  height: { type: Number, default: 100 },
  width: { type: Number, default: 40 }, // Ancho base (para erlenmeyer) o ancho tubo (probeta)
  type: { type: String, default: 'cylinder' }, // 'cylinder' (probeta) | 'erlenmeyer'
  level: { type: Number, default: 50 },
  color: { type: String, default: 'blue' },
  showGraduation: { type: Boolean, default: true },
  label: { type: String, default: '' }
});

const liquidColor = computed(() => {
  if (props.color === 'red') return '#FCA5A5';
  if (props.color === 'green') return '#86EFAC';
  if (props.color === 'yellow') return '#FDE047';
  return '#93C5FD';
});

// Referencia X para las marcas de graduación
const gradX = computed(() => {
    if (props.type === 'erlenmeyer') return props.x + props.width/4; // En el cuello? mejor en la base ancha visualmente
    return props.x + props.width/2; // Borde derecho probeta
});

const glassPath = computed(() => {
  const h = props.height;
  const w = props.width;
  
  if (props.type === 'erlenmeyer') {
     // Base ancha abajo, cuello estrecho arriba
     const neckW = w * 0.4;
     const neckH = h * 0.35;
     const baseWhalf = w / 2;
     
     // Svg coords: x,y is top-center of the neck? Let's say x,y is center-bottom reference? 
     // Standardize: x,y is top-left bounding box anchor like others?
     // Let's us x as CENTER of the object horizontally to align easier.
     
     const topY = props.y;
     const botY = props.y + h;
     
     return `
        M ${props.x - neckW/2} ${topY}
        L ${props.x - neckW/2} ${topY + neckH} 
        L ${props.x - baseWhalf} ${botY} 
        Q ${props.x} ${botY + 5} ${props.x + baseWhalf} ${botY}
        L ${props.x + neckW/2} ${topY + neckH}
        L ${props.x + neckW/2} ${topY}
     `;
  } else {
     // Probeta (Cylinder)
     const r = w / 2;
     return `
        M ${props.x - r} ${props.y}
        L ${props.x - r} ${props.y + h - 5}
        Q ${props.x} ${props.y + h + 5} ${props.x + r} ${props.y + h - 5}
        L ${props.x + r} ${props.y}
     `;
     // Optional base foot?
  }
});

const liquidPath = computed(() => {
  const h = props.height;
  const w = props.width;
  const liqH = h * (props.level / 100);
  const surfaceY = props.y + h - liqH;
  
  if (props.type === 'erlenmeyer') {
      const neckW = w * 0.4;
      const neckH = h * 0.35;
      const baseWhalf = w / 2;
      const botY = props.y + h;

      // Calcular ancho en la superficie del líquido (interpolación linear trapezoidal)
      // Pendiente del lado:
      // (baseWhalf - neckW/2) / (h - neckH)
      // Si surfaceY está en el cuello, ancho es neckW. Si está abajo, interpola.
      // Simplificacion visual: Solo dibujamos la parte de abajo llena
      
      return `
        M ${props.x - baseWhalf} ${botY}
        L ${props.x - baseWhalf + 5} ${surfaceY} 
        L ${props.x + baseWhalf - 5} ${surfaceY}
        L ${props.x + baseWhalf} ${botY}
        Z
      `; 
      // FIXME: Math exacto del trapecio liquido es complejo en v-path simple sin path clipping. 
      // Visual Hack: Usar clip-path sería mejor, pero path manual funciona.
  } else {
      // Cylinder
      const r = w / 2;
      return `
        M ${props.x - r} ${surfaceY}
        L ${props.x - r} ${props.y + h - 5}
        Q ${props.x} ${props.y + h + 5} ${props.x + r} ${props.y + h - 5}
        L ${props.x + r} ${surfaceY}
        Z
      `;
  }
});
</script>
