<template>
  <el-card class="chart-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ title }}</span>
      </div>
    </template>
    <div v-if="hasData" ref="chartRef" class="chart-container"></div>
    <div v-else class="empty-wrapper">
      <el-empty :description="emptyDescription">
        <template #extra>
          <el-button :type="emptyButtonType" @click="$emit('empty-action')">
            {{ emptyActionLabel }}
          </el-button>
        </template>
      </el-empty>
    </div>
  </el-card>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: {
    type: String,
    default: '成本 / 收益趨勢',
  },
  items: {
    type: Array,
    default: () => [],
  },
  emptyActionLabel: {
    type: String,
    required: true,
  },
  emptyButtonType: {
    type: String,
    default: 'primary',
  },
  emptyDescription: {
    type: String,
    default: '尚無資料',
  },
})

const chartRef = ref(null)
let chartInstance = null

const hasData = computed(() => (props.items ?? []).length > 0)

const renderChart = () => {
  if (!chartRef.value || !hasData.value) {
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
    return
  }

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)
  const labels = props.items.map((item) => item.group)
  const costData = props.items.map((item) => Number(item.metrics?.total_cost ?? 0))
  const revenueData = props.items.map((item) => Number(item.metrics?.total_revenue ?? 0))

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['總成本', '總收益'] },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value' },
    series: [
      { name: '總成本', type: 'line', data: costData, smooth: true },
      { name: '總收益', type: 'line', data: revenueData, smooth: true },
    ],
  })
}

watch(
  () => props.items,
  () => {
    nextTick(() => renderChart())
  },
  { deep: true }
)

onMounted(() => {
  nextTick(() => renderChart())
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>
