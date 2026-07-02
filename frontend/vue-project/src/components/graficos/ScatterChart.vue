<template>
  <div class="w-full h-64 md:h-80">
    <Scatter :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Scatter } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, PointElement, LineElement, LinearScale } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, PointElement, LineElement, LinearScale);

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  },
  darkMode: {
    type: Boolean,
    default: false
  }
});

const chartData = computed(() => {
  const sourceData = props.config.data || props.config;
  const datasets = sourceData.datasets || [];

  return {
    datasets: datasets.map(ds => ({
      ...ds,
      backgroundColor: ds.backgroundColor || '#5a5cf2',
      borderColor: ds.borderColor || ds.backgroundColor || '#5a5cf2',
      pointRadius: ds.pointRadius || 6
    }))
  };
});

const chartOptions = computed(() => {
  const explicitOptions = props.config.options || {};
  const explicitPlugins = explicitOptions.plugins || {};
  const explicitLegend = explicitPlugins.legend || {};
  const explicitLegendLabels = explicitLegend.labels || {};
  const explicitTitle = explicitPlugins.title || {};

  const explicitScales = explicitOptions.scales || {};
  const explicitX = explicitScales.x || {};
  const explicitY = explicitScales.y || {};
  const explicitXTicks = explicitX.ticks || {};
  const explicitYTicks = explicitY.ticks || {};
  const explicitXGrid = explicitX.grid || {};
  const explicitYGrid = explicitY.grid || {};
  const explicitXTitle = explicitX.title || {};
  const explicitYTitle = explicitY.title || {};

  const tituloY = props.config.titulo_eje_y || explicitYTitle.text;
  const tituloX = props.config.titulo_eje_x || explicitXTitle.text;
  const textColor = props.darkMode ? '#E2E8F0' : '#334155';
  const gridColor = props.darkMode ? 'rgba(148, 163, 184, 0.25)' : 'rgba(100, 116, 139, 0.2)';

  return {
    responsive: true,
    maintainAspectRatio: false,
    ...explicitOptions,
    plugins: {
      ...explicitPlugins,
      legend: {
        position: explicitLegend.position ?? 'bottom',
        ...explicitLegend,
        labels: {
          ...explicitLegendLabels,
          color: explicitLegendLabels.color ?? textColor
        }
      },
      title: {
        ...explicitTitle,
        display: explicitTitle.display ?? !!tituloY,
        text: explicitTitle.text ?? tituloY,
        color: explicitTitle.color ?? textColor
      }
    },
    scales: {
      ...explicitScales,
      x: {
        ...explicitX,
        type: 'linear',
        position: explicitX.position ?? 'bottom',
        ticks: {
          ...explicitXTicks,
          color: explicitXTicks.color ?? textColor
        },
        grid: {
          ...explicitXGrid,
          color: explicitXGrid.color ?? gridColor
        },
        title: {
          ...explicitXTitle,
          display: explicitXTitle.display ?? !!tituloX,
          text: explicitXTitle.text ?? tituloX,
          color: explicitXTitle.color ?? textColor
        },
      },
      y: {
        ...explicitY,
        beginAtZero: explicitY.beginAtZero ?? true,
        ticks: {
          ...explicitYTicks,
          color: explicitYTicks.color ?? textColor
        },
        grid: {
          ...explicitYGrid,
          color: explicitYGrid.color ?? gridColor
        },
        title: {
          ...explicitYTitle,
          display: explicitYTitle.display ?? !!tituloY,
          text: explicitYTitle.text ?? tituloY,
          color: explicitYTitle.color ?? textColor
        },
      }
    }
  };
});
</script>
