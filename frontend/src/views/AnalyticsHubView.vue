<template>
  <div class="analytics-hub">
    <el-page-header content="Analytics Hub" class="page-header" />

    <el-row :gutter="16">
      <el-col :lg="18" :md="24">
        <el-card class="filters-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>分析篩選條件</span>
            </div>
          </template>
          <el-form label-width="90px" :model="filters" class="filters-form">
            <el-row :gutter="12">
              <el-col :md="12" :sm="24">
                <el-form-item label="時間範圍">
                  <el-date-picker
                    v-model="filters.timeRange"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="開始日期"
                    end-placeholder="結束日期"
                    value-format="YYYY-MM-DD"
                    unlink-panels
                  />
                </el-form-item>
              </el-col>
              <el-col :md="12" :sm="24">
                <el-form-item label="聚合維度">
                  <el-select v-model="filters.cohortBy" multiple collapse-tags placeholder="選擇維度">
                    <el-option
                      v-for="item in dimensionOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :md="12" :sm="24">
                <el-form-item label="指標">
                  <el-select v-model="filters.metrics" multiple collapse-tags placeholder="選擇 KPI">
                    <el-option v-for="item in metricOptions" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :md="12" :sm="24">
                <el-form-item label="成本分類">
                  <el-select v-model="filters.categories" multiple collapse-tags placeholder="全部">
                    <el-option label="飼料" value="feed" />
                    <el-option label="保健" value="health" />
                    <el-option label="人工" value="labor" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>

        <el-alert
          v-if="store.error"
          class="error-alert"
          type="error"
          show-icon
          :closable="false"
        >
          {{ store.error }}
        </el-alert>

        <el-row :gutter="16" class="kpi-row">
          <el-col v-for="card in store.kpiCards" :key="card.label" :lg="8" :md="12" :sm="12" :xs="24">
            <el-card shadow="hover" class="kpi-card">
              <div class="kpi-label">{{ card.label }}</div>
              <div class="kpi-value">{{ formatNumber(card.value) }}<span class="kpi-unit">{{ card.unit }}</span></div>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>分群淨收益</span>
            </div>
          </template>
          <div v-if="store.cohortHasData" ref="cohortChartRef" class="chart-container"></div>
          <div v-else class="empty-wrapper">
            <el-empty description="尚無資料">
              <template #extra>
                <el-button type="primary" @click="scrollToFinanceForms('cost')">前往新增成本紀錄</el-button>
              </template>
            </el-empty>
          </div>
        </el-card>

        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>成本 / 收益趨勢</span>
            </div>
          </template>
          <div v-if="store.costBenefitHasData" ref="costBenefitChartRef" class="chart-container"></div>
          <div v-else class="empty-wrapper">
            <el-empty description="尚無資料">
              <template #extra>
                <el-button type="primary" @click="scrollToFinanceForms('revenue')">前往新增收益紀錄</el-button>
              </template>
            </el-empty>
          </div>
        </el-card>
      </el-col>

      <el-col :lg="6" :md="24">
        <div ref="financeSectionRef" class="finance-section">
          <el-card class="form-card" shadow="never">
            <template #header>
              <span>新增成本紀錄</span>
            </template>
            <el-form ref="costFormRef" :model="costForm" :rules="financeRules" label-width="90px">
              <el-form-item label="日期" prop="recorded_at">
                <el-date-picker v-model="costForm.recorded_at" type="date" value-format="YYYY-MM-DD" placeholder="選擇日期" />
              </el-form-item>
              <el-form-item label="分類" prop="category">
                <el-input v-model="costForm.category" placeholder="例如：feed" />
              </el-form-item>
              <el-form-item label="金額" prop="amount">
                <el-input-number v-model="costForm.amount" :min="0" :precision="2" />
              </el-form-item>
              <el-form-item label="備註">
                <el-input v-model="costForm.notes" type="textarea" :rows="2" />
              </el-form-item>
              <el-button type="primary" :loading="store.loading.costEntries" @click="submitCostForm">新增成本</el-button>
            </el-form>
          </el-card>

          <el-card class="form-card" shadow="never">
            <template #header>
              <span>新增收益紀錄</span>
            </template>
            <el-form ref="revenueFormRef" :model="revenueForm" :rules="financeRules" label-width="90px">
              <el-form-item label="日期" prop="recorded_at">
                <el-date-picker v-model="revenueForm.recorded_at" type="date" value-format="YYYY-MM-DD" placeholder="選擇日期" />
              </el-form-item>
              <el-form-item label="分類" prop="category">
                <el-input v-model="revenueForm.category" placeholder="例如：milk" />
              </el-form-item>
              <el-form-item label="金額" prop="amount">
                <el-input-number v-model="revenueForm.amount" :min="0" :precision="2" />
              </el-form-item>
              <el-form-item label="備註">
                <el-input v-model="revenueForm.notes" type="textarea" :rows="2" />
              </el-form-item>
              <el-button type="success" :loading="store.loading.revenueEntries" @click="submitRevenueForm">新增收益</el-button>
            </el-form>
          </el-card>

          <el-card class="form-card" shadow="never">
            <template #header>
              <span>AI 報告</span>
            </template>
            <el-form label-width="80px">
              <el-form-item label="API Key">
                <el-input v-model="reportApiKey" placeholder="輸入 X-Api-Key" />
              </el-form-item>
              <el-form-item label="備註">
                <el-input v-model="reportNotes" type="textarea" :rows="2" placeholder="可選的補充說明" />
              </el-form-item>
              <el-text class="helper-text" size="small">使用下方浮動按鈕即可即時產生報告</el-text>
              <el-button class="mt-2" text type="primary" :disabled="!store.reportState.markdown" @click="copyReport">複製 Markdown</el-button>
              <el-button class="mt-2" text type="primary" :disabled="!store.reportState.markdown" @click="downloadReport">下載報告</el-button>
            </el-form>
            <div v-if="store.reportState.html" class="report-preview" v-html="store.reportState.html"></div>
          </el-card>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="tables-row">
      <el-col :md="12" :sm="24">
        <el-card shadow="never">
          <template #header>
            <span>最新成本紀錄</span>
          </template>
          <el-table :data="store.costEntries" size="small" height="260">
            <el-table-column prop="recorded_at" label="日期" width="120" />
            <el-table-column prop="category" label="分類" />
            <el-table-column prop="amount" label="金額" width="100" />
            <el-table-column prop="notes" label="備註" />
            <el-table-column label="操作" width="80">
              <template #default="scope">
                <el-button type="danger" size="small" link @click="store.removeCostEntry(scope.row.id)">刪除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="尚無資料">
                <template #extra>
                  <el-button type="primary" @click="scrollToFinanceForms('cost')">前往新增成本紀錄</el-button>
                </template>
              </el-empty>
            </template>
          </el-table>
        </el-card>
      </el-col>
      <el-col :md="12" :sm="24">
        <el-card shadow="never">
          <template #header>
            <span>最新收益紀錄</span>
          </template>
          <el-table :data="store.revenueEntries" size="small" height="260">
            <el-table-column prop="recorded_at" label="日期" width="120" />
            <el-table-column prop="category" label="分類" />
            <el-table-column prop="amount" label="金額" width="100" />
            <el-table-column prop="notes" label="備註" />
            <el-table-column label="操作" width="80">
              <template #default="scope">
                <el-button type="danger" size="small" link @click="store.removeRevenueEntry(scope.row.id)">刪除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="尚無資料">
                <template #extra>
                  <el-button type="success" @click="scrollToFinanceForms('revenue')">前往新增收益紀錄</el-button>
                </template>
              </el-empty>
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <div class="floating-actions">
      <el-button-group>
        <el-button
          class="fab-button"
          type="primary"
          :loading="store.loading.cohort || store.loading.costBenefit"
          @click="runAnalysis"
        >
          重新分析
        </el-button>
        <el-button
          class="fab-button"
          type="info"
          :disabled="!store.costBenefitHasData && !(store.costBenefitResult?.summary)"
          @click="exportCostBenefitCsv"
        >
          匯出 CSV
        </el-button>
        <el-button
          class="fab-button"
          type="success"
          :loading="store.loading.report"
          :disabled="!reportApiKey"
          @click="generateReport"
        >
          產生報告
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useAnalyticsStore } from '../stores/analytics'

const store = useAnalyticsStore()

const filters = reactive({
  timeRange: [],
  cohortBy: ['breed'],
  metrics: ['sheep_count', 'total_cost', 'total_revenue', 'net_profit'],
  categories: [],
})

const dimensionOptions = [
  { label: '品種', value: 'breed' },
  { label: '胎次', value: 'lactation_number' },
  { label: '生產階段', value: 'production_stage' },
]

const metricOptions = [
  { label: '羊隻數量', value: 'sheep_count' },
  { label: '平均體重', value: 'avg_weight' },
  { label: '總成本', value: 'total_cost' },
  { label: '總收益', value: 'total_revenue' },
  { label: '淨收益', value: 'net_profit' },
  { label: '每頭成本', value: 'cost_per_head' },
  { label: '每頭收益', value: 'revenue_per_head' },
]

const costFormRef = ref()
const revenueFormRef = ref()
const cohortChartRef = ref(null)
const costBenefitChartRef = ref(null)
const reportApiKey = ref('')
const reportNotes = ref('')

const financeRules = {
  recorded_at: [{ required: true, message: '請選擇日期', trigger: 'change' }],
  category: [{ required: true, message: '請輸入分類', trigger: 'blur' }],
  amount: [{ required: true, message: '請輸入金額', trigger: 'blur' }],
}

const costForm = reactive({
  recorded_at: '',
  category: '',
  amount: null,
  notes: '',
})

const revenueForm = reactive({
  recorded_at: '',
  category: '',
  amount: null,
  notes: '',
})

let cohortChartInstance = null
let costBenefitChartInstance = null

const financeSectionRef = ref(null)

const formatNumber = (value) => {
  if (value == null) return '—'
  return new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 }).format(value)
}

const formatGroupLabel = (item) => {
  const dims = Object.entries(item || {}).filter(([key]) => key !== 'metrics')
  if (!dims.length) return '全部'
  return dims
    .map(([key, value]) => {
      if (value == null || value === '未填寫') {
        return `${key}:未指定`
      }
      return `${key}:${value}`
    })
    .join(' / ')
}

const runAnalysis = async () => {
  const payload = {
    cohort_by: filters.cohortBy,
    metrics: filters.metrics,
    filters: {},
  }
  if (filters.categories.length) {
    payload.filters.category = filters.categories
  }
  if (filters.timeRange?.length === 2) {
    payload.time_range = {
      start: new Date(filters.timeRange[0]).toISOString(),
      end: new Date(filters.timeRange[1]).toISOString(),
    }
  }
  await Promise.all([
    store.fetchCohortAnalysis(payload),
    store.fetchCostBenefit({
      filters: payload.filters,
      time_range: payload.time_range,
      metrics: ['total_cost', 'total_revenue', 'net_profit', 'avg_cost_per_head', 'avg_revenue_per_head'],
      group_by: 'month',
    }),
  ])
  await nextTick()
  renderCharts()
}

const submitCostForm = () => {
  costFormRef.value.validate(async (valid) => {
    if (!valid) return
    await store.saveCostEntry({
      ...costForm,
      recorded_at: new Date(costForm.recorded_at).toISOString(),
    })
    Object.assign(costForm, { recorded_at: '', category: '', amount: null, notes: '' })
    ElMessage.success('已新增成本紀錄')
  })
}

const submitRevenueForm = () => {
  revenueFormRef.value.validate(async (valid) => {
    if (!valid) return
    await store.saveRevenueEntry({
      ...revenueForm,
      recorded_at: new Date(revenueForm.recorded_at).toISOString(),
    })
    Object.assign(revenueForm, { recorded_at: '', category: '', amount: null, notes: '' })
    ElMessage.success('已新增收益紀錄')
  })
}

const renderCohortChart = () => {
  if (!cohortChartRef.value || !store.cohortHasData) {
    if (cohortChartInstance) {
      cohortChartInstance.dispose()
      cohortChartInstance = null
    }
    return
  }
  if (cohortChartInstance) {
    cohortChartInstance.dispose()
  }
  cohortChartInstance = echarts.init(cohortChartRef.value)
  const items = store.cohortResult?.items || []
  const categories = items.map((item) => formatGroupLabel(item))
  const profits = items.map((item) => Number(item.metrics?.net_profit ?? 0))
  cohortChartInstance.setOption({
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

const renderCostBenefitChart = () => {
  if (!costBenefitChartRef.value || !store.costBenefitHasData) {
    if (costBenefitChartInstance) {
      costBenefitChartInstance.dispose()
      costBenefitChartInstance = null
    }
    return
  }
  if (costBenefitChartInstance) {
    costBenefitChartInstance.dispose()
  }
  costBenefitChartInstance = echarts.init(costBenefitChartRef.value)
  const items = store.costBenefitResult?.items || []
  const labels = items.map((item) => item.group)
  const costData = items.map((item) => item.metrics?.total_cost ?? 0)
  const revenueData = items.map((item) => item.metrics?.total_revenue ?? 0)
  costBenefitChartInstance.setOption({
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

const renderCharts = () => {
  renderCohortChart()
  renderCostBenefitChart()
}

const generateReport = async () => {
  if (!reportApiKey.value) {
    ElMessage.warning('請先填寫 API Key')
    return
  }
  const reportFilters = {}
  if (filters.categories.length) {
    reportFilters.category = [...filters.categories]
  }
  if (filters.timeRange?.length === 2) {
    reportFilters.time_range = `${filters.timeRange[0]} 至 ${filters.timeRange[1]}`
  }
  await store.generateReport({
    apiKey: reportApiKey.value,
    filters: reportFilters,
    cohort: store.cohortResult?.items || [],
    cost_benefit: store.costBenefitResult || {},
    insights: reportNotes.value ? [reportNotes.value] : [],
  })
  ElMessage.success('AI 報告已產生')
}

const scrollToFinanceForms = (target = 'cost') => {
  if (financeSectionRef.value) {
    financeSectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  nextTick(() => {
    const formEl = target === 'cost' ? costFormRef.value?.$el : revenueFormRef.value?.$el
    const input = formEl?.querySelector('input')
    input?.focus()
  })
}

const exportCostBenefitCsv = () => {
  const analysis = store.costBenefitResult
  const summary = analysis?.summary
  const items = analysis?.items || []
  if ((!items.length) && !summary) {
    ElMessage.warning('目前沒有可匯出的分析資料')
    return
  }

  const formatCsvNumber = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return ''
    }
    return Number(value).toFixed(2)
  }

  const rows = [['群組', '總成本', '總收益', '淨收益', '成本收益比']]
  items.forEach((item) => {
    const metrics = item.metrics || {}
    const totalCost = Number(metrics.total_cost ?? 0)
    const totalRevenue = Number(metrics.total_revenue ?? 0)
    const netProfit = Number(metrics.net_profit ?? 0)
    const ratio = totalCost ? totalRevenue / totalCost : null
    rows.push([
      `"${item.group}"`,
      formatCsvNumber(totalCost),
      formatCsvNumber(totalRevenue),
      formatCsvNumber(netProfit),
      ratio === null ? '' : formatCsvNumber(ratio),
    ])
  })
  if (summary) {
    const totalCost = Number(summary.total_cost ?? 0)
    const totalRevenue = Number(summary.total_revenue ?? 0)
    const netProfit = Number(summary.net_profit ?? 0)
    const ratio = totalCost ? totalRevenue / totalCost : null
    rows.push([
      '"總計"',
      formatCsvNumber(totalCost),
      formatCsvNumber(totalRevenue),
      formatCsvNumber(netProfit),
      ratio === null ? '' : formatCsvNumber(ratio),
    ])
  }

  const csvContent = rows.map((row) => row.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `cost-benefit-${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已匯出成本收益 CSV')
}

const copyReport = async () => {
  if (!store.reportState.markdown) return
  try {
    await navigator.clipboard.writeText(store.reportState.markdown)
    ElMessage.success('已複製 Markdown')
  } catch (err) {
    ElMessage.error('複製失敗，請手動選取內容')
  }
}

const downloadReport = () => {
  if (!store.reportState.markdown) return
  const blob = new Blob([store.reportState.markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `analytics-report-${Date.now()}.md`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await Promise.all([store.loadCostEntries(), store.loadRevenueEntries()])
  await runAnalysis()
})

watch(
  () => store.cohortResult,
  () => {
    nextTick(() => renderCohortChart())
  },
  { deep: true }
)

watch(
  () => store.costBenefitResult,
  () => {
    nextTick(() => renderCostBenefitChart())
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (cohortChartInstance) {
    cohortChartInstance.dispose()
  }
  if (costBenefitChartInstance) {
    costBenefitChartInstance.dispose()
  }
})
</script>

<style scoped>
.analytics-hub {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  margin-bottom: 8px;
}

.filters-card {
  margin-bottom: 16px;
}

.filters-form {
  width: 100%;
}

.error-alert {
  margin-bottom: 12px;
}

.kpi-row {
  margin-bottom: 16px;
}

.kpi-card {
  text-align: center;
  padding: 12px 0;
}

.kpi-label {
  font-size: 0.9rem;
  color: #475569;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 1.6rem;
  font-weight: 600;
}

.kpi-unit {
  font-size: 0.8rem;
  margin-left: 4px;
  color: #64748b;
}

.chart-card {
  margin-bottom: 16px;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.form-card {
  margin-bottom: 16px;
}

.finance-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.helper-text {
  display: block;
  color: #64748b;
}

.report-preview {
  margin-top: 12px;
  padding: 12px;
  border: 1px dashed #cbd5f5;
  border-radius: 6px;
  max-height: 280px;
  overflow: auto;
}

.empty-wrapper {
  padding: 32px 0;
}

.tables-row {
  margin-top: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.floating-actions {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1000;
}

.fab-button {
  min-width: 120px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.18);
}

@media (max-width: 768px) {
  .chart-container {
    height: 260px;
  }

  .floating-actions {
    right: 16px;
    bottom: 16px;
  }
}
</style>
