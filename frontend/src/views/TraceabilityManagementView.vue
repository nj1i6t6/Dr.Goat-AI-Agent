<template>
  <div class="traceability-page" v-loading="traceStore.isLoading">
    <div class="header">
      <div>
        <h1 class="page-title">產銷履歷管理</h1>
        <p class="subtitle">建立批次、串聯羊隻資料，讓消費者看見從牧場到餐桌的精彩故事。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateForm">新增產品批次</el-button>
    </div>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>產品批次列表</span>
          <el-switch
            v-model="includeDetails"
            active-text="顯示詳細資訊"
            inactive-text="僅顯示基本資料"
            @change="refreshList"
          />
        </div>
      </template>

      <template v-if="showEmptyState">
        <EmptyState
          icon="📦"
          title="尚未建立任何產品批次。"
          message="在這裡您可以為您的產品建立可追溯的履歷，提升品牌價值。"
        >
          <el-button type="primary" :icon="Plus" @click="openCreateForm">+ 建立第一個產品批次</el-button>
        </EmptyState>
      </template>
      <template v-else>
        <el-table :data="traceStore.sortedBatches" stripe style="width: 100%">
          <el-table-column prop="batch_number" label="批次號" width="160" />
          <el-table-column prop="product_name" label="產品名稱" min-width="200" />
          <el-table-column label="生產日期" width="140">
            <template #default="scope">
              {{ formatDate(scope.row.production_date) }}
            </template>
          </el-table-column>
          <el-table-column label="公開狀態" width="110">
            <template #default="scope">
              <el-tag :type="scope.row.is_public ? 'success' : 'info'">
                {{ scope.row.is_public ? '公開中' : '僅內部' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="建立時間" width="160">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="240">
            <template #default="scope">
              <el-button type="primary" link @click="openDrawer(scope.row)">查看 / 編輯</el-button>
              <el-button type="success" link @click="copyPublicLink(scope.row)">複製公開連結</el-button>
              <el-button type="danger" link @click="confirmDelete(scope.row)">刪除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-card>

    <!-- 建立批次表單 -->
    <el-dialog v-model="formVisible" title="新增產品批次" width="600px">
      <el-form :model="formModel" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="批次號" prop="batch_number">
          <el-input v-model="formModel.batch_number" placeholder="請輸入對外批次號" />
        </el-form-item>
        <el-form-item label="產品名稱" prop="product_name">
          <el-input v-model="formModel.product_name" placeholder="如：鮮羊乳 946ml" />
        </el-form-item>
        <el-form-item label="產品類型">
          <el-input v-model="formModel.product_type" placeholder="如：乳品、肉品等" />
        </el-form-item>
        <el-form-item label="生產日期">
          <el-date-picker v-model="formModel.production_date" type="date" placeholder="選擇日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="到期日">
          <el-date-picker v-model="formModel.expiration_date" type="date" placeholder="選擇日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="產品簡介">
          <el-input v-model="formModel.description" type="textarea" autosize placeholder="簡述產品特色" />
        </el-form-item>
        <el-form-item label="ESG 亮點">
          <el-input v-model="formModel.esg_highlights" type="textarea" autosize placeholder="突出永續與動物福利重點" />
        </el-form-item>
        <el-form-item label="品牌故事">
          <el-input v-model="formModel.origin_story" type="textarea" autosize placeholder="分享品牌或牧場故事" />
  </el-form-item>
        <el-form-item label="立即公開">
          <el-switch v-model="formModel.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="formVisible = false">取消</el-button>
          <el-button type="primary" :loading="traceStore.isSaving" @click="submitForm">建立批次</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 詳情抽屜 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="70%" destroy-on-close>
      <template #default>
        <div v-if="currentBatch" class="drawer-content">
          <section class="section">
            <h2>批次基本資料</h2>
            <el-form :model="detailForm" label-width="120px" class="detail-form">
              <el-row :gutter="20">
                <el-col :md="12" :xs="24">
                  <el-form-item label="批次號">
                    <el-input v-model="detailForm.batch_number" readonly />
                  </el-form-item>
                </el-col>
                <el-col :md="12" :xs="24">
                  <el-form-item label="產品名稱">
                    <el-input v-model="detailForm.product_name" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :md="12" :xs="24">
                  <el-form-item label="產品類型">
                    <el-input v-model="detailForm.product_type" />
                  </el-form-item>
                </el-col>
                <el-col :md="12" :xs="24">
                  <el-form-item label="公開狀態">
                    <el-switch v-model="detailForm.is_public" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :md="12" :xs="24">
                  <el-form-item label="生產日期">
                    <el-date-picker v-model="detailForm.production_date" type="date" style="width: 100%;" />
                  </el-form-item>
                </el-col>
                <el-col :md="12" :xs="24">
                  <el-form-item label="到期日">
                    <el-date-picker v-model="detailForm.expiration_date" type="date" style="width: 100%;" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="產品簡介">
                <el-input v-model="detailForm.description" type="textarea" autosize />
              </el-form-item>
              <el-form-item label="ESG 亮點">
                <el-input v-model="detailForm.esg_highlights" type="textarea" autosize />
              </el-form-item>
              <el-form-item label="品牌故事">
                <el-input v-model="detailForm.origin_story" type="textarea" autosize />
              </el-form-item>
            </el-form>
            <div class="actions">
              <el-button type="primary" :loading="traceStore.isSaving" @click="saveDetails">儲存變更</el-button>
              <el-button @click="copyPublicLink(currentBatch)">複製公開連結</el-button>
            </div>
          </section>

          <section class="section">
            <div class="section-header">
              <h2>羊隻關聯</h2>
              <el-button type="primary" link @click="openSheepDialog">編輯羊隻</el-button>
            </div>
            <el-table :data="currentBatch.sheep_links || []" empty-text="尚未綁定羊隻">
              <el-table-column label="耳號" min-width="120">
                <template #default="scope">
                  {{ scope.row.sheep?.EarNum || '未知' }}
                </template>
              </el-table-column>
              <el-table-column prop="role" label="角色" min-width="120" />
              <el-table-column prop="contribution_type" label="貢獻類型" min-width="120" />
              <el-table-column label="數量" min-width="100">
                <template #default="scope">
                  <span v-if="scope.row.quantity != null">{{ scope.row.quantity }} {{ scope.row.quantity_unit || '' }}</span>
                  <span v-else>—</span>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="備註" min-width="200" show-overflow-tooltip />
            </el-table>
          </section>

          <section class="section">
            <div class="section-header">
              <h2>加工流程</h2>
              <el-button type="primary" link @click="openAddStepDialog">新增步驟</el-button>
            </div>
            <el-table :data="sortedSteps" empty-text="尚未建立加工步驟">
              <el-table-column prop="sequence_order" label="順序" width="80" />
              <el-table-column prop="title" label="步驟" min-width="160" />
              <el-table-column label="時間" min-width="220">
                <template #default="scope">
                  {{ formatStepTime(scope.row) }}
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
              <el-table-column label="操作" width="160">
                <template #default="scope">
                  <el-button type="primary" link @click="openEditStepDialog(scope.row)">編輯</el-button>
                  <el-button type="danger" link @click="confirmDeleteStep(scope.row)">刪除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>
        </div>
      </template>
    </el-drawer>

    <!-- 羊隻設定 -->
    <el-dialog v-model="sheepDialogVisible" title="設定批次參與羊隻" width="700px">
      <div class="sheep-dialog">
        <el-alert type="info" show-icon title="僅會列出您帳戶下的羊隻"></el-alert>
        <el-form label-width="120px" class="sheep-form">
          <el-form-item label="選擇羊隻">
            <el-select v-model="selectedSheepIds" multiple filterable placeholder="搜尋耳號或品種" style="width: 100%;">
              <el-option
                v-for="sheep in sheepOptions"
                :key="sheep.id"
                :label="`${sheep.EarNum}｜${sheep.Breed || '未提供'}`"
                :value="sheep.id"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <div v-if="selectedSheepIds.length" class="sheep-detail-list">
          <el-divider>詳細設定</el-divider>
          <div class="sheep-detail-card" v-for="link in sheepLinkDraft" :key="link.sheep_id">
            <h4>{{ getSheepLabel(link.sheep_id) }}</h4>
            <el-row :gutter="12">
              <el-col :md="12" :xs="24">
                <el-form-item label="角色">
                  <el-input v-model="link.role" />
                </el-form-item>
              </el-col>
              <el-col :md="12" :xs="24">
                <el-form-item label="貢獻類型">
                  <el-input v-model="link.contribution_type" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :md="12" :xs="24">
                <el-form-item label="數量">
                  <el-input-number v-model="link.quantity" :min="0" :step="0.1" style="width: 100%;" />
                </el-form-item>
              </el-col>
              <el-col :md="12" :xs="24">
                <el-form-item label="單位">
                  <el-input v-model="link.quantity_unit" placeholder="如：公升、公斤" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="備註">
              <el-input v-model="link.notes" type="textarea" autosize />
            </el-form-item>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="sheepDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="traceStore.isSaving" @click="saveSheepLinks">儲存設定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增 / 編輯步驟 -->
    <el-dialog v-model="stepDialogVisible" :title="stepDialogMode === 'create' ? '新增加工步驟' : '編輯加工步驟'" width="560px">
      <el-form :model="stepForm" label-width="120px">
        <el-form-item label="步驟名稱">
          <el-input v-model="stepForm.title" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="stepForm.sequence_order" :min="1" />
        </el-form-item>
        <el-form-item label="開始時間">
          <el-date-picker v-model="stepForm.started_at" type="datetime" placeholder="選擇時間" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="完成時間">
          <el-date-picker v-model="stepForm.completed_at" type="datetime" placeholder="選擇時間" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="佐證連結">
          <el-input v-model="stepForm.evidence_url" placeholder="可填入圖片或文件連結" />
        </el-form-item>
        <el-form-item label="步驟描述">
          <el-input v-model="stepForm.description" type="textarea" autosize />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="stepDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="stepSaving" @click="submitStep">儲存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useTraceabilityStore } from '../stores/traceability';
import { useSheepStore } from '../stores/sheep';
import EmptyState from '../components/common/EmptyState.vue';

const traceStore = useTraceabilityStore();
const sheepStore = useSheepStore();

const includeDetails = ref(false);
const formVisible = ref(false);
const formRef = ref(null);
const formModel = reactive({
  batch_number: '',
  product_name: '',
  product_type: '',
  production_date: null,
  expiration_date: null,
  description: '',
  esg_highlights: '',
  origin_story: '',
  is_public: false,
});

const formRules = {
  batch_number: [
    { required: true, message: '請輸入批次號', trigger: 'blur' },
  ],
  product_name: [
    { required: true, message: '請輸入產品名稱', trigger: 'blur' },
  ],
};

const drawerVisible = ref(false);
const detailForm = reactive({});
const stepSaving = ref(false);
const stepDialogVisible = ref(false);
const stepDialogMode = ref('create');
const stepForm = reactive({
  id: null,
  title: '',
  sequence_order: null,
  started_at: null,
  completed_at: null,
  evidence_url: '',
  description: '',
});

const sheepDialogVisible = ref(false);
const selectedSheepIds = ref([]);
const sheepLinkDraft = ref([]);
const showEmptyState = computed(() => !traceStore.sortedBatches.length && !traceStore.isLoading);

const drawerTitle = computed(() => {
  if (!currentBatch.value) return '批次詳情';
  return `${currentBatch.value.product_name}（${currentBatch.value.batch_number}）`;
});

const currentBatch = computed(() => traceStore.selectedBatch);

const sheepOptions = computed(() => {
  return sheepStore.sortedSheepList.map((sheep) => ({
    id: sheep.id,
    EarNum: sheep.EarNum,
    Breed: sheep.Breed,
  }));
});

const sortedSteps = computed(() => {
  if (!currentBatch.value?.steps) return [];
  return [...currentBatch.value.steps].sort((a, b) => (a.sequence_order || 0) - (b.sequence_order || 0));
});

const resetForm = () => {
  Object.assign(formModel, {
    batch_number: '',
    product_name: '',
    product_type: '',
    production_date: null,
    expiration_date: null,
    description: '',
    esg_highlights: '',
    origin_story: '',
    is_public: false,
  });
};

const openCreateForm = () => {
  resetForm();
  formVisible.value = true;
};

const refreshList = async () => {
  await traceStore.fetchBatches(includeDetails.value);
};

const submitForm = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return;
    try {
      const payload = {
        ...formModel,
        production_date: formModel.production_date ? formatDateISO(formModel.production_date) : null,
        expiration_date: formModel.expiration_date ? formatDateISO(formModel.expiration_date) : null,
      };
      const created = await traceStore.createBatch(payload);
      ElMessage.success('批次建立成功');
      formVisible.value = false;
      openDrawer(created);
    } catch (error) {
      ElMessage.error(error?.error || error?.message || '建立批次失敗');
    }
  });
};

const openDrawer = async (batch) => {
  try {
    const data = await traceStore.fetchBatch(batch.id);
    Object.assign(detailForm, {
      id: data.id,
      batch_number: data.batch_number,
      product_name: data.product_name,
      product_type: data.product_type,
      production_date: data.production_date ? new Date(data.production_date) : null,
      expiration_date: data.expiration_date ? new Date(data.expiration_date) : null,
      description: data.description,
      esg_highlights: data.esg_highlights,
      origin_story: data.origin_story,
      is_public: data.is_public,
    });
    drawerVisible.value = true;
  } catch (error) {
    ElMessage.error(error?.error || error?.message || '載入批次資料失敗');
  }
};

const saveDetails = async () => {
  if (!currentBatch.value) return;
  try {
    const payload = {
      product_name: detailForm.product_name,
      product_type: detailForm.product_type,
      description: detailForm.description,
      esg_highlights: detailForm.esg_highlights,
      origin_story: detailForm.origin_story,
      is_public: detailForm.is_public,
      production_date: detailForm.production_date ? formatDateISO(detailForm.production_date) : null,
      expiration_date: detailForm.expiration_date ? formatDateISO(detailForm.expiration_date) : null,
    };
    await traceStore.updateBatch(currentBatch.value.id, payload);
    ElMessage.success('批次資料已更新');
  } catch (error) {
    ElMessage.error(error?.error || error?.message || '更新失敗');
  }
};

const confirmDelete = (batch) => {
  ElMessageBox.confirm(`確定要刪除批次「${batch.product_name}」嗎？`, '警告', {
    type: 'warning',
    confirmButtonText: '刪除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await traceStore.deleteBatch(batch.id);
      ElMessage.success('批次已刪除');
    } catch (error) {
      ElMessage.error(error?.error || error?.message || '刪除失敗');
    }
  }).catch(() => {});
};

const formatDate = (value) => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString();
  } catch (error) {
    return value;
  }
};

const formatDateTime = (value) => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
};

const formatDateISO = (value) => {
  if (!value) return null;
  if (typeof value === 'string') return value;
  try {
    return value.toISOString().split('T')[0];
  } catch (error) {
    return null;
  }
};

const formatDateTimeLocal = (value) => {
  if (!value) return null;
  const dateObj = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(dateObj.getTime())) return null;
  const pad = (num) => String(num).padStart(2, '0');
  const year = dateObj.getFullYear();
  const month = pad(dateObj.getMonth() + 1);
  const day = pad(dateObj.getDate());
  const hours = pad(dateObj.getHours());
  const minutes = pad(dateObj.getMinutes());
  const seconds = pad(dateObj.getSeconds());
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
};

const copyPublicLink = async (batch) => {
  const origin = window.location.origin;
  const link = `${origin}/trace/${batch.batch_number}`;
  try {
    await navigator.clipboard.writeText(link);
    ElMessage.success('公開連結已複製到剪貼簿');
  } catch (error) {
    ElMessage.error('無法複製連結，請手動複製');
  }
};

const openSheepDialog = () => {
  const existingLinks = currentBatch.value?.sheep_links || [];
  selectedSheepIds.value = existingLinks.map(link => link.sheep_id);
  sheepLinkDraft.value = existingLinks.map(link => ({
    sheep_id: link.sheep_id,
    role: link.role || '',
    contribution_type: link.contribution_type || '',
    quantity: link.quantity ?? null,
    quantity_unit: link.quantity_unit || '',
    notes: link.notes || '',
  }));
  sheepDialogVisible.value = true;
};

watch(selectedSheepIds, (newIds) => {
  const draftMap = new Map(sheepLinkDraft.value.map(link => [link.sheep_id, link]));
  const result = [];
  newIds.forEach((id) => {
    if (draftMap.has(id)) {
      result.push(draftMap.get(id));
    } else {
      result.push({
        sheep_id: id,
        role: '',
        contribution_type: '',
        quantity: null,
        quantity_unit: '',
        notes: '',
      });
    }
  });
  sheepLinkDraft.value = result;
});

const getSheepLabel = (id) => {
  const sheep = sheepOptions.value.find(s => s.id === id);
  if (!sheep) return `ID: ${id}`;
  return `${sheep.EarNum}｜${sheep.Breed || '未提供品種'}`;
};

const saveSheepLinks = async () => {
  if (!currentBatch.value) return;
  try {
    const payload = sheepLinkDraft.value.map(link => ({
      sheep_id: link.sheep_id,
      role: link.role || undefined,
      contribution_type: link.contribution_type || undefined,
      quantity: link.quantity !== null ? Number(link.quantity) : undefined,
      quantity_unit: link.quantity_unit || undefined,
      notes: link.notes || undefined,
    }));
    await traceStore.replaceSheepLinks(currentBatch.value.id, payload);
    sheepDialogVisible.value = false;
    ElMessage.success('羊隻設定已更新');
  } catch (error) {
    ElMessage.error(error?.error || error?.message || '更新羊隻設定失敗');
  }
};

const openAddStepDialog = () => {
  stepDialogMode.value = 'create';
  Object.assign(stepForm, {
    id: null,
    title: '',
    sequence_order: currentBatch.value?.steps?.length ? Math.max(...currentBatch.value.steps.map(s => s.sequence_order || 0)) + 1 : 1,
    started_at: null,
    completed_at: null,
    evidence_url: '',
    description: '',
  });
  stepDialogVisible.value = true;
};

const openEditStepDialog = (step) => {
  stepDialogMode.value = 'edit';
  Object.assign(stepForm, {
    id: step.id,
    title: step.title,
    sequence_order: step.sequence_order,
    started_at: step.started_at ? new Date(step.started_at) : null,
    completed_at: step.completed_at ? new Date(step.completed_at) : null,
    evidence_url: step.evidence_url,
    description: step.description,
  });
  stepDialogVisible.value = true;
};

const formatStepTime = (step) => {
  if (!step.started_at && !step.completed_at) return '—';
  const started = step.started_at ? new Date(step.started_at).toLocaleString() : '';
  const completed = step.completed_at ? new Date(step.completed_at).toLocaleString() : '';
  if (started && completed) {
    return `${started} ~ ${completed}`;
  }
  return started || completed;
};

const submitStep = async () => {
  if (!currentBatch.value) return;
  if (!stepForm.title) {
    ElMessage.warning('請輸入步驟名稱');
    return;
  }
  stepSaving.value = true;
  try {
    const payload = {
      title: stepForm.title,
      sequence_order: stepForm.sequence_order,
      started_at: stepForm.started_at ? formatDateTimeLocal(stepForm.started_at) : null,
      completed_at: stepForm.completed_at ? formatDateTimeLocal(stepForm.completed_at) : null,
      evidence_url: stepForm.evidence_url,
      description: stepForm.description,
    };
    if (stepDialogMode.value === 'create') {
      await traceStore.addProcessingStep(currentBatch.value.id, payload);
      await traceStore.fetchBatch(currentBatch.value.id);
      ElMessage.success('步驟已新增');
    } else {
      await traceStore.updateProcessingStep(stepForm.id, payload);
      await traceStore.fetchBatch(currentBatch.value.id);
      ElMessage.success('步驟已更新');
    }
    stepDialogVisible.value = false;
  } catch (error) {
    ElMessage.error(error?.error || error?.message || '儲存步驟時發生錯誤');
  } finally {
    stepSaving.value = false;
  }
};

const confirmDeleteStep = (step) => {
  ElMessageBox.confirm(`確定要刪除步驟「${step.title}」嗎？`, '提醒', {
    confirmButtonText: '刪除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await traceStore.deleteProcessingStep(step.id);
      await traceStore.fetchBatch(currentBatch.value.id);
      ElMessage.success('步驟已刪除');
    } catch (error) {
      ElMessage.error(error?.error || error?.message || '刪除步驟失敗');
    }
  }).catch(() => {});
};

onMounted(async () => {
  await Promise.all([
    sheepStore.fetchSheepList(),
    traceStore.fetchBatches(includeDetails.value),
  ]);
});
</script>

<style scoped>
.traceability-page {
  animation: fadeIn 0.5s ease-out;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 1.8em;
  color: #1e3a8a;
}

.subtitle {
  margin: 6px 0 0;
  color: #475569;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-content {
  padding: 10px 0 40px;
}

.section {
  margin-bottom: 32px;
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-form {
  margin-top: 10px;
}

.actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.sheep-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sheep-form {
  margin-top: 12px;
}

.sheep-detail-list {
  max-height: 360px;
  overflow-y: auto;
  padding-right: 8px;
}

.sheep-detail-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
  .section {
    padding: 16px;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
