import { defineStore } from 'pinia';
import { ref, reactive, toRaw } from 'vue';
import api from '../api';

// Helper function to create a clean, initial state for the form
const createInitialFormState = () => ({
  EarNum: '', Breed: '', Sex: '', BirthDate: '',
  Body_Weight_kg: null, Age_Months: null,
  breed_category: 'Dairy', status: 'maintenance', status_description: '',
  target_average_daily_gain_g: null, milk_yield_kg_day: null,
  milk_fat_percentage: null, number_of_fetuses: null,
  activity_level: 'confined', other_remarks: '',
  optimization_goal: 'balanced',
});


export const useConsultationStore = defineStore('consultation', () => {
  // --- State ---
  // 將表單數據本身也作為 store 的一部分
  const form = reactive(createInitialFormState());

  const isLoading = ref(false);
  // 串流狀態（背景任務）
  const isStreaming = ref(false);
  const streamBuffer = ref('');
  let streamHandle = null;
  const resultHtml = ref('');
  const error = ref('');
  
  // --- Actions ---

  // Action to update the form with new data (e.g., from loading a sheep)
  function setFormData(data) {
    // Reset form to initial state first to clear old values
    Object.assign(form, createInitialFormState());
    // Assign new values
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) {
        form[key] = data[key];
      }
    });
    // When new data is loaded, clear the previous AI result
    resultHtml.value = '';
    error.value = '';
  }

  // Action to get recommendation（非串流備援/同步版本）
  async function getRecommendation(apiKey) {
    // We use the form state stored within this store
    const formData = toRaw(form);

    isLoading.value = true;
    resultHtml.value = ''; // Clear previous result before fetching new one
    error.value = '';

    try {
      const response = await api.getRecommendation(apiKey, formData);
      resultHtml.value = response.recommendation_html;
    } catch (err) {
      const errorMessage = err.error || err.message || '獲取建議時發生未知錯誤';
      error.value = errorMessage;
      resultHtml.value = `<div style="color:red;">獲取建議失敗: ${errorMessage}</div>`;
    } finally {
      isLoading.value = false;
    }
  }

  // 背景串流：營養建議（SSE）
  function startStreamingRecommendation(apiKey) {
    // 若已有串流，先中止
    if (isStreaming.value && streamHandle && typeof streamHandle.close === 'function') {
      streamHandle.close();
      streamHandle = null;
    }
    // 重置舊結果
    resultHtml.value = '';
    error.value = '';
    streamBuffer.value = '';
    isStreaming.value = true;

    // 建立串流連線
    try {
      const payload = toRaw(form);
      streamHandle = api.streamRecommendation(
        apiKey,
        payload,
        (chunk) => { streamBuffer.value += chunk; },
        () => { isStreaming.value = false; streamHandle = null; },
        (err) => { error.value = err?.message || '串流中斷'; isStreaming.value = false; streamHandle = null; }
      );
    } catch (e) {
      error.value = '無法建立串流連線';
      isStreaming.value = false;
      streamHandle = null;
    }
  }

  function cancelStreaming() {
    if (streamHandle && typeof streamHandle.close === 'function') {
      streamHandle.close();
    }
    streamHandle = null;
    isStreaming.value = false;
  }

  // Action to reset everything
  function reset() {
    Object.assign(form, createInitialFormState());
    isLoading.value = false;
    cancelStreaming();
    streamBuffer.value = '';
    resultHtml.value = '';
    error.value = '';
  }

  return {
    form,
    isLoading,
    isStreaming,
    streamBuffer,
    resultHtml,
    error,
    setFormData,
    getRecommendation,
    startStreamingRecommendation,
    cancelStreaming,
    reset,
  };
});