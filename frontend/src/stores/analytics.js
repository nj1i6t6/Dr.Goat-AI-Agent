import { defineStore } from 'pinia';
import { computed, reactive, ref } from 'vue';
import api from '../api';

const CACHE_TTL_MS = 120_000;
const THROTTLE_MS = 1_500;

function toIsoString(value) {
  if (!value) return undefined;
  if (value instanceof Date) return value.toISOString();
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return undefined;
  return date.toISOString();
}

function normalizeTimeRange(range) {
  if (!range || range.length !== 2) return undefined;
  const [start, end] = range;
  const startIso = toIsoString(start);
  const endIso = toIsoString(end);
  if (!startIso && !endIso) {
    return undefined;
  }
  return {
    start: startIso,
    end: endIso,
  };
}

function normalizeFilters(filters) {
  if (!filters) return undefined;
  const normalized = {};
  Object.entries(filters).forEach(([key, values]) => {
    if (Array.isArray(values) && values.length > 0) {
      normalized[key] = values;
    }
  });
  return Object.keys(normalized).length ? normalized : undefined;
}

function stableSerialize(value) {
  if (Array.isArray(value)) {
    return value.map(stableSerialize);
  }
  if (value && typeof value === 'object') {
    const sorted = {};
    Object.keys(value).sort().forEach((key) => {
      sorted[key] = stableSerialize(value[key]);
    });
    return sorted;
  }
  return value;
}

function buildCacheKey(payload) {
  return JSON.stringify(stableSerialize(payload));
}

export const useAnalyticsStore = defineStore('analytics', () => {
  const costEntries = ref([]);
  const revenueEntries = ref([]);
  const cohortResult = ref(null);
  const costBenefitResult = ref(null);
  const aiReport = ref(null);
  const errorMessage = ref('');

  const loadingStates = reactive({
    costEntries: false,
    revenueEntries: false,
    cohort: false,
    costBenefit: false,
    aiReport: false,
  });

  const cohortForm = reactive({
    dimensions: ['breed'],
    metrics: ['total_cost', 'total_revenue', 'net_income'],
    limit: 15,
    filters: {
      breed: [],
      age_group: [],
      parity: [],
      herd_tag: [],
    },
    timeRange: [],
  });

  const costBenefitForm = reactive({
    metrics: ['total_cost', 'total_revenue', 'net_income', 'cost_revenue_ratio'],
    granularity: 'month',
    filters: {
      breed: [],
      age_group: [],
      parity: [],
      herd_tag: [],
    },
    timeRange: [],
  });

  const cacheStore = reactive({});
  const lastQueryKey = ref(null);
  const lastQueryTimestamp = ref(0);

  const hasCohortData = computed(() => Array.isArray(cohortResult.value?.rows) && cohortResult.value.rows.length > 0);
  const trendData = computed(() => costBenefitResult.value?.trend ?? []);
  const kpis = computed(() => costBenefitResult.value?.kpis ?? {});

  function clearCache() {
    Object.keys(cacheStore).forEach((key) => {
      delete cacheStore[key];
    });
  }

  function handleError(err) {
    if (err?.response?.data?.error) {
      errorMessage.value = err.response.data.error;
    } else if (err?.message) {
      errorMessage.value = err.message;
    } else {
      errorMessage.value = '未知錯誤';
    }
  }

  async function fetchCostEntries(params = {}) {
    loadingStates.costEntries = true;
    errorMessage.value = '';
    try {
      const data = await api.getCostEntries(params);
      costEntries.value = Array.isArray(data) ? data : [];
      return costEntries.value;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      loadingStates.costEntries = false;
    }
  }

  async function createCostEntry(entry) {
    errorMessage.value = '';
    const payload = {
      ...entry,
      recorded_at: toIsoString(entry.recorded_at) || toIsoString(new Date()),
    };
    const created = await api.createCostEntry(payload);
    costEntries.value = [created, ...costEntries.value];
    clearCache();
    return created;
  }

  async function updateCostEntry(id, entry) {
    errorMessage.value = '';
    const payload = {
      ...entry,
    };
    if (entry.recorded_at) {
      payload.recorded_at = toIsoString(entry.recorded_at);
    }
    const updated = await api.updateCostEntry(id, payload);
    const index = costEntries.value.findIndex(item => item.id === updated.id);
    if (index !== -1) {
      costEntries.value.splice(index, 1, updated);
    }
    clearCache();
    return updated;
  }

  async function deleteCostEntry(id) {
    await api.deleteCostEntry(id);
    costEntries.value = costEntries.value.filter(item => item.id !== id);
    clearCache();
  }

  async function fetchRevenueEntries(params = {}) {
    loadingStates.revenueEntries = true;
    errorMessage.value = '';
    try {
      const data = await api.getRevenueEntries(params);
      revenueEntries.value = Array.isArray(data) ? data : [];
      return revenueEntries.value;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      loadingStates.revenueEntries = false;
    }
  }

  async function createRevenueEntry(entry) {
    errorMessage.value = '';
    const payload = {
      ...entry,
      recorded_at: toIsoString(entry.recorded_at) || toIsoString(new Date()),
    };
    const created = await api.createRevenueEntry(payload);
    revenueEntries.value = [created, ...revenueEntries.value];
    clearCache();
    return created;
  }

  async function updateRevenueEntry(id, entry) {
    errorMessage.value = '';
    const payload = {
      ...entry,
    };
    if (entry.recorded_at) {
      payload.recorded_at = toIsoString(entry.recorded_at);
    }
    const updated = await api.updateRevenueEntry(id, payload);
    const index = revenueEntries.value.findIndex(item => item.id === updated.id);
    if (index !== -1) {
      revenueEntries.value.splice(index, 1, updated);
    }
    clearCache();
    return updated;
  }

  async function deleteRevenueEntry(id) {
    await api.deleteRevenueEntry(id);
    revenueEntries.value = revenueEntries.value.filter(item => item.id !== id);
    clearCache();
  }

  function buildCohortRequest(overrides = {}) {
    const filters = normalizeFilters(overrides.filters ?? cohortForm.filters);
    const timeRange = normalizeTimeRange(overrides.timeRange ?? cohortForm.timeRange);
    const payload = {
      dimensions: overrides.dimensions ?? cohortForm.dimensions,
      metrics: overrides.metrics ?? cohortForm.metrics,
      limit: overrides.limit ?? cohortForm.limit,
    };
    if (filters) {
      payload.filters = filters;
    }
    if (timeRange) {
      payload.time_range = timeRange;
    }
    return payload;
  }

  function buildCostBenefitRequest(overrides = {}) {
    const filters = normalizeFilters(overrides.filters ?? costBenefitForm.filters);
    const timeRange = normalizeTimeRange(overrides.timeRange ?? costBenefitForm.timeRange);
    const payload = {
      metrics: overrides.metrics ?? costBenefitForm.metrics,
      granularity: overrides.granularity ?? costBenefitForm.granularity,
    };
    if (filters) {
      payload.filters = filters;
    }
    if (timeRange) {
      payload.time_range = timeRange;
    }
    return payload;
  }

  async function runCohortAnalysis(options = {}) {
    const requestPayload = buildCohortRequest(options);
    const cacheKey = buildCacheKey(requestPayload);
    const now = Date.now();

    if (!options.force && lastQueryKey.value === cacheKey && now - lastQueryTimestamp.value < THROTTLE_MS) {
      return cohortResult.value;
    }

    const cached = cacheStore[cacheKey];
    if (!options.force && cached && now - cached.timestamp < CACHE_TTL_MS) {
      cohortResult.value = cached.data;
      return cached.data;
    }

    loadingStates.cohort = true;
    errorMessage.value = '';
    try {
      const response = await api.requestCohortAnalysis(requestPayload);
      cohortResult.value = response;
      cacheStore[cacheKey] = { data: response, timestamp: now };
      lastQueryKey.value = cacheKey;
      lastQueryTimestamp.value = now;
      return response;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      loadingStates.cohort = false;
    }
  }

  async function runCostBenefit(options = {}) {
    const requestPayload = buildCostBenefitRequest(options);
    const cacheKey = buildCacheKey({ endpoint: 'cost-benefit', ...requestPayload });
    const now = Date.now();

    const cached = cacheStore[cacheKey];
    if (!options.force && cached && now - cached.timestamp < CACHE_TTL_MS) {
      costBenefitResult.value = cached.data;
      return cached.data;
    }

    loadingStates.costBenefit = true;
    errorMessage.value = '';
    try {
      const response = await api.requestCostBenefit(requestPayload);
      costBenefitResult.value = response;
      cacheStore[cacheKey] = { data: response, timestamp: now };
      return response;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      loadingStates.costBenefit = false;
    }
  }

  async function generateAiReport(apiKey, highlights = []) {
    if (!apiKey) {
      throw new Error('缺少 API 金鑰');
    }
    const aggregates = costBenefitResult.value?.kpis ?? {};
    const requestPayload = {
      metrics: costBenefitForm.metrics,
      filters: normalizeFilters(costBenefitForm.filters),
      time_range: normalizeTimeRange(costBenefitForm.timeRange),
      highlights,
      aggregates,
    };

    loadingStates.aiReport = true;
    errorMessage.value = '';
    try {
      const response = await api.requestBiAiReport(apiKey, requestPayload);
      aiReport.value = response;
      return response;
    } catch (err) {
      handleError(err);
      throw err;
    } finally {
      loadingStates.aiReport = false;
    }
  }

  return {
    costEntries,
    revenueEntries,
    cohortResult,
    costBenefitResult,
    aiReport,
    errorMessage,
    loadingStates,
    cohortForm,
    costBenefitForm,
    hasCohortData,
    trendData,
    kpis,
    fetchCostEntries,
    createCostEntry,
    updateCostEntry,
    deleteCostEntry,
    fetchRevenueEntries,
    createRevenueEntry,
    updateRevenueEntry,
    deleteRevenueEntry,
    runCohortAnalysis,
    runCostBenefit,
    generateAiReport,
    clearCache,
  };
});
