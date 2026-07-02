<template>
  <div
    class="grafico-renderer w-full max-w-3xl mx-auto my-6 p-4 rounded-lg border flex justify-center transition-colors"
    :class="darkMode ? 'bg-slate-800 border-slate-700 text-slate-100' : 'bg-gray-50 border-gray-100 text-slate-800'"
  >
    
    <!-- SVG Geométrico (Nuevo Spec JSON) -->
    <SvgSpecRenderer 
      v-if="(tipo === 'svg_geometrico' || tipo === 'diagrama_svg') && config.svg_spec" 
      :spec="config.svg_spec" 
      :dark-mode="darkMode"
    />

    <!-- SVG Legacy (String Html) -->
    <div 
      v-else-if="(tipo === 'svg_geometrico' || tipo === 'diagrama_svg') && config.svg_content" 
      v-html="config.svg_content" 
      class="svg-container rounded-md p-2"
      :class="darkMode ? 'bg-slate-900/40 border border-slate-700/60' : 'bg-white border border-gray-100'"
    ></div>

    <!-- SVG Artístico (Generado por Opus) -->
    <div 
      v-else-if="tipo === 'svg_artistico' && config.svg_code" 
      v-html="config.svg_code" 
      class="svg-container artistic-svg rounded-md p-2"
      :class="darkMode ? 'bg-slate-900/40 border border-slate-700/60' : 'bg-white border border-gray-100'"
    ></div>

    <!-- Fallback Artístico (Si falló la generación) -->
    <div 
      v-else-if="tipo === 'svg_artistico'" 
      class="w-full p-4 rounded text-center text-sm italic"
      :class="darkMode ? 'bg-slate-800 border border-slate-700 text-slate-400' : 'bg-gray-100 border border-gray-200 text-gray-500'"
    >
      <p class="font-semibold not-italic mb-1">Imagen no disponible</p>
      "{{ config.descripcion_visual }}"
    </div>
    
    <!-- Chart.js Barra -->
    <BarChart v-else-if="tipo === 'chartjs_bar'" :config="config" :dark-mode="darkMode" />

    <!-- Chart.js Pie -->
    <PieChart v-else-if="tipo === 'chartjs_pie'" :config="config" :dark-mode="darkMode" />

    <!-- Chart.js Line -->
    <LineChart v-else-if="tipo === 'chartjs_line'" :config="config" :dark-mode="darkMode" />

    <!-- Chart.js Scatter (Nuevo) -->
    <ScatterChart v-else-if="tipo === 'chartjs_scatter'" :config="config" :dark-mode="darkMode" />

    <!-- Tabla de Datos -->
    <div
      v-else-if="tipo === 'tabla_datos'"
      class="overflow-x-auto w-full rounded-lg border"
      :class="darkMode ? 'border-slate-700' : 'border-gray-200'"
    >
      <table class="min-w-full divide-y text-sm" :class="darkMode ? 'divide-slate-700' : 'divide-gray-200'">
        <thead :class="darkMode ? 'bg-slate-800' : 'bg-gray-100'">
          <tr>
            <th
              v-for="(col, i) in config.columnas"
              :key="i"
              scope="col"
              class="px-6 py-3 text-left font-medium uppercase tracking-wider"
              :class="darkMode ? 'text-slate-300' : 'text-gray-500'"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody :class="darkMode ? 'bg-slate-900 divide-y divide-slate-700' : 'bg-white divide-y divide-gray-200'">
          <tr v-for="(fila, i) in config.filas" :key="i">
            <td
              v-for="(celda, j) in fila"
              :key="j"
              class="px-6 py-4 whitespace-nowrap"
              :class="darkMode ? 'text-slate-200' : 'text-gray-700'"
            >
              {{ celda }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="text-xs" :class="darkMode ? 'text-rose-400' : 'text-red-500'">Tipo de gráfico no soportado: {{ tipo }}</div>
  </div>
</template>

<script setup>
import { defineAsyncComponent } from 'vue';

const props = defineProps({
  tipo: String,
  config: {
    type: Object,
    default: () => ({})
  },
  darkMode: {
    type: Boolean,
    default: false
  }
});

const SvgSpecRenderer = defineAsyncComponent(() => import('./SvgSpecRenderer.vue'));
const BarChart = defineAsyncComponent(() => import('./BarChart.vue'));
const PieChart = defineAsyncComponent(() => import('./PieChart.vue'));
const LineChart = defineAsyncComponent(() => import('./LineChart.vue'));
const ScatterChart = defineAsyncComponent(() => import('./ScatterChart.vue'));
</script>

<style scoped>
.svg-container {
  display: flex;
  justify-content: center;
  width: 100%;
}

:deep(svg) {
  max-height: 300px;
  width: 100%;
  height: auto;
  max-width: 500px; /* Evita que se estire demasiado */
}
</style>
