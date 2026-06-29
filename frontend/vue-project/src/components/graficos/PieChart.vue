<template>
  <div class="w-full h-64 md:h-80">
    <Pie :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Pie } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, ArcElement);

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

const defaultColors = [
  '#5a5cf2', '#10b981', '#f59e0b', '#ef4444', 
  '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
  '#6366f1', '#14b8a6', '#f97316', '#d946ef'
];

const chartData = computed(() => {
  const sourceData = props.config.data || props.config;
  const labels = sourceData.labels || [];
  const datasets = sourceData.datasets || [];

  return {
    labels: labels,
    datasets: datasets.map(ds => ({
      ...ds,
      backgroundColor: ds.backgroundColor || defaultColors,
      borderColor: ds.borderColor || '#ffffff',
      borderWidth: 2
    }))
  };
});

const chartOptions = computed(() => {
  const explicitOptions = props.config.options || {};
  const explicitPlugins = explicitOptions.plugins || {};
  const explicitLegend = explicitPlugins.legend || {};
  const explicitLegendLabels = explicitLegend.labels || {};
  const explicitTitle = explicitPlugins.title || {};
  const textColor = props.darkMode ? '#E2E8F0' : '#334155';

  return {
    responsive: true,
    maintainAspectRatio: false,
    ...explicitOptions,
    plugins: {
      ...explicitPlugins,
      legend: {
        position: explicitLegend.position ?? 'right',
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
    }
  };
});
</script>
