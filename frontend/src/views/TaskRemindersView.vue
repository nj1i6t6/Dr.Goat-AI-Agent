<template>
  <div class="tasks-page" v-loading="taskStore.loading">
    <header class="tasks-page__header">
      <div>
        <h1 class="tasks-page__title">任務提醒</h1>
        <p class="tasks-page__subtitle">
          預設顯示今日待辦與已逾期的工作，協助您即時掌握牧場最重要的行動項目。
        </p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openTaskDialog()">+ 新增任務</el-button>
    </header>

    <section class="tasks-summary">
      <div class="summary-card">
        <span class="summary-card__label">今日待辦</span>
        <strong class="summary-card__value">{{ taskStore.summary.today }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-card__label">已逾期</span>
        <strong class="summary-card__value is-danger">{{ taskStore.summary.overdue }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-card__label">即將到期 (7 日內)</span>
        <strong class="summary-card__value">{{ taskStore.summary.upcoming }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-card__label">全部未完成</span>
        <strong class="summary-card__value">{{ taskStore.summary.total }}</strong>
      </div>
    </section>

    <el-segmented v-model="activeFilter" class="tasks-filter" :options="filterOptions" size="large" />

    <section class="tasks-list" v-if="filteredTasks.length">
      <article
        v-for="task in filteredTasks"
        :key="task.id"
        class="task-card"
        :class="{
          'task-card--critical': task.type === 'withdrawal' && task.status !== 'completed',
          'task-card--completed': task.status === 'completed',
        }"
      >
        <header class="task-card__header">
          <div class="task-card__title-group">
            <el-tag
              :type="tagType(task)"
              size="small"
              effect="dark"
              round
              class="task-card__badge"
            >
              {{ taskLabel(task.type) }}
            </el-tag>
            <h2 class="task-card__title">{{ task.title }}</h2>
            <span v-if="task.earTag" class="task-card__meta">
              耳號：
              <button type="button" class="task-card__ear-link" @click="navigateToSheep(task.earTag)">
                {{ task.earTag }}
              </button>
            </span>
            <span v-else-if="task.groupName" class="task-card__meta">{{ task.groupName }}</span>
          </div>
          <div class="task-card__due">
            <el-tag :type="dueTagType(task)" effect="plain">
              {{ formatDue(task) }}
            </el-tag>
            <el-tag v-if="task.status === 'completed'" type="success" effect="plain">已完成</el-tag>
          </div>
        </header>

        <p class="task-card__message">{{ task.message }}</p>

        <footer class="task-card__footer">
          <div class="task-card__actions">
            <el-button
              size="small"
              type="success"
              plain
              :icon="Check"
              :disabled="task.status === 'completed'"
              @click="completeTask(task.id)"
            >
              ✓ 完成
            </el-button>
            <el-button
              size="small"
              type="warning"
              plain
              :icon="Clock"
              :disabled="task.status === 'completed'"
              @click="snoozeTask(task.id)"
            >
              ⏰ 稍後提醒
            </el-button>
            <el-button size="small" type="primary" text :icon="Edit" @click="openTaskDialog(task)">
              ✎ 編輯
            </el-button>
          </div>
          <div v-if="task.type === 'withdrawal' && task.status !== 'completed'" class="task-card__alert">
            <el-icon><WarningFilled /></el-icon>
            <span>停藥期結束前的乳汁/肉品請勿出場或販售。</span>
          </div>
        </footer>
      </article>
    </section>

    <EmptyState
      v-else
      icon="📝"
      title="暫無符合條件的任務"
      message="所有任務都安排妥當了！您可以建立新的待辦事項，或調整篩選條件。"
    >
      <el-button type="primary" :icon="Plus" @click="openTaskDialog()">+ 新增任務</el-button>
    </EmptyState>

    <el-dialog v-model="taskDialogVisible" :title="taskDialogTitle" width="520px" destroy-on-close>
      <el-form ref="taskFormRef" :model="taskForm" label-width="120px" :rules="taskFormRules">
        <el-form-item label="任務類型" prop="type">
          <el-select v-model="taskForm.type" placeholder="選擇類型">
            <el-option v-for="option in taskTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="任務標題" prop="title">
          <el-input v-model="taskForm.title" placeholder="請輸入任務標題" />
        </el-form-item>
        <el-form-item label="關聯耳號">
          <el-input v-model="taskForm.earTag" placeholder="若適用，輸入耳號" />
        </el-form-item>
        <el-form-item label="群體/備註">
          <el-input v-model="taskForm.groupName" placeholder="全場或群體名稱" />
        </el-form-item>
        <el-form-item label="到期日" prop="dueDate">
          <el-date-picker v-model="taskForm.dueDate" type="date" placeholder="選擇日期" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="優先級">
          <el-radio-group v-model="taskForm.priority">
            <el-radio-button label="high">高</el-radio-button>
            <el-radio-button label="medium">中</el-radio-button>
            <el-radio-button label="low">低</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="提醒內容" prop="message">
          <el-input v-model="taskForm.message" type="textarea" rows="4" placeholder="輸入提醒內容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitTask">儲存任務</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { format, parseISO } from 'date-fns';
import { zhTW } from 'date-fns/locale';
import { ElMessage } from 'element-plus';
import { Check, Clock, Edit, Plus, WarningFilled } from '@element-plus/icons-vue';
import EmptyState from '@/components/common/EmptyState.vue';
import { useTaskStore } from '@/stores/tasks';

const toDateOrEmpty = (value) => {
  if (!value) return '';
  try {
    return value instanceof Date ? value : parseISO(value);
  } catch (error) {
    console.warn('[tasks] failed to parse due date, reset to empty', error);
    return '';
  }
};

const serialiseDueDate = (value) => {
  if (!value) return '';
  if (value instanceof Date) return value.toISOString();
  const coerced = new Date(value);
  return Number.isNaN(coerced.getTime()) ? '' : coerced.toISOString();
};

const router = useRouter();
const taskStore = useTaskStore();

const activeFilter = ref('today');
const filterOptions = [
  { label: '今日待辦', value: 'today' },
  { label: '即將到期', value: 'upcoming' },
  { label: '已逾期', value: 'overdue' },
  { label: '全部任務', value: 'all' },
];

const filteredTasks = computed(() => {
  const source = activeFilter.value === 'all' ? taskStore.tasksWithMeta : taskStore.getTasksByFilter(activeFilter.value);
  return [...source].sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate));
});

const taskDialogVisible = ref(false);
const saving = ref(false);
const taskFormRef = ref();
const editingTaskId = ref(null);
const taskForm = reactive({
  type: 'custom',
  title: '',
  earTag: '',
  groupName: '',
  dueDate: '',
  priority: 'medium',
  message: '',
});

const taskFormRules = {
  type: [{ required: true, message: '請選擇任務類型', trigger: 'change' }],
  title: [{ required: true, message: '請輸入任務標題', trigger: 'blur' }],
  dueDate: [{ required: true, message: '請選擇到期日', trigger: 'change' }],
  message: [{ required: true, message: '請輸入提醒內容', trigger: 'blur' }],
};

const taskTypeOptions = [
  { value: 'vaccination', label: '疫苗接種提醒' },
  { value: 'deworming', label: '驅蟲計畫提醒' },
  { value: 'health-check', label: '定期健康檢查' },
  { value: 'withdrawal', label: '停藥期提醒' },
  { value: 'pregnancy-check', label: '繁殖節點提醒' },
  { value: 'prepartum-care', label: '預產期照護' },
  { value: 'custom', label: '自訂待辦事項' },
];

const taskDialogTitle = computed(() => (editingTaskId.value ? '編輯任務' : '新增任務'));

const openTaskDialog = (task = null) => {
  if (task) {
    editingTaskId.value = task.id;
    Object.assign(taskForm, {
      type: task.type,
      title: task.title,
      earTag: task.earTag || '',
      groupName: task.groupName || '',
      dueDate: toDateOrEmpty(task.dueDate),
      priority: task.priority || 'medium',
      message: task.message || '',
    });
  } else {
    editingTaskId.value = null;
    Object.assign(taskForm, {
      type: 'custom',
      title: '',
      earTag: '',
      groupName: '',
      dueDate: '',
      priority: 'medium',
      message: '',
    });
  }
  taskDialogVisible.value = true;
};

const submitTask = () => {
  taskFormRef.value?.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      const payload = {
        id: editingTaskId.value || undefined,
        type: taskForm.type,
        title: taskForm.title,
        earTag: taskForm.earTag || undefined,
        groupName: taskForm.groupName || undefined,
        dueDate: serialiseDueDate(taskForm.dueDate),
        priority: taskForm.priority,
        message: taskForm.message,
      };
      taskStore.upsertTask(payload);
      taskDialogVisible.value = false;
      ElMessage.success(editingTaskId.value ? '任務已更新' : '任務已建立');
    } finally {
      saving.value = false;
    }
  });
};

const formatDue = (task) => {
  const date = parseISO(task.dueDate);
  const prefix = task.status === 'completed' ? '完成於' : '到期';
  return `${prefix} ${format(date, 'MM 月 dd 日', { locale: zhTW })}`;
};

const tagType = (task) => {
  if (task.type === 'withdrawal') return 'danger';
  if (task.type === 'vaccination' || task.type === 'deworming') return 'warning';
  if (task.type === 'health-check') return 'info';
  return 'primary';
};

const dueTagType = (task) => {
  if (task.status === 'completed') return 'success';
  switch (task.dueState) {
    case 'overdue':
      return 'danger';
    case 'today':
      return 'warning';
    case 'upcoming':
      return 'info';
    default:
      return 'primary';
  }
};

const taskLabel = (type) => {
  const option = taskTypeOptions.find((item) => item.value === type);
  return option ? option.label : type;
};

const completeTask = (taskId) => {
  taskStore.markCompleted(taskId);
  ElMessage.success('任務已完成');
};

const snoozeTask = (taskId) => {
  taskStore.snoozeTask(taskId, 1);
  ElMessage.info('已延後一天提醒');
};

const navigateToSheep = (earTag) => {
  router.push({ name: 'SheepList', query: { earNum: earTag } });
};

onMounted(() => {
  taskStore.loadFromApi();
});
</script>

<style scoped>
.tasks-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tasks-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.tasks-page__title {
  margin: 0;
  font-size: 1.8rem;
  color: #1e3a8a;
}

.tasks-page__subtitle {
  margin: 4px 0 0;
  color: #475569;
  font-size: 0.95rem;
}

.tasks-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.summary-card__label {
  font-size: 0.85rem;
  color: #1d4ed8;
}

.summary-card__value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-card__value.is-danger {
  color: #b91c1c;
}

.tasks-filter {
  align-self: flex-start;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 18px 30px rgba(15, 23, 42, 0.08);
}

.task-card--critical {
  border-color: rgba(239, 68, 68, 0.6);
  box-shadow: 0 18px 32px rgba(239, 68, 68, 0.15);
}

.task-card--completed {
  opacity: 0.65;
}

.task-card__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.task-card__title-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.task-card__badge {
  font-weight: 600;
}

.task-card__title {
  margin: 0;
  font-size: 1.25rem;
  color: #0f172a;
}

.task-card__meta {
  font-size: 0.9rem;
  color: #334155;
}

.task-card__ear-link {
  background: none;
  border: none;
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
}

.task-card__due {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-card__message {
  margin: 0;
  line-height: 1.5;
  color: #1f2937;
}

.task-card__footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.task-card__alert {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #b91c1c;
  font-weight: 600;
}

@media (max-width: 768px) {
  .tasks-page__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .tasks-page__title {
    font-size: 1.5rem;
  }

  .tasks-summary {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }
}
</style>
