import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'

// 導入 Element Plus UI 庫及其樣式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

// 導入我們自己的全域樣式
import './style.css'
import './assets/styles/main.css'

import { useSettingsStore } from './stores/settings'

const applyFontScale = (scale) => {
  const root = document.documentElement
  root.setAttribute('data-font-scale', scale)
}

// 建立 Vue 應用實例
const app = createApp(App)

// 註冊 Pinia 狀態管理
const pinia = createPinia()
app.use(pinia)
// 註冊 Vue Router
app.use(router)
// 註冊 Element Plus UI 庫
app.use(ElementPlus)

const settingsStore = useSettingsStore(pinia)
applyFontScale(settingsStore.fontScale)

watch(
  () => settingsStore.fontScale,
  (scale) => {
    applyFontScale(scale)
  }
)

// 將應用掛載到 index.html 中的 #app 元素上
app.mount('#app')