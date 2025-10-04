docker-compose exec db pg_dump -U goat_user goat_nutrition_db > backup.sql
docker-compose exec -T db psql -U goat_user goat_nutrition_db < backup.sql
grep "2025-08-07" logs/app.log
db.Index('idx_sheep_user_ear', Sheep.user_id, Sheep.EarNum)
db.Index('idx_events_date', SheepEvent.event_date)
docker-compose exec db pg_dump -U goat_user goat_nutrition_db > backup.sql
git pull origin main
docker-compose down
docker-compose up --build -d
docker-compose ps
docker-compose logs backend
def endpoint_function():
def not_found(error):
def internal_error(error):
# 領頭羊博士 - 後端指南

> Flask 3 / SQLAlchemy 2 後端服務，支援 AI 餘裕、Excel 導入導出與生長預測。

## 1. 快速概覽

- **框架**：Flask 3、SQLAlchemy 2、Flask-Login、Pydantic 2。
- **資料庫**：生產建議 PostgreSQL，開發預設 SQLite (`instance/app.db`)。
- **模組**：Auth、Sheep、Data Management、Dashboard、Agent、Prediction、Traceability。
- **AI 整合**：Google Gemini (`X-Api-Key` 標頭)。
- **部署**：Docker Compose（Waitress + Gunicorn），詳細見 `docs/Deployment.md`。

## 2. 目錄結構

```
backend/
├── app/
│   ├── __init__.py       # create_app、CORS、藍圖註冊
│   ├── models.py         # User、Sheep、事件、歷史與 ESG 欄位
│   ├── schemas.py        # Pydantic 驗證模型
│   ├── utils.py          # Gemini 呼叫、羊隻上下文
│   ├── cache.py          # 儀表板記憶體快取 (threading.Lock)
│   └── api/
│       ├── auth.py
│       ├── sheep.py
│       ├── data_management.py
│       ├── dashboard.py
│       ├── agent.py
│       ├── prediction.py
│       └── traceability.py    # 產品批次 / 加工流程 / 公開履歷
├── tests/                # Pytest（含 Gemini mock Fixtures）
├── migrations/           # Alembic 遷移腳本
├── docs/                 # （本檔）
├── logs/                 # `app.log`
├── docker-entrypoint.sh
├── Dockerfile
└── run.py
```

## 3. 主要元件

### 認證 (`app/api/auth.py`)
- Cookie Session + Flask-Login。
- 註冊時會建立預設事件類型與描述。
- `/api/auth/health` 供 Docker 健康檢查。

### 羊隻管理 (`app/api/sheep.py`)
- CRUD、事件、歷史資料均以 `current_user.id` 隔離。
- 透過 Pydantic 驗證資料並自動記錄體重/奶量變化。

### Data Management (`app/api/data_management.py`)
- Pandas + openpyxl 匯入匯出。
- 內建 0009-0013 系列工作表映射，亦支援自訂 `mapping_config`。
- 會自動補齊耳號映射、產生匯入報告。

### 儀表板 (`app/api/dashboard.py`)
- 提供提醒、停藥、健康警示、ESG 指標。
- 透過 `app/cache.py` 以 `user_id` 為 key 記憶體快取 90 秒。

### AI 代理 (`app/api/agent.py`)
- 每日提示、營養建議、圖片/文字聊天。
- 每次呼叫均需 `X-Api-Key`；若為圖片請以 `multipart/form-data` 上傳。
- 聊天紀錄儲存於 `ChatHistory`。

### 生長預測 (`app/api/prediction.py`)
- 線性迴歸 (sklearn) + LLM 說明。
- 先做資料品質檢查（數量、時間跨度、異常值）。
- 回傳預測體重、平均日增重、參考範圍、AI Markdown 分析。

### 產品產銷履歷 (`app/api/traceability.py`)
- 為每位使用者提供批次管理、加工步驟與羊隻貢獻關聯。
- `ProductBatch` / `ProcessingStep` / `BatchSheepAssociation` 模型支援多對多串接與排序。
- 登入端 `/api/traceability/batches` 系列提供 CRUD 與羊隻維護；公開端 `/api/traceability/public/<批次號>` 提供脫敏後的故事資料。
- 公開回應會整理加工時間軸、羊隻事件與 ESG 亮點，並移除內部 ID。

## 4. 組態

| 類別 | 變數 | 說明 |
|------|------|------|
| Flask | `SECRET_KEY` | Session 密鑰 |
| CORS | `CORS_ORIGINS` | 允許的前端來源（逗號分隔） |
| DB | `POSTGRES_*` | 提供時使用 PostgreSQL，否則採 SQLite |
| AI | `GOOGLE_API_KEY` | 若未設定，AI 相關端點會回傳提示訊息 |

開發模式可直接執行 `python run.py`，若 `.env` 不存在將自動建立 SQLite。

## 5. 開發提示

- `create_app()` 會根據 `.env` 或 `DOTENV_PATH` 載入設定。
- `debug_test.py` 於模組層建立 app，若保留 `.env` 內的 PostgreSQL 設定會在 Pytest 時造成連線錯誤；測試前請暫時改名 `.env`。
- 儀表板快取：若測試需要即時資料，可呼叫 `from app.cache import clear_dashboard_cache`。
- 日誌：`logs/app.log`，部署時建議設定輪轉。

## 6. 測試

```powershell
# 建議流程（避免讀取 .env）
Rename-Item ..\..\.env ..\..\.env.bak
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest
C:/Users/7220s/AppData/Local/Programs/Python/Python311/python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=html
Rename-Item ..\..\.env.bak ..\..\.env
```

- 測試內容涵蓋 Auth、Sheep、Data Management、Dashboard、Agent、Prediction 與 Traceability。
- `tests/test_traceability_api.py` 驗證批次 CRUD、步驟管理、羊隻關聯更新與公開端權限。
- 覆蓋率總覽於 `../../docs/backend/coverage/index.html`，`app/api/dashboard.py` 仍為主要補強目標。
- HTML 報告：`../../docs/backend/coverage/index.html`。

Fixtures 亮點（`tests/conftest.py`）：
- 自動清除 Postgres 相關環境變數，強制使用臨時 SQLite。
- 提供 `authenticated_client`（帳號 `testuser/testpass`）。
- `mock_gemini_api` 將 LLM 呼叫替換為固定回傳值。

## 7. 常用指令

```powershell
# 資料庫遷移
flask db migrate -m "add new field"
flask db upgrade

# 快速手動測試
python manual_functional_test.py
python manual_test.py

# 產出匯出範例
python create_test_data.py
```

## 8. 故障排除

| 狀況 | 檢查 |
|------|------|
| Pytest 嘗試連 Postgres | 確認 `.env` 已暫時改名；或設定 `$env:DOTENV_PATH="NON_EXISTENT_.env"` |
| AI 端點回傳缺少金鑰 | 確認請求標頭 `X-Api-Key` 或 `.env` 內的 `GOOGLE_API_KEY` |
| 匯入 Excel 失敗 | 檔案副檔名、欄位名稱、日期格式 (`YYYY-MM-DD`) |
| 儀表板沒有更新 | 呼叫 `clear_dashboard_cache(user_id)` 或等待 90 秒 |

## 9. 授權與文件

- 授權：MIT（見專案根目錄 `LICENSE`）。
- 更新日期：2025-10-05。
- 相關文件：
  - [docs/README.md](../../docs/README.md) — 全域說明
  - [docs/QuickStart.md](../../docs/QuickStart.md) — 啟動流程
  - [docs/API.md](../../docs/API.md) — 端點索引

---

需要增加新模組或欄位時，請同步更新對應的 Pydantic Schema、Pytest 與文件，並重新產出覆蓋率報告。
