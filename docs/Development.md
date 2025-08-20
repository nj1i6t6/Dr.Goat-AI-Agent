# 開發指南

## 前端
```powershell
cd frontend
npm install
npm run dev
```
- Vite 代理已轉發 /api -> http://127.0.0.1:5001

## 後端
```powershell
cd backend
python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
$env:FLASK_ENV="development"; $env:SECRET_KEY="dev"; $env:CORS_ORIGINS="http://localhost:5173"
python run.py
```

## 測試
```powershell
# backend
cd backend
pytest

# frontend
cd ../frontend
npm run test
```
