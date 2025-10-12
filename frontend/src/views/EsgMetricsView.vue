<template>
  <div class="esg-metrics" v-loading="loading">
    <header class="esg-metrics__header">
      <div>
        <h1 class="esg-metrics__title">ESG 指標</h1>
        <p class="esg-metrics__subtitle">
          以現有資料庫為基礎，追蹤牧場的永續表現與改善軌跡。
        </p>
      </div>
      <el-button type="primary" :icon="Histogram" @click="navigateToGovernance">前往資料治理</el-button>
    </header>

    <EmptyState
      v-if="!loading && !hasMetrics"
      icon="🌱"
      title="尚未有 ESG 相關數據"
      message="完成資料治理設定後，即可在此檢視牧場的永續績效與改善建議。"
    >
      <el-button type="primary" @click="navigateToGovernance">開啟資料治理</el-button>
    </EmptyState>

    <section v-else class="metrics-grid">
      <el-row :gutter="20">
        <el-col
          v-for="metric in formattedMetrics"
          :key="metric.key"
          :xs="24"
          :sm="12"
          :lg="6"
        >
          <el-card shadow="hover" class="metric-card">
            <div class="metric-card__header">
              <el-icon class="metric-card__icon"><component :is="metric.icon" /></el-icon>
              <div>
                <h3 class="metric-card__title">{{ metric.label }}</h3>
                <p class="metric-card__hint">{{ metric.hint }}</p>
              </div>
            </div>
            <div class="metric-card__body">
              <span v-if="metric.displayValue !== null" class="metric-card__value">{{ metric.displayValue }}</span>
              <el-tag v-else type="info" effect="light">數據不足</el-tag>
              <p v-if="metric.unit && metric.displayValue !== null" class="metric-card__unit">{{ metric.unit }}</p>
              <p class="metric-card__description">{{ metric.description }}</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Histogram, ScaleToOriginal, Watermelon, WindPower, Medal } from '@element-plus/icons-vue';
import api from '@/api';
import EmptyState from '@/components/common/EmptyState.vue';

const router = useRouter();

const loading = ref(false);
const esgMetrics = ref(null);

const metricBlueprint = [
  {
    key: 'fcr',
    label: '飼料轉換率 (FCR)',
    unit: 'kg 飼料／kg 增重',
    hint: '越低代表飼料利用率越佳',
    icon: ScaleToOriginal,
    description: '追蹤飼料使用效率，協助調整配方與飼養策略。',
  },
  {
    key: 'water_usage',
    label: '單位產出耗水量',
    unit: 'L／kg 產出',
    hint: '越低越能節省用水',
    icon: Watermelon,
    description: '衡量牧場的水資源使用，識別節水潛力與設備投資優先順序。',
  },
  {
    key: 'carbon_intensity',
    label: '碳排密度估算',
    unit: 'kg CO₂e／kg 產出',
    hint: '越低代表碳足跡越小',
    icon: WindPower,
    description: '反映牧場運營對環境的影響，可與碳權或淨零策略相互對應。',
  },
  {
    key: 'welfare_index',
    label: '動物福利指數',
    unit: '分數 (0-100)',
    hint: '越高代表照護品質越佳',
    icon: Medal,
    description: '綜合評量牧場在環境舒適度、健康監測與行為表現等面向的表現。',
  },
];

const formattedMetrics = computed(() => {
  if (!esgMetrics.value) {
    return metricBlueprint.map((metric) => ({ ...metric, displayValue: null }));
  }

  return metricBlueprint.map((metric) => {
    const rawValue = esgMetrics.value?.[metric.key];
    if (rawValue === null || rawValue === undefined || rawValue === '') {
      return { ...metric, displayValue: null };
    }

    const value = Number(rawValue);
    if (Number.isNaN(value)) {
      return { ...metric, displayValue: String(rawValue) };
    }

    const displayValue = value % 1 === 0 ? value.toString() : value.toFixed(2);
    return { ...metric, displayValue };
  });
});

const hasMetrics = computed(() => formattedMetrics.value.some((metric) => metric.displayValue !== null));

const navigateToGovernance = () => {
  router.push('/analytics');
};

const loadMetrics = async () => {
  loading.value = true;
  try {
    const data = await api.getDashboardData();
    esgMetrics.value = data?.esg_metrics ?? null;
  } catch (error) {
    ElMessage.error('讀取 ESG 指標失敗，請稍後再試。');
  } finally {
    loading.value = false;
  }
};

onMounted(loadMetrics);
</script>

<style scoped>
.esg-metrics {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.esg-metrics__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.esg-metrics__title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
}

.esg-metrics__subtitle {
  margin: 4px 0 0;
  color: #475569;
  line-height: 1.6;
}

.metrics-grid {
  width: 100%;
}

.metric-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-card__header {
  display: flex;
  gap: 12px;
  align-items: center;
}

.metric-card__icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.22), rgba(45, 212, 191, 0.2));
  color: #0f172a;
  font-size: 20px;
}

.metric-card__title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
}

.metric-card__hint {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 0.85rem;
}

.metric-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-card__value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
}

.metric-card__unit {
  margin: 0;
  font-size: 0.85rem;
  color: #475569;
}

.metric-card__description {
  margin: 0;
  color: #64748b;
  font-size: 0.85rem;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .esg-metrics__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .metric-card__value {
    font-size: 1.6rem;
  }
}
</style>
