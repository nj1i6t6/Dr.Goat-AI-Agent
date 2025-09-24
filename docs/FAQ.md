# 常見問題（FAQ）

## 無法登入？
先以 /api/auth/register 註冊，再 /api/auth/login 登入。未登入端點會回 401。

## AI 相關錯誤？
確認請求內提供 api_key 或 .env/Compose 設定 GOOGLE_API_KEY。

## 匯入日期格式？
建議 YYYY-MM-DD；Excel 1900/1/1 類型會被視為空值。

## 端口衝突？
確保 80/3000/5001/5432 未被其他服務占用。
