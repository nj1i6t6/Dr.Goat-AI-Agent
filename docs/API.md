# API 概覽

- Swagger UI：http://localhost:5001/docs
- 規格檔（OpenAPI）：http://localhost:5001/openapi.yaml

## 模組
- /api/auth：註冊、登入、登出、狀態、健康檢查
- /api/sheep：羊隻 CRUD、事件、歷史數據
- /api/data：Excel 匯入/匯出/分析
- /api/dashboard：提醒、牧場報告、事件選項 CRUD
- /api/agent：每日提示、AI 養分建議、聊天（需 api_key）
- /api/prediction：生長預測與圖表資料

> 詳細請參考 swagger 介面或 `backend/openapi.yaml`。
