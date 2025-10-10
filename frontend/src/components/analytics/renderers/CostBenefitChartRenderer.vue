<template>
  <div ref="chartRef" class="chart-shell" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useLazyCharts } from '@/composables/useLazyCharts';

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
});

const chartRef = ref(null);
const { ensureChart, dispose } = useLazyCharts(chartRef, { initOptions: { renderer: 'canvas' } });

const hasData = computed(() => (props.items ?? []).length > 0);

const renderChart = async () => {
  if (!hasData.value) {
    dispose();
    return;
  }

  const chart = await ensureChart();
  if (!chart) return;

  const labels = props.items.map((item) => item.group);
  const costData = props.items.map((item) => Number(item.metrics?.total_cost ?? 0));
  const revenueData = props.items.map((item) => Number(item.metrics?.total_revenue ?? 0));

  chart.setOption(
    {
      grid: {
        left: '6%',
        right: '6%',
        top: 48,
        bottom: 40,
      },
      tooltip: { trigger: 'axis' },
      legend: {
        data: ['總成本', '總收益'],
        textStyle: { color: 'var(--aurora-text-muted)' },
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.4)' } },
        axisLabel: { color: 'var(--aurora-text-muted)' },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.4)' } },
        splitLine: { lineStyle: { color: 'var(--aurora-gridline)' } },
        axisLabel: { color: 'var(--aurora-text-muted)' },
      },
      series: [
        {
          name: '總成本',
          type: 'line',
          smooth: true,
          data: costData,
          lineStyle: {
            width: 3,
            color: 'rgba(14, 165, 233, 0.85)',
          },
          areaStyle: {
            color: 'rgba(14, 165, 233, 0.18)',
          },
        },
        {
          name: '總收益',
          type: 'line',
          smooth: true,
          data: revenueData,
          lineStyle: {
            width: 3,
            color: 'rgba(168, 85, 247, 0.85)',
          },
          areaStyle: {
            color: 'rgba(168, 85, 247, 0.18)',
          },
        },
      ],
    },
    { notMerge: true }
  );
};

watch(
  () => props.items,
  () => {
    renderChart();
  },
  { deep: true }
);

onMounted(() => {
  renderChart();
});

onBeforeUnmount(() => {
  dispose();
});
</script>

<style scoped>
.chart-shell {
  width: 100%;
  min-height: 320px;
}
</style>
