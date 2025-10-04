# 常見問題（FAQ）

## 登入 API 回傳 401？
- 先呼叫 `POST /api/auth/register` 建立帳號（會自動登入）。
- 若已登入仍收到 401，請確認瀏覽器允許 Cookie，或 API 客戶端是否攜帶 Session Cookie。

## 後端測試嘗試連線 PostgreSQL 導致失敗？
`backend/debug_test.py` 會在模組載入時讀取 `.env`。執行測試前請暫時將 `.env` 改名或設定 `$env:DOTENV_PATH="NON_EXISTENT_.env"`，測試完成後再還原。

## AI 相關端點（/api/agent, /api/prediction）回傳缺少 API 金鑰？
- 請在 `POST`/`GET` 請求加上標頭 `X-Api-Key: <你的 Google Gemini API Key>`。
- 或於 `.env`/Docker Compose 設定 `GOOGLE_API_KEY`，前端也能讀取使用。

## 匯入 Excel 失敗？
- 確認檔案為 `.xlsx` / `.xls`。
- 日期欄位建議為 `YYYY-MM-DD`，1900/1/1 或串有 1900 的值會被視為空值。
- 自訂映射模式需提供 `mapping_config` JSON 並於 `FormData` 中傳遞。

## 如何查看最新測試覆蓋率？
- 後端：`docs/backend/coverage/index.html`
- 前端：`docs/frontend/coverage/index.html`
- 若 HTML 尚未更新，請依 [QuickStart](./QuickStart.md) 中指令重新產生。

## Docker 啟動後前端顯示空白？
- 確認前端容器的 Nginx 已啟動：`docker compose logs frontend`。
- 檢查 `.env` 是否設定 `CORS_ORIGINS`，至少包含 `http://localhost:3000`。
- 若仍無法載入，請清除瀏覽器快取或開啟開發者工具查看 4xx/5xx 錯誤。

## 端口衝突？
- 前端：3000（對外 80），後端：5001，PostgreSQL：5432。
- 若本地已有服務占用，可調整 `docker-compose.yml` 或 `.env` 中對應埠口後重建。

## 可以不依賴 Docker 嗎？
可以，請依 [Development](./Development.md) 啟動 Flask 與 Vite。本機測試預設使用 SQLite，若需 PostgreSQL 請自行啟動資料庫並更新 `.env`。

## 何處可以找到系統架構示意圖？
所有圖片都集中在 `docs/assets/`，例如部署架構 `docs/assets/deployment.png`。

## 產品產銷履歷公開頁會不會洩漏資料？
- 公開 API `/api/traceability/public/<批次號>` 只回傳必要欄位，已移除帳號 ID 與內部識別碼。
- 管理端 `/api/traceability/batches` 等端點仍需登入，未授權會獲得 401。
- 若擔心批次號容易被猜測，可為公開用戶提供難以預測的批次編碼或加上一層 URL 簽章；也可配置速率限制與監控日誌。
