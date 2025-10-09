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
          class="error-bar"
          type="error"
          show-icon
          :closable="false"
          :description="store.error"
        />

        <el-row v-if="store.kpiCards.length" :gutter="16" class="kpi-row">
          <el-col v-for="card in store.kpiCards" :key="card.label" :lg="6" :md="12" :sm="12" :xs="24">
            <el-card shadow="hover" class="kpi-card">
              <div class="kpi-label">{{ card.label }}</div>
              <div class="kpi-value">{{ formatKpiValue(card) }}<span v-if="card.unit" class="kpi-unit">{{ card.unit }}</span></div>
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
          <el-empty v-else description="尚無資料">
            <el-button type="primary" @click="navigateToFinance('cost')">前往新增成本紀錄</el-button>
          </el-empty>
        </el-card>

        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>成本 / 收益趨勢</span>
            </div>
          </template>
          <div v-if="store.costBenefitHasData" ref="costBenefitChartRef" class="chart-container"></div>
          <el-empty v-else description="尚無資料">
            <el-button type="primary" @click="navigateToFinance('revenue')">前往新增收益紀錄</el-button>
          </el-empty>
        </el-card>
      </el-col>

      <el-col :lg="6" :md="24">
        <el-card ref="costFormSection" class="form-card" shadow="never">
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

        <el-card ref="revenueFormSection" class="form-card" shadow="never">
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
            <el-button class="mt-2" text type="primary" :disabled="!store.reportState.markdown" @click="copyReport">複製 Markdown</el-button>
            <el-button class="mt-2" text type="primary" :disabled="!store.reportState.markdown" @click="downloadReport">下載報告</el-button>
          </el-form>
          <div v-if="store.reportState.html" class="report-preview" v-html="store.reportState.html"></div>
        </el-card>
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
              <el-empty description="尚無成本資料">
                <el-button type="primary" @click="navigateToFinance('cost')">前往新增成本紀錄</el-button>
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
              <el-empty description="尚無收益資料">
                <el-button type="primary" @click="navigateToFinance('revenue')">前往新增收益紀錄</el-button>
              </el-empty>
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <div class="fab-container">
    <el-button-group>
      <el-button
        type="primary"
        round
        :loading="store.loading.cohort || store.loading.costBenefit"
        @click="runAnalysis"
      >
        重新分析
      </el-button>
      <el-button
        type="success"
        round
        :disabled="!store.cohortHasData && !store.costBenefitHasData"
        @click="exportAnalysisCsv"
      >
        匯出 CSV
      </el-button>
      <el-button
        type="warning"
        round
        :loading="store.loading.report"
        @click="generateReport"
      >
        產生報告
      </el-button>
    </el-button-group>
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
const costFormSection = ref(null)
const revenueFormSection = ref(null)
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

const numberFormatter = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 })
const ratioFormatter = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 })

const formatKpiValue = (card) => {
  if (card.value == null) return '—'
  if (card.type === 'ratio') {
    return `${ratioFormatter.format(card.value)}×`
  }
  return numberFormatter.format(card.value)
}

const buildFiltersPayload = () => {
  const payload = {}
  if (filters.categories.length) {
    payload.category = [...filters.categories]
  }
  return payload
}

const buildTimeRangePayload = () => {
  if (filters.timeRange?.length === 2) {
    return {
      start: new Date(filters.timeRange[0]).toISOString(),
      end: new Date(filters.timeRange[1]).toISOString(),
    }
  }
  return undefined
}

const buildAnalysisPayload = () => {
  const baseFilters = buildFiltersPayload()
  const payload = {
    cohort_by: [...filters.cohortBy],
    metrics: [...filters.metrics],
    filters: baseFilters,
  }
  const timeRange = buildTimeRangePayload()
  if (timeRange) {
    payload.time_range = timeRange
  }
  return payload
}

const runAnalysis = async () => {
  const analysisPayload = buildAnalysisPayload()
  const costBenefitPayload = {
    filters: analysisPayload.filters,
    time_range: analysisPayload.time_range,
    metrics: ['total_cost', 'total_revenue', 'net_profit', 'avg_cost_per_head', 'avg_revenue_per_head'],
    group_by: 'month',
  }
  try {
    await Promise.all([
      store.fetchCohortAnalysis(analysisPayload),
      store.fetchCostBenefit(costBenefitPayload),
    ])
    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('分析失敗', error)
  }
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

const disposeCohortChart = () => {
  if (cohortChartInstance) {
    cohortChartInstance.dispose()
    cohortChartInstance = null
  }
}

const disposeCostBenefitChart = () => {
  if (costBenefitChartInstance) {
    costBenefitChartInstance.dispose()
    costBenefitChartInstance = null
  }
}

const renderCohortChart = () => {
  if (!store.cohortHasData) {
    disposeCohortChart()
    return
  }
  if (!cohortChartRef.value) return
  disposeCohortChart()
  cohortChartInstance = echarts.init(cohortChartRef.value)
  const items = store.cohortResult?.items || []
  const categories = items.map((item) => item.breed || item.production_stage || '未指定')
  const profits = items.map((item) => item.metrics?.net_profit ?? 0)
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
  if (!store.costBenefitHasData) {
    disposeCostBenefitChart()
    return
  }
  if (!costBenefitChartRef.value) return
  disposeCostBenefitChart()
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

const buildReportFilters = () => {
  const reportFilters = {}
  if (filters.categories.length) {
    reportFilters.category = [...filters.categories]
  }
  if (filters.timeRange?.length === 2) {
    reportFilters.time_range = `${filters.timeRange[0]} 至 ${filters.timeRange[1]}`
  }
  return reportFilters
}

const generateReport = async () => {
  if (!reportApiKey.value) {
    ElMessage.warning('請先填寫 API Key')
    return
  }
  try {
    await store.generateReport(
      {
        filters: buildReportFilters(),
        cohort: store.cohortResult?.items || [],
        cost_benefit: store.costBenefitResult || {},
        insights: reportNotes.value ? [reportNotes.value] : [],
      },
      reportApiKey.value,
    )
    ElMessage.success('AI 報告已產生')
  } catch (error) {
    console.error('產生報告失敗', error)
    ElMessage.error('產生報告失敗，請稍後再試')
  }
}

const escapeCsv = (value) => {
  if (value == null) return ''
  const str = String(value)
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

const exportAnalysisCsv = () => {
  const lines = []
  const cohortItems = store.cohortResult?.items || []
  if (cohortItems.length) {
    lines.push('Cohort Analysis')
    const cohortMetrics = store.cohortResult?.metrics || []
    const header = ['Group', ...cohortMetrics]
    lines.push(header.map(escapeCsv).join(','))
    cohortItems.forEach((item) => {
      const dims = Object.entries(item)
        .filter(([key]) => key !== 'metrics')
        .map(([, value]) => value)
        .filter((value) => value != null)
      const label = dims.length ? dims.join(' / ') : '未指定'
      const row = [label, ...cohortMetrics.map((metric) => item.metrics?.[metric] ?? '')]
      lines.push(row.map(escapeCsv).join(','))
    })
    lines.push('')
  }

  const costBenefit = store.costBenefitResult
  if (costBenefit) {
    lines.push('Cost Benefit Summary')
    const summary = costBenefit.summary || {}
    lines.push(['total_cost', summary.total_cost ?? ''].map(escapeCsv).join(','))
    lines.push(['total_revenue', summary.total_revenue ?? ''].map(escapeCsv).join(','))
    lines.push(['net_profit', summary.net_profit ?? ''].map(escapeCsv).join(','))
    lines.push('')
    const metricsHeader = ['Group', ...(costBenefit.metrics || [])]
    lines.push(metricsHeader.map(escapeCsv).join(','))
    ;(costBenefit.items || []).forEach((item) => {
      const row = [item.group, ...(costBenefit.metrics || []).map((metric) => item.metrics?.[metric] ?? '')]
      lines.push(row.map(escapeCsv).join(','))
    })
  }

  const csvContent = lines.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `analytics-export-${Date.now()}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已匯出分析 CSV')
}

const scrollToElement = (elementRef) => {
  const el = elementRef?.value?.$el ?? elementRef?.value
  if (el?.scrollIntoView) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const navigateToFinance = (type) => {
  if (type === 'cost') {
    scrollToElement(costFormSection)
  } else {
    scrollToElement(revenueFormSection)
  }
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
    nextTick(() => {
      if (store.cohortHasData) {
        renderCohortChart()
      } else {
        disposeCohortChart()
      }
    })
  },
  { deep: true }
)

watch(
  () => store.costBenefitResult,
  () => {
    nextTick(() => {
      if (store.costBenefitHasData) {
        renderCostBenefitChart()
      } else {
        disposeCostBenefitChart()
      }
    })
  },
  { deep: true }
)

onBeforeUnmount(() => {
  disposeCohortChart()
  disposeCostBenefitChart()
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

.error-bar {
  margin-bottom: 16px;
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

.report-preview {
  margin-top: 12px;
  padding: 12px;
  border: 1px dashed #cbd5f5;
  border-radius: 6px;
  max-height: 280px;
  overflow: auto;
}

.tables-row {
  margin-top: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fab-container {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 30;
}

.fab-container :deep(.el-button-group) {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
  border-radius: 999px;
  overflow: hidden;
}

.fab-container :deep(.el-button) {
  padding: 0 20px;
}

@media (max-width: 768px) {
  .chart-container {
    height: 260px;
  }

  .fab-container {
    right: 12px;
    bottom: 12px;
  }
}
</style>
