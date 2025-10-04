docker compose ps
docker compose logs -f backend
docker compose down
docker compose restart backend
# 部署指南

> 建議使用 Docker Compose：三個容器涵蓋前端 Nginx、後端 Flask、PostgreSQL。

![部署架構示意](./assets/deployment.png)

## 事前準備

| 項目 | 建議版本 |
|------|----------|
| Docker Desktop / Engine | 24.x 以上 |
| Docker Compose | v2 |
| 伺服器資源 | 至少 2 vCPU / 4 GB RAM |

## 1. 設定環境變數

```powershell
Copy-Item .env.example .env
notepad .env
```

請確認以下關鍵設定：

| 變數 | 說明 |
|------|------|
| `POSTGRES_*` | 資料庫帳號/密碼/主機/埠口/資料庫名 |
| `SECRET_KEY` | Flask Session 使用的密鑰 |
| `CORS_ORIGINS` | 允許呼叫 API 的前端來源清單 |
| `GOOGLE_API_KEY` | Google Gemini API 金鑰（若使用 AI 功能） |

## 2. 佈署與檢查

```powershell
docker compose up --build -d
docker compose ps
```

啟動後可透過以下連結驗證：

| 項目 | URL | 正常回應 |
|------|-----|-----------|
| 前端 | http://localhost:3000 | Vue SPA |
| 後端健康檢查 | http://localhost:5001/api/auth/status | `{ "authenticated": false }` |
| Swagger | http://localhost:5001/docs | Swagger UI |
| 公開履歷 API | http://localhost:5001/api/traceability/public/BATCH-001 | 404 或批次故事（視資料而定） |
| PostgreSQL | `docker compose logs db` | `database system is ready to accept connections` |

## 3. 資料庫版本控制

容器啟動時會載入 `backend/migrations/` 內容。若需手動執行 Alembic 遷移：

```powershell
docker compose exec backend flask db upgrade
```

若第一次使用 PostgreSQL，可將既有 SQLite 資料轉換為 SQL 匯出後再匯入。

## 4. 常見維運命令

```powershell
# 查看特定服務日誌
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# 重啟單一服務
docker compose restart backend

# 套用新映像並重啟
docker compose up --build -d

# 停止並移除容器、網路、匿名 volume
docker compose down
```

## 5. 版本更新流程

1. `git pull` 或更新程式碼。
2. （必要時）更新 `.env` 或 `docker-compose.yml`。
3. `docker compose up --build -d` 重建映像。
4. `docker compose exec backend flask db upgrade` 檢查資料庫遷移。
5. 透過 `/api/auth/status` 與前端頁面確認服務可用。

## 6. 備份與還原

```powershell
# PostgreSQL 備份
docker compose exec db pg_dump -U $env:POSTGRES_USER $env:POSTGRES_DB > backup.sql

# PostgreSQL 還原
type backup.sql | docker compose exec -T db psql -U $env:POSTGRES_USER $env:POSTGRES_DB

# 後端日誌
docker compose cp backend:/app/logs ./logs-backup
```

## 7. 佈署後檢查清單

- [ ] `/api/auth/status` 回傳 200。
- [ ] 前端登入流程順利（Cookie 寫入成功）。
- [ ] `/api/data/export_excel` 能匯出檔案。
- [ ] `/api/traceability/batches` 與 `/api/traceability/public/<批次號>` 依權限回傳正確資料。
- [ ] `/api/agent/tip` 提供提示（若無 API key 會回傳錯誤，為正常行為）。
- [ ] `docs/backend/coverage/index.html` 與 `docs/frontend/coverage/index.html` 覆蓋率報告已更新。

完成上述步驟後即可交付或進行監控布建。更多開發細節請參閱 [Development](./Development.md)。
