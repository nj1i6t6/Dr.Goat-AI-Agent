# 部署指南（Docker Compose）

## 先決條件
- Docker Desktop（Windows/Mac）或 Docker Engine（Linux）
- Docker Compose v2

## 步驟
```powershell
# 於專案根目錄
Copy-Item .env.example .env
# 編輯 .env 後執行

docker compose up --build -d
# 查看
docker compose ps
# 查看日誌（範例：後端）
docker compose logs -f backend
```

## 服務與埠口
- frontend（Nginx）：80 對外映射 3000
- backend（Flask/Waitress）：5001
- db（PostgreSQL）：5432

## 常見維運指令
```powershell
# 停止
docker compose down
# 重建
docker compose up --build -d
# 重啟單一服務
docker compose restart backend
```
