# 領頭羊博士專案全景指南

> 山羊營養智慧管理一站式平台：結合 Flask 後端、Vue 3 前端、Gemini AI、LightGBM 生長模型與 Excel 批次資料匯入匯出，支援 ESG 追蹤、產銷履歷公開與多角色協作。

---

## 目錄

1. [專案使命與產品價值](#1-專案使命與產品價值)
2. [系統架構與運作流程](#2-系統架構與運作流程)
3. [後端服務（Flask）詳解](#3-後端服務flask詳解)
4. [前端應用（Vue 3）詳解](#4-前端應用vue-3詳解)
5. [AI 與機器學習能力](#5-ai-與機器學習能力)
6. [開發與執行環境建置](#6-開發與執行環境建置)
7. [環境變數與組態](#7-環境變數與組態)
8. [資料導入與匯出流程](#8-資料導入與匯出流程)
9. [測試與品質保證](#9-測試與品質保證)
10. [部署與維運指引](#10-部署與維運指引)
11. [安全性與隱私保護](#11-安全性與隱私保護)
12. [文件、資產與腳本索引](#12-文件資產與腳本索引)
13. [常見排錯與最佳化建議](#13-常見排錯與最佳化建議)
14. [版本沿革與路線圖](#14-版本沿革與路線圖)

---

## 1. 專案使命與產品價值

### 1.1 解決的核心問題
- 統整牧場多來源資料（羊隻、事件、歷史紀錄、產銷履歷、ESG 指標）。
- 以 AI 提供營養諮詢、每日提示、圖像輔助診斷與 ESG 建議。
- 透過預測模型呈現羊隻成長趨勢、置信區間與管理建議。
- 提供 Excel 批次匯入、自動欄位對應、匯出多工作表與資料簽核流程。
- 建立可公開分享的產品產銷履歷與 QR Code 擴散能力。

### 1.2 功能地圖

| 領域 | 代表功能 | 主要後端模組 | 前端視圖 / 組件 | 對應測試 |
|------|----------|--------------|-----------------|-----------|
| 身份驗證 | 註冊、登入、會話管理 | `app/api/auth.py` | `LoginView.vue`、`auth` store | `test_auth_api.py`, `test_auth_agent_enhanced.py` |
| 羊隻管理 | 基本資料、事件、歷史數據 | `app/api/sheep.py` | `SheepListView.vue` + sheep 組件 | `test_sheep_*` 系列 |
| 儀表板 | 聚合統計、提醒、快取 | `app/api/dashboard.py` + `cache.py` | `DashboardView.vue` | `test_dashboard_*` 系列 |
| 資料匯入匯出 | Excel 分析、AI 對應、批次導入 | `app/api/data_management.py` | `DataManagementView.vue` | `test_data_management_*` 系列 |
| AI 協作 | 每日提示、諮詢、圖片聊天 | `app/api/agent.py` + `utils.py` | `ChatView.vue`、`ConsultationView.vue` | `test_agent_*` 系列 |
| 生長預測 | LightGBM + 線性迴歸備援 | `app/api/prediction.py` | `PredictionView.vue` | `test_prediction_api.py`, `test_prediction_manual.py` |
| 產銷履歷 | 批次、加工流程、公開頁 | `app/api/traceability.py` | `TraceabilityManagementView.vue`, `TraceabilityPublicView.vue` | `test_traceability_api.py`, `test_traceability_enhanced.py` |
| ESG 協助 | ESG 欄位、建議、故事 | `models.py`、`agent.py` | Dashboard 卡片、AI 輸出 | `test_dashboard_enhanced.py` |
| 背景任務 | 儀表板快照、匯出等耗時流程排程 | `app/api/tasks.py`、`app/tasks.py` | （未提供專屬前端頁，透過 API 觸發） | `test_tasks_api.py` |

---

## 2. 系統架構與運作流程

### 2.1 高階架構圖

```mermaid
graph TB
        subgraph Client[使用者瀏覽器]
                UI[Vue 3 SPA]
                Pinia[Pinia Stores]
        end

        subgraph Frontend[Frontend (Vite build → Nginx)]
                Router[Vue Router 4]
                Components[Element Plus Components]
                ApiClient[Axios API client]
        end

        subgraph Backend[Backend (Flask 3)]
                Auth[Auth Blueprint]
                Sheep[Sheep Blueprint]
                Dashboard[Dashboard Blueprint]
                Data[Data Management Blueprint]
                Prediction[Prediction Blueprint]
                Agent[Agent Blueprint]
                Traceability[Traceability Blueprint]
                Tasks[Tasks Blueprint]
        end

        subgraph DataTier[Persistence Layer]
                Postgres[(PostgreSQL 13+/Prod)]
                SQLite[(SQLite/Dev&Test)]
                Filesystem[(模型與媒體檔案)]
                Redis[(Redis Cache & Queue)]
        end

        subgraph Worker[Background Worker]
                WorkerNode[Worker]
        end

        subgraph External[外部整合]
                Gemini[Google Gemini API]
        end

        UI --> Router --> ApiClient --> Auth
        ApiClient --> Sheep
        ApiClient --> Dashboard
        ApiClient --> Data
        ApiClient --> Prediction
        ApiClient --> Agent
        ApiClient --> Traceability

        Auth --> Postgres
        Sheep --> Postgres
        Dashboard --> Redis
        Data --> Postgres
        Prediction --> Postgres
        Traceability --> Postgres
        Tasks --> Redis

        Prediction --> Gemini
        Agent --> Gemini

        WorkerNode --> Redis
        WorkerNode --> Postgres
```

### 2.2 核心流程
- **瀏覽→登入**：Vue Router 透過導航守衛檢查 `auth` store，使用 Axios `withCredentials` 與 Flask-Login Session 維持身份。
- **資料展示**：Dashboard Blueprint 聚合多個模型後以快取 (`cache.py`, TTL 90 秒) 回應；前端以 ECharts/Element Plus 呈現。
- **AI 諮詢**：前端取得使用者 API key（或系統設定），呼叫 `/api/agent/*`，由 `utils.call_gemini_api` 統一對 Gemini 呼叫並回傳 Markdown。
- **預測**：`/api/prediction` 載入 LightGBM joblib 與回歸備援模型，產生每日體重預估與信賴區間，再返回給前端繪圖。
- **產銷履歷公開**：批次資訊與羊隻關聯儲存於 `ProductBatch`、`ProcessingStep`、`BatchSheepAssociation`，`/api/traceability/public/<batch_number>` 提供匿名存取以供 QR Code 分享。

### 2.3 部署拓撲
- **開發模式**：Flask `run.py`（Waitress）+ Vite Dev Server；SQLite 儲存於 `backend/instance/app.db`。
- **Docker Compose**：`db`(Postgres 15)、`backend`(Flask + Waitress)、`frontend`(Nginx)；健康檢查覆蓋 `/api/auth/status` 與 `http://frontend/`。
- **Codespaces/Codespace**：`deploy-codespaces.sh` 自動化建置；`start_codespaces.sh`、`start_production.sh` 提供啟動腳本。

---

## 3. 後端服務（Flask）詳解

### 3.1 技術棧
- Flask 3.0.3（應用程式工廠 `app/__init__.py`）
- SQLAlchemy 2.0 + Alembic 資料庫遷移
- Pydantic 2.x 驗證請求/回應模型
- Waitress 3.0 作為 WSGI 伺服器
- Pandas + OpenPyXL 處理 Excel
- Google Generative AI SDK 0.8.5
- Redis 5 + Flask-Session 0.5（Session/快取）
- 輕量 RQ 風格佇列（背景任務）
- pytest 8.2 + pytest-cov 作為單元/整合測試框架

### 3.2 應用結構

```
backend/app/
├── __init__.py        # App factory, Blueprint 註冊, DB/CORS/Login、Redis/佇列設定
├── cache.py           # Redis setex 快取 + 分佈式 Lock（90 秒）
├── error_handlers.py  # 全域例外對應 JSON 錯誤格式
├── models.py          # ORM 模型（含複合索引/ESG 欄位）
├── schemas.py         # Pydantic 模型 & 錯誤格式化
├── tasks.py           # 輕量佇列工具與示範任務
├── utils.py           # Gemini API 呼叫、上下文組裝、圖片 base64
└── api/               # Blueprint modules（詳見下表）
```

### 3.3 Blueprint 對照表

| Blueprint | 路徑前綴 | 核心職責 | 重要依賴 | 關鍵測試檔 |
|-----------|----------|----------|----------|------------|
| `auth` (`auth.py`) | `/api/auth` | 註冊/登入/登出/狀態，Flask-Login session | `User` 模型、`flask_login` | `test_auth_api.py`, `test_auth_agent_enhanced.py` |
| `sheep` (`sheep.py`) | `/api/sheep` | 羊隻 CRUD、事件、歷史紀錄、批次關聯 | `Sheep`, `SheepEvent`, `SheepHistoricalData`, `BatchSheepAssociation` | `test_sheep_api.py`, `test_sheep_events_api.py`, `test_sheep_history_api.py` |
| `dashboard` (`dashboard.py`) | `/api/dashboard` | 統計數據、關鍵提醒、自定義事件選項 | `cache.py`, SQL 聚合, ESG 欄位 | `test_dashboard_api.py`, `test_dashboard_enhanced.py` |
| `data_management` | `/api/data` | Excel 匯入匯出、AI 欄位映射、批次處理 | Pandas, Gemini API, `Sheep*` 模型 | `test_data_management_*` 系列 |
| `prediction` | `/api/prediction` | LightGBM/線性回歸預測、圖表資料 | Joblib 模型、`utils.call_gemini_api` (ESG 文案) | `test_prediction_api.py`, `test_prediction_manual.py` |
| `agent` | `/api/agent` | 每日提示、營養建議、圖片聊天、聊天記錄 | Gemini API、`ChatHistory` | `test_agent_api.py`, `test_agent_enhanced.py` |
| `traceability` | `/api/traceability` | 產品批次、加工流程、羊隻貢獻、公開端 | `ProductBatch`, `ProcessingStep`, `BatchSheepAssociation` | `test_traceability_api.py`, `test_traceability_enhanced.py` |
| `tasks` | `/api/tasks` | 透過 Redis + 輕量佇列觸發背景任務 | `tasks.py`, Redis Broker | `test_tasks_api.py` |

### 3.4 資料模型摘要

| 模型 | 說明 | 關聯重點 |
|------|------|----------|
| `User` | 系統使用者帳號（Flask-Login 會話） | `sheep`, `events`, `product_batches`, `chat_history` 一對多 |
| `Sheep` | 羊隻主檔，涵蓋識別、血統、ESG 與生產欄位，`EarNum` + `user_id` 唯一 | 與 `SheepEvent`, `SheepHistoricalData`, `BatchSheepAssociation` 一對多 |
| `SheepEvent` | 羊隻事件（含 ESG 食品安全欄位） | 連動 `Sheep`，刪除羊隻 cascade |
| `SheepHistoricalData` | 歷史測量，如體重/乳量 | 紀錄類型 + 數值 + 備註 |
| `ChatHistory` | AI 對話記錄（含 session 與耳號上下文） | 供 ChatView 重建歷史與 prompt |
| `ProductBatch` | 產品批次資訊、ESG 故事、公開旗標 | 關聯 `ProcessingStep`、`BatchSheepAssociation` |
| `ProcessingStep` | 加工流程步驟（順序、證據 URL） | 與批次多對一，具排序索引 |
| `BatchSheepAssociation` | 批次-羊隻多對多關聯（貢獻類型、角色、數量） | 與 `Sheep`、`ProductBatch` 建立多對多 |

### 3.5 AI 與預測服務
- `utils.call_gemini_api`：統一處理 API key 驗證、safety settings、錯誤訊息格式。
- `agent.py`：Markdown 回傳 + 圖片上傳（支援 JPEG/PNG/GIF/WebP ≤10MB），並將圖片 Base64 送往 Gemini。
- `prediction.py`：
    - 讀取 `sheep_growth_lgbm.joblib`（回歸）與 `sheep_growth_lgbm_q10/q50/q90.joblib`（分位數模型）。
    - 以 `sheep_growth_lgbm_metadata.json` 定義特徵、類別欄位、訓練統計與 `AgeDays` 限制。
    - 若缺模型或超出訓練範圍，退回 sklearn 線性迴歸備援。
    - 產出 `daily_forecasts` 與 `daily_confidence_band`，供 `/prediction/chart-data` 前端繪圖。

### 3.6 Excel 資料管線
- `_extract_excel_summary`：截取前 5 筆預覽，供 AI 判斷欄位用途。
- `_validate_ai_mapping`：比對 AI JSON 結果與實際欄位，回傳 warnings/errors/metadata。
- `process_import`：接受「預設模式」或「自訂映射」，建立/更新 `Sheep`、`SheepEvent`、`SheepHistoricalData`。
- `export_excel`：將羊隻、事件、歷史與聊天紀錄分工作表輸出（無資料時提供 `Empty_Export` 說明頁）。

### 3.7 快取與鎖機制
- `cache.CACHE_TTL_SECONDS = 90`，透過 Redis `setex` 以 `dashboard-cache:<user>` 儲存儀表板統計。
- `get_user_lock` 改採 Redis 分佈式 Lock，避免跨實例同時重算。
- `clear_dashboard_cache(user_id)` 供 API/管理員強制刷新。

### 3.8 背景任務
- `tasks.py` 提供共用輕量佇列存取與 `example_generate_dashboard_snapshot` 示範任務。
- `enqueue_example_task` 會推送至 Redis-backed Queue，Worker 於 `backend/run_worker.py` 啟動。
- 可擴充為報表產生、通知寄送等長時間流程。

### 3.9 日誌、錯誤與腳本
- 日誌輸出預設在 `/app/logs/app.log`（Docker volume 對應 `backend/logs/`）。
- `error_handlers.py` 將常見例外（驗證錯誤、401/403/404/500）標準化為 JSON。
- 手動測試腳本：`debug_test.py`、`manual_functional_test.py`、`manual_test.py`、`auth_debug.py`。

---

## 4. 前端應用（Vue 3）詳解

### 4.1 技術棧
- Vue.js 3.5（Composition API）
- Vue Router 4（巢狀路由 + 導航守衛）
- Pinia 3（狀態跨頁共享，localStorage 永續化）
- Element Plus UI 2.10 + ECharts 5.5 + Chart.js 4
- Axios 1.11 API client，支援 Blob 下載、401 自動登出
- Vite 7 建置 + Vitest 3 測試（多配置切換）

### 4.2 路由與頁面

| 路徑 | 名稱 | 元件 | 說明 |
|------|------|------|------|
| `/login` | `LoginView` | 登入頁 | 未登入訪客入口 |
| `/` (巢狀) | `AppLayout` | `AppLayout.vue` | 登入後主框架（含側邊欄） |
| `/dashboard` | `DashboardView` | 儀表板 | 圖表、提醒、快取資料 |
| `/consultation` | `ConsultationView` | 營養建議表單 → Gemini |
| `/chat` | `ChatView` | AI 即時聊天（含圖片） |
| `/flock` | `SheepListView` | 羊群列表、篩選、CRUD |
| `/data-management` | `DataManagementView` | Excel 匯入匯出、AI 映射設定 |
| `/prediction` | `PredictionView` | 預測圖表、信賴區間 |
| `/traceability` | `TraceabilityManagementView` | 產品批次/流程/羊隻管理 |
| `/trace/:batchNumber` | `TraceabilityPublicView` | 公開故事頁（免登入） |
| `/settings` | `SettingsView` | API key 設定、事件選項維護 |

導航守衛在 `router/index.js` 動態載入 `auth` store，確保避免循環依賴並支援頁面刷新後的 localStorage 還原。

### 4.3 Pinia Store 概觀

| Store | 職責 | 亮點 |
|-------|------|------|
| `auth` | 使用者會話、登入/註冊/登出、localStorage 永續化 | 401 interceptor 自動登出、避免重複登出請求 |
| `sheep` | 羊隻清單、排序、快取與篩選 | `fetchSheepList` 避免重複請求、提供篩選選項 |
| `chat` | AI 聊天訊息狀態與 session | 控制滾動、載入更多訊息 |
| `consultation` | AI 營養建議表單資料與 API key | 自動補齊羊隻背景欄位 |
| `settings` | 事件類型/描述與 API key | 與 Dashboard 事件選項 API 同步 |

### 4.4 API 客戶端行為
- Base URL 指向相對路徑 `/`，以便與 Flask 併部署。
- `withCredentials: true` 保留 Session Cookie。
- Response interceptor：Blob 直接回傳 Response，其餘回傳 `data`；401 時動態載入 `auth` store 並呼叫 `logout()`。
- `withErrorHandling` 封裝錯誤，並可搭配前端 `handleApiError` 統一 toast。
- 支援 FormData（圖片上傳、Excel 上傳、批次匯入）與自訂 Header（`X-Api-Key`）。

### 4.5 UI/UX
- Element Plus 表格/表單/Dialog 統一風格。
- Chart.js + ECharts 呈現預測趨勢、儀表板指標。
- 響應式：採彈性網格，並於 Traceability 公開頁支援手機私人分享。
- 動態載入 (`defineAsyncComponent`) 降低首屏載入時間。

### 4.6 測試與品質工具
- Vitest 多重設定（`vitest.config.*`）對應不同 CI/本地需求。
- `tests/mocks.js`、`tests/setup.js` 提供 Axios/DOM Mock。
- 覆蓋率輸出於 `frontend/coverage/` 與 `docs/frontend/coverage/`。

---

## 5. AI 與機器學習能力

### 5.1 LightGBM 模型
- 模型檔案：
    - `sheep_growth_lgbm.joblib`（主模型）
    - `sheep_growth_lgbm_q10.joblib` / `q50` / `q90`（信賴區間）
- 依 `sheep_growth_lgbm_metadata.json` 定義：
    - 特徵順序：`AgeDays`, `BirWei`, `Sex`, `Breed`, `LittleSize`, `Lactation`, `DaysInMilk`, `ReproStatus`, `Seasonality`
    - 分類特徵：`Sex`, `Breed`, `ReproStatus`
    - 訓練資料：5,200 筆，`AgeDays` 建議 ≤365 天（但上限 3720）
    - CV 表現：MAE ≈ 2.62、RMSE ≈ 4.64
- 預測流程：
 1. 檢查羊隻是否具備出生日期與日齡。
 2. 準備特徵 → LightGBM 推論。
 3. 若缺 Quantile 模型或資料不足，回退線性迴歸。
 4. 回傳每日體重預估 + 區間，並可搭配 Gemini 生成 ESG 文案。

### 5.2 Gemini 整合
- 模型：`gemini-flash-latest`
- `AgentRecommendationModel`、`AgentChatModel` 驗證輸入數據。
- 自訂安全設定：所有 Harm 類別 threshold 設 `BLOCK_NONE`，確保農務用語不被誤判。
- 圖片支援：Base64 內嵌於 `generateContent` payload。
- 超時：180s，錯誤時回傳具體訊息，並在伺服器端記錄。
- ESG 區塊：系統指示必須提供環境影響（甲烷估算）、低碳飼料建議、動物福利改善。

### 5.3 ESG 與永續
- ORM 模型新增 `manure_management`, `primary_forage_type`, `welfare_score` 等欄位。
- Dashboard 與 AI 輸出均可引用 ESG 欄位，前端卡片顯示可追蹤指標。

---

## 6. 開發與執行環境建置

### 6.1 本機開發（建議 Python 3.11、Node 20）
1. 複製 `.env.example` → `.env`，調整必要變數。
2. 後端：
     ```bash
     cd backend
     python -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     FLASK_ENV=development CORS_ORIGINS=http://localhost:5173 python run.py
     ```
3. 前端：
     ```bash
     cd frontend
     npm install
     npm run dev
     ```
4. 瀏覽：`http://localhost:5173`，Swagger：`http://localhost:5001/docs`。

### 6.2 Docker Compose
```bash
Copy-Item .env.example .env   # 或 cp .env.example .env
docker compose up --build -d
docker compose ps
```
- 服務：前端 `:3000→80`、後端 `:5001`、Postgres `:5432`。
- 初次啟動後建議執行 `docker compose exec backend flask db upgrade`。

### 6.3 Codespaces / GitHub 雲端
- `start_codespaces.sh`：初始化 Python venv、安裝前端依賴、啟動後端。
- `deploy-codespaces.sh`：自動建構 Docker Compose，適合作為 demo/測試環境。

---

## 7. 環境變數與組態

| 變數 | 說明 | 必填 | 預設/備註 |
|------|------|------|-----------|
| `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME` | 生產用資料庫連線 | ✅ (生產) | 開發可改用 SQLite |
| `SECRET_KEY` | Flask Session 秘鑰 | ✅ | 請換強密碼 |
| `FLASK_ENV` | `development` / `production` | ✅ | Docker 預設 `production` |
| `CORS_ORIGINS` | 允許前端來源列表 | ✅ | 多域以逗號分隔 |
| `GOOGLE_API_KEY` | Gemini API 金鑰 | ⚠️ | 可於前端設定頁儲存個人 key |
| `WAITRESS_THREADS`, `WAITRESS_CONNECTION_LIMIT` | Waitress 調校 | 選填 | `.env.example` 提供建議值 |
| `LOG_LEVEL`, `LOG_FILE` | 日誌輸出 | 選填 | 預設 INFO, `/app/logs/app.log` |
| `POSTGRES_*` | Docker Compose Postgres 帳密 | ⚠️ | 預設 `goat_user/goat_password`，建議調整 |
| `REDIS_URL` | 若導入外部快取 | 選填 | 目前未使用 |
| `SENTRY_DSN` | 外部監控 | 選填 | 須自行設定 |

> 📌 測試環境建議暫時移除 `.env` 的 PostgreSQL 變數以強制使用 SQLite（`backend/tests/conftest.py` 會自動處理）。

---

## 8. 資料導入與匯出流程

### 8.1 匯出 (Export)
1. 前端 `DataManagementView` 呼叫 `/api/data/export_excel`。
2. 後端查詢 `Sheep`, `SheepEvent`, `SheepHistoricalData`, `ChatHistory`。
3. 依資料動態建立工作表，空資料則提供 `Empty_Export` 說明表。

### 8.2 匯入 (Import)
1. 使用者上傳 Excel → `/api/data/analyze_excel` 回傳欄位預覽。
2. （可選）`/api/data/ai_import_mapping`：
     - 以 `_extract_excel_summary` 取樣 → Gemini 產生 JSON 映射建議。
     - `_validate_ai_mapping` 檢查用途/必要欄位 → 回傳 warnings。
3. `/api/data/process_import`：
     - 預設模式：固定欄位對應。
     - 自訂模式：依映射 JSON 對應到 ORM 模型，支援批次 upsert。
4. 匯入後會回傳列數統計、錯誤清單。

### 8.3 欄位用途 (AI Sheet Purposes)
- `basic_info`、`kidding_record`、`mating_record`、`weight_record`、`milk_yield_record`、`milk_analysis_record`、`breed_mapping`、`sex_mapping`、`ignore`。
- 必要欄位參考 `REQUIRED_COLUMNS_BY_PURPOSE`，缺失時會在 warnings 呈現。

---

## 9. 測試與品質保證

### 9.1 後端 (pytest)
- 定位：`backend/tests/`
- 208+ 測試涵蓋 Auth、Sheep、Data、Dashboard、Prediction、Traceability、AI。
- 常用指令：
    ```bash
    cd backend
    pytest
    pytest tests/test_traceability_api.py -v
    pytest --cov=app --cov-report=term-missing --cov-report=html
    ```
- 覆蓋率：總體約 85%，`app/api/dashboard.py` 仍可補強。
- HTML 報告：`docs/backend/coverage/index.html`。

### 9.2 前端 (Vitest)
- 測試檔：`frontend/src/tests/`、`frontend/src/test/`、`frontend/tests/`
- 指令：
    ```bash
    cd frontend
    npm run test -- --run
    npm run test:coverage -- --run
    npx vitest run traceability
    ```
- 覆蓋率（2025-10-05）：Statements 81.73%、Branches 85.92%、Functions 66.43%、Lines 81.73%。
- HTML 報告：`docs/frontend/coverage/index.html`。

### 9.3 靜態/其他檢查
- ESLint：`npm run lint` / `npm run lint:fix`
- Alembic：`flask db check`（確認遷移狀態）
- 手動腳本：`manual_functional_test.py` 檢查主要流程。

---

## 10. 部署與維運指引

### 10.1 常用命令
```bash
docker compose up --build -d       # 建構並啟動
docker compose ps                  # 檢視服務狀態
docker compose logs -f backend     # 追蹤後端日誌
docker compose restart backend     # 滾動重啟單一服務
docker compose down                # 停止並移除資源
```

### 10.2 健康檢查與監控
- 後端：`/api/auth/status` 回傳 `{"authenticated": false}` 即為健康。
- 前端：Nginx 健康檢查 `GET /`。
- Postgres：`pg_isready -U goat_user -d goat_nutrition_db`。

### 10.3 資料庫遷移
```bash
flask db migrate -m "message"
flask db upgrade
flask db history
```
- Docker 環境可用：`docker compose exec backend flask db upgrade`。

### 10.4 備份與還原
```bash
docker compose exec db pg_dump -U goat_user goat_nutrition_db > backup.sql
cat backup.sql | docker compose exec -T db psql -U goat_user goat_nutrition_db
docker compose cp backend:/app/logs ./logs-backup
```

### 10.5 部署後驗證清單
- [ ] `/api/auth/status` 200。
- [ ] 前端登入流程正常（Cookie 寫入）。
- [ ] `/api/data/export_excel` 能下載。
- [ ] `/api/traceability/batches` 與公開端回傳合理資料或 404。
- [ ] `/api/agent/tip`（無 API key 時應回傳錯誤訊息）。
- [ ] 前端 Traceability 公開頁可直接存取。

---

## 11. 安全性與隱私保護
- **身份驗證**：Flask-Login Session + 密碼雜湊（Werkzeug）。
- **授權**：API 須登入，除 `auth`、`traceability/public` 端點外。
- **輸入驗證**：Pydantic、SQLAlchemy ORM 預防注入。
- **錯誤處理**：`error_handlers.py` 過濾堆疊訊息，僅輸出必要資訊。
- **圖片上傳**：限制 MIME、大小（10MB），AI 端僅編碼後送出。
- **API Key**：不儲存於後端資料庫，交由前端使用者設定；缺失時回傳 401/提示。
- **CORS**：支援自訂來源，Docker 預設覆蓋 Codespaces / 本機。

---

## 12. 文件、資產與腳本索引

| 類型 | 路徑 | 摘要 |
|------|------|------|
| 快速開始 | `docs/QuickStart.md` | PowerShell 示範指令、Docker、API 試跑 |
| 開發指南 | `docs/Development.md` | 測試建議、Traceability 模組說明、覆蓋率數據 |
| 部署指南 | `docs/Deployment.md` | Docker 架構、維運命令、備份流程 |
| API 索引 | `docs/API.md` | 端點授權、參數、範例（若更新請同步 Swagger） |
| FAQ | `docs/FAQ.md` | 常見錯誤與排錯建議 |
| Backend Guide | `backend/docs/README.md` | 模型詳解、測試、遷移、版本記錄 |
| Frontend Guide | `frontend/docs/README.md` | 路由、Store、測試策略 |
| 架構圖 | `docs/assets/backend_dependency_graph.svg`、`docs/assets/deployment.png` | 程式依賴、部署拓撲 |
| 覆蓋率 | `docs/backend/coverage/`、`docs/frontend/coverage/` | HTML 報告入口 |
| 腳本 | `deploy.sh`, `deploy-codespaces.sh`, `generate_architecture.py` | 部署與架構視覺化 |

---

## 13. 常見排錯與最佳化建議
- **pytest 嘗試連線 PostgreSQL**：臨時將 `.env` 改名或刪除 PostgreSQL 變數（`tests/conftest.py` 會退回 SQLite）。
- **Gemini API 錯誤**：確認 `GOOGLE_API_KEY` 有效且未達流量上限；`utils.call_gemini_api` 會回傳 `error` 欄位。
- **Excel AI 映射不準**：檢視 API 回傳的 `warnings`，必要時改採自訂映射模式。
- **前端 401 無限循環**：Axios interceptor 已避免登出/登入請求觸發自動登出，若仍重現請檢查 API 伺服器 Session。
- **Traceability 公開頁 404**：確認批次 `is_public` 設為 `true`，且 URL `batch_number` 正確。
- **Dashboard 數據未更新**：呼叫 `/api/dashboard/clear-cache`（若有提供）或於後端使用 `clear_dashboard_cache(user_id)`；確認 Redis 服務運作正常。
- **背景任務未執行**：確認有啟動 `python run_worker.py`，並檢查 Redis 內是否存在對應佇列。
- **Docker 初次啟動後端失敗**：檢查 `GOOGLE_API_KEY`、`POSTGRES_*` 是否正確；查看 `docker compose logs backend`。

---

## 14. 版本沿革與路線圖

### 已版本亮點
- **v2.1.0 (2025-10-05)**
    - 新增完整產銷履歷 API + 公開分享機制。
    - 擴充 ESG 欄位與故事生成。
    - 增強測試覆蓋率（Traceability、Dashboard）。
- **v2.0.0 (2025-07-30)**
    - Pydantic V2 遷移、測試覆蓋率達 94%。
    - 整合 Gemini AI、增強錯誤處理。
- **v1.5.0**
    - Excel 匯入匯出、Docker 化部署、AI 對話初版。

### 建議 Roadmap
- [ ] 提升 Dashboard Blueprint 測試覆蓋率 ≥80%。
- [ ] 擴充 `SettingsView.vue`、`SheepListView.vue` 的互動測試。
- [x] 導入 Redis/外部快取取代記憶體快取（多機部署）。
- [x] 建立輕量背景任務佇列基礎（示範任務 + Worker）。
- [ ] 將 AI 金鑰安全儲存在伺服器端密鑰管家（可選）。
- [ ] 建立 CI Pipeline（GitHub Actions）自動執行 pytest/vitest + Docker build。

---

> 📣 本文件旨在作為專案的「單一事實來源 (Single Source of Truth)」，更新功能或架構時請同步更新此處並附註日期，確保跨團隊皆能快速理解系統全貌。
