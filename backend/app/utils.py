import requests
import json
import base64
from .models import Sheep, SheepEvent, SheepHistoricalData
from flask import current_app
from typing import Generator, Union, List, Dict, Any

def call_gemini_api(
    prompt_text,
    api_key=None,
    generation_config_override=None,
    safety_settings_override=None,
    timeout_seconds: int = 60,
):
    """通用 Gemini API 調用函數 (支援文字 / 多輪訊息 / 圖片)。

    改進內容:
    1. api_key 參數現在為可選; 若未提供則嘗試從 Flask config['GOOGLE_API_KEY'] 取得。
    2. 新增 timeout_seconds 參數 (預設 60s，原本硬編碼 180s 防止 Nginx upstream timeout)。
    3. 可透過 generation_config_override 覆寫 maxOutputTokens 等，避免過大輸出導致延遲。
    """
    # 若未傳入 api_key，嘗試由設定取得
    api_key = api_key or (current_app.config.get('GOOGLE_API_KEY') if current_app else None)
    if not api_key or api_key in ('your-gemini-api-key', 'your-gemini-api-key-here'):
        return {"error": "缺少有效的 Google Gemini API 金鑰 (GOOGLE_API_KEY)。請於 .env 或請求中提供。"}
    
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
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
        "safetySettings": safety_settings,
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(
            GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=timeout_seconds
        )
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


def stream_gemini_api(
    prompt_or_messages: Union[str, List[Dict[str, Any]]],
    api_key: str = None,
    generation_config_override: Dict[str, Any] = None,
) -> Generator[str, None, None]:
    """以真串流方式呼叫 Gemini，逐段 yield 文字片段。

    - 優先使用 google-genai GA 客戶端的 generate_content_stream。
    - 若環境缺套件或失敗，丟出例外給呼叫端回退。
    """
    api_key = api_key or (current_app.config.get('GOOGLE_API_KEY') if current_app else None)
    if not api_key:
        raise RuntimeError("缺少 GOOGLE_API_KEY，無法啟動串流")

    try:
        from google import genai
    except Exception as e:
        raise RuntimeError(f"未安裝 google-genai 套件: {e}")

    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-flash"
    config = {"temperature": 0.5}
    if generation_config_override:
        config.update(generation_config_override)

    # 直接將字串或 messages 傳入 contents；google-genai 會處理基本格式
    stream = client.models.generate_content_stream(
        model=model,
        contents=prompt_or_messages,
        config=config,
    )

    for chunk in stream:
        try:
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
            else:
                # 兼容性：嘗試從 candidates 擷取
                cands = getattr(chunk, 'candidates', []) or []
                if cands:
                    parts = getattr(cands[0], 'content', None)
                    if parts and getattr(parts, 'parts', None):
                        _text = getattr(parts.parts[0], 'text', '')
                        if _text:
                            yield _text
        except Exception:
            # 單片段解析失敗時略過，持續串流
            continue


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


def stream_gemini_api(
    prompt_text,
    api_key=None,
    generation_config_override=None,
):
    """真正串流：使用 google-genai GA 版客戶端 (generate_content_stream)。

    參數:
    - prompt_text: str 或 list(contents)，與 call_gemini_api 一致。
    - api_key: 若未提供，嘗試從 Flask config['GOOGLE_API_KEY'] 取得。
    - generation_config_override: 可覆寫 temperature 等參數。

    產生器：逐段 yield 純文字 chunk（已過濾空白）。
    若套件缺失或發生錯誤，會 raise 例外；呼叫端需捕捉並回退到非串流或回傳錯誤。
    """
    # 取得金鑰
    api_key = api_key or (current_app.config.get('GOOGLE_API_KEY') if current_app else None)
    if not api_key or api_key in ('your-gemini-api-key', 'your-gemini-api-key-here'):
        raise RuntimeError("缺少有效的 Google Gemini API 金鑰 (GOOGLE_API_KEY)")

    try:
        from google import genai
    except Exception as e:
        raise RuntimeError("未安裝 google-genai 套件，請在 backend/requirements.txt 加入 google-genai") from e

    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    client = genai.Client(api_key=api_key)

    # 準備 contents
    if isinstance(prompt_text, str):
        contents = prompt_text
    else:
        # 直接將 list(contents) 傳入新版 SDK
        contents = prompt_text

    # 預設參數（盡量少設，以尊重上層 max tokens 設定）
    gen_config = {"temperature": 0.4}
    if generation_config_override:
        gen_config.update(generation_config_override)

    # 逐塊產生
    stream = client.models.generate_content_stream(
        model=GEMINI_MODEL_NAME,
        contents=contents,
        generation_config=gen_config,
    )
    for chunk in stream:
        text = getattr(chunk, 'text', None)
        if text:
            yield text