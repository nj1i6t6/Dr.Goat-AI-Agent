# 系統功能頁面快照

本文件彙整目前前端應用程式中主要功能頁面的導覽階層、路由位址與核心元件，協助快速檢視「領頭羊博士」系統現況。若需更新此清單，請同步檢查 `frontend/src/router/index.js` 與對應檢視元件。

## 主要導覽分類

| 導覽分組 | 子項目 | 對應路由 | Vue 元件 | 功能重點 |
| --- | --- | --- | --- | --- |
| 📊 代理人儀表板 | 任務提醒卡片、健康與福利警示、ESG 指標速覽、活動日誌 | `/dashboard` | `src/views/DashboardView.vue` | 串接任務 Store 展示「今日待辦」「逾期」「即將到期」，可從儀表板跳轉任務提醒頁；同時顯示健康警示、羊群狀態概覽與 ESG 指標。 |
| 🐑 日常管理 | 羊群總覽 | `/flock` | `src/views/SheepListView.vue` | 提供羊隻篩選、表格檢視與編輯／刪除動作；無資料時顯示空狀態，附手動新增與批次匯入按鈕。 |
|  | 任務提醒 | `/task-reminders` | `src/views/TaskRemindersView.vue` | 與代理人儀表板連結一致，列出疫苗、驅蟲、健康檢查、停藥期、繁殖節點與自訂待辦等任務。 |
| 🤖 智慧羊博士 | 營養代理人與 ESG 建議 | `/consultation` | `src/views/ConsultationView.vue` | 透過耳號載入羊隻資料後，由使用者補充體重、月齡、生理狀態等欄位並呼叫 AI 取得永續飼養建議。 |
|  | 羊博士問答 | `/chat` | `src/views/ChatView.vue` | 提供羊隻耳號上下文、圖片上傳與聊天紀錄管理的 AI 問答介面。 |
| 📈 數據與預測 | 生長預測 | `/prediction` | `src/views/PredictionView.vue` | 選擇耳號與預測天數後呼叫預測 API 顯示體重成長趨勢、日增重、資料品質等指標。 |
|  | 資料治理（原 Analytics Hub） | `/analytics` | `src/views/AnalyticsHubView.vue` | 包含 KPI、同 cohort 分析、成本／收益圖表、自動化報表與成本／收益紀錄表格，提供 CSV 匯出與報表生成功能。 |
| 🌿 永續與追溯 | 產銷履歷 | `/traceability` | `src/views/TraceabilityManagementView.vue` | 管理產品批次與公開資訊，支援空狀態提示、批次詳細抽屜、連結複製與刪除。 |
|  | ESG 指標 | `/esg-metrics` | `src/views/EsgMetricsView.vue` | 專屬 ESG 指標頁面，呈現 FCR、耗水量、碳排密度與動物福利指數等指標，並提供導向資料治理的動作。 |
| 📡 物聯網自動化 | 物聯網儀表 | `/iot-dashboard` | `src/views/IotDashboardView.vue` | 顯示裝置上線狀態、離線警示、連線概況長條圖與活動日誌；無裝置時顯示空狀態並導向裝置管理。 |
|  | IoT 裝置管理 | `/iot` | `src/views/IotManagementView.vue` | 列出裝置、提供 CRUD、顯示裝置詳情抽屜與最近讀數圖表，並管理自動化規則。 |
| ⚙️ 系統設定 | 系統設定 | `/settings` | `src/views/SettingsView.vue` | 管理介面字級、Gemini API 金鑰與事件選項。 |
| 其他 | 數據管理中心 | `/data-management` | `src/views/DataManagementView.vue` | 提供資料匯出、標準範本下載、快速／自訂／AI 導入流程與映射設定。 |
|  | 登入／註冊 | `/login` | `src/views/LoginView.vue` | 供使用者登入或註冊帳號，成功後導向儀表板。 |
|  | 公開產銷履歷 | `/trace/:batchNumber` | `src/views/TraceabilityPublicView.vue` | 對外公開批次資訊，包含加工歷程、羊隻細節與佐證連結。 |

## 補充說明

- 所有受保護頁面皆以 `AppLayout` 為母版並透過 `vue-router` 子路由切換，包含固定頂部標頭與左側導覽列。`AppLayout` 組件內建桌面／行動響應、導覽收合、深淺色模式切換佔位與漢堡選單。 
- `EmptyState` 元件用於羊群總覽、產銷履歷與 IoT 裝置管理等頁面，在無資料時提供圖示、標題、訊息與操作插槽。
- 任務提醒頁面連動 `src/stores/tasks.js`，覆蓋疫苗、驅蟲、健康檢查、停藥期、繁殖節點以及自訂待辦，並將摘要資訊回饋至儀表板卡片。
- 物聯網儀表與裝置管理共用 `useIotStore`，前者提供儀表概覽與活動日誌，後者則以表格、抽屜與規則管理呈現詳細操作。 
- 若需實際畫面截圖，可先執行 `npm install` 後啟動 `npm run dev`，再使用 Playwright 或其他自動化工具對上述路由進行瀏覽與截圖。稍後若取得實際畫面資源，可於 `docs/` 目錄新增對應圖片並在此文件補上連結。
