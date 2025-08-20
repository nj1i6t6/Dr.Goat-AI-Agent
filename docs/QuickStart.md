# 快速開始（Windows / PowerShell）

## Docker（推薦）

```powershell
Copy-Item .env.example .env
# 可自行編輯 .env 調整變數

docker compose up --build -d
# 查看狀態
docker compose ps
```

啟動後：
- 前端：http://localhost:3000
- API：http://localhost:5001
- 健康檢查：http://localhost:5001/api/auth/health
- API 文件：http://localhost:5001/docs（Swagger UI）

## 本機開發（不使用 Docker）

後端
```powershell
cd backend
python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
$env:FLASK_ENV="development"; $env:SECRET_KEY="dev"; $env:CORS_ORIGINS="http://localhost:5173"
python run.py
```

前端
```powershell
cd frontend
npm install
npm run dev
```

## 快速 API 範例
```powershell
# 註冊 + 登入
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/auth/register" -ContentType "application/json" -Body '{"username":"demo","password":"demo123"}' -SessionVariable s
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/auth/login" -ContentType "application/json" -Body '{"username":"demo","password":"demo123"}' -WebSession $s

# 建立羊隻
Invoke-RestMethod -Method Post -Uri "http://localhost:5001/api/sheep/" -ContentType "application/json" -Body '{"EarNum":"A001","Breed":"台灣黑山羊","Sex":"母","BirthDate":"2024-01-15"}' -WebSession $s
```
