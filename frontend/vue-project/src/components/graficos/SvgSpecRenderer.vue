<template>
  <div class="svg-spec-container w-full flex justify-center transition-colors">
    <svg 
      v-if="spec"
      :viewBox="spec.viewBox || '0 0 400 300'"
      class="w-full max-w-[500px] h-auto shadow-sm rounded transition-colors"
      :class="darkMode ? 'border border-slate-600 bg-slate-900' : 'border border-gray-100 bg-white'"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- Definiciones Globales (Flechas, etc) -->
      <defs>
        <!-- Marcador de Flecha Estándar -->
        <marker 
          id="arrowhead" 
          markerWidth="10" 
          markerHeight="7" 
          refX="9" 
          refY="3.5" 
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" :fill="defaultStrokeColor" />
        </marker>
        <!-- Marcador de Flecha Roja -->
        <marker 
          id="arrowhead-red" 
          markerWidth="10" 
          markerHeight="7" 
          refX="9" 
          refY="3.5" 
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#EF4444" />
        </marker>
         <!-- Marcador de Flecha Azul -->
         <marker 
          id="arrowhead-blue" 
          markerWidth="10" 
          markerHeight="7" 
          refX="9" 
          refY="3.5" 
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#3B82F6" />
        </marker>
      </defs>

      <!-- Renderizado Dinámico de Formas -->
      <g v-for="(shape, index) in spec.shapes" :key="index">
        
        <!-- RECTANGLE -->
        <rect 
          v-if="shape.type === 'rect'"
          :x="shape.x"
          :y="shape.y"
          :width="shape.width"
          :height="shape.height"
          :fill="shape.fill || 'none'"
          :stroke="shape.stroke || defaultStrokeColor"
          :stroke-width="2"
          :transform="shape.transform"
        />

        <!-- CIRCLE -->
        <circle 
          v-if="shape.type === 'circle'"
          :cx="shape.cx"
          :cy="shape.cy"
          :r="shape.r"
          :fill="shape.fill || 'none'"
          :stroke="shape.stroke || defaultStrokeColor"
          :stroke-width="2"
        />

        <!-- LINE -->
        <line 
          v-if="shape.type === 'line'"
          :x1="shape.x1"
          :y1="shape.y1"
          :x2="shape.x2"
          :y2="shape.y2"
          :stroke="shape.stroke || defaultStrokeColor"
          :stroke-width="2"
        />

        <!-- ARROW (Line with Marker) -->
        <line 
          v-if="shape.type === 'arrow'"
          :x1="shape.x1"
          :y1="shape.y1"
          :x2="shape.x2"
          :y2="shape.y2"
          :stroke="getArrowColor(shape.color)"
          :stroke-width="2"
          :marker-end="`url(#arrowhead${getArrowSuffix(shape.color)})`"
        />

        <!-- PATH -->
        <path 
          v-if="shape.type === 'path'"
          :d="shape.d"
          :fill="shape.fill || 'none'"
          :stroke="shape.stroke || defaultStrokeColor"
          :stroke-width="2"
          :transform="shape.transform"
        />

        <!-- TEXT -->
        <text 
          v-if="shape.type === 'text'"
          :x="shape.x"
          :y="shape.y"
          :fill="shape.fill || defaultTextColor"
          font-family="sans-serif"
          :font-size="shape.fontSize || 14"
          text-anchor="middle" 
          dominant-baseline="middle"
        >
          {{ shape.value || shape.label }}
        </text>

        <!-- Etiqueta para Flechas (Opcional, si viene 'label' en type arrow) -->
        <text
          v-if="shape.type === 'arrow' && shape.label"
          :x="(shape.x1 + shape.x2) / 2"
          :y="((shape.y1 + shape.y2) / 2) - 10"
          :fill="getArrowColor(shape.color)"
          font-family="sans-serif"
          font-size="12"
          font-weight="bold"
          text-anchor="middle"
        >
          {{ shape.label }}
        </text>

        <!-- COMPONENTES RICOS (Nuevo Sistema) -->
        <g v-if="shape.type === 'component'">
          
          <!-- Resistencia -->
          <SvgResistor 
            v-if="shape.name === 'resistor'"
            :x1="shape.x1" :y1="shape.y1" 
            :x2="shape.x2" :y2="shape.y2"
            :label="shape.label"
          />

          <!-- Beaker (Vaso) -->
          <SvgBeaker 
            v-if="shape.name === 'beaker'"
            :x="shape.x" :y="shape.y"
            :width="shape.width" :height="shape.height"
            :level="shape.params?.level ?? 50"
            :color="shape.params?.color"
            :label="shape.label"
          />

          <!-- Bloque -->
          <SvgBlock 
            v-if="shape.name === 'block'"
            :x="shape.x" :y="shape.y"
            :width="shape.width" :height="shape.height"
            :rotation="shape.rotation || shape.angle || 0"
            :label="shape.label"
            :showCM="shape.showCM"
          />

          <!-- Caja de Particulas -->
          <SvgParticleBox 
            v-if="shape.name === 'particle_box'"
            :x="shape.x" :y="shape.y"
            :width="shape.width" :height="shape.height"
            :count="shape.params?.count"
            :color="shape.params?.color"
            :label="shape.label"
          />

          <!-- Lente Optica -->
          <SvgOpticLens 
            v-if="shape.name === 'optic_lens'"
            :cx="shape.x || shape.cx" :cy="shape.y || shape.cy"
            :type="shape.params?.type || 'convex'"
            :focalLength="shape.params?.focalLength"
          />

          <!-- Onda -->
          <SvgWave 
            v-if="shape.name === 'wave'"
            :x1="shape.x1" :y1="shape.y1"
            :x2="shape.x2" :y2="shape.y2"
            :amplitude="shape.params?.amplitude"
            :wavelength="shape.params?.wavelength"
          />

          <!-- Rayo de Luz -->
          <SvgRay 
            v-if="shape.name === 'ray'"
            :x1="shape.x1" :y1="shape.y1"
            :x2="shape.x2" :y2="shape.y2"
          />
          
          <!-- Vector de Fuerza -->
          <SvgForceVector 
             v-if="shape.name === 'force_vector'"
             :x1="shape.x1" :y1="shape.y1" 
             :x2="shape.x2" :y2="shape.y2"
             :label="shape.label"
             :color="shape.color"
          />

          <!-- ============================ -->
          <!--      PACK BIOLOGÍA           -->
          <!-- ============================ -->

          <!-- Célula -->
          <SvgCell 
             v-if="shape.name === 'cell'"
             :x="shape.x" :y="shape.y"
             :radius="shape.params?.radius ?? 60"
             :type="shape.params?.type || 'animal'"
             :label="shape.label"
          />

          <!-- Cuadro de Punnett -->
          <SvgPunnettSquare 
             v-if="shape.name === 'punnett'"
             :x="shape.x" :y="shape.y"
             :size="shape.width || shape.params?.size"
             :p1="shape.params?.p1"
             :p2="shape.params?.p2"
          />

          <!-- ADN Hélice -->
          <SvgDNAHelix 
             v-if="shape.name === 'dna'"
             :x="shape.x" :y="shape.y"
             :width="shape.width" :height="shape.height"
             :label="shape.label"
          />

          <!-- Neurona -->
          <SvgNeuron 
             v-if="shape.name === 'neuron'"
             :x="shape.x" :y="shape.y"
             :length="shape.width || 150"
             :label="shape.label"
          />

          <!-- ============================ -->
          <!--      PACK FÍSICA PRO         -->
          <!-- ============================ -->

          <!-- Polea -->
          <SvgPulley 
             v-if="shape.name === 'pulley'"
             :x="shape.x" :y="shape.y"
             :radius="shape.params?.radius"
             :ropeLeft="shape.params?.ropeLeft"
             :ropeRight="shape.params?.ropeRight"
             :label="shape.label"
          />

          <!-- Resorte -->
          <SvgSpring 
             v-if="shape.name === 'spring'"
             :x1="shape.x1" :y1="shape.y1"
             :length="shape.width || 100"
             :width="shape.height || 20"
             :rotation="shape.rotation || shape.angle || 0"
             :label="shape.label"
          />

          <!-- Péndulo -->
          <SvgPendulum 
             v-if="shape.name === 'pendulum'"
             :pivotX="shape.x" :pivotY="shape.y"
             :length="shape.params?.length"
             :angle="shape.params?.angle"
             :label="shape.label"
          />

          <!-- Proyectil -->
          <SvgProjectile 
             v-if="shape.name === 'projectile'"
             :x1="shape.x1" :y1="shape.y1"
             :x2="shape.x2" :peakHeight="shape.params?.peakHeight"
             :v0="shape.params?.v0"
             :label="shape.label"
          />

          <!-- Termómetro -->
          <SvgThermometer 
             v-if="shape.name === 'thermometer'"
             :x="shape.x" :y="shape.y"
             :height="shape.height"
             :temperature="shape.params?.temperature"
             :label="shape.label"
          />

          <!-- Pistón -->
          <SvgPiston 
             v-if="shape.name === 'piston'"
             :x="shape.x" :y="shape.y"
             :width="shape.width" :height="shape.height"
             :compression="shape.params?.volume ?? 0.5"
             :weight="shape.params?.weight"
             :label="shape.label"
          />

          <!-- ============================ -->
          <!--      PACK LABORATORIO        -->
          <!-- ============================ -->

          <!-- Vidrio Lab (Erlenmeyer / Probeta) -->
          <SvgLabContainer 
             v-if="shape.name === 'lab_container'"
             :x="shape.x" :y="shape.y"
             :width="shape.width" :height="shape.height"
             :type="shape.params?.type || 'cylinder'" 
             :level="shape.params?.level"
             :color="shape.params?.color"
             :label="shape.label"
          />

          <!-- Medidor Eléctrico (V, A) -->
          <SvgMeter 
             v-if="shape.name === 'meter'"
             :x="shape.x" :y="shape.y"
             :type="shape.params?.type || 'V'"
             :reading="shape.params?.reading"
          />

          <!-- ============================ -->
          <!--      PACK INGLÉS             -->
          <!-- ============================ -->

          <!-- Señal / Aviso -->
          <SvgSign 
             v-if="shape.name === 'sign'"
             :x="shape.x" :y="shape.y"
             :width="shape.width"
             :type="shape.params?.type || 'warning'"
             :label="shape.label"
          />

          <!-- Dashboards / Pantallas -->
          <SvgDashboard 
             v-if="shape.name === 'dashboard'"
             :x="shape.x" :y="shape.y"
             :width="shape.width"
             :type="shape.params?.type || 'atm-insert-card'"
             :label="shape.label"
          />

          <!-- Etiquetas / Labels -->
          <SvgLabel 
             v-if="shape.name === 'label'"
             :x="shape.x" :y="shape.y"
             :width="shape.width"
             :type="shape.params?.type || 'clothing-wash-label'"
             :label="shape.label"
          />

          <!-- Chats / Burbujas -->
          <SvgChatBubble 
             v-if="shape.name === 'chat'"
             :x="shape.x" :y="shape.y"
             :width="shape.width"
             :type="shape.params?.type || 'chat-single-received'"
             :label="shape.label"
          />

          <!-- Tarjetas / Iconos -->
          <SvgIconCard 
             v-if="shape.name === 'card'"
             :x="shape.x" :y="shape.y"
             :width="shape.width"
             :type="shape.params?.type || 'card-apple'"
             :label="shape.label"
          />

          <!-- Anatomía (Stickers / SVGs Externos) -->
          <SvgAnatomy 
             v-if="shape.name === 'anatomy'"
             :x="shape.x" :y="shape.y"
             :part="shape.params?.part || 'heart'"
             :width="shape.width"
             :label="shape.label"
          />

        </g>

      </g>
    </svg>
    <div v-else class="text-xs p-4" :class="darkMode ? 'text-slate-500' : 'text-gray-400'">
      Sin especificación visual disponible.
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue';

// Importar Componentes Ricos dinámicamente
const SvgResistor = defineAsyncComponent(() => import('./shapes/SvgResistor.vue'));
const SvgBeaker = defineAsyncComponent(() => import('./shapes/SvgBeaker.vue'));
const SvgBlock = defineAsyncComponent(() => import('./shapes/SvgBlock.vue'));
const SvgParticleBox = defineAsyncComponent(() => import('./shapes/SvgParticleBox.vue'));
const SvgOpticLens = defineAsyncComponent(() => import('./shapes/SvgOpticLens.vue'));
const SvgWave = defineAsyncComponent(() => import('./shapes/SvgWave.vue'));
const SvgRay = defineAsyncComponent(() => import('./shapes/SvgRay.vue'));
const SvgForceVector = defineAsyncComponent(() => import('./shapes/SvgForceVector.vue'));

// Importar Pack Biología
const SvgCell = defineAsyncComponent(() => import('./shapes/SvgCell.vue'));
const SvgPunnettSquare = defineAsyncComponent(() => import('./shapes/SvgPunnettSquare.vue'));
const SvgDNAHelix = defineAsyncComponent(() => import('./shapes/SvgDNAHelix.vue'));
const SvgNeuron = defineAsyncComponent(() => import('./shapes/SvgNeuron.vue'));
const SvgAnatomy = defineAsyncComponent(() => import('./shapes/SvgAnatomy.vue'));

// Importar Pack Física Pro
const SvgPulley = defineAsyncComponent(() => import('./shapes/SvgPulley.vue'));
const SvgSpring = defineAsyncComponent(() => import('./shapes/SvgSpring.vue'));
const SvgPendulum = defineAsyncComponent(() => import('./shapes/SvgPendulum.vue'));
const SvgProjectile = defineAsyncComponent(() => import('./shapes/SvgProjectile.vue'));
const SvgThermometer = defineAsyncComponent(() => import('./shapes/SvgThermometer.vue'));
const SvgPiston = defineAsyncComponent(() => import('./shapes/SvgPiston.vue'));

// Importar Pack Inglés
const SvgSign = defineAsyncComponent(() => import('./shapes/ingles/SvgSign.vue'));
const SvgDashboard = defineAsyncComponent(() => import('./shapes/ingles/SvgDashboard.vue'));
const SvgLabel = defineAsyncComponent(() => import('./shapes/ingles/SvgLabel.vue'));
const SvgChatBubble = defineAsyncComponent(() => import('./shapes/ingles/SvgChatBubble.vue'));
const SvgIconCard = defineAsyncComponent(() => import('./shapes/ingles/SvgIconCard.vue'));

// Importar Pack Laboratorio
const SvgLabContainer = defineAsyncComponent(() => import('./shapes/SvgLabContainer.vue'));
const SvgMeter = defineAsyncComponent(() => import('./shapes/SvgMeter.vue'));

const props = defineProps({
  spec: {
    type: Object,
    required: true,
    default: () => ({ viewBox: '0 0 400 300', shapes: [] })
  },
  darkMode: {
    type: Boolean,
    default: false
  }
});

const defaultStrokeColor = computed(() => (props.darkMode ? '#E2E8F0' : '#374151'));
const defaultTextColor = computed(() => (props.darkMode ? '#F8FAFC' : '#1F2937'));

// Helpers para colores de flechas
const getArrowColor = (color) => {
  if (color === 'red') return '#EF4444';
  if (color === 'blue') return '#3B82F6';
  return defaultStrokeColor.value;
};

const getArrowSuffix = (color) => {
  if (color === 'red') return '-red';
  if (color === 'blue') return '-blue';
  return ''; // Default marker id "arrowhead"
};
</script>

<style scoped>
/* Estilos adicionales si fueran necesarios */
</style>
