# Terminology Glossary

| English Term | zh-TW Term | Notes |
|--------------|-----------|-------|
| Sheep | 羊隻 | Core animal entity managed across modules. |
| Flock | 羊群 | Grouping used in dashboards and reports. |
| Batch | 批次 | Production batch for traceability workflows. |
| Traceability | 產銷履歷 | Public-facing supply-chain storytelling. |
| ESG | 永續 / ESG 指標 | Environmental, social, and governance metrics. |
| Sensor Reading | 感測數據 | IoT ingestion payload stored per device. |
| IoT Device | IoT 裝置 | Managed hardware endpoint for telemetry. |
| Automation Rule | 自動化規則 | Maps sensor triggers to actuator commands. |
| Background Task | 背景任務 | Redis-backed job executed by `run_worker.py`. |
| Dashboard Cache | 儀表板快取 | Redis layer for cached analytics widgets. |
| API Key | API 金鑰 | Must be hashed server-side; shown once to users. |
| Growth Prediction | 生長預測 | ML-powered forecast served via `/api/prediction`. |
| Daily Tip | 每日提示 | Gemini-generated guidance for caretakers. |
| Intake Form | 匯入表單 | Excel-powered batch data ingestion forms. |
| Pinia Store | Pinia Store 狀態 | Vue global state container. |
| Element Plus | Element Plus 元件庫 | Frontend UI component library. |
| Worker Queue | 佇列 | Redis queue feeding the worker process. |
| Alembic Migration | 資料庫遷移 | Schema migration script under `backend/migrations/`. |
| Coverage Report | 覆蓋率報告 | Stored under `docs/backend/coverage/` and `docs/frontend/coverage/`. |

Maintain this glossary whenever terminology changes in the English SoT or zh-TW documentation.
