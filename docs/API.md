# API 索引

- Swagger UI：<http://localhost:5001/docs>
- OpenAPI 規格：<http://localhost:5001/openapi.yaml>
- 所有 `/api/*` 端點預設回傳 JSON，除 `export_excel` 為二進位檔案。
- 除 `/api/auth/*`（部分）外，其餘端點皆需登入；登入後以 Cookie Session 維持狀態。

## 認證模組 `/api/auth`

| Method | Path | 說明 | 備註 |
|--------|------|------|------|
| POST | `/register` | 建立新帳號並自動登入 | 初次註冊會建立預設事件選項 |
| POST | `/login` | 使用者登入 | 失敗回傳 401 |
| POST | `/logout` | 登出目前登入者 | 需登入 |
| GET | `/status` | 回傳登入狀態與帳號資訊 | 可作健康檢查 |
| GET | `/health` | 健康檢查 | Docker liveness probe |

## 羊隻管理 `/api/sheep`

| Method | Path | 說明 |
|--------|------|------|
| GET | `/` | 列出當前使用者所有羊隻（依耳號排序） |
| POST | `/` | 新增羊隻，使用 Pydantic `SheepCreateModel` 驗證 |
| GET | `/{ear_num}` | 取得單一羊隻所有欄位與事件列表 |
| PUT | `/{ear_num}` | 更新羊隻資料，會自動記錄體重/產奶歷史 |
| DELETE | `/{ear_num}` | 刪除羊隻（連帶刪除事件與歷史） |
| GET | `/{ear_num}/events` | 取得羊隻事件列表（依時間 DESC） |
| POST | `/{ear_num}/events` | 新增事件，驗證 `SheepEventCreateModel` |
| PUT | `/events/{event_id}` | 更新事件內容 |
| DELETE | `/events/{event_id}` | 刪除事件 |
| GET | `/{ear_num}/history` | 取得歷史數據（體重/奶量/乳脂等） |
| DELETE | `/history/{record_id}` | 刪除單筆歷史記錄 |

## 資料管理 `/api/data`

| Method | Path | 說明 | 注意事項 |
|--------|------|------|----------|
| GET | `/export_excel` | 匯出羊隻、事件、歷史、聊天紀錄 | 回傳 `xlsx`，空資料時會提供說明工作表 |
| POST | `/analyze_excel` | 分析上傳 Excel 結構並回傳欄位預覽 | `multipart/form-data`，檔案欄位為 `file` |
| POST | `/process_import` | 導入 Excel | `is_default_mode=true` 使用內建映射，否則需提供 `mapping_config` JSON |

## 儀表板 `/api/dashboard`

| Method | Path | 說明 |
|--------|------|------|
| GET | `/data` | 聚合提醒、停藥、健康警示、ESG 指標；含 90 秒快取 |
| GET | `/farm_report` | 產生牧場統計報告（品種、性別、疾病統計） |
| GET | `/event_options` | 取得自訂與預設事件類型（含描述） |
| POST | `/event_types` | 新增事件類型 |
| DELETE | `/event_types/{type_id}` | 刪除事件類型（不可刪預設項） |
| POST | `/event_descriptions` | 新增事件描述 |
| DELETE | `/event_descriptions/{desc_id}` | 刪除事件描述 |

## AI 代理 `/api/agent`

> 所有端點需在標頭帶入 `X-Api-Key: <Google Gemini API Key>`，若未提供會回傳 401。

| Method | Path | 說明 |
|--------|------|------|
| GET | `/tip` | 根據季節產出每日飼養小提示（Markdown 轉 HTML） |
| POST | `/recommendation` | 產生營養建議、ESG 分析與餵飼指引 | 需傳 `EarNum`、體重、日增重等欄位；可自動補入資料庫背景 |
| POST | `/chat` | 與 AI 對話；支援文字 JSON 或 `multipart/form-data` 圖片上傳 | `image` 欄位支援 JPEG/PNG/GIF/WebP，最大 10MB |

## 生長預測 `/api/prediction`

> 需登入，且必須提供 `X-Api-Key`（同上）。

| Method | Path | 說明 |
|--------|------|------|
| GET | `/goats/{ear_tag}/prediction?target_days=30` | 以歷史體重做線性迴歸，回傳預測體重、平均日增重、數據品質檢查與 AI 說明 |
| GET | `/goats/{ear_tag}/prediction/chart-data?target_days=30` | 取得圖表所需的歷史點、趨勢線、預測點 |

## 通用規則

- 例外處理：所有 Blueprint 會在失敗情況回傳 `{ "error": "..." }`，HTTP 狀態碼對應錯誤類型。
- 日期格式：統一採 `YYYY-MM-DD`；Excel 匯入會自動排除 `1900-01-01` 等空值標記。
- 權限：所有資料均依 `current_user.id` 隔離，無跨使用者操作。
- 快取：儀表板資料以 user_id 鎖定，若需強制更新請呼叫 `/api/dashboard/data` 後端函式 `clear_dashboard_cache`。

更多詳細欄位、Schema 與範例請開啟 Swagger UI 或檢視 `backend/openapi.yaml`。
