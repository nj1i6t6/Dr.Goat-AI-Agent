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
      
      <!-- 羊隻選擇區域 -->
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
                <el-option label="預測30天後" :value="30" />
                <el-option label="預測60天後" :value="60" />
                <el-option label="預測90天後" :value="90" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label=" ">
              <el-button 
                type="primary" 
                size="large" 
                @click="startPrediction" 
                :loading="loading"
                :disabled="!selectedEarTag || !settingsStore.hasApiKey"
                style="width: 100%"
              >
                開始預測
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- API Key 提醒 -->
      <el-alert
        v-if="!settingsStore.hasApiKey"
        title="請先設定 API 金鑰"
        description="請前往「系統設定」頁面設定您的 Gemini API 金鑰以使用預測功能。"
        type="warning"
        :closable="false"
        show-icon
      />
    </el-card>

    <!-- 預測結果卡片 -->
    <el-card shadow="never" v-if="predictionResult || loading" class="results-card">
      <template #header>
        <div class="card-header">
          <span>預測分析結果</span>
          <span v-if="predictionResult" class="data-info">
            此預測基於 {{ predictionResult.historical_data_count }} 筆有效歷史資料
          </span>
        </div>
      </template>

      <div v-loading="loading" class="results-content">
        <el-row :gutter="20" v-if="predictionResult">
          <!-- 左側：數據分析區 -->
          <el-col :span="14">
            <div class="chart-section">
              <h3>體重成長趨勢圖</h3>
              <div ref="chartContainer" class="chart-container"></div>
              
              <!-- 關鍵指標 -->
              <div class="key-metrics">
                <el-row :gutter="16">
                  <el-col :span="8">
                    <div class="metric-card">
                      <div class="metric-label">預測體重</div>
                      <div class="metric-value">{{ predictionResult.predicted_weight }} kg</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="metric-card">
                      <div class="metric-label">平均日增重</div>
                      <div class="metric-value">{{ predictionResult.average_daily_gain }} kg/天</div>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="metric-card" :class="getQualityStatusClass(predictionResult.data_quality_report.status)">
                      <div class="metric-label">數據品質</div>
                      <div class="metric-value">{{ predictionResult.data_quality_report.status }}</div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </el-col>

          <!-- 右側：AI 報告區 -->
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
import { ref, onMounted, nextTick, computed } from 'vue';
import { TrendCharts } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore } from '../stores/settings';
import api from '../api';
import * as echarts from 'echarts';
import markdown from 'markdown-it';

const settingsStore = useSettingsStore();

// 響應式數據
const selectedEarTag = ref('');
const targetDays = ref(30);
const loading = ref(false);
const predictionResult = ref(null);
const chartContainer = ref(null);
const sheepOptions = ref([]);

// Markdown 解析器
const md = markdown();

// 計算屬性
const aiAnalysisHtml = computed(() => {
  if (!predictionResult.value?.ai_analysis) return '';
  return md.render(predictionResult.value.ai_analysis);
});

// 方法
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
    ? sheepOptions.value.filter(sheep => 
        sheep.value.toLowerCase().includes(queryString.toLowerCase())
      )
    : sheepOptions.value;
  cb(results);
};

const handleSelect = (item) => {
  selectedEarTag.value = item.value;
};

const clearSelection = () => {
  selectedEarTag.value = '';
  predictionResult.value = null;
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

  if (!settingsStore.hasApiKey) {
    ElMessage.error('請先在系統設定中設定 API 金鑰');
    return;
  }

  loading.value = true;
  predictionResult.value = null;

  try {
    // 獲取預測結果
    const result = await api.getSheepPrediction(
      selectedEarTag.value,
      targetDays.value,
      settingsStore.apiKey
    );

    predictionResult.value = result;
    
    // 等待 DOM 更新後渲染圖表
    await nextTick();
    await renderChart();

    ElMessage.success('預測分析完成');
  } catch (error) {
    console.error('預測失敗:', error);
    ElMessage.error(error.message || '預測分析失敗');
  } finally {
    loading.value = false;
  }
};

const renderChart = async () => {
  if (!chartContainer.value || !predictionResult.value) return;

  try {
    // 獲取圖表數據
    const chartData = await api.getPredictionChartData(
      selectedEarTag.value,
      targetDays.value
    );

    const chart = echarts.init(chartContainer.value);

    const option = {
      title: {
        text: `${selectedEarTag.value} 體重成長預測`,
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          let result = '';
          params.forEach(param => {
            if (param.seriesName === '歷史記錄') {
              const point = chartData.historical_points.find(p => p.x === param.data[0]);
              result += `${param.seriesName}: ${point?.label || `${param.data[1]}kg`}<br/>`;
            } else if (param.seriesName === '預測值') {
              result += `${param.seriesName}: ${chartData.prediction_point?.label || `${param.data[1]}kg`}<br/>`;
            } else {
              result += `${param.seriesName}: ${param.data[1].toFixed(2)}kg<br/>`;
            }
          });
          return result;
        }
      },
      legend: {
        data: ['歷史記錄', '增長趨勢', '預測值'],
        bottom: 10
      },
      xAxis: {
        type: 'value',
        name: '出生後天數',
        nameLocation: 'middle',
        nameGap: 30
      },
      yAxis: {
        type: 'value',
        name: '體重 (kg)',
        nameLocation: 'middle',
        nameGap: 40
      },
      series: [
        {
          name: '歷史記錄',
          type: 'scatter',
          data: chartData.historical_points.map(point => [point.x, point.y]),
          itemStyle: {
            color: '#409EFF'
          },
          symbolSize: 8
        },
        {
          name: '增長趨勢',
          type: 'line',
          data: chartData.trend_line.map(point => [point.x, point.y]),
          itemStyle: {
            color: '#909399'
          },
          lineStyle: {
            type: 'solid',
            width: 2
          },
          symbol: 'none'
        },
        {
          name: '預測值',
          type: 'scatter',
          data: chartData.prediction_point ? [[chartData.prediction_point.x, chartData.prediction_point.y]] : [],
          itemStyle: {
            color: '#F56C6C'
          },
          symbolSize: 12,
          symbol: 'star'
        }
      ]
    };

    chart.setOption(option);

    // 響應式調整
    window.addEventListener('resize', () => {
      chart.resize();
    });

  } catch (error) {
    console.error('圖表渲染失敗:', error);
    ElMessage.error('圖表載入失敗');
  }
};

// 生命週期
onMounted(() => {
  loadSheepList();
});
</script>

<style scoped>
.prediction-page {
  animation: fadeIn 0.5s ease-out;
}

.page-title {
  font-size: 1.8em;
  color: #1e3a8a;
  margin-bottom: 20px;
}

.card-header {
  font-size: 1.2em;
  font-weight: bold;
}

.data-info {
  font-size: 0.9em;
  color: #6b7280;
  font-weight: normal;
}

.sheep-selection-area {
  padding: 10px 0;
}

.results-card {
  margin-top: 25px;
}

.results-content {
  min-height: 450px;
}

.chart-section {
  padding-right: 20px;
}

.chart-container {
  width: 100%;
  height: 380px;
  margin-bottom: 20px;
}

.key-metrics {
  margin-top: 10px;
}

.metric-card {
  background: #f8fafc;
  padding: 15px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid #eef2f7;
  transition: all 0.3s ease;
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

.metric-label {
  font-size: 0.9em;
  color: #64748b;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.5em;
  font-weight: 700;
  color: #0f172a;
}
.metric-card.status-good .metric-value { color: #16a34a; }
.metric-card.status-warning .metric-value { color: #f97316; }
.metric-card.status-error .metric-value { color: #dc2626; }

.ai-report-section {
  background-color: #f0f9ff;
  border: 1px solid #e0f2fe;
  padding: 25px;
  border-radius: 12px;
  height: 100%;
}
.ai-report-section h3 {
  font-size: 1.2em;
  color: #0c4a6e;
  margin-top: 0;
}

.ai-analysis-content {
  margin-top: 16px;
  line-height: 1.7;
  font-size: 0.95em;
}

.ai-analysis-content :deep(h1),
.ai-analysis-content :deep(h2),
.ai-analysis-content :deep(h3) {
  color: #0891b2;
  border-bottom: 1px solid #e0f2fe;
  padding-bottom: 5px;
  margin-top: 20px;
}

.ai-analysis-content :deep(strong) {
  color: #075985;
}

.ai-analysis-content :deep(ul) {
  padding-left: 20px;
  list-style-type: disc;
}
</style>
