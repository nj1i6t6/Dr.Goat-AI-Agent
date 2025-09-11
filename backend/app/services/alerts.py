from datetime import datetime
from typing import Optional, Dict, Any

from flask import current_app
from app.models import Sheep, SheepHistoricalData, db
from app.utils import call_gemini_api, get_sheep_info_for_context
from .growth_model import load_model, predict_weight

ALERT_DEVIATION_RATIO = 0.95  # 可移到 config


def _calc_day_from_birth(birth_date_str: Optional[str], record_date_str: str) -> Optional[int]:
    if not record_date_str:
        return None
    try:
        record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()
    except Exception:
        return None
    if not birth_date_str:
        return None
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    except Exception:
        return None
    return (record_date - birth_date).days


def evaluate_weight_deviation(ear_num: str, user_id: int, new_weight: float, new_date: str) -> Optional[Dict[str, Any]]:
    """Return alert payload if deviation detected; otherwise None."""
    sheep = Sheep.query.filter_by(user_id=user_id, EarNum=ear_num).first()
    if not sheep:
        return None

    # 第一關：筆數檢查
    count = SheepHistoricalData.query.filter_by(sheep_id=sheep.id, record_type='Body_Weight_kg').count()
    if count < 5:
        return None

    # 第二關：模型可用性
    model = load_model(ear_num)
    if not model:
        return None

    day_from_birth = _calc_day_from_birth(sheep.BirthDate, new_date)
    if day_from_birth is None:
        return None

    predicted = predict_weight(model, day_from_birth)
    if new_weight < predicted * ALERT_DEVIATION_RATIO:
        deviation_pct = round(100.0 * (predicted - new_weight) / max(predicted, 1e-6), 2)
        return {
            "ear_num": ear_num,
            "user_id": user_id,
            "actual_weight": float(new_weight),
            "predicted_weight": float(predicted),
            "deviation_pct": deviation_pct,
            "record_date": new_date,
            "model_name": "Polynomial+Ridge",
        }

    return None


def build_alert_prompt(payload: Dict[str, Any]) -> str:
    ear_num = payload["ear_num"]
    user_id = payload["user_id"]
    sheep_ctx = get_sheep_info_for_context(ear_num, user_id) or {}

    breed = sheep_ctx.get('Breed')
    sex = sheep_ctx.get('Sex')
    status = sheep_ctx.get('status')
    activity = sheep_ctx.get('activity_level')
    forage = sheep_ctx.get('primary_forage_type')
    events = sheep_ctx.get('recent_events', [])[:3]

    events_text = "\n".join([
        f"- {e.get('event_date')} {e.get('event_type')}: {e.get('description','')}" for e in events
    ]) or "(近期無事件記錄)"

    text = f"""
你是獸醫與營養顧問，請用繁體中文，務實且簡潔回覆。整體 ≤ 200 字，使用 Markdown，條列重點即可。

[個體資料]
- 耳號: {ear_num}；品種: {breed}；性別: {sex}；生理狀態: {status}
- 活動量: {activity}；主要草料: {forage}

[偏離警示]
- 當日實測體重: {payload['actual_weight']} kg
- 模型預測體重({payload['model_name']}): {payload['predicted_weight']} kg
- 偏離幅度: {payload['deviation_pct']}%
- 記錄日期: {payload['record_date']}

[近期事件]
{events_text}

請輸出：
- 可能原因（2–3 點）
- 立即檢查步驟（2–3 點，可操作）
- 飼養管理與福利建議（1–2 點，含 ESG 角度）
若資料不足，請指出缺哪些紀錄以利追蹤。
"""
    return text


def create_alert_with_gemini(payload: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    prompt = build_alert_prompt(payload)
    result = call_gemini_api(prompt, api_key=api_key, generation_config_override={"temperature": 0.4})
    return result
