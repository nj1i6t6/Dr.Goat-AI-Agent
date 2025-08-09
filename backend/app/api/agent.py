from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils import call_gemini_api, get_sheep_info_for_context, encode_image_to_base64
from app.models import db, ChatHistory
from app.schemas import AgentRecommendationModel, AgentChatModel, create_error_response
from pydantic import ValidationError
from datetime import datetime
import markdown
import base64

bp = Blueprint('agent', __name__)

@bp.route('/tip', methods=['GET'])
@login_required
def get_agent_tip():
    """獲取每日提示"""
    api_key = request.headers.get('X-Api-Key')
    if not api_key:
        return jsonify(error="未提供API金鑰於請求頭中 (X-Api-Key)"), 401
    
    current_month = datetime.now().month
    season = "夏季"
    if 3 <= current_month <= 5: season = "春季"
    elif 9 <= current_month <= 11: season = "秋季"
    elif current_month in [12, 1, 2]: season = "冬季"
    
    prompt = f"作為『領頭羊博士』，請給我一條關於台灣當前季節（{season}）的實用山羊飼養小提示，簡短且易懂，請使用 Markdown 格式，例如將重點字詞用 `**` 包裹起來。"

    result = call_gemini_api(prompt, api_key, generation_config_override={"temperature": 0.7})
    if "error" in result:
        return jsonify(error=result["error"]), 500
    
    tip_text = result.get("text", "保持羊舍通風乾燥，提供清潔飲水。")
    tip_html = markdown.markdown(tip_text, extensions=['nl2br', 'fenced_code', 'tables'])
    return jsonify(tip_html=tip_html)

@bp.route('/recommendation', methods=['POST'])
@login_required
def get_recommendation():
    """獲取飼養建議"""
    try:
        # 使用 Pydantic 驗證請求資料
        recommendation_data = AgentRecommendationModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response("請求資料驗證失敗", e.errors())), 400

    # 將 Pydantic 模型轉換為字典
    data = recommendation_data.model_dump(exclude_unset=True)
    api_key = data.pop('api_key')
    
    ear_num = data.get('EarNum')
    sheep_context_str = ""
    if ear_num:
        sheep_db_info = get_sheep_info_for_context(ear_num, current_user.id)
        if sheep_db_info:
            # 使用資料庫數據填充空值
            for key in ['Breed', 'Sex', 'BirthDate', 'agent_notes', 'activity_level', 'primary_forage_type']:
                if not data.get(key) and sheep_db_info.get(key):
                    data[key] = sheep_db_info.get(key)
            
            # 組合背景資料字串
            sheep_context_str += f"\n\n--- 關於耳號 {sheep_db_info['EarNum']} 的額外背景資料 ---\n"
            if sheep_db_info.get('agent_notes'): sheep_context_str += f"我的觀察筆記: {sheep_db_info['agent_notes']}\n"
            if sheep_db_info.get('primary_forage_type'): sheep_context_str += f"主要草料: {sheep_db_info['primary_forage_type']}\n"
            
            if sheep_db_info.get('history_records'):
                history_by_type = {}
                # 將紀錄按類型分組
                for rec in reversed(sheep_db_info['history_records']):
                    rec_type_str = rec.get('record_type')
                    if rec_type_str not in history_by_type:
                        history_by_type[rec_type_str] = []
                    history_by_type[rec_type_str].append(f"{rec['record_date']}({rec['value']})")
                
                sheep_context_str += "歷史數據趨勢:\n"
                for rec_type, values in history_by_type.items():
                    sheep_context_str += f"- {rec_type}: {', '.join(values)}\n"

            if sheep_db_info.get('recent_events'):
                sheep_context_str += "近期事件:\n"
                for event in sheep_db_info['recent_events']:
                    sheep_context_str += f"- {event['event_date']} {event['event_type']}: {event.get('description','無描述')}\n"

    # ESG Prompt 升級
    esg_prompt_instruction = (
        "\n--- ESG 永續性分析 ---\n"
        "除了上述營養建議，請務必增加一個「環境影響與動物福利」的分析區塊。在這個區塊中，請包含：\n"
        "1. **環境影響評估**：根據羊隻的體重和生理狀態，粗估其每日的甲烷排放量(g/day)。\n"
        "2. **低碳飼養建議**：推薦 1-2 種可行的低碳飼料替代方案或添加劑（例如，使用在地草料、海藻粉、單寧等），並簡要說明其減排潛力。\n"
        "3. **動物福利建議**：根據羊隻的生理狀態，提供 1-2 項能減少緊迫 (stress) 的具體管理建議（例如，飼養密度、環境豐富化等）。"
    )

    prompt_parts = [
        f"你是一位名叫『領頭羊博士』的AI羊隻飼養顧問，你非常了解台灣的氣候和常見飼養方式，並且嚴格遵循美國國家科學研究委員會 NRC (2007) 《Nutrient Requirements of Small Ruminants》的指南。你正在為耳號為 **{data.get('EarNum', '一隻未指定耳號')}** 的羊隻提供飼養營養建議。",
        "請根據以下提供的羊隻數據和背景資料，提供一份每日飼料營養需求的詳細建議，包括DMI, ME, CP, Ca, P, 鈣磷比，以及其他適用礦物質和維生素。並針對特定生理狀態給予台灣本土化操作建議。請用 Markdown 格式清晰呈現。\n",
        "--- 羊隻當前數據 ---"
    ]
    
    # 動態添加用戶輸入的數據
    field_map = {
        'EarNum': '耳號', 'Breed': '品種', 'Body_Weight_kg': '體重 (kg)',
        'Age_Months': '月齡 (月)', 'Sex': '性別', 'status': '生理狀態',
        'target_average_daily_gain_g': '目標日增重 (g/天)', 'milk_yield_kg_day': '日產奶量 (kg/天)',
        'milk_fat_percentage': '乳脂率 (%)', 'number_of_fetuses': '懷胎數'
    }
    for key, label in field_map.items():
        if data.get(key):
            prompt_parts.append(f"- {label}: {data[key]}")

    full_prompt = "\n".join(prompt_parts) + sheep_context_str
    if data.get('other_remarks'):
        full_prompt += f"\n\n--- 使用者提供的其他備註 ---\n{data.get('other_remarks')}"
    
    full_prompt += esg_prompt_instruction
    full_prompt += "\n\n請開始提供您的綜合建議。"

    result = call_gemini_api(full_prompt, api_key)
    if "error" in result:
        return jsonify(error=result["error"]), 500
    
    recommendation_html = markdown.markdown(result.get("text",""), extensions=['fenced_code', 'tables', 'nl2br'])
    return jsonify(recommendation_html=recommendation_html)


from werkzeug.exceptions import UnsupportedMediaType

@bp.route('/chat', methods=['POST'])
@login_required
def chat_with_agent():
    """與 AI 聊天，支援文字和圖片"""
    api_key = None
    user_message = ''
    session_id = None
    ear_num_context = None
    image_base64 = None
    image_file = None

    try:
        if 'image' in request.files:
            api_key = request.form.get('api_key')
            user_message = request.form.get('message', '')
            session_id = request.form.get('session_id')
            ear_num_context = request.form.get('ear_num_context')
            image_file = request.files['image']

            if not all([api_key, session_id]):
                return jsonify(error="缺少必要參數(api_key, session_id)"), 400
            if not image_file or not image_file.filename:
                return jsonify(error="未選擇圖片檔案"), 400
            
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return jsonify(error=f"不支援的圖片格式: {image_file.content_type}"), 415
            
            image_data = image_file.read()
            if len(image_data) > 10 * 1024 * 1024:
                return jsonify(error="圖片檔案不能超過 10MB"), 413
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            json_data = request.get_json()
            if not json_data:
                return jsonify(error="請求中未包含 JSON 數據"), 400

            chat_data = AgentChatModel(**json_data)
            api_key = chat_data.api_key
            user_message = chat_data.message
            session_id = chat_data.session_id
            ear_num_context = chat_data.ear_num_context

    except UnsupportedMediaType as e:
        return jsonify(error=f'無效的請求格式: {e.description}'), 415
    except ValidationError as e:
        return jsonify(create_error_response("聊天資料驗證失敗", e.errors())), 400
    except Exception as e:
        current_app.logger.error(f"請求處理錯誤: {e}", exc_info=True)
        return jsonify(error=f"處理請求時發生未知錯誤: {str(e)}"), 500

    # ... (rest of the function remains the same) ...
    # 獲取聊天歷史
    history = ChatHistory.query.filter_by(
        user_id=current_user.id, 
        session_id=session_id
    ).order_by(ChatHistory.timestamp.asc()).limit(20).all()
    
    # 建立對話歷史
    chat_messages_for_api = [
        {"role": "user", "parts": [{"text": "你是一位名叫『領頭羊博士』的AI羊隻飼養代理人，你非常了解台灣的氣候和常見飼養方式。請友善且專業地回答使用者的問題。當用戶上傳山羊照片時，請仔細分析照片中山羊的外觀、健康狀況、環境等，並給出專業的飼養建議。"}]},
        {"role": "model", "parts": [{"text": "是的，領頭羊博士在此為您服務。請問有什麼問題嗎？"}]}
    ]
    for entry in history:
        chat_messages_for_api.append({"role": entry.role, "parts": [{"text": entry.content}]})

    # 加入羊隻背景資料
    sheep_context_text = ""
    if ear_num_context:
        sheep_cxt = get_sheep_info_for_context(ear_num_context, current_user.id)
        if sheep_cxt:
            context_parts = [f"\n\n[背景資料] 我目前正在關注羊隻 {ear_num_context}。"]
            basic_info = {k: v for k, v in sheep_cxt.items() if k in ['Breed', 'Sex', 'BirthDate', 'status'] and v is not None}
            if basic_info:
                context_parts.append("牠的基本資料如下：")
                for key, value in basic_info.items():
                    context_parts.append(f"- {key}: {value}")
            
            if sheep_cxt.get('recent_events'):
                context_parts.append("\n牠最近的事件記錄：")
                for event in sheep_cxt['recent_events']:
                    context_parts.append(f"- {event['event_date']} {event['event_type']}: {event.get('description','無描述')}")
            
            sheep_context_text = "\n".join(context_parts)

    # 準備用戶訊息
    current_user_message_with_context = user_message + sheep_context_text
    
    # 如果有圖片，加入圖片部分
    user_message_parts = [{"text": current_user_message_with_context}]
    if image_base64:
        mime_type = "image/jpeg"
        if image_file:
            mime_type = image_file.content_type
        
        user_message_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_base64
            }
        })
    
    chat_messages_for_api.append({"role": "user", "parts": user_message_parts})

    # 呼叫 Gemini API
    gemini_response = call_gemini_api(chat_messages_for_api, api_key, generation_config_override={"temperature": 0.7})

    if "error" in gemini_response:
        return jsonify(error=gemini_response['error']), 500

    model_reply_text = gemini_response.get("text", "抱歉，我暫時無法回答。")
    
    # 儲存聊天記錄
    try:
        user_content = user_message + (" [包含圖片]" if image_base64 else "")
        user_entry = ChatHistory(user_id=current_user.id, session_id=session_id, role='user', content=user_content, ear_num_context=ear_num_context)
        model_entry = ChatHistory(user_id=current_user.id, session_id=session_id, role='model', content=model_reply_text, ear_num_context=ear_num_context)
        db.session.add(user_entry)
        db.session.add(model_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"儲存聊天記錄失败: {e}")

    reply_html = markdown.markdown(model_reply_text, extensions=['fenced_code', 'tables', 'nl2br'])
    return jsonify(reply_html=reply_html)