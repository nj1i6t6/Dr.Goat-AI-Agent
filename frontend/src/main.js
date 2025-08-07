import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 導入 Element Plus UI 庫及其樣式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

// 導入我們自己的全域樣式
import './assets/styles/main.css'

// 建立 Vue 應用實例
const app = createApp(App)

// 註冊 Pinia 狀態管理
app.use(createPinia())
// 註冊 Vue Router
app.use(router)
// 註冊 Element Plus UI 庫
app.use(ElementPlus)

// 將應用掛載到 index.html 中的 #app 元素上
app.mount('#app')