<template>
  <div class="settings-page">
    <h1 class="page-title">
      <el-icon><Setting /></el-icon>
      系統設定
    </h1>

    <!-- API 金鑰設定 -->
    <el-card shadow="never">
      <template #header><div class="card-header">Gemini API 金鑰設定</div></template>
      <p>請在此輸入您的 Google Gemini API 金鑰。此金鑰將被儲存在您的瀏覽器本地，用於與領頭羊博士 AI 進行通訊。</p>
      <el-input v-model="apiKeyInput" placeholder="在此貼上您的 API 金鑰" show-password clearable />
      <div class="api-key-status" :class="apiKeyStatus.type">
        {{ apiKeyStatus.message }}
      </div>
      <el-button type="primary" :loading="testLoading" @click="handleTestAndSaveApiKey">
        測試並儲存金鑰
      </el-button>
    </el-card>

    <!-- 字級設定 -->
    <el-card shadow="never" class="font-scale-card">
      <template #header><div class="card-header">介面字級</div></template>
      <p>
        依據使用者回饋，我們提供預設與大字兩種介面字級。預設字級符合一般建議值，大字級則放大整個系統的文字與行距，適合長時間使用或銀髮族群。
      </p>
      <el-radio-group v-model="fontScale" class="font-scale-group">
        <el-radio-button label="default">預設字級（建議）</el-radio-button>
        <el-radio-button label="large">大字級（放大 12.5%）</el-radio-button>
      </el-radio-group>
      <div class="font-scale-preview">
        <div class="preview-sample" data-scale="default">
          <span class="preview-title">預設字級</span>
          <span class="preview-text">常用段落會以 16px 為基準。</span>
        </div>
        <div class="preview-sample" data-scale="large">
          <span class="preview-title">大字級</span>
          <span class="preview-text">放大至約 18px，適合需要更高可讀性的使用情境。</span>
        </div>
      </div>
    </el-card>

    <!-- 事件選項管理 -->
    <el-card shadow="never" class="event-options-card">
      <template #header><div class="card-header">事件選項管理</div></template>
      <p>您可以在這裡自訂事件記錄時的「事件類型」和對應的「簡要描述」選項。預設選項無法刪除。</p>
      
      <div class="add-type-form">
        <el-input v-model="newEventType" placeholder="輸入新的事件類型名稱" @keyup.enter="handleAddEventType" />
        <el-button type="success" :icon="Plus" @click="handleAddEventType">新增類型</el-button>
      </div>

      <el-collapse v-model="activeCollapseItems" v-loading="optionsLoading">
        <el-empty v-if="!eventOptions.length && !optionsLoading" description="尚未有任何事件選項" />
        <el-collapse-item v-for="type in eventOptions" :key="type.id" :name="type.id">
          <template #title>
            <span class="collapse-title">{{ type.name }}</span>
            <el-tag v-if="type.is_default" type="info" size="small" effect="plain" class="title-tag">預設</el-tag>
            <el-tag type="primary" size="small" effect="plain" class="title-tag">{{ type.descriptions.length }} 個描述</el-tag>
          </template>
          
          <div class="description-list">
            <div v-for="desc in type.descriptions" :key="desc.id" class="description-item">
              <span>{{ desc.description }}</span>
              <el-button
                v-if="!desc.is_default"
                type="danger"
                :icon="Delete"
                @click="handleDeleteDescription(desc.id)"
                size="small"
                circle
                plain
              />
            </div>
            <div class="add-description-form">
              <el-input v-model="newDescriptions[type.id]" placeholder="為此類型新增簡要描述" size="small" @keyup.enter="handleAddDescription(type.id)" />
              <el-button type="primary" @click="handleAddDescription(type.id)" size="small">新增描述</el-button>
            </div>
          </div>
          
          <div v-if="!type.is_default" class="type-actions">
            <el-popconfirm
              title="確定要刪除此類型嗎？其下所有描述將一併刪除。"
              @confirm="handleDeleteType(type.id)"
              width="250"
            >
              <template #reference>
                <el-button type="danger" plain size="small">刪除整個「{{ type.name }}」類型</el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { Setting, Plus, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSettingsStore } from '../stores/settings';
import api from '../api';

const settingsStore = useSettingsStore();

// API Key State
const apiKeyInput = ref('');
const testLoading = ref(false);
const apiKeyStatus = reactive({ type: 'info', message: '尚未設定 API 金鑰。' });
const fontScale = computed({
  get: () => settingsStore.fontScale,
  set: (value) => settingsStore.setFontScale(value),
});

// Event Options State
const optionsLoading = ref(false);
const eventOptions = ref([]);
const newEventType = ref('');
const newDescriptions = reactive({});
const activeCollapseItems = ref([]);

const updateApiKeyStatus = () => {
  if (settingsStore.hasApiKey) {
    apiKeyStatus.type = 'success';
    apiKeyStatus.message = '已載入儲存的 API 金鑰。建議點擊測試以驗證其有效性。';
  } else {
    apiKeyStatus.type = 'error';
    apiKeyStatus.message = '尚未設定 API 金鑰。';
  }
};

const handleTestAndSaveApiKey = async () => {
  if (!apiKeyInput.value) {
    ElMessage.error('請輸入 API 金鑰');
    return;
  }
  testLoading.value = true;
  apiKeyStatus.type = 'info';
  apiKeyStatus.message = '正在測試金鑰...';
  try {
    await api.getAgentTip(apiKeyInput.value);
    settingsStore.setApiKey(apiKeyInput.value);
    apiKeyStatus.type = 'success';
    apiKeyStatus.message = 'API 金鑰驗證成功！已儲存。';
    ElMessage.success('API 金鑰已儲存');
  } catch (error) {
    settingsStore.clearApiKey();
    apiKeyStatus.type = 'error';
    apiKeyStatus.message = `金鑰驗證失敗: ${error.error || error.message}`;
    ElMessage.error('金鑰驗證失敗');
  } finally {
    testLoading.value = false;
  }
};

const fetchEventOptions = async () => {
  optionsLoading.value = true;
  try {
    const data = await api.getEventOptions();
    eventOptions.value = data;
    // 為每個類型初始化一個空的 newDescriptions 屬性
    data.forEach(type => {
      if (!newDescriptions[type.id]) {
        newDescriptions[type.id] = '';
      }
    });
  } catch (error) {
    ElMessage.error(`載入事件選項失敗: ${error.error || error.message}`);
  } finally {
    optionsLoading.value = false;
  }
};

const handleAddEventType = async () => {
  const name = newEventType.value.trim();
  if (!name) {
    ElMessage.warning('請輸入事件類型名稱');
    return;
  }
  try {
    await api.addEventType(name);
    ElMessage.success('事件類型新增成功');
    newEventType.value = '';
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`新增失敗: ${error.error || error.message}`);
  }
};

const handleDeleteType = async (typeId) => {
  try {
    await api.deleteEventType(typeId);
    ElMessage.success('事件類型已刪除');
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`刪除失敗: ${error.error || error.message}`);
  }
};

const handleAddDescription = async (typeId) => {
  const description = newDescriptions[typeId]?.trim();
  if (!description) {
    ElMessage.warning('請輸入簡要描述內容');
    return;
  }
  try {
    await api.addEventDescription(typeId, description);
    ElMessage.success('簡要描述新增成功');
    newDescriptions[typeId] = '';
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`新增失敗: ${error.error || error.message}`);
  }
};

const handleDeleteDescription = async (descId) => {
  try {
    await api.deleteEventDescription(descId);
    ElMessage.success('簡要描述已刪除');
    await fetchEventOptions();
  } catch (error) {
    ElMessage.error(`刪除失敗: ${error.error || error.message}`);
  }
};

onMounted(() => {
  apiKeyInput.value = settingsStore.apiKey;
  updateApiKeyStatus();
  fetchEventOptions();
});
</script>

<style scoped>
.settings-page { animation: fadeIn 0.5s ease-out; }
.page-title {
  font-size: 1.8em; color: #1e3a8a; margin-top: 0;
  margin-bottom: 20px; display: flex; align-items: center;
}
.page-title .el-icon { margin-right: 10px; }
.card-header { font-size: 1.2em; font-weight: bold; }
.el-card { margin-bottom: 20px; }

.font-scale-group {
  margin-top: 12px;
}

.font-scale-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}

.preview-sample {
  flex: 1 1 240px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #ffffff;
  line-height: 1.6;
}

.preview-sample[data-scale='large'] {
  font-size: 1.125rem;
}

.preview-title {
  font-weight: 600;
  color: #1f2937;
}

.preview-text {
  color: #4b5563;
}

.api-key-status {
  margin: 10px 0;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 0.9em;
}
.api-key-status.info { background-color: #f4f4f5; color: #909399; }
.api-key-status.success { background-color: #f0f9eb; color: #67c23a; }
.api-key-status.error { background-color: #fef0f0; color: #f56c6c; }

.add-type-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.collapse-title {
  font-size: 1.1em;
  font-weight: 500;
}
.title-tag {
  margin-left: 10px;
}

.description-list {
  padding: 0 10px;
}
.description-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f2f5;
}
.add-description-form {
  display: flex;
  gap: 8px;
  margin-top: 15px;
}
.type-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
  text-align: right;
}
</style>