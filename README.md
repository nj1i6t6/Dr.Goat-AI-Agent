# 🐐 領頭羊博士（Goat Nutrition App）

智慧化山羊營養與牧場管理系統。後端 Flask + SQLAlchemy，前端 Vue 3 + Vite，提供羊隻資料管理、AI 諮詢、生長預測、Excel 匯入/匯出與儀表板。

---

## 快速連結
- 快速開始：`docs/QuickStart.md`
- 部署指南：`docs/Deployment.md`
- API 概覽：`docs/API.md`
- 開發指南：`docs/Development.md`
- 常見問題：`docs/FAQ.md`

## 服務入口（預設）
- 前端：http://localhost:3000
- API：http://localhost:5001
- 健康檢查：http://localhost:5001/api/auth/health
- API 文件（Swagger UI）：http://localhost:5001/docs
- OpenAPI 規格檔：http://localhost:5001/openapi.yaml

## 主要功能
- 羊隻管理：建檔、查詢、編輯、刪除；事件與歷史紀錄
- AI 諮詢：整合 Google Gemini（後端 HTTP 呼叫）
- 生長預測：以 scikit-learn 線性回歸做簡易預測
- 資料管理：Excel 匯入/匯出、範本下載
- 儀表板：關鍵統計與健康摘要

## 認證與安全
- 認證：Cookie 會話（Flask-Login），登入後以 Session 維持狀態
- 端點：`/api/auth/register`、`/api/auth/login`、`/api/auth/logout`、`/api/auth/me`、`/api/auth/health`
- CORS：可由環境變數設定允許來源

## 快速開始（摘要）
- Windows（批次檔）：在專案根目錄執行 `deploy.bat`
- Docker（Compose）：`docker-compose up -d`（詳見 `docs/Deployment.md`）
- 本機開發（簡述）：
  - 後端：`cd backend` → `pip install -r requirements.txt` → `python run.py`
  - 前端：`cd frontend` → `npm install` → `npm run dev`

## 環境變數（摘要）
- 支援以 `.env` 設定；亦可用 `DOTENV_PATH` 指定檔案位置
- 需設定如資料庫連線、CORS、Google API Key 等（詳見 `docs/Deployment.md`）

## 專案結構
```
backend/   Flask 後端（API、模型、藍圖、OpenAPI 規格）
frontend/  Vue 3 前端（Vite、Element Plus、Pinia、Router）
docs/      文件（快速開始、部署、API、開發、FAQ）
```

## 參與貢獻
- 提交 PR 前請先閱讀 `docs/Development.md`
- 建議遵循簡明提交訊息與小步提交

## 授權
- MIT License（若有 LICENSE 檔）

—

本檔僅保留精要資訊；完整說明與操作請參考 `docs/` 與後端內建的 Swagger UI。