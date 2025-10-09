<template>
  <div class="analytics-hub">
    <section class="kpi-section">
      <h2>Analytics Hub — 關鍵績效指標</h2>
      <el-row :gutter="16">
        <el-col v-for="card in kpiCards" :key="card.key" :xs="12" :sm="8" :md="6">
          <el-card shadow="hover" class="kpi-card">
            <div class="kpi-title">{{ card.title }}</div>
            <div class="kpi-value">{{ formatMetricValue(kpis[card.key], card.format) }}</div>
            <div class="kpi-subtitle">{{ card.subtitle }}</div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section class="analytics-section">
      <el-card shadow="never" class="filter-card">
        <template #header>
          <div class="card-header">
            <span>分群分析條件</span>
            <div class="card-actions">
              <el-button text type="primary" size="small" @click="resetCohortFilters">重置</el-button>
              <el-button type="primary" size="small" :loading="loadingStates.cohort" @click="submitCohort">
                查詢 Cohort
              </el-button>
            </div>
          </div>
        </template>
        <el-form :model="cohortForm" label-width="96px" class="filter-form">
          <el-row :gutter="16">
            <el-col :xs="24" :sm="12" :md="8">
              <el-form-item label="維度">
                <el-select v-model="cohortForm.dimensions" multiple filterable placeholder="選擇分群維度" collapse-tags>
                  <el-option v-for="option in dimensionOptions" :key="option.value" :label="option.label" :value="option.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="8">
              <el-form-item label="指標">
                <el-select v-model="cohortForm.metrics" multiple filterable placeholder="選擇指標" collapse-tags>
                  <el-option v-for="option in metricOptions" :key="option.value" :label="option.label" :value="option.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="4">
              <el-form-item label="上限筆數">
                <el-input-number v-model="cohortForm.limit" :min="5" :max="200" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="12">
              <el-form-item label="時間區間">
                <el-date-picker
                  v-model="cohortForm.timeRange"
                  type="daterange"
                  unlink-panels
                  range-separator="至"
                  start-placeholder="開始日期"
                  end-placeholder="結束日期"
                  :shortcuts="dateShortcuts"
                  format="YYYY-MM-DD"
                />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="品種">
                <el-select v-model="cohortForm.filters.breed" multiple collapse-tags filterable placeholder="選擇品種">
                  <el-option v-for="option in breedOptions" :key="option" :label="option" :value="option" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="月齡群組">
                <el-select v-model="cohortForm.filters.age_group" multiple collapse-tags filterable placeholder="選擇月齡">
                  <el-option v-for="option in ageGroupOptions" :key="option" :label="option" :value="option" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="胎次">
                <el-select v-model="cohortForm.filters.parity" multiple collapse-tags filterable placeholder="選擇胎次">
                  <el-option v-for="option in parityOptions" :key="option" :label="option" :value="option" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="群組標籤">
                <el-input v-model="cohortHerdTagText" placeholder="輸入群組標籤，逗號分隔" @change="normalizeHerdTags" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-alert
            v-if="errorMessage"
            :title="errorMessage"
            type="error"
            show-icon
            class="mt-12"
          />
        </el-form>
      </el-card>

      <el-row :gutter="16" class="chart-row">
        <el-col :xs="24" :md="12">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>分群指標比較</span>
              </div>
            </template>
            <div ref="cohortChartRef" class="chart-container" />
            <el-empty v-if="!hasCohortData && !loadingStates.cohort" description="尚無資料，請調整條件" />
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>成本與收益趨勢</span>
                <div class="card-actions">
                  <el-select v-model="costBenefitForm.granularity" size="small" @change="submitCostBenefit">
                    <el-option label="逐日" value="day" />
                    <el-option label="逐月" value="month" />
                  </el-select>
                </div>
              </div>
            </template>
            <div ref="trendChartRef" class="chart-container" />
            <el-empty v-if="trendData.length === 0 && !loadingStates.costBenefit" description="尚無趨勢資料" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="table-card">
        <template #header>
          <div class="card-header">
            <span>分群明細表</span>
            <el-button text type="primary" size="small" @click="exportCohortCsv" :disabled="!hasCohortData">匯出 CSV</el-button>
          </div>
        </template>
        <el-table :data="cohortTableData" stripe size="small" v-loading="loadingStates.cohort">
          <template v-for="dimension in cohortForm.dimensions" :key="dimension">
            <el-table-column :prop="dimension" :label="dimensionLabelMap[dimension] || dimension" min-width="120" />
          </template>
          <template v-for="metric in cohortForm.metrics" :key="metric">
            <el-table-column :prop="metric" :label="metricLabelMap[metric] || metric" min-width="140" :formatter="metricFormatter" />
          </template>
        </el-table>
      </el-card>
    </section>

    <section class="finance-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>成本 / 收益資料管理</span>
          </div>
        </template>
        <el-tabs v-model="financeTab">
          <el-tab-pane label="成本" name="cost">
            <el-form ref="costFormRef" :model="costForm" :rules="financeRules" label-width="96px" class="finance-form">
              <el-row :gutter="16">
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="分類" prop="category">
                    <el-input v-model="costForm.category" placeholder="例如：飼料" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="子分類">
                    <el-input v-model="costForm.subcategory" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="金額" prop="amount">
                    <el-input-number v-model="costForm.amount" :min="0" :step="100" controls-position="right" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="紀錄時間" prop="recorded_at">
                    <el-date-picker v-model="costForm.recorded_at" type="datetime" placeholder="選擇時間" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="品種">
                    <el-input v-model="costForm.breed" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="月齡群組">
                    <el-input v-model="costForm.age_group" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="胎次">
                    <el-input-number v-model="costForm.parity" :min="0" :max="12" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="群組標籤">
                    <el-input v-model="costForm.herd_tag" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="說明">
                    <el-input v-model="costForm.description" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="備註">
                    <el-input v-model="costForm.notes" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
              </el-row>
              <div class="form-actions">
                <el-button @click="resetCostForm">重置</el-button>
                <el-button type="primary" :loading="loadingStates.costEntries" @click="submitCostForm">
                  {{ editingCostId ? '更新成本' : '新增成本' }}
                </el-button>
              </div>
            </el-form>
            <el-table :data="recentCostEntries" stripe size="small" class="mt-16">
              <el-table-column prop="category" label="分類" min-width="120" />
              <el-table-column prop="subcategory" label="子分類" min-width="120" />
              <el-table-column prop="amount" label="金額" min-width="120" :formatter="tableCurrencyFormatter" />
              <el-table-column prop="recorded_at" label="紀錄時間" min-width="180" :formatter="tableDateFormatter" />
              <el-table-column prop="breed" label="品種" min-width="120" />
              <el-table-column prop="notes" label="備註" min-width="180" show-overflow-tooltip />
              <el-table-column label="操作" min-width="160">
                <template #default="scope">
                  <el-button type="primary" link size="small" @click="loadCost(scope.row)">編輯</el-button>
                  <el-popconfirm title="確定刪除此筆資料？" @confirm="removeCost(scope.row.id)">
                    <template #reference>
                      <el-button type="danger" link size="small">刪除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="收益" name="revenue">
            <el-form ref="revenueFormRef" :model="revenueForm" :rules="financeRules" label-width="96px" class="finance-form">
              <el-row :gutter="16">
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="分類" prop="category">
                    <el-input v-model="revenueForm.category" placeholder="例如：乳品" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="子分類">
                    <el-input v-model="revenueForm.subcategory" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="金額" prop="amount">
                    <el-input-number v-model="revenueForm.amount" :min="0" :step="100" controls-position="right" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="紀錄時間" prop="recorded_at">
                    <el-date-picker v-model="revenueForm.recorded_at" type="datetime" placeholder="選擇時間" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="品種">
                    <el-input v-model="revenueForm.breed" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="月齡群組">
                    <el-input v-model="revenueForm.age_group" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="胎次">
                    <el-input-number v-model="revenueForm.parity" :min="0" :max="12" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                  <el-form-item label="群組標籤">
                    <el-input v-model="revenueForm.herd_tag" placeholder="選填" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="說明">
                    <el-input v-model="revenueForm.description" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="備註">
                    <el-input v-model="revenueForm.notes" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
              </el-row>
              <div class="form-actions">
                <el-button @click="resetRevenueForm">重置</el-button>
                <el-button type="primary" :loading="loadingStates.revenueEntries" @click="submitRevenueForm">
                  {{ editingRevenueId ? '更新收益' : '新增收益' }}
                </el-button>
              </div>
            </el-form>
            <el-table :data="recentRevenueEntries" stripe size="small" class="mt-16">
              <el-table-column prop="category" label="分類" min-width="120" />
              <el-table-column prop="subcategory" label="子分類" min-width="120" />
              <el-table-column prop="amount" label="金額" min-width="120" :formatter="tableCurrencyFormatter" />
              <el-table-column prop="recorded_at" label="紀錄時間" min-width="180" :formatter="tableDateFormatter" />
              <el-table-column prop="breed" label="品種" min-width="120" />
              <el-table-column prop="notes" label="備註" min-width="180" show-overflow-tooltip />
              <el-table-column label="操作" min-width="160">
                <template #default="scope">
                  <el-button type="primary" link size="small" @click="loadRevenue(scope.row)">編輯</el-button>
                  <el-popconfirm title="確定刪除此筆資料？" @confirm="removeRevenue(scope.row.id)">
                    <template #reference>
                      <el-button type="danger" link size="small">刪除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </section>

    <section class="ai-report-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>AI 營運報告</span>
            <div class="card-actions">
              <el-button type="primary" :loading="loadingStates.aiReport" @click="generateReport">
                生成報告
              </el-button>
            </div>
          </div>
        </template>
        <el-form :model="aiForm" label-width="120px" class="ai-form">
          <el-row :gutter="16">
            <el-col :xs="24" :md="12">
              <el-form-item label="AI API 金鑰">
                <el-input v-model="aiForm.apiKey" type="password" show-password placeholder="輸入 Gemini API key" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="亮點摘要">
                <el-input v-model="aiForm.highlights" type="textarea" :rows="2" placeholder="輸入欲強調的觀察，換行可分項" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        <el-alert
          v-if="aiReport && aiReport.report_markdown"
          title="報告已生成，可複製 Markdown 或下載 HTML"
          type="success"
          show-icon
          class="mb-12"
        />
        <div v-if="aiReport && aiReport.report_html" class="report-output" v-html="aiReport.report_html" />
        <el-empty v-else description="尚未生成報告" />
        <div class="report-actions" v-if="aiReport && aiReport.report_markdown">
          <el-button @click="copyReport">複製 Markdown</el-button>
          <el-button type="primary" @click="downloadReport">下載 HTML</el-button>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useAnalyticsStore } from '../stores/analytics'
import { storeToRefs } from 'pinia'

const analyticsStore = useAnalyticsStore()
const cohortForm = analyticsStore.cohortForm
const costBenefitForm = analyticsStore.costBenefitForm
const { loadingStates, kpis, trendData, hasCohortData, cohortResult, costBenefitResult, costEntries, revenueEntries, errorMessage, aiReport } = storeToRefs(analyticsStore)

const dimensionOptions = [
  { label: '成本分類', value: 'category' },
  { label: '子分類', value: 'subcategory' },
  { label: '品種', value: 'breed' },
  { label: '月齡群組', value: 'age_group' },
  { label: '胎次', value: 'parity' },
  { label: '群組標籤', value: 'herd_tag' },
  { label: '紀錄日期', value: 'recorded_date' }
]

const metricOptions = [
  { label: '總成本', value: 'total_cost' },
  { label: '總收益', value: 'total_revenue' },
  { label: '淨收益', value: 'net_income' },
  { label: '成本筆數', value: 'cost_entries' },
  { label: '收益筆數', value: 'revenue_entries' },
  { label: '平均成本', value: 'avg_cost' },
  { label: '平均收益', value: 'avg_revenue' },
  { label: '成本收益比', value: 'cost_revenue_ratio' }
]

const dimensionLabelMap = dimensionOptions.reduce((acc, item) => ({ ...acc, [item.value]: item.label }), {})
const metricLabelMap = metricOptions.reduce((acc, item) => ({ ...acc, [item.value]: item.label }), {})

const breedOptions = ['撒能', '台灣黑山羊', '努比亞', '波爾羊', '阿爾拜因']
const ageGroupOptions = ['小羊 (0-6個月)', '青年 (6-12個月)', '成羊 (12-36個月)', '高齡 (36個月以上)']
const parityOptions = Array.from({ length: 6 }, (_, idx) => `${idx}`)

const dateShortcuts = [
  {
    text: '最近 30 天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 30)
      return [start, end]
    },
  },
  {
    text: '今年至今',
    value: () => {
      const now = new Date()
      return [new Date(now.getFullYear(), 0, 1), now]
    },
  },
]

const financeTab = ref('cost')
const costFormRef = ref()
const revenueFormRef = ref()
const cohortChartRef = ref()
const trendChartRef = ref()
let cohortChartInstance = null
let trendChartInstance = null

const cohortHerdTagText = ref('')

const costForm = reactive({
  category: '',
  subcategory: '',
  amount: null,
  recorded_at: new Date(),
  description: '',
  notes: '',
  breed: '',
  age_group: '',
  parity: null,
  herd_tag: '',
})

const revenueForm = reactive({
  category: '',
  subcategory: '',
  amount: null,
  recorded_at: new Date(),
  description: '',
  notes: '',
  breed: '',
  age_group: '',
  parity: null,
  herd_tag: '',
})

const editingCostId = ref(null)
const editingRevenueId = ref(null)

const financeRules = {
  category: [{ required: true, message: '請輸入分類', trigger: 'blur' }],
  amount: [{ required: true, message: '請輸入金額', trigger: 'change' }],
  recorded_at: [{ required: true, message: '請選擇時間', trigger: 'change' }],
}

const kpiCards = [
  { key: 'total_cost', title: '總成本', subtitle: '包含所有成本紀錄', format: 'currency' },
  { key: 'total_revenue', title: '總收益', subtitle: '包含所有收益紀錄', format: 'currency' },
  { key: 'net_income', title: '淨收益', subtitle: '收益扣除成本', format: 'currency' },
  { key: 'cost_revenue_ratio', title: '成本收益比', subtitle: '成本 / 收益', format: 'ratio' },
]

const cohortRows = computed(() => cohortResult.value?.rows ?? [])
const cohortTableData = computed(() => cohortRows.value.map((row) => ({
  ...row.dimensions,
  ...row.metrics,
})))

const recentCostEntries = computed(() => costEntries.value.slice(0, 20))
const recentRevenueEntries = computed(() => revenueEntries.value.slice(0, 20))

const aiForm = reactive({
  apiKey: localStorage.getItem('analytics-ai-key') || '',
  highlights: '',
})

watch(() => aiForm.apiKey, (value) => {
  localStorage.setItem('analytics-ai-key', value || '')
})

function formatMetricValue(value, format = 'currency') {
  if (value === null || value === undefined) {
    return '—'
  }
  if (format === 'currency') {
    return new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', maximumFractionDigits: 0 }).format(value)
  }
  if (format === 'ratio') {
    return typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—'
  }
  return value
}

function metricFormatter(row, column, cellValue) {
  if (cellValue === null || cellValue === undefined) return '—'
  if (column.property?.includes('ratio')) {
    return `${(cellValue * 100).toFixed(1)}%`
  }
  if (typeof cellValue === 'number') {
    return cellValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  }
  return cellValue
}

function tableCurrencyFormatter(row, column, cellValue) {
  if (cellValue === null || cellValue === undefined) return '—'
  return new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', maximumFractionDigits: 0 }).format(cellValue)
}

function tableDateFormatter(row) {
  if (!row.recorded_at) return '—'
  const date = new Date(row.recorded_at)
  if (Number.isNaN(date.getTime())) return row.recorded_at
  return date.toLocaleString()
}

function normalizeHerdTags() {
  if (!cohortHerdTagText.value) {
    cohortForm.filters.herd_tag = []
    return
  }
  const tags = cohortHerdTagText.value.split(',').map(tag => tag.trim()).filter(Boolean)
  cohortForm.filters.herd_tag = Array.from(new Set(tags))
}

async function submitCohort() {
  await analyticsStore.runCohortAnalysis()
  await analyticsStore.runCostBenefit()
  await nextTick()
  updateCohortChart()
  updateTrendChart()
}

async function submitCostBenefit() {
  await analyticsStore.runCostBenefit()
  await nextTick()
  updateTrendChart()
}

function resetCohortFilters() {
  cohortForm.dimensions = ['breed']
  cohortForm.metrics = ['total_cost', 'total_revenue', 'net_income']
  cohortForm.limit = 15
  cohortForm.timeRange = []
  cohortForm.filters.breed = []
  cohortForm.filters.age_group = []
  cohortForm.filters.parity = []
  cohortForm.filters.herd_tag = []
}

async function submitCostForm() {
  if (!costFormRef.value) return
  await costFormRef.value.validate(async (valid) => {
    if (!valid) return
    const payload = { ...costForm }
    try {
      if (editingCostId.value) {
        await analyticsStore.updateCostEntry(editingCostId.value, payload)
        ElMessage.success('成本資料已更新')
      } else {
        await analyticsStore.createCostEntry(payload)
        ElMessage.success('成本資料已新增')
      }
      resetCostForm()
      await fetchFinanceSummaries()
    } catch (error) {
      // 錯誤訊息已由 store 處理
    }
  })
}

async function submitRevenueForm() {
  if (!revenueFormRef.value) return
  await revenueFormRef.value.validate(async (valid) => {
    if (!valid) return
    const payload = { ...revenueForm }
    try {
      if (editingRevenueId.value) {
        await analyticsStore.updateRevenueEntry(editingRevenueId.value, payload)
        ElMessage.success('收益資料已更新')
      } else {
        await analyticsStore.createRevenueEntry(payload)
        ElMessage.success('收益資料已新增')
      }
      resetRevenueForm()
      await fetchFinanceSummaries()
    } catch (error) {
      // store 已處理錯誤
    }
  })
}

function resetCostForm() {
  editingCostId.value = null
  Object.assign(costForm, {
    category: '',
    subcategory: '',
    amount: null,
    recorded_at: new Date(),
    description: '',
    notes: '',
    breed: '',
    age_group: '',
    parity: null,
    herd_tag: '',
  })
  costFormRef.value?.clearValidate()
}

function resetRevenueForm() {
  editingRevenueId.value = null
  Object.assign(revenueForm, {
    category: '',
    subcategory: '',
    amount: null,
    recorded_at: new Date(),
    description: '',
    notes: '',
    breed: '',
    age_group: '',
    parity: null,
    herd_tag: '',
  })
  revenueFormRef.value?.clearValidate()
}

function loadCost(row) {
  editingCostId.value = row.id
  Object.assign(costForm, {
    category: row.category,
    subcategory: row.subcategory,
    amount: row.amount,
    recorded_at: row.recorded_at ? new Date(row.recorded_at) : new Date(),
    description: row.description,
    notes: row.notes,
    breed: row.breed,
    age_group: row.age_group,
    parity: row.parity,
    herd_tag: row.herd_tag,
  })
}

function loadRevenue(row) {
  editingRevenueId.value = row.id
  Object.assign(revenueForm, {
    category: row.category,
    subcategory: row.subcategory,
    amount: row.amount,
    recorded_at: row.recorded_at ? new Date(row.recorded_at) : new Date(),
    description: row.description,
    notes: row.notes,
    breed: row.breed,
    age_group: row.age_group,
    parity: row.parity,
    herd_tag: row.herd_tag,
  })
}

async function removeCost(id) {
  await analyticsStore.deleteCostEntry(id)
  ElMessage.success('已刪除成本紀錄')
  await fetchFinanceSummaries()
}

async function removeRevenue(id) {
  await analyticsStore.deleteRevenueEntry(id)
  ElMessage.success('已刪除收益紀錄')
  await fetchFinanceSummaries()
}

function getDimensionLabel(row) {
  const parts = cohortForm.dimensions.map((key) => {
    const label = dimensionLabelMap[key] || key
    const value = row.dimensions?.[key] ?? '—'
    return `${label}: ${value}`
  })
  return parts.join(' / ')
}

function updateCohortChart() {
  if (!cohortChartRef.value) return
  if (!cohortChartInstance) {
    cohortChartInstance = echarts.init(cohortChartRef.value)
  }
  if (!hasCohortData.value) {
    cohortChartInstance.clear()
    return
  }
  const categories = cohortRows.value.map(row => getDimensionLabel(row))
  const metricSeries = []

  if (cohortForm.metrics.includes('total_cost')) {
    metricSeries.push({
      name: '總成本',
      type: 'bar',
      emphasis: { focus: 'series' },
      data: cohortRows.value.map(row => row.metrics.total_cost ?? 0),
    })
  }
  if (cohortForm.metrics.includes('total_revenue')) {
    metricSeries.push({
      name: '總收益',
      type: 'bar',
      emphasis: { focus: 'series' },
      data: cohortRows.value.map(row => row.metrics.total_revenue ?? 0),
    })
  }
  if (cohortForm.metrics.includes('net_income')) {
    metricSeries.push({
      name: '淨收益',
      type: 'line',
      smooth: true,
      data: cohortRows.value.map(row => row.metrics.net_income ?? 0),
    })
  }

  cohortChartInstance.setOption({
    color: ['#3b82f6', '#22c55e', '#f97316'],
    tooltip: { trigger: 'axis' },
    legend: { data: metricSeries.map(series => series.name) },
    grid: { top: 50, left: 50, right: 20, bottom: 60 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { interval: 0, rotate: categories.length > 4 ? 24 : 0 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (value) => value.toLocaleString() },
    },
    series: metricSeries,
  })
}

function updateTrendChart() {
  if (!trendChartRef.value) return
  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChartRef.value)
  }
  if (trendData.value.length === 0) {
    trendChartInstance.clear()
    return
  }
  const categories = trendData.value.map(item => item.period)
  const series = []
  if (costBenefitForm.metrics.includes('total_cost')) {
    series.push({ name: '總成本', type: 'line', smooth: true, data: trendData.value.map(item => item.metrics.total_cost ?? 0) })
  }
  if (costBenefitForm.metrics.includes('total_revenue')) {
    series.push({ name: '總收益', type: 'line', smooth: true, data: trendData.value.map(item => item.metrics.total_revenue ?? 0) })
  }
  if (costBenefitForm.metrics.includes('net_income')) {
    series.push({ name: '淨收益', type: 'line', smooth: true, data: trendData.value.map(item => item.metrics.net_income ?? 0) })
  }

  trendChartInstance.setOption({
    color: ['#0ea5e9', '#16a34a', '#f97316'],
    tooltip: { trigger: 'axis' },
    legend: { data: series.map(s => s.name) },
    grid: { top: 50, left: 50, right: 20, bottom: 50 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { formatter: (value) => value?.replace('T', ' ') ?? value },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (value) => value.toLocaleString() },
    },
    series,
  })
}

async function exportCohortCsv() {
  if (!hasCohortData.value) return
  const headers = [...cohortForm.dimensions.map(dim => dimensionLabelMap[dim] || dim), ...cohortForm.metrics.map(metric => metricLabelMap[metric] || metric)]
  const rows = cohortTableData.value.map((row) => headers.map((_, idx) => {
    const key = idx < cohortForm.dimensions.length ? cohortForm.dimensions[idx] : cohortForm.metrics[idx - cohortForm.dimensions.length]
    const value = row[key]
    return value !== undefined && value !== null ? value : ''
  }))
  const csvLines = [headers.join(','), ...rows.map(line => line.join(','))]
  const blob = new Blob([`\ufeff${csvLines.join('\n')}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `cohort-analysis-${Date.now()}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function fetchFinanceSummaries() {
  await Promise.all([
    analyticsStore.fetchCostEntries({ limit: 50 }),
    analyticsStore.fetchRevenueEntries({ limit: 50 }),
    analyticsStore.runCostBenefit({ force: true }),
  ])
  await nextTick()
  updateTrendChart()
}

async function generateReport() {
  if (!aiForm.apiKey) {
    ElMessage.warning('請先輸入 API 金鑰')
    return
  }
  try {
    const highlights = aiForm.highlights
      ? aiForm.highlights.split('\n').map(item => item.trim()).filter(Boolean)
      : []
    await analyticsStore.generateAiReport(aiForm.apiKey, highlights)
    ElMessage.success('AI 報告已生成')
  } catch (error) {
    ElMessage.error(analyticsStore.errorMessage || 'AI 報告生成失敗')
  }
}

async function copyReport() {
  if (!analyticsStore.aiReport?.report_markdown) return
  try {
    await navigator.clipboard.writeText(analyticsStore.aiReport.report_markdown)
    ElMessage.success('已複製 Markdown')
  } catch (error) {
    ElMessage.error('複製失敗，請手動選取文字')
  }
}

function downloadReport() {
  if (!analyticsStore.aiReport?.report_html) return
  const blob = new Blob([analyticsStore.aiReport.report_html], { type: 'text/html;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `analytics-report-${Date.now()}.html`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function handleResize() {
  cohortChartInstance?.resize()
  trendChartInstance?.resize()
}

watch(cohortRows, () => {
  nextTick(updateCohortChart)
}, { deep: true })

watch(trendData, () => {
  nextTick(updateTrendChart)
}, { deep: true })

watch(() => cohortForm.filters.herd_tag, (value) => {
  if (Array.isArray(value) && value.length > 0) {
    cohortHerdTagText.value = value.join(', ')
  } else {
    cohortHerdTagText.value = ''
  }
}, { immediate: true, deep: true })

onMounted(async () => {
  await fetchFinanceSummaries()
  await submitCohort()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  cohortChartInstance?.dispose()
  trendChartInstance?.dispose()
})

</script>

<style scoped>
.analytics-hub {
  display: flex;
  flex-direction: column;
  gap: 32px;
  padding: 24px 0 48px;
}

.kpi-section .kpi-card {
  min-height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.kpi-title {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 600;
  color: #0f172a;
}

.kpi-subtitle {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.analytics-section .filter-card,
.analytics-section .chart-card,
.table-card,
.finance-section .el-card,
.ai-report-section .el-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-form {
  padding-top: 12px;
}

.chart-row {
  margin-top: 16px;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.mt-12 {
  margin-top: 12px;
}

.mt-16 {
  margin-top: 16px;
}

.finance-form {
  padding-top: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.report-output {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  background-color: #f8fafc;
  max-height: 380px;
  overflow-y: auto;
}

.report-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .chart-container {
    height: 280px;
  }
  .form-actions {
    justify-content: stretch;
    flex-direction: column;
  }
}
</style>
