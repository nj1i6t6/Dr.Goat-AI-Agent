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

import { formatCohortGroupLabel } from '../../utils/analyticsFormatting'

const props = defineProps({
  title: {
    type: String,
    default: '分群淨收益',
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
  const categories = props.items.map((item) => formatCohortGroupLabel(item))
  const profits = props.items.map((item) => Number(item.metrics?.net_profit ?? 0))

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value', name: '淨收益 (TWD)' },
    series: [
      {
        name: '淨收益',
        type: 'bar',
        data: profits,
        itemStyle: { color: '#3b82f6' },
      },
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
