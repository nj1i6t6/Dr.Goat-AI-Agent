# 領頭羊博士技術總覽

> 智慧化山羊營養管理系統，整合 Flask 後端、Vue 3 前端、AI 輔助決策與資料導入導出流程。

## 系統重點

- **資料握在手上**：羊隻基本資料、事件、歷史生產數據與 ESG 指標皆可在後端追蹤，前端提供完整的視覺化管理介面。
- **AI 協作**：後端透過 Google Gemini API 提供每日提示、營養建議、圖片強化對話；前端提供聊天體驗與 API 金鑰管理。
- **資料匯入匯出**：支援表單範本分析、批次導入、自動欄位對應與匯出多張工作表。
- **預測模型**：以 sklearn 線性回歸計算羊隻生長趨勢並結合 LLM 提供 ESG 觀點的建議。
- **完整測試**：後端 208 項 Pytest、前端 281 項 Vitest 皆通過，對應的 HTML 覆蓋率報告已收納在 `docs/backend/coverage/` 與 `docs/frontend/coverage/`。

## 架構一覽

```mermaid
graph LR
    subgraph Frontend [Vue 3 SPA]
        Router
        Pinia
        Components
        ApiClient
    end

    subgraph Backend [Flask App]
        Auth[Auth Blueprint]
        Sheep[Sheep Blueprint]
        Data[Data Blueprint]
        Agent[Agent Blueprint]
        Dashboard[Dashboard Blueprint]
        Prediction[Prediction Blueprint]
        Cache[(In-memory Cache)]
    end

    subgraph Storage
        Postgres[(PostgreSQL \n(Production))]
        SQLite[(SQLite \n(Dev/Test))]
    end

    Router -->|REST/JSON| ApiClient
    ApiClient -->|/api/*| Auth
    ApiClient --> Sheep
    ApiClient --> Data
    ApiClient --> Agent
    ApiClient --> Dashboard
    ApiClient --> Prediction

    Sheep --> Postgres
    Data --> Postgres
    Dashboard --> Cache
    Prediction --> Postgres
    Auth --> Postgres
    Agent --> Postgres

    Prediction -->|LLM prompt| Gemini[(Google Gemini)]
```

## 文件地圖

| 範疇 | 文件 | 說明 |
|------|------|------|
| 快速啟動 | [QuickStart](./QuickStart.md) | 本機開發、Docker、基本 API 操作 |
| 部署 | [Deployment](./Deployment.md) | Docker Compose、健康檢查、維運指令 |
| 開發 | [Development](./Development.md) | 開發環境、常見指令、測試策略 |
| API | [API 索引](./API.md) | 分模組端點與授權需求 |
| FAQ | [FAQ](./FAQ.md) | 常見問題與排錯建議 |
| 後端 | [Backend Guide](../backend/docs/README.md) | 模型、快取、測試、故障排除 |
| 前端 | [Frontend Guide](../frontend/docs/README.md) | 視圖、狀態管理、測試、效能 |

> 圖片與架構圖集中於 `docs/assets/`，覆蓋率 HTML 報告集中於 `docs/backend/coverage/` 與 `docs/frontend/coverage/`。

## 最新測試結果（2025-09-25）

| 範疇 | 指令 | 結果摘要 |
|------|------|-----------|
| 後端單元與整合測試 | `C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest` | 208 測試全通過，19 則 SQLAlchemy 2.x LegacyAPI 警告。
| 後端覆蓋率 | `... -m pytest --cov=app --cov-report=html --cov-report=term-missing` | 總覆蓋率 **85%**；`app/api/dashboard.py` 57% 為主要補強對象。
| 前端測試 | `npm run test -- --run` | 32 個測試檔、281 測試全通過。
| 前端覆蓋率 | `npm run test:coverage -- --run` | Statements 81.73%、Branches 85.92%、Functions 66.43%、Lines 81.73%。

📍 覆蓋率 HTML 報告入口：
- 後端：[`docs/backend/coverage/index.html`](./backend/coverage/index.html)
- 前端：[`docs/frontend/coverage/index.html`](./frontend/coverage/index.html)

## 目錄結構速查

```
goat-nutrition-app/
├─ backend/          # Flask API、模型、遷移、測試
├─ frontend/         # Vue 3 SPA、Pinia、Vitest
├─ docs/             # 目前文件、資產、覆蓋率報告
│  ├─ assets/        # 架構圖、流程圖
│  ├─ backend/       # 後端覆蓋率 HTML
│  └─ frontend/      # 前端覆蓋率 HTML
└─ docker-compose.yml
```

## 快速開始

1. **準備環境**：依照 [QuickStart](./QuickStart.md) 建立 venv 與 npm 套件。
2. **後端**：啟動 `python run.py`（預設使用 SQLite `instance/app.db`）。
3. **前端**：執行 `npm run dev`，瀏覽 `http://localhost:5173`。
4. **Swagger**：`http://localhost:5001/docs` 檢視 API 規格。

## 進階主題

- **部署管線**：Docker Compose 三容器，詳細見 [Deployment](./Deployment.md)。
- **資料導入導出**：`/api/data` 模組，完整流程記於後端指南。
- **AI 與預測**：`/api/agent`、`/api/prediction` 模組，需提供 `GOOGLE_API_KEY`。
- **儀表板快取**：`app/cache.py` 記憶體快取 90 秒，可呼叫 `clear_dashboard_cache` 強制刷新。

## 下一步建議

- 增補 `app/api/dashboard.py` 測試覆蓋率（目前 57%）。
- 補齊前端 `SettingsView.vue`、`SheepListView.vue` 行為測試，提升 Function 覆蓋率。
- 如使用 PostgreSQL，本機執行測試前建議暫時改用 SQLite（見 [Development](./Development.md) 中的測試章節）。

---

若需編輯或擴充文件，請沿用本文件中的結構與語氣，確保資訊集中於 `docs/` 目錄。
