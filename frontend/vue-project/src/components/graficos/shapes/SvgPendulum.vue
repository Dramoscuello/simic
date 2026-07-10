<template>
  <g class="svg-pendulum">
    <!-- Soporte (techo) -->
    <line :x1="pivotX - 20" :y1="pivotY" :x2="pivotX + 20" :y2="pivotY" stroke="#374151" stroke-width="2" />
    <path d="M 0 0 L 5 10 L -5 10 Z" fill="#374151" :transform="`translate(${pivotX}, ${pivotY})`" /> 
    
    <!-- Trayectoria punteada (opcional) -->
    <path 
      v-if="showPath" 
      :d="arcPath" 
      fill="none" 
      stroke="#9CA3AF" 
      stroke-width="1" 
      stroke-dasharray="4 2" 
    />

    <!-- Cuerda y Masa rotada -->
    <g :transform="`rotate(${angle}, ${pivotX}, ${pivotY})`">
       <line :x1="pivotX" :y1="pivotY" :x2="pivotX" :y2="pivotY + length" stroke="#4B5563" stroke-width="1.5" />
       
       <!-- Masa (Bob) -->
       <circle :cx="pivotX" :cy="pivotY + length" :r="radius" fill="#6B7280" stroke="#374151" />
       
       <!-- Etiqueta Masa -->
       <text v-if="label" :x="pivotX" :y="pivotY + length + radius + 15" text-anchor="middle" font-size="12">{{ label }}</text>
    </g>
    
    <!-- Ángulo Theta -->
    <path 
       v-if="angle !== 0" 
       :d="angleArc" 
       fill="none" 
       stroke="#374151" 
       stroke-width="1"
    />
    <text v-if="angle !== 0" :x="pivotX + Math.sin(angle * Math.PI / 360) * 35" :y="pivotY + 40" font-size="10">θ</text>

  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  pivotX: { type: Number, required: true },
  pivotY: { type: Number, required: true },
  length: { type: Number, default: 150 },
  angle: { type: Number, default: 0 }, // Grados, positivo derecha, negativo izquierda
  radius: { type: Number, default: 10 },
  label: { type: String, default: 'm' },
  showPath: { type: Boolean, default: true }
});

const arcPath = computed(() => {
   // Dibuja el arco de oscilación probable (de -angle a +angle simétrico)
   const maxAngle = Math.abs(props.angle) + 15; 
   const startA = (90 - maxAngle) * Math.PI / 180;
   const endA = (90 + maxAngle) * Math.PI / 180;
   
   const startX = props.pivotX + props.length * Math.cos(startA);
   const startY = props.pivotY + props.length * Math.sin(startA);
   
   // Esto es aproximado dibujando solo un arco visual simple debajo
   return `M ${props.pivotX - props.length*Math.sin(maxAngle*Math.PI/180)} ${props.pivotY + props.length*Math.cos(maxAngle*Math.PI/180)} Q ${props.pivotX} ${props.pivotY + props.length + 20} ${props.pivotX + props.length*Math.sin(maxAngle*Math.PI/180)} ${props.pivotY + props.length*Math.cos(maxAngle*Math.PI/180)}`;
});

const angleArc = computed(() => {
    // Pequeño arco cerca del pivote para indicar theta
    const r = 30;
    const startX = props.pivotX;
    const startY = props.pivotY + r;
    const endrad = (90 - props.angle) * Math.PI / 180; // SVG coordinate hell correction (90deg is down? No 0 is right in math)
    // Actually SVG: Y is down. 0 deg is Right. 90 is Down.
    // Vertical line is 90 deg.
    
    // Simple vertical dashed reference line
    return `M ${props.pivotX} ${props.pivotY} L ${props.pivotX} ${props.pivotY + 40}`; 
});
</script>
