<template>
  <div ref="chartRef" class="chart-shell" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useLazyCharts } from '@/composables/useLazyCharts';
import { formatCohortGroupLabel } from '@/utils/analyticsFormatting';

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

  const categories = props.items.map((item) => formatCohortGroupLabel(item));
  const profits = props.items.map((item) => Number(item.metrics?.net_profit ?? 0));

  chart.setOption(
    {
      grid: {
        left: '5%',
        right: '5%',
        top: 40,
        bottom: 40,
      },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.4)' } },
        axisLabel: { color: 'var(--aurora-text-muted)' },
      },
      yAxis: {
        type: 'value',
        name: '淨收益 (TWD)',
        axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.4)' } },
        splitLine: { lineStyle: { color: 'var(--aurora-gridline)' } },
        axisLabel: { color: 'var(--aurora-text-muted)' },
      },
      series: [
        {
          name: '淨收益',
          type: 'bar',
          data: profits,
          itemStyle: {
            borderRadius: [10, 10, 0, 0],
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(14, 165, 233, 0.95)' },
                { offset: 1, color: 'rgba(168, 85, 247, 0.65)' },
              ],
            },
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
