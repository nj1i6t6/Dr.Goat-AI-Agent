docker compose ps
# 快速開始

> 以下指令以 **Windows PowerShell** 為例；若使用 macOS/Linux，請將反斜線換為斜線並改用 `python3`。

## 1. 準備環境

```powershell
# 專案根目錄
Copy-Item .env.example .env

# 後端虛擬環境
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 前端相依
cd ..\frontend
npm install
```

## 2. 啟動服務

後端（預設 SQLite，啟動於 http://localhost:5001 ）

```powershell
cd backend
$env:FLASK_ENV="development"
$env:CORS_ORIGINS="http://localhost:5173"
python run.py
```

前端（Vite 開發伺服器，啟動於 http://localhost:5173 ）

```powershell
cd frontend
npm run dev
```

啟動完成後可立即造訪：

| 項目 | URL |
|------|-----|
| 前端 SPA | http://localhost:5173 |
| 後端 API | http://localhost:5001 |
| Swagger UI | http://localhost:5001/docs |
| 健康檢查 | http://localhost:5001/api/auth/status |

## 3. Docker Compose（整合部署）

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

服務連接埠：前端 `3000 → 80`、後端 `5001`、PostgreSQL `5432`。詳細參考 [Deployment](./Deployment.md)。

## 4. 試跑幾個 API

```powershell
# 註冊 + 登入
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/auth/register" -ContentType "application/json" -Body '{"username":"demo","password":"demo123"}' -SessionVariable s
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/auth/login" -ContentType "application/json" -Body '{"username":"demo","password":"demo123"}' -WebSession $s

# 建立羊隻
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/sheep/" -ContentType "application/json" -Body '{"EarNum":"A001","Breed":"台灣黑山羊","Sex":"母","BirthDate":"2024-01-15"}' -WebSession $s

# 建立產品批次並公開
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/traceability/batches" -ContentType "application/json" -Body '{"batch_number":"BATCH-001","product_name":"鮮羊乳 946ml","production_date":"2025-10-04","is_public":true}' -WebSession $s

# 導向公開履歷頁（瀏覽器）
start http://localhost:5173/trace/BATCH-001

# 取得儀表板摘要
Invoke-RestMethod -Method Get -Uri "http://localhost:5001/api/dashboard/data" -WebSession $s | ConvertTo-Json -Depth 4
```

## 5. 執行測試

### 後端

`backend/debug_test.py` 在模組層會讀取 `.env`，若環境含 PostgreSQL 設定會導致測試啟動 PostgreSQL 連線。請先暫存 `.env`：

```powershell
cd backend
Rename-Item ..\..\.env ..\..\.env.bak
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=html
Rename-Item ..\..\.env.bak ..\..\.env
```

產出的覆蓋率 HTML 位於 `docs/backend/coverage/index.html`。

### 前端

Vitest 預設為互動模式，建議以 `--run` 參數一次性執行：

```powershell
cd frontend
npm run test -- --run
npm run test:coverage -- --run
npx vitest run traceability
```

HTML 覆蓋率報告位於 `docs/frontend/coverage/index.html`。

---

完成以上步驟即可開始瀏覽系統、調整 `.env` 連線到 PostgreSQL，或繼續閱讀 [Development](./Development.md) 了解更多開發細節。
