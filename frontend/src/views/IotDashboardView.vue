<template>
  <div class="iot-dashboard" v-loading="iotStore.deviceLoading">
    <header class="iot-dashboard__header">
      <div>
        <h1 class="iot-dashboard__title">物聯網儀表</h1>
        <p class="iot-dashboard__subtitle">快速掌握感測器與制動器的連線狀態、動態日誌與警示。</p>
      </div>
      <el-button :icon="Refresh" @click="refresh" :loading="iotStore.deviceLoading">重新整理</el-button>
    </header>

    <EmptyState
      v-if="!iotStore.devices.length && !iotStore.deviceLoading"
      icon="📡"
      title="尚未接入任何 IoT 裝置"
      message="完成裝置註冊後，您將在此看到即時的感測資訊與自動化狀態。"
    >
      <el-button type="primary" @click="$router.push('/iot')">前往裝置管理</el-button>
    </EmptyState>

    <template v-else>
      <section class="iot-dashboard__grid">
        <el-card shadow="hover">
          <template #header>系統概況</template>
          <div class="status-grid">
            <div class="status-item">
              <span class="status-item__label">感測器上線</span>
              <strong class="status-item__value">{{ onlineSensors }}</strong>
              <span class="status-item__meta">/{{ sensorCount }} 台</span>
            </div>
            <div class="status-item">
              <span class="status-item__label">制動器上線</span>
              <strong class="status-item__value">{{ onlineActuators }}</strong>
              <span class="status-item__meta">/{{ actuatorCount }} 台</span>
            </div>
            <div class="status-item">
              <span class="status-item__label">離線警示</span>
              <strong class="status-item__value status-item__value--danger">{{ offlineDevices.length }}</strong>
            </div>
            <div class="status-item">
              <span class="status-item__label">自動化規則</span>
              <strong class="status-item__value">{{ iotStore.rules.length }}</strong>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover">
          <template #header>連線概況</template>
          <Bar v-if="chartReady" :data="chartData" :options="chartOptions" class="iot-chart" />
          <el-skeleton v-else animated rows="4" />
        </el-card>
      </section>

      <section class="iot-dashboard__panels">
        <el-card class="panel" shadow="hover">
          <template #header>離線與警告裝置</template>
          <el-empty v-if="!offlineDevices.length" description="所有裝置都正常運作" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="device in offlineDevices"
              :key="device.id"
              type="danger"
              :timestamp="formatLastSeen(device.last_seen)"
            >
              <div class="timeline-item">
                <strong>{{ device.name }}</strong>
                <span class="timeline-item__meta">{{ formatStatus(device.status) }}</span>
                <span class="timeline-item__location" v-if="device.location">@ {{ device.location }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card class="panel" shadow="hover">
          <template #header>最新動態日誌</template>
          <el-table :data="activityLogs" style="width: 100%" size="small">
            <el-table-column prop="device" label="裝置" min-width="160" />
            <el-table-column prop="status" label="狀態" width="120" />
            <el-table-column prop="time" label="時間" width="180" />
            <el-table-column prop="message" label="內容" min-width="220" />
          </el-table>
        </el-card>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { formatDistanceToNowStrict, format } from 'date-fns';
import { zhTW } from 'date-fns/locale';
import { Bar } from 'vue-chartjs';
import {
  CategoryScale,
  Chart,
  BarController,
  BarElement,
  LinearScale,
  Legend,
  Tooltip,
} from 'chart.js';
import { Refresh } from '@element-plus/icons-vue';
import EmptyState from '@/components/common/EmptyState.vue';
import { useIotStore } from '@/stores/iot';

Chart.register(CategoryScale, LinearScale, BarController, BarElement, Legend, Tooltip);

const iotStore = useIotStore();
const chartReady = ref(false);

const sensorDevices = computed(() => iotStore.devices.filter((device) => device.category === 'sensor'));
const actuatorDevices = computed(() => iotStore.devices.filter((device) => device.category === 'actuator'));

const onlineSensors = computed(() => sensorDevices.value.filter((device) => device.status === 'online').length);
const onlineActuators = computed(() => actuatorDevices.value.filter((device) => device.status === 'online').length);

const offlineDevices = computed(() => iotStore.devices.filter((device) => device.status && device.status !== 'online'));

const sensorCount = computed(() => sensorDevices.value.length);
const actuatorCount = computed(() => actuatorDevices.value.length);

const chartData = computed(() => ({
  labels: ['感測器', '致動器'],
  datasets: [
    {
      label: '上線',
      data: [onlineSensors.value, onlineActuators.value],
      backgroundColor: 'rgba(14, 165, 233, 0.7)',
    },
    {
      label: '離線',
      data: [sensorCount.value - onlineSensors.value, actuatorCount.value - onlineActuators.value],
      backgroundColor: 'rgba(248, 113, 113, 0.65)',
    },
  ],
}));

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      ticks: { stepSize: 1 },
    },
  },
  plugins: {
    legend: {
      labels: {
        color: '#0f172a',
      },
    },
  },
};

const activityLogs = computed(() => {
  const logs = iotStore.devices.map((device) => ({
    device: device.name,
    status: formatStatus(device.status),
    time: formatLastSeen(device.last_seen),
    message: device.status === 'online' ? '連線穩定' : '連線異常，需要檢查',
  }));
  return logs.slice(0, 8);
});

const formatStatus = (status) => {
  if (!status) return '未知';
  if (status === 'online') return '上線';
  if (status === 'offline') return '離線';
  return status;
};

const formatLastSeen = (value) => {
  if (!value) return '尚無資料';
  try {
    return formatDistanceToNowStrict(new Date(value), { addSuffix: true, locale: zhTW });
  } catch (error) {
    return format(new Date(value), 'MM/dd HH:mm', { locale: zhTW });
  }
};

const refresh = async () => {
  await Promise.all([iotStore.fetchDevices(true), iotStore.fetchRules(true)]);
  chartReady.value = true;
};

onMounted(async () => {
  await Promise.all([iotStore.fetchDevices(), iotStore.fetchRules()]);
  chartReady.value = true;
});
</script>

<style scoped>
.iot-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.iot-dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.iot-dashboard__title {
  margin: 0;
  font-size: 1.8rem;
  color: #0f172a;
}

.iot-dashboard__subtitle {
  margin: 6px 0 0;
  color: #475569;
  font-size: 0.95rem;
}

.iot-dashboard__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.status-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.status-item {
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.12);
}

.status-item__label {
  font-size: 0.85rem;
  color: #1d4ed8;
}

.status-item__value {
  font-size: 1.6rem;
  font-weight: 700;
  color: #0f172a;
}

.status-item__value--danger {
  color: #dc2626;
}

.status-item__meta {
  font-size: 0.8rem;
  color: #475569;
}

.iot-chart {
  width: 100%;
  height: 260px;
}

.iot-dashboard__panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}

.panel {
  min-height: 320px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.timeline-item__meta {
  font-size: 0.85rem;
  color: #dc2626;
}

.timeline-item__location {
  font-size: 0.85rem;
  color: #475569;
}

@media (max-width: 768px) {
  .iot-dashboard__title {
    font-size: 1.5rem;
  }
}
</style>
