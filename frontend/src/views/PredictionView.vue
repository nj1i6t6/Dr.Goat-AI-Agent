<template>
  <div class="prediction-page">
    <h1 class="page-title">
      <el-icon><TrendCharts /></el-icon>
      羊隻生長預測
    </h1>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">智慧預測系統</div>
      </template>

      <div class="sheep-selection-area">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="選擇羊隻耳號">
              <el-autocomplete
                v-model="selectedEarTag"
                :fetch-suggestions="querySearch"
                placeholder="輸入耳號搜尋羊隻"
                clearable
                style="width: 100%"
                @select="handleSelect"
                @clear="clearSelection"
              >
                <template #default="{ item }">
                  <div class="ear-tag-suggestion">
                    <span class="ear-tag">{{ item.value }}</span>
                    <span class="sheep-info">{{ item.breed }} | {{ item.sex }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="預測時長">
              <el-select v-model="targetDays" placeholder="選擇預測天數" style="width: 100%">
                <el-option label="預測7天後" :value="7" />
                <el-option label="預測14天後" :value="14" />
                <el-option label="預測30天後" :value="30" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label=" ">
              <el-button
                type="primary"
                size="large"
                @click="startPrediction"
                :loading="predictionStore.isLoading"
                :disabled="!selectedEarTag || !settingsStore.hasApiKey"
                style="width: 100%"
              >
                開始預測
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <el-alert
        v-if="!settingsStore.hasApiKey"
        title="請先設定 API 金鑰"
        description="請前往「系統設定」頁面設定您的 Gemini API 金鑰以使用預測功能。"
        type="warning"
        :closable="false"
        show-icon
      />
    </el-card>

    <el-card shadow="never" v-if="predictionStore.result || predictionStore.isLoading" class="results-card">
      <template #header>
        <div class="card-header">
          <span>預測分析結果</span>
          <span v-if="predictionStore.result" class="data-info">
            此預測基於 {{ predictionStore.result.historical_data_count }} 筆有效歷史資料
          </span>
        </div>
      </template>

      <div v-loading="predictionStore.isLoading" class="results-content">
        <el-row :gutter="20" v-if="predictionStore.result">
          <el-col :span="14">
            <div class="chart-section">
              <h3>體重成長趨勢圖</h3>
              <div ref="chartContainer" class="chart-container"></div>

              <div class="key-metrics">
                <el-row :gutter="16">
                  <el-col :span="8">
                    <div class="metric-card">
                      <div class="metric-label">預測體重</div>
                      <div class="metric-value">{{ predictionStore.result.predicted_weight }} kg</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="metric-card">
                      <div class="metric-label">平均日增重</div>
                      <div class="metric-value">{{ predictionStore.result.average_daily_gain }} kg/天</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="metric-card" :class="getQualityStatusClass(predictionStore.result.data_quality_report.status)">
                      <div class="metric-label">數據品質</div>
                      <div class="metric-value">{{ predictionStore.result.data_quality_report.status }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-col>

          <el-col :span="10">
            <div class="ai-report-section">
              <h3>領頭羊博士 AI 分析報告</h3>
              <div class="ai-analysis-content" v-html="aiAnalysisHtml"></div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue';
import { TrendCharts } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore } from '../stores/settings';
import { usePredictionStore } from '../stores/prediction';
import api from '../api';
import * as echarts from 'echarts';
import markdown from 'markdown-it';

const settingsStore = useSettingsStore();
const predictionStore = usePredictionStore();

const selectedEarTag = ref('');
const targetDays = ref(30);
const chartContainer = ref(null);
const sheepOptions = ref([]);
let chartInstance = null;
let resizeHandler = null;

// 兼容舊代碼/測試的公開狀態（僅讀）
const predictionResult = computed(() => predictionStore.result || null);
const loading = computed(() => predictionStore.isLoading);

const md = markdown();

const aiAnalysisHtml = computed(() => {
  const r = predictionStore.result;
  if (!r || !r.ai_analysis) return '';
  return md.render(r.ai_analysis);
});

const loadSheepList = async () => {
  try {
    const response = await api.getAllSheep();
    sheepOptions.value = response.map(sheep => ({
      value: sheep.EarNum,
      breed: sheep.Breed || '未指定',
      sex: sheep.Sex || '未指定',
      birth_date: sheep.BirthDate
    }));
  } catch (error) {
    console.error('載入羊隻清單失敗:', error);
  }
};

const querySearch = (queryString, cb) => {
  const results = queryString
    ? sheepOptions.value.filter(sheep => sheep.value.toLowerCase().includes(queryString.toLowerCase()))
    : sheepOptions.value;
  cb(results);
};

const handleSelect = (item) => {
  selectedEarTag.value = item.value;
  predictionStore.setSelectedEarTag(item.value);
};

const clearSelection = () => {
  selectedEarTag.value = '';
  targetDays.value = 30;
  predictionStore.clear();
};

const getQualityStatusClass = (status) => {
  switch (status) {
    case 'Good':
      return 'status-good';
    case 'Warning':
      return 'status-warning';
    case 'Error':
      return 'status-error';
    default:
      return '';
  }
};

const startPrediction = async () => {
  if (!selectedEarTag.value) {
    ElMessage.error('請選擇羊隻耳號');
    return;
  }
  const apiKeyStr = (settingsStore.apiKey || localStorage.getItem('geminiApiKey') || localStorage.getItem('gemini_api_key') || '').trim();
  try {
    predictionStore.setSelectedEarTag(selectedEarTag.value);
    predictionStore.setTargetDays(targetDays.value);
    await predictionStore.startPrediction(apiKeyStr);
    await nextTick();
    await renderChart();
    ElMessage.success('預測分析完成');
  } catch (error) {
    console.error('預測失敗:', error);
    ElMessage.error(error.message || '預測分析失敗');
  }
};

const renderChart = async () => {
  if (!chartContainer.value || !predictionStore.result) return;
  try {
    const old = echarts.getInstanceByDom?.(chartContainer.value);
    if (old) old.dispose();
    chartInstance = echarts.init(chartContainer.value);
    const raw = predictionStore.chartData || await api.getPredictionChartData(selectedEarTag.value, targetDays.value);
    const data = raw && raw.value ? raw.value : raw;
    const safe = (v) => Number.isFinite(v) ? v : null;
    const option = {
      title: { text: `${selectedEarTag.value} 體重成長預測`, left: 'center' },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          let result = '';
          params.forEach(param => {
            if (param.seriesName === '歷史記錄') {
              const point = data.historical_points.find(p => p.x === param.data[0]);
              result += `${param.seriesName}: ${point?.label || `${param.data[1]}kg`}<br/>`;
            } else if (param.seriesName === '預測值') {
              result += `${param.seriesName}: ${data.prediction_point?.label || `${param.data[1]}kg`}<br/>`;
            } else {
              const v = safe(param.data?.[1]);
              result += `${param.seriesName}: ${v != null ? v.toFixed?.(2) : '-'}kg<br/>`;
            }
          });
          return result;
        }
      },
      legend: { data: ['歷史記錄', '增長趨勢', '預測值'], bottom: 10 },
      xAxis: { type: 'value', name: '出生後天數', nameLocation: 'middle', nameGap: 30 },
      yAxis: { type: 'value', name: '體重 (kg)', nameLocation: 'middle', nameGap: 40 },
      series: [
        { name: '歷史記錄', type: 'scatter', data: data.historical_points.map(p => [p.x, p.y]), itemStyle: { color: '#409EFF' }, symbolSize: 8 },
        { name: '增長趨勢', type: 'line', data: data.trend_line.map(p => [p.x, p.y]), itemStyle: { color: '#909399' }, lineStyle: { type: 'solid', width: 2 }, symbol: 'none' },
        { name: '預測值', type: 'scatter', data: data.prediction_point ? [[data.prediction_point.x, data.prediction_point.y]] : [], itemStyle: { color: '#F56C6C' }, symbolSize: 12, symbol: 'star' }
      ]
    };
    chartInstance.setOption(option);
    if (!resizeHandler) {
      resizeHandler = () => { if (chartInstance) chartInstance.resize(); };
      window.addEventListener('resize', resizeHandler);
    }
  } catch (error) {
    console.error('圖表渲染失敗:', error);
    ElMessage.error('圖表載入失敗');
  }
};

onMounted(async () => {
  await loadSheepList();
  if (!settingsStore.apiKey) {
    const saved = localStorage.getItem('geminiApiKey') || localStorage.getItem('gemini_api_key');
    if (saved) settingsStore.setApiKey(saved);
  }
  if (predictionStore.selectedEarTag) selectedEarTag.value = predictionStore.selectedEarTag;
  if (predictionStore.targetDays) targetDays.value = predictionStore.targetDays;
  if (predictionStore.result) {
    await nextTick();
    await renderChart();
  }
});

watch(targetDays, (val) => predictionStore.setTargetDays(val));
watch(() => predictionStore.result, async (val) => {
  if (val) {
    await nextTick();
    await renderChart();
  }
});

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
    resizeHandler = null;
  }
  if (chartInstance) {
    try { chartInstance.dispose(); } catch (_) {}
    chartInstance = null;
  }
});
</script>

<style scoped>
.prediction-page {
  padding: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-info {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.sheep-selection-area {
  margin-bottom: 20px;
}

.ear-tag-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ear-tag {
  font-weight: 600;
}

.sheep-info {
  color: #909399;
  font-size: 12px;
}

.results-card {
  margin-top: 20px;
}

.results-content {
  min-height: 400px;
}

.chart-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin: 20px 0;
}

.key-metrics {
  margin-top: 20px;
}

.metric-card {
  background: white;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  border: 2px solid #e4e7ed;
}

.metric-card.status-good {
  border-color: #67c23a;
}

.metric-card.status-warning {
  border-color: #e6a23c;
}

.metric-card.status-error {
  border-color: #f56c6c;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.ai-report-section {
  background: #f0f9ff;
  padding: 20px;
  border-radius: 8px;
  height: 100%;
}

.ai-analysis-content {
  margin-top: 16px;
  line-height: 1.6;
}

.ai-analysis-content :deep(h3) {
  color: #409eff;
  font-size: 16px;
  margin: 16px 0 8px 0;
}

.ai-analysis-content :deep(h4) {
  color: #606266;
  font-size: 14px;
  margin: 12px 0 6px 0;
}

.ai-analysis-content :deep(p) {
  margin: 8px 0;
}

.ai-analysis-content :deep(strong) {
  color: #303133;
}

.ai-analysis-content :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.ai-analysis-content :deep(li) {
  margin: 4px 0;
}
</style>
