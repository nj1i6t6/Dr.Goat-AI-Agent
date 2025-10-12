import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { addDays, differenceInCalendarDays, isBefore, isToday, parseISO } from 'date-fns';
import api from '@/api';

const seedTasks = [
  {
    id: 'vaccination-001',
    type: 'vaccination',
    title: '疫苗接種提醒',
    message: '羊隻 A102 的 口蹄疫 疫苗，即將於 2024-12-18 到期，請準備施打。',
    dueDate: addDays(new Date(), 1).toISOString(),
    earTag: 'A102',
    vaccineName: '口蹄疫',
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 'deworm-001',
    type: 'deworming',
    title: '驅蟲計畫提醒',
    message: '羊群 全場 的例行驅蟲，即將於 2024-12-15 到期。',
    dueDate: addDays(new Date(), -1).toISOString(),
    groupName: '全場',
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 'health-001',
    type: 'health-check',
    title: '定期健康檢查',
    message: '本季度的全場羊隻健康檢查，預計於 2025-01-10 進行。',
    dueDate: addDays(new Date(), 25).toISOString(),
    priority: 'low',
    status: 'pending',
  },
  {
    id: 'withdrawal-001',
    type: 'withdrawal',
    title: '停藥期提醒',
    message: '羊隻 B215 正處於停藥期，距離結束還有 3 天。其乳汁/肉品禁止使用。',
    dueDate: addDays(new Date(), 3).toISOString(),
    earTag: 'B215',
    priority: 'high',
    status: 'pending',
  },
  {
    id: 'pregnancy-check-001',
    type: 'pregnancy-check',
    title: '繁殖週期節點提醒',
    message: '羊隻 C332 距離配種已 30 天，建議進行驗孕。',
    dueDate: addDays(new Date(), 0).toISOString(),
    earTag: 'C332',
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 'prepartum-001',
    type: 'prepartum-care',
    title: '預產期照護提醒',
    message: '羊隻 C332 即將進入預產期 (預計 2025-03-01)，請準備移至分娩欄位並加強產前照護。',
    dueDate: addDays(new Date(), 80).toISOString(),
    earTag: 'C332',
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 'custom-001',
    type: 'custom',
    title: '牧草庫存盤點',
    message: '完成牧草庫存盤點並回報採購需求。',
    dueDate: addDays(new Date(), 2).toISOString(),
    priority: 'low',
    status: 'pending',
  },
];

const normaliseTask = (task) => ({
  ...task,
  dueDate: task.dueDate || task.due_date,
  status: task.status || 'pending',
  priority: task.priority || 'medium',
  message: task.message || task.description || '',
});

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref([]);
  const loading = ref(false);
  const lastError = ref(null);

  const loadFromApi = async () => {
    loading.value = true;
    lastError.value = null;
    try {
      const response = await api.getTaskReminders?.();
      if (response && Array.isArray(response)) {
        tasks.value = response.map(normaliseTask);
      } else if (response?.tasks) {
        tasks.value = response.tasks.map(normaliseTask);
      } else {
        tasks.value = seedTasks;
      }
    } catch (error) {
      console.warn('[tasks] fallback to seed tasks due to API error', error);
      lastError.value = error;
      tasks.value = seedTasks;
    } finally {
      loading.value = false;
    }
  };

  const findTaskIndex = (taskId) => tasks.value.findIndex((task) => task.id === taskId);

  const upsertTask = (payload) => {
    const index = findTaskIndex(payload.id);
    const merged = normaliseTask({
      id: payload.id || `custom-${Date.now()}`,
      ...payload,
    });
    if (index === -1) {
      tasks.value = [merged, ...tasks.value];
    } else {
      const updated = [...tasks.value];
      updated.splice(index, 1, { ...updated[index], ...merged });
      tasks.value = updated;
    }
    return merged;
  };

  const markCompleted = (taskId) => {
    const index = findTaskIndex(taskId);
    if (index === -1) return;
    const updated = [...tasks.value];
    updated[index] = {
      ...updated[index],
      status: 'completed',
      completedAt: new Date().toISOString(),
    };
    tasks.value = updated;
  };

  const snoozeTask = (taskId, days = 1) => {
    const index = findTaskIndex(taskId);
    if (index === -1) return;
    const task = tasks.value[index];
    const newDate = addDays(parseISO(task.dueDate), days);
    const updated = [...tasks.value];
    updated[index] = {
      ...task,
      dueDate: newDate.toISOString(),
      status: 'pending',
    };
    tasks.value = updated;
  };

  const updateTask = (taskId, updates) => {
    const index = findTaskIndex(taskId);
    if (index === -1) return;
    const updated = [...tasks.value];
    updated[index] = normaliseTask({ ...updated[index], ...updates, id: taskId });
    tasks.value = updated;
  };

  const activeTasks = computed(() => tasks.value.filter((task) => task.status !== 'completed'));

  const computeDueState = (task) => {
    const due = parseISO(task.dueDate);
    if (isToday(due)) return 'today';
    if (isBefore(due, new Date())) return 'overdue';
    if (differenceInCalendarDays(due, new Date()) <= 7) return 'upcoming';
    return 'scheduled';
  };

  const tasksWithMeta = computed(() =>
    tasks.value.map((task) => ({
      ...task,
      dueState: computeDueState(task),
      dueDateObj: parseISO(task.dueDate),
    }))
  );

  const todayTasks = computed(() => tasksWithMeta.value.filter((task) => task.dueState === 'today' && task.status !== 'completed'));
  const overdueTasks = computed(() => tasksWithMeta.value.filter((task) => task.dueState === 'overdue' && task.status !== 'completed'));
  const upcomingTasks = computed(() => tasksWithMeta.value.filter((task) => task.dueState === 'upcoming' && task.status !== 'completed'));

  const summary = computed(() => ({
    today: todayTasks.value.length,
    overdue: overdueTasks.value.length,
    upcoming: upcomingTasks.value.length,
    total: activeTasks.value.length,
  }));

  const getTasksByFilter = (filter) => {
    switch (filter) {
      case 'today':
        return todayTasks.value;
      case 'overdue':
        return overdueTasks.value;
      case 'upcoming':
        return upcomingTasks.value;
      default:
        return tasksWithMeta.value;
    }
  };

  const reset = () => {
    tasks.value = seedTasks;
  };

  return {
    tasks,
    loading,
    lastError,
    summary,
    tasksWithMeta,
    todayTasks,
    overdueTasks,
    upcomingTasks,
    loadFromApi,
    upsertTask,
    markCompleted,
    snoozeTask,
    updateTask,
    getTasksByFilter,
    reset,
  };
});
