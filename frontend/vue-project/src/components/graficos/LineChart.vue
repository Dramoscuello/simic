<template>
  <div class="w-full h-64 md:h-80">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale);

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
  // Support both flat structure (legacy) and nested 'data' structure (standard Chart.js)
  const sourceData = props.config.data || props.config;
  const labels = sourceData.labels || [];
  const datasets = sourceData.datasets || [];

  return {
    labels: labels,
    datasets: datasets.map(ds => ({
        ...ds, // Keep original props
        fill: ds.fill !== undefined ? ds.fill : false,
        tension: ds.tension !== undefined ? ds.tension : 0.1,
        backgroundColor: ds.backgroundColor || '#5a5cf2',
        borderColor: ds.borderColor || ds.backgroundColor || '#5a5cf2',
        borderWidth: ds.borderWidth || 2
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
  const textColor = props.darkMode ? '#FFFFFF' : '#334155';
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
        color: explicitTitle.color ?? textColor
      }
    },
    scales: {
      ...explicitScales,
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
      },
      x: {
        ...explicitX,
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
        }
      }
    }
  };
});
</script>
