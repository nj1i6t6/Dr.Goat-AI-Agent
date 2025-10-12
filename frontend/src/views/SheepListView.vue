<template>
  <div class="sheep-list-page">
    <h1 class="page-title">
      <el-icon><Tickets /></el-icon>
      羊群總覽
    </h1>

    <EmptyState
      v-if="showEmptyState"
      icon="🐑"
      title="您的牧場還沒有任何羊隻記錄。"
      message="您可以選擇手動新增第一筆資料，或透過我們提供的 Excel 範本進行批次匯入。"
    >
      <el-button type="primary" :icon="Plus" @click="openModal(null)">+ 手動新增羊隻</el-button>
      <el-button type="success" plain @click="handleBatchImport">🚀 批次匯入資料</el-button>
    </EmptyState>

    <template v-else>
      <!-- 篩選器元件 -->
      <SheepFilter @filter="applyFilters" />

      <el-card shadow="never">
        <div class="table-header">
          <el-button type="primary" :icon="Plus" @click="openModal(null)">新增羊隻資料</el-button>
          <div class="list-summary">{{ summaryText }}</div>
        </div>

        <!-- 表格元件 -->
        <SheepTable
          :sheep-data="filteredSheep"
          :loading="sheepStore.isLoading"
          @edit="openModal"
          @delete="handleDelete"
          @view-log="openModalWithTab('eventsLogTab', $event)"
          @consult="navigateToConsultation"
        />
      </el-card>
    </template>

    <!-- 模態窗元件 -->
    <SheepModal
      v-if="isModalVisible"
      :ear-num="editingEarNum"
      :initial-tab="initialTab"
      @close="closeModal"
      @data-updated="handleDataUpdated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Tickets, Plus } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useSheepStore } from '../stores/sheep';
import api from '../api';

// 導入子元件
import SheepFilter from '../components/sheep/SheepFilter.vue';
import SheepTable from '../components/sheep/SheepTable.vue';
import SheepModal from '../components/sheep/SheepModal.vue';
import EmptyState from '../components/common/EmptyState.vue';

const router = useRouter();
const sheepStore = useSheepStore();

const filters = ref({});
const filteredSheep = ref([]);

const isModalVisible = ref(false);
const editingEarNum = ref(null);
const initialTab = ref('basicInfoTab');
const showEmptyState = computed(() => !sheepStore.isLoading && sheepStore.sheepList.length === 0);

const summaryText = computed(() => `共 ${sheepStore.sheepList.length} 隻，顯示 ${filteredSheep.value.length} 隻`);

const applyFilters = (newFilters) => {
  filters.value = newFilters;
  let result = [...sheepStore.sheepList];

  // --- 新增：應用耳號模糊搜尋邏輯 ---
  if (filters.value.earNumSearch) {
    const searchTerm = filters.value.earNumSearch.toLowerCase();
    result = result.filter(s => s.EarNum && s.EarNum.toLowerCase().includes(searchTerm));
  }

  // 應用其他篩選邏輯
  if (filters.value.farmNum) result = result.filter(s => s.FarmNum === filters.value.farmNum);
  if (filters.value.breed) result = result.filter(s => s.Breed === filters.value.breed);
  if (filters.value.sex) result = result.filter(s => s.Sex === filters.value.sex);
  if (filters.value.breedCategory) result = result.filter(s => s.breed_category === filters.value.breedCategory);
  if (filters.value.status) result = result.filter(s => s.status === filters.value.status);
  
  if (filters.value.startDate) {
    const start = new Date(filters.value.startDate).getTime();
    result = result.filter(s => s.BirthDate && new Date(s.BirthDate).getTime() >= start);
  }
  if (filters.value.endDate) {
    const end = new Date(filters.value.endDate).getTime();
    result = result.filter(s => s.BirthDate && new Date(s.BirthDate).getTime() <= end);
  }

  filteredSheep.value = result;
};

const openModal = (earNum) => {
  editingEarNum.value = earNum;
  initialTab.value = 'basicInfoTab';
  isModalVisible.value = true;
};

const openModalWithTab = (tab, earNum) => {
  editingEarNum.value = earNum;
  initialTab.value = tab;
  isModalVisible.value = true;
};

const closeModal = () => {
  isModalVisible.value = false;
  editingEarNum.value = null;
};

const handleDataUpdated = () => {
  closeModal();
  applyFilters(filters.value);
};

const handleDelete = async (earNum) => {
  try {
    await ElMessageBox.confirm(`確定要刪除耳號為 ${earNum} 的羊隻資料及其所有相關記錄嗎？此操作無法復原。`, '警告', {
      confirmButtonText: '確定刪除',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await api.deleteSheep(earNum);
    sheepStore.removeSheep(earNum);
    applyFilters(filters.value);
    ElMessage.success('刪除成功');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`刪除失敗: ${error.error || error.message}`);
    }
  }
};

const navigateToConsultation = (earNum) => {
  router.push({ name: 'Consultation', query: { earNum } });
};

const handleBatchImport = () => {
  ElMessage.info('批次匯入功能將引導您使用 Excel 範本，敬請期待。');
};

onMounted(async () => {
  await sheepStore.fetchSheepList();
  applyFilters({}); 
});
</script>

<style scoped>
.sheep-list-page { animation: fadeIn 0.5s ease-out; }
.page-title {
  font-size: 1.8em; color: #1e3a8a; margin-top: 0;
  margin-bottom: 20px; display: flex; align-items: center;
}
.page-title .el-icon { margin-right: 10px; }
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.list-summary {
  font-weight: 500;
  color: #606266;
}
</style>