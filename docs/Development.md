# 開發指南

## 開發環境

| 範疇 | 推薦版本 |
|------|-----------|
| Python | 3.11.x |
| Node.js | 20.x |
| npm | 10.x |
| PostgreSQL（選用） | 14+ |
| Redis | 5+ |

### 建立虛擬環境（後端）

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 安裝前端依賴

```powershell
cd frontend
npm install
```

## 後端開發流程

1. 啟動 Flask：
	```powershell
        cd backend
        $env:REDIS_PASSWORD="simon7220"
        $env:FLASK_ENV="development"
        $env:CORS_ORIGINS="http://localhost:5173"
        python run.py
        ```
2. 預設會使用 `instance/app.db`（SQLite）。若需 PostgreSQL，請於 `.env` 中填入 `POSTGRES_*` 後重新啟動。
3. Redis 預設連線 `localhost:6379`，可使用 `docker run --rm -p 6379:6379 redis:7.2-alpine redis-server --requirepass simon7220` 快速啟動。
4. Swagger 文件位於 `http://localhost:5001/docs`，`/openapi.yaml` 可供匯入 Postman/Insomnia。
5. Redis 快取：`/api/dashboard/data` 使用 `app/cache.py` setex 90 秒快取，可在需要時呼叫 `clear_dashboard_cache(user_id)` 清除。

### 重要模組

- `app/api/agent.py`：AI 提示、營養建議、圖片聊天。
- `app/api/data_management.py`：Excel 匯入匯出與欄位映射。
- `app/api/prediction.py`：線性回歸 + LLM 解釋。
- `app/models.py`：User、Sheep、事件、歷史資料、ESG 欄位。
- `app/api/tasks.py` / `app/tasks.py`：Redis + 輕量佇列背景任務、示範佇列。
- `app/api/traceability.py`：產品批次、加工流程、羊隻關聯與公開履歷查詢 API。
- `app/models.py` 新增 `ProductBatch`、`ProcessingStep`、`BatchSheepAssociation`，提供多對多批次資料模型。
- 前端 `src/views/TraceabilityManagementView.vue` 與 `TraceabilityPublicView.vue` 負責管理介面與公開故事頁。

### 產銷履歷模組速覽

- 管理端 API：`/api/traceability/batches`（CRUD）、`/steps`、`/sheep` 系列端點均需登入。
- 公開端 API：`/api/traceability/public/<batch_number>` 傳回批次故事、加工流程時間軸與羊隻事件摘要。
- 前端管理：登入後的新路由 `/traceability` 可建立批次、綁定羊隻、維護加工流程與一鍵複製公開連結。
- 公開分享：任何裝置可直接造訪 `/trace/<批次號>`，支援透過 ngrok 或正式網域轉為 QR Code 分享。

## 前端開發流程

1. 啟動 Vite：
	```powershell
	cd frontend
	npm run dev
	```
2. 開發伺服器位於 `http://localhost:5173`，預設代理 `/api` 至 `http://127.0.0.1:5001`。
3. Vue Router 採巢狀結構，所有受保護路由掛載於 `AppLayout`，需登入方可進入。
4. Pinia store 位於 `src/stores`，`auth` store 會同步資訊到 `localStorage`。

## 測試與覆蓋率

### 後端

`debug_test.py` 於模組載入時會讀取 `.env`，若含 PostgreSQL 設定會造成測試連線失敗。建議流程：

```powershell
cd backend
Rename-Item ..\..\.env ..\..\.env.bak
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest tests/test_traceability_api.py
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=html
Rename-Item ..\..\.env.bak ..\..\.env
```

- 測試總數：208，全數通過。
- 覆蓋率總覽：85%，主要待補強模組為 `app/api/dashboard.py`（57%）。
- HTML 報告位置：`docs/backend/coverage/index.html`。

fixtures 位於 `backend/tests/conftest.py`，會自動：
- 清除資料庫與 Redis 相關環境變數並強制使用 SQLite。
- 啟用 fakeredis（`USE_FAKE_REDIS_FOR_TESTS=1`），避免外部依賴。
- 建立 `authenticated_client` 與基本帳號 testuser/testpass。
- 模擬 Gemini API 回傳內容。

### 前端

Vitest 若未加 `--run` 會保持監聽模式。

```powershell
cd frontend
npm run test -- traceability  # 互動模式下僅執行產銷履歷 store 測試
npx vitest run traceability   # 以一次性方式跑產銷履歷 store 測試
npm run test -- --run
npm run test:coverage -- --run
```

- 測試檔：32，測試數 281（全部通過）。
- 覆蓋率：Statements 81.73%、Branches 85.92%、Functions 66.43%、Lines 81.73%。
- HTML 報告：`docs/frontend/coverage/index.html`。

建議優先補齊 `SettingsView.vue` 與 `SheepListView.vue` 的互動測試，以提高 Function 覆蓋率。

## 常用指令速查

```powershell
# 後端重新產生資料庫遷移
flask db migrate -m "描述"
flask db upgrade

# 只重跑指定測試
pytest tests/test_prediction_api.py::TestPredictionAPI::test_get_prediction_success

# 啟動背景任務 Worker
python run_worker.py

# 前端分析打包結果
npm run build -- --analyze
```

## 日誌與除錯

- 後端日誌：`backend/logs/app.log`。
- 快速手動測試腳本：`backend/manual_functional_test.py`、`backend/manual_test.py`。
- 前端除錯：建議安裝 Vue DevTools 與 Pinia DevTools。

## 開發建議

- 保持 AI 相關功能時提供有效的 `GOOGLE_API_KEY`，否則 `/api/agent/*` 與 `/api/prediction` 會回傳錯誤描述。
- 若需同時開啟 Docker 與本機服務，請調整 `.env` 中的 CORS 與資料庫設定避免衝突。
- Redis 須與後端使用相同密碼；如需暫時停用可將 `REDIS_URL` 指向測試伺服器或啟用 fakeredis。
- 文件與圖片集中於 `docs/`，更新說明請同步維護該目錄。
