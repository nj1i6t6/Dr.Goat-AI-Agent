<template>
  <div class="dashboard-page" v-loading="initialLoading">
    <div v-if="!initialLoading && !hasSheep">
      <!-- 羊群為空時的引導畫面 -->
      <el-result
        icon="info"
        title="歡迎, 開始建立您的羊群檔案吧！"
        sub-title="系統中尚無羊隻資料。請前往「數據管理中心」導入您的第一批資料。"
      >
        <template #extra>
          <el-button type="primary" size="large" @click="$router.push('/data-management')">
            🚀 前往數據管理中心
          </el-button>
        </template>
      </el-result>
    </div>

    <div v-else-if="!initialLoading && hasSheep">
      <!-- 儀表板主內容 -->
      <el-card shadow="never" class="welcome-card">
        <h3 class="welcome-title">領頭羊博士的問候！</h3>
        <!-- 修改：直接綁定 settingsStore 中的 agentTip 狀態 -->
        <div class="agent-tip" v-loading="settingsStore.agentTip.loading" v-html="settingsStore.agentTip.html"></div>
      </el-card>

      <el-row :gutter="20">
        <el-col :md="12">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span>📅 任務與安全提醒</span>
              </div>
            </template>
            <el-empty v-if="!dashboardData.reminders || dashboardData.reminders.length === 0" description="暫無待辦事項" />
            <ul v-else class="dashboard-list">
              <li v-for="(reminder, index) in dashboardData.reminders" :key="index">
                <span class="ear-num-link">{{ reminder.ear_num }}</span>: {{ reminder.type }} (至 {{ reminder.due_date }})
                <el-tag :type="getTagType(reminder.status)" size="small" effect="light">{{ reminder.status }}</el-tag>
              </li>
            </ul>
          </el-card>
        </el-col>
        <el-col :md="12">
           <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span>❤️ 健康與福利警示</span>
              </div>
            </template>
            <el-empty v-if="!dashboardData.health_alerts || dashboardData.health_alerts.length === 0" description="羊群健康狀況良好" />
             <ul v-else class="dashboard-list">
              <li v-for="(alert, index) in dashboardData.health_alerts" :key="index" class="alert-item">
                <strong>{{ alert.type }}</strong>
                <div>
                  <span class="ear-num-link">{{ alert.ear_num }}</span> - 
                  <span class="alert-message">{{ alert.message }}</span>
                </div>
              </li>
            </ul>
          </el-card>
        </el-col>
      </el-row>
      
      <el-card shadow="never" style="margin-top: 20px;">
        <el-row :gutter="40">
          <el-col :md="12">
            <h3>🐑 羊群狀態速覽</h3>
             <el-empty v-if="!dashboardData.flock_status_summary || dashboardData.flock_status_summary.length === 0" description="暫無狀態數據" />
            <div v-else>
              <p v-for="summary in dashboardData.flock_status_summary" :key="summary.status">
                <strong>{{ getStatusText(summary.status) }}:</strong> {{ summary.count }} 隻
              </p>
            </div>
          </el-col>
          <el-col :md="12">
             <h3>🌿 ESG 指標速覽</h3>
             <div v-if="dashboardData.esg_metrics">
               <p>
                 <strong>飼料轉換率 (FCR) 估算:</strong> 
                 <span v-if="dashboardData.esg_metrics.fcr" class="esg-value">{{ dashboardData.esg_metrics.fcr.toFixed(2) }}</span>
                 <el-tag v-else type="info" size="small">數據不足</el-tag>
                 <span class="form-note">(kg飼料/kg增重)</span>
               </p>
               <el-button 
                 type="success" 
                 :loading="reportLoading" 
                 @click="generateFarmReport"
                 style="margin-top: 15px;"
               >
                 生成牧場報告
               </el-button>
             </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSettingsStore } from '../stores/settings';
import api from '../api';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();
const settingsStore = useSettingsStore();

const initialLoading = ref(true);
const hasSheep = ref(false);
const reportLoading = ref(false);
const dashboardData = reactive({
  reminders: [],
  health_alerts: [],
  flock_status_summary: [],
  esg_metrics: {},
});

const statusMap = {
  maintenance: "維持期", growing_young: "生長前期", growing_finishing: "生長育肥期",
  gestating_early: "懷孕早期", gestating_late: "懷孕晚期", lactating_early: "泌乳早期",
  lactating_peak: "泌乳高峰期", lactating_mid: "泌乳中期", lactating_late: "泌乳晚期",
  dry_period: "乾乳期", breeding_male_active: "配種期公羊", breeding_male_non_active: "非配種期公羊",
  fiber_producing: "產毛期", other_status: "其他"
};
const getStatusText = (status) => statusMap[status] || status || '未分類';

const getTagType = (status) => {
  if (status === '已過期') return 'danger';
  if (status === '即將到期') return 'warning';
  if (status === '停藥中') return 'info';
  return 'primary';
};

async function fetchInitialData() {
  try {
    const sheepList = await api.getAllSheep();
    hasSheep.value = sheepList && sheepList.length > 0;
    
    if (hasSheep.value) {
      fetchDashboardContent();
    }
  } catch (error) {
    ElMessage.error('無法獲取羊群資料');
  } finally {
    initialLoading.value = false;
  }
}

async function fetchDashboardContent() {
  // 修改：調用 store 中的 action 來獲取每日提示
  settingsStore.fetchAndSetAgentTip();
  fetchDashboardData();
}

async function fetchDashboardData() {
  try {
    const data = await api.getDashboardData();
    Object.assign(dashboardData, data);
  } catch (error) {
    ElMessage.error(`載入儀表板數據失敗: ${error.error || error.message}`);
  }
}

async function generateFarmReport() {
  reportLoading.value = true;
  try {
    const report = await api.getFarmReport();
    const reportHtml = `
      <h4>羊群結構 (總計: ${report.flock_composition.total} 隻)</h4>
      <div style="display:flex; gap: 20px;">
        <div style="flex:1;"><strong>品種分佈:</strong><ul>${report.flock_composition.by_breed.map(b => `<li>${b.name}: ${b.count} 隻</li>`).join('')}</ul></div>
        <div style="flex:1;"><strong>性別分佈:</strong><ul>${report.flock_composition.by_sex.map(s => `<li>${s.name}: ${s.count} 隻</li>`).join('')}</ul></div>
      </div>
      <hr>
      <h4>生產性能摘要</h4>
      <ul>
        <li>平均出生體重: <strong>${report.production_summary.avg_birth_weight || 'N/A'} kg</strong></li>
        <li>平均窩仔數: <strong>${report.production_summary.avg_litter_size || 'N/A'} 隻</strong></li>
        <li>平均日產奶量 (有記錄者): <strong>${report.production_summary.avg_milk_yield || 'N/A'} kg/天</strong></li>
      </ul>
      <hr>
      <h4>健康狀況摘要 (最常見的5項疾病事件)</h4>
      <ul>
        ${report.health_summary.top_diseases.length > 0 ? report.health_summary.top_diseases.map(d => `<li>${d.name}: ${d.count} 次</li>`).join('') : '<li>暫無疾病記錄</li>'}
      </ul>
    `;
    ElMessageBox.alert(reportHtml, '牧場年度報告摘要', {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '關閉',
    });
  } catch (error) {
    ElMessage.error(`生成報告失敗: ${error.error || error.message}`);
  } finally {
    reportLoading.value = false;
  }
}

onMounted(() => {
  fetchInitialData();
});
</script>

<style scoped>
.dashboard-page {
  animation: fadeIn 0.5s ease-out;
}
.welcome-card {
  margin-bottom: 20px;
}
.welcome-title {
  font-size: 1.5em;
  color: #1e40af;
  margin-top: 0;
  margin-bottom: 10px;
}
.agent-tip {
  font-size: 1em;
  color: #4b5563;
  font-style: italic;
  min-height: 24px;
}
.card-header {
  font-size: 1.2em;
  font-weight: bold;
}
.dashboard-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.dashboard-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f2f5;
}
.dashboard-list li:last-child {
  border-bottom: none;
}
.ear-num-link {
  font-weight: bold;
  color: #3b82f6;
  cursor: pointer;
}
.alert-item {
  flex-direction: column;
  align-items: flex-start;
}
.alert-message {
  font-size: 0.9em;
  color: #555;
}
.esg-value {
  font-size: 1.2em;
  font-weight: bold;
  color: #8b5cf6;
  margin: 0 5px;
}
.form-note {
  font-size: 0.85em;
  color: #94a3b8;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>