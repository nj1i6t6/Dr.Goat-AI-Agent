import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api'; // 導入 api 模組

export const FONT_SCALE = Object.freeze({
  DEFAULT: 'default',
  LARGE: 'large',
  EXTRA_LARGE: 'extra-large',
});

const FONT_SCALE_STORAGE_KEY = 'uiFontScale';

function normaliseFontScale(value) {
  return Object.values(FONT_SCALE).includes(value) ? value : FONT_SCALE.DEFAULT;
}

function applyFontScale(scale) {
  if (typeof document === 'undefined') return;
  const htmlEl = document.documentElement;
  const normalised = normaliseFontScale(scale);
  htmlEl.setAttribute('data-font-scale', normalised);
}

export const useSettingsStore = defineStore('settings', () => {
  // --- State ---
  const apiKey = ref(localStorage.getItem('geminiApiKey') || '');
  const fontScale = ref(normaliseFontScale(localStorage.getItem(FONT_SCALE_STORAGE_KEY)));
  // 新增：用於緩存 AI 每日提示的狀態
  const agentTip = ref({
    html: '',       // 提示的 HTML 內容
    loading: false, // 是否正在加載
    loaded: false,  // 是否已經成功加載過
  });

  applyFontScale(fontScale.value);

  // --- Getters ---
  const hasApiKey = computed(() => !!apiKey.value);

  // --- Actions ---
  function setApiKey(newKey) {
    apiKey.value = newKey;
    localStorage.setItem('geminiApiKey', newKey);
  }

  function clearApiKey() {
    apiKey.value = '';
    localStorage.removeItem('geminiApiKey');
  }

  function setFontScale(newScale) {
    const normalised = normaliseFontScale(newScale);
    fontScale.value = normalised;
    localStorage.setItem(FONT_SCALE_STORAGE_KEY, normalised);
    applyFontScale(normalised);
  }

  function ensureFontScaleApplied() {
    applyFontScale(fontScale.value);
  }

  // 新增：獲取並緩存 AI 每日提示的 action
  async function fetchAndSetAgentTip() {
    // 如果沒有 API Key，或者正在加載中，或者已經加載過了，就直接返回，不再重複請求
    if (!hasApiKey.value || agentTip.value.loading || agentTip.value.loaded) {
      if (!hasApiKey.value && !agentTip.value.loaded) {
        agentTip.value.html = "請先在「系統設定」中設定有效的API金鑰以獲取提示。";
      }
      return;
    }
    
    agentTip.value.loading = true;
    try {
      const response = await api.getAgentTip(apiKey.value);
      agentTip.value.html = response.tip_html;
      agentTip.value.loaded = true; // 標記為已成功加載
    } catch (error) {
      agentTip.value.html = `<span style="color:red;">無法獲取提示: ${error.error || error.message}</span>`;
      // 注意：即使請求失敗，我們也標記為 loaded，以避免在同一次會話中反覆嘗試失敗的請求
      agentTip.value.loaded = true; 
    } finally {
      agentTip.value.loading = false;
    }
  }

  return {
    apiKey,
    fontScale,
    hasApiKey,
    agentTip, // 導出 agentTip 狀態
    setApiKey,
    clearApiKey,
    setFontScale,
    ensureFontScaleApplied,
    fetchAndSetAgentTip, // 導出新的 action
  };
});