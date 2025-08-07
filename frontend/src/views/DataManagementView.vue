<template>
  <div class="data-management-page">
    <h1 class="page-title">
      <el-icon><Upload /></el-icon>
      數據管理中心
    </h1>

    <!-- 資料匯出 -->
    <el-card shadow="never">
      <template #header><div class="card-header">資料匯出</div></template>
      <p>將您帳戶中所有的羊隻基礎資料、事件日誌、歷史數據及 AI 聊天記錄備份為一份完整的 Excel (.xlsx) 檔案。</p>
      <el-button type="primary" :loading="exportLoading" @click="handleExport" :icon="Download">
        匯出全部資料
      </el-button>
    </el-card>

    <!-- 資料導入 -->
    <h2 class="section-title">資料導入</h2>
    <el-tabs v-model="activeTab" type="border-card" class="import-tabs">
      <!-- 快速導入 -->
      <el-tab-pane label="快速導入 (使用標準範本)" name="default">
        <el-steps :active="defaultStep" finish-status="success" simple>
          <el-step title="下載範本" />
          <el-step title="上傳檔案" />
          <el-step title="執行導入" />
        </el-steps>
        <div class="step-content">
          <h4>步驟一：下載並填寫標準範本</h4>
          <p>請下載系統提供的標準 Excel 範本，並將您的數據按照範本的格式填寫。</p>
          <a href="/templates/goat_import_template.xlsx" download>
            <el-button type="success" :icon="Download">下載標準範本.xlsx</el-button>
          </a>
          <el-divider />
          <h4>步驟二：上傳已填寫的範本檔案</h4>
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleDefaultFileChange"
            :limit="1"
            :on-exceed="handleFileExceed"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">將檔案拖曳至此，或<em>點擊上傳</em></div>
          </el-upload>
          <el-divider />
          <h4>步驟三：執行導入</h4>
          <el-button type="primary" :disabled="!defaultFile" :loading="defaultImportLoading" @click="handleProcessImport(true)">
            執行快速導入
          </el-button>
          <div v-if="defaultImportResult" class="import-result" v-html="defaultImportResult"></div>
        </div>
      </el-tab-pane>

      <!-- 自訂導入 -->
      <el-tab-pane label="自訂導入 (使用我的格式)" name="custom">
        <el-steps :active="customStep" finish-status="success" simple>
          <el-step title="上傳檔案" />
          <el-step title="設定映射" />
          <el-step title="執行導入" />
        </el-steps>
        <div class="step-content">
          <h4>步驟一：上傳您的 Excel 檔案</h4>
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleCustomFileChange"
            :limit="1"
            :on-exceed="handleFileExceed"
            v-loading="analysisLoading"
          >
             <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">將檔案拖曳至此，或<em>點擊上傳</em></div>
          </el-upload>
          <div v-if="analyzedData">
            <el-divider />
            <h4>步驟二：設定工作表用途與欄位映射</h4>
            <div v-for="(sheet, name) in analyzedData.sheets" :key="name" class="sheet-mapping-item">
              <p><strong>工作表: {{ name }}</strong> (共 {{ sheet.rows }} 筆資料)</p>
              <el-select v-model="mappingConfig[name].purpose" placeholder="請選擇此工作表的用途" style="width:100%; margin-bottom: 10px;">
                <el-option v-for="opt in sheetPurposeOptions" :key="opt.value" :label="opt.text" :value="opt.value" />
              </el-select>
              <div v-if="systemFieldMappings[mappingConfig[name].purpose]">
                <div v-for="field in systemFieldMappings[mappingConfig[name].purpose]" :key="field.key" class="field-mapping-row">
                  <span class="system-field-label">
                    {{ field.label }}
                    <el-tag v-if="field.required" type="danger" size="small">必填</el-tag>
                  </span>
                  <el-select v-model="mappingConfig[name].columns[field.key]" placeholder="對應您的欄位" clearable style="width: 100%;">
                    <el-option v-for="col in sheet.columns" :key="col" :label="col" :value="col" />
                  </el-select>
                </div>
              </div>
            </div>
            <el-divider />
            <h4>步驟三：執行導入</h4>
            <el-button type="primary" :loading="customImportLoading" @click="handleProcessImport(false)">執行導入</el-button>
            <div v-if="customImportResult" class="import-result" v-html="customImportResult"></div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { Upload, Download, UploadFilled } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import api from '../api';
import { sheetPurposeOptions, systemFieldMappings } from '../utils';

const activeTab = ref('default');
const exportLoading = ref(false);

// Default Import State
const defaultStep = ref(1);
const defaultFile = ref(null);
const defaultImportLoading = ref(false);
const defaultImportResult = ref('');

// Custom Import State
const customStep = ref(0);
const customFile = ref(null);
const analysisLoading = ref(false);
const analyzedData = ref(null);
const mappingConfig = reactive({});
const customImportLoading = ref(false);
const customImportResult = ref('');

const handleExport = async () => {
  exportLoading.value = true;
  try {
    const response = await api.exportExcel();
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'goat_data_export.xlsx';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    ElMessage.success('檔案已成功匯出');
  } catch (error) {
    ElMessage.error(`匯出失敗: ${error.error || error.message}`);
  } finally {
    exportLoading.value = false;
  }
};

const handleFileExceed = (files) => {
  ElMessage.warning(`一次只能上傳一個檔案，您已選擇 ${files.length} 個檔案`);
};

const handleDefaultFileChange = (file) => {
  defaultFile.value = file.raw;
  defaultStep.value = 2;
  defaultImportResult.value = '';
};

const handleCustomFileChange = async (file) => {
  customFile.value = file.raw;
  customStep.value = 1;
  analysisLoading.value = true;
  customImportResult.value = '';
  analyzedData.value = null;
  Object.keys(mappingConfig).forEach(key => delete mappingConfig[key]);

  try {
    const result = await api.analyzeExcel(customFile.value);
    analyzedData.value = result;
    // 初始化映射配置
    for (const sheetName in result.sheets) {
      mappingConfig[sheetName] = {
        purpose: '',
        columns: {},
      };
    }
    customStep.value = 2;
  } catch (error) {
    ElMessage.error(`檔案分析失敗: ${error.error || error.message}`);
    customStep.value = 0;
  } finally {
    analysisLoading.value = false;
  }
};

const handleProcessImport = async (isDefault) => {
  const file = isDefault ? defaultFile.value : customFile.value;
  if (!file) {
    ElMessage.error('請先上傳檔案');
    return;
  }

  if (isDefault) {
    defaultImportLoading.value = true;
    defaultImportResult.value = '';
  } else {
    customImportLoading.value = true;
    customImportResult.value = '';
  }

  try {
    const result = await api.processImport(file, isDefault, mappingConfig);
    let resultHtml = `<h4>導入報告</h4><p class="success">${result.message}</p>`;
    if (result.details && result.details.length > 0) {
      resultHtml += `<ul>${result.details.map(d => `<li><strong>${d.sheet}</strong>: ${d.message}</li>`).join('')}</ul>`;
    }
    
    if (isDefault) {
      defaultImportResult.value = resultHtml;
      defaultStep.value = 3;
    } else {
      customImportResult.value = resultHtml;
      customStep.value = 3;
    }
    ElMessage.success('導入操作完成');
  } catch (error) {
    const errorHtml = `<p class="error">導入失敗: ${error.error || error.message}</p>`;
    if (isDefault) {
      defaultImportResult.value = errorHtml;
    } else {
      customImportResult.value = errorHtml;
    }
    ElMessage.error('導入過程中發生錯誤');
  } finally {
    if (isDefault) {
      defaultImportLoading.value = false;
    } else {
      customImportLoading.value = false;
    }
  }
};
</script>

<style scoped>
.data-management-page { animation: fadeIn 0.5s ease-out; }
.page-title, .section-title {
  font-size: 1.8em; color: #1e3a8a; margin-top: 0;
  margin-bottom: 20px; display: flex; align-items: center;
}
.section-title { font-size: 1.5em; margin-top: 30px; }
.page-title .el-icon { margin-right: 10px; }
.card-header { font-size: 1.2em; font-weight: bold; }
.import-tabs { margin-top: 20px; }
.step-content { padding: 20px; }
.import-result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
  background-color: #f4f4f5;
  border: 1px solid #e9e9eb;
}
.import-result :deep(p.success) { color: #67c23a; font-weight: bold; }
.import-result :deep(p.error) { color: #f56c6c; font-weight: bold; }
.import-result :deep(ul) { padding-left: 20px; }
.sheet-mapping-item {
  border: 1px solid #dcdfe6;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}
.field-mapping-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
  padding: 8px;
  background-color: #fafafa;
  border-radius: 4px;
}
.system-field-label {
  flex-basis: 40%;
  font-size: 0.9em;
}
</style>