from datetime import date, datetime
from typing import Any

import base64
import json
import requests
from flask import current_app

from .models import Sheep, SheepEvent, SheepHistoricalData


def normalise_json_payload(value: Any) -> Any:
    """Normalise nested structures for deterministic JSON serialisation."""

    if isinstance(value, datetime):
        return value.isoformat(timespec="microseconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [normalise_json_payload(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalise_json_payload(val) for key, val in value.items()}
    return value

def call_gemini_api(prompt_text, api_key, generation_config_override=None, safety_settings_override=None):
    """
    通用 Gemini API 調用函數。
    """
    # 檢查 API 金鑰是否有效
    if not api_key or api_key == 'your-gemini-api-key-here':
        return {"error": "請設置有效的 Google Gemini API 金鑰。請在 .env 文件中設置 GOOGLE_API_KEY。"}
    
    GEMINI_MODEL_NAME = "gemini-flash-latest"
    MAX_OUTPUT_TOKENS_GEMINI = 16384 
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={api_key}"
    
    generation_config = {
        "temperature": 0.4, 
        "topK": 1, 
        "topP": 0.95, 
        "maxOutputTokens": MAX_OUTPUT_TOKENS_GEMINI,
    }
    if generation_config_override: 
        generation_config.update(generation_config_override)

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    if safety_settings_override: 
        safety_settings = safety_settings_override
    
    payload_contents = []
    if isinstance(prompt_text, str):
        payload_contents.append({"role": "user", "parts": [{"text": prompt_text}]})
    elif isinstance(prompt_text, list):
        payload_contents = prompt_text

    payload = {
        "contents": payload_contents,
        "generationConfig": generation_config,
        "safetySettings": safety_settings
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=180)
        response.raise_for_status()
        result_json = response.json()

        if result_json.get("candidates"):
            candidate = result_json["candidates"][0]
            text_content = ""
            if candidate.get("content") and candidate["content"].get("parts") and candidate["content"]["parts"][0].get("text"):
                text_content = candidate["content"]["parts"][0].get("text", "")
            
            finish_reason = candidate.get("finishReason", "UNKNOWN")
            return {"text": text_content, "finish_reason": finish_reason}
        
        elif result_json.get("promptFeedback"):
            block_reason = result_json["promptFeedback"].get("blockReason", "未知原因")
            safety_ratings = result_json["promptFeedback"].get("safetyRatings", [])
            return {"error": f"提示詞被拒絕。原因：{block_reason}。安全評級: {safety_ratings}"}
        else:
            return {"error": "API 回應格式不符合預期。", "raw_response": result_json}

    except requests.exceptions.HTTPError as e:
        error_message = f"API 請求失敗 (碼: {e.response.status_code if e.response else 'N/A'})"
        try:
            error_detail = e.response.json()
            api_error_msg = error_detail.get("error", {}).get("message", "API 金鑰無效或請求錯誤。")
            error_message = f"{api_error_msg} (碼: {e.response.status_code if e.response else 'N/A'})"
        except (ValueError, json.JSONDecodeError):
            pass
        return {"error": error_message}
    except requests.exceptions.RequestException as e:
        return {"error": f"網路或請求錯誤: {e}"}
    except Exception as e:
        current_app.logger.error(f"處理 API 請求時發生未知錯誤: {e}", exc_info=True)
        return {"error": f"處理 API 請求時發生未知錯誤: {e}"}


def get_sheep_info_for_context(ear_num, user_id):
    """
    獲取指定羊隻的資訊，用於組合AI提示詞。
    """
    if not ear_num: return None
    
    sheep_info = Sheep.query.filter_by(EarNum=ear_num, user_id=user_id).first()
    if not sheep_info: return None
    
    sheep_dict = sheep_info.to_dict()
    
    # 獲取最近的5條事件記錄
    recent_events = SheepEvent.query.filter_by(sheep_id=sheep_info.id)\
        .order_by(SheepEvent.event_date.desc(), SheepEvent.id.desc())\
        .limit(5).all()
    sheep_dict['recent_events'] = [event.to_dict() for event in recent_events]
    
    # 獲取最近的10條歷史數據
    history_records = SheepHistoricalData.query.filter_by(
        sheep_id=sheep_info.id, user_id=user_id
    ).order_by(SheepHistoricalData.record_date.desc()).limit(10).all()
    sheep_dict['history_records'] = [rec.to_dict() for rec in history_records]

    return sheep_dict


def encode_image_to_base64(image_data):
    """
    將圖片數據編碼為 base64 字符串
    """
    return base64.b64encode(image_data).decode('utf-8')
