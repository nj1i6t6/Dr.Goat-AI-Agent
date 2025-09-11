from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import db, Sheep, SheepEvent, SheepHistoricalData, HealthAlert
from app.schemas import (
    SheepCreateModel, SheepUpdateModel, SheepEventCreateModel, 
    HistoricalDataCreateModel, create_error_response
)
from pydantic import ValidationError
from datetime import datetime, date
from app.services.alerts import evaluate_weight_deviation, create_alert_with_gemini

bp = Blueprint('sheep', __name__)

# --- Sheep (羊隻) API Endpoints ---

@bp.route('/', methods=['GET'])
@login_required
def get_all_sheep():
    """取得該用戶的所有羊隻列表"""
    sheep_list = Sheep.query.filter_by(user_id=current_user.id).order_by(Sheep.EarNum).all()
    return jsonify([s.to_dict() for s in sheep_list])

@bp.route('/', methods=['POST'])
@login_required
def add_sheep():
    """新增一隻羊"""
    if not request.is_json:
        return jsonify(error="請求必須是 JSON 格式"), 400
    
    try:
        # 使用 Pydantic 驗證資料
        sheep_data = SheepCreateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response("資料驗證失敗", e.errors())), 400
    
    # 檢查耳號是否已存在
    if Sheep.query.filter_by(user_id=current_user.id, EarNum=sheep_data.EarNum).first():
        return jsonify(error=f"耳號 {sheep_data.EarNum} 已存在"), 409

    try:
        # 將 Pydantic 模型轉換為字典，排除未設置的值
        sheep_dict = sheep_data.model_dump(exclude_unset=True)
        new_sheep = Sheep(user_id=current_user.id, **sheep_dict)
        db.session.add(new_sheep)
        db.session.commit()
        return jsonify(
            success=True, 
            message="羊隻資料新增成功", 
            sheep=new_sheep.to_dict()
        ), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"新增羊隻失敗: {e}")
        return jsonify(error=f"新增羊隻失敗: {str(e)}"), 500

@bp.route('/<string:ear_num>', methods=['GET'])
@login_required
def get_sheep_details(ear_num):
    """取得單一羊隻的詳細資料 (包含事件)"""
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first()
    if not sheep:
        return jsonify(error="找不到該耳號的羊隻或您沒有權限"), 404
    
    sheep_data = sheep.to_dict()
    events = SheepEvent.query.filter_by(sheep_id=sheep.id).order_by(SheepEvent.event_date.desc(), SheepEvent.id.desc()).all()
    sheep_data['events'] = [e.to_dict() for e in events]
    return jsonify(sheep_data)

@bp.route('/<string:ear_num>', methods=['PUT'])
@login_required
def update_sheep(ear_num):
    """更新羊隻資料"""
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first()
    if not sheep:
        return jsonify(error="找不到該耳號的羊隻或您沒有權限"), 404
    
    try:
        # 使用 Pydantic 驗證資料
        update_data = SheepUpdateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response("資料驗證失敗", e.errors())), 400
    
    record_date = request.get_json().get('record_date', date.today().strftime('%Y-%m-%d'))
    if not record_date:
        record_date = date.today().strftime('%Y-%m-%d')
    
    historical_fields = ['Body_Weight_kg', 'milk_yield_kg_day', 'milk_fat_percentage']
    
    try:
        # 只處理在 Pydantic 模型中定義且有值的欄位
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            # 確保欄位存在於資料庫模型中
            if hasattr(sheep, key):
                new_value = value if value != '' else None
                
                # 處理歷史數據記錄
                if key in historical_fields and new_value is not None:
                    old_value = getattr(sheep, key)
                    if old_value != new_value:
                        try:
                            record_date_obj = datetime.strptime(record_date, '%Y-%m-%d').date()
                            history_record = SheepHistoricalData(
                                sheep_id=sheep.id,
                                user_id=current_user.id,
                                record_date=record_date_obj.strftime('%Y-%m-%d'),
                                record_type=key,
                                value=float(new_value),
                                notes=f"從 {old_value or '空值'} 更新為 {new_value}"
                            )
                            db.session.add(history_record)
                            # 觸發健康警示檢查（僅體重）
                            if key == 'Body_Weight_kg':
                                try:
                                    payload = evaluate_weight_deviation(
                                        ear_num=sheep.EarNum,
                                        user_id=current_user.id,
                                        new_weight=float(new_value),
                                        new_date=record_date_obj.strftime('%Y-%m-%d'),
                                    )
                                    if payload:
                                        ai_res = create_alert_with_gemini(payload, api_key=current_app.config.get('GOOGLE_API_KEY'))
                                        if 'error' in ai_res:
                                            current_app.logger.warning(f"警示 AI 生成失敗: {ai_res['error']}")
                                        else:
                                            summary = ai_res.get('text', '')
                                            # 建立 HealthAlert 記錄
                                            alert = HealthAlert(
                                                user_id=current_user.id,
                                                sheep_id=sheep.id,
                                                ear_num=sheep.EarNum,
                                                alert_type='體重偏離',
                                                message=(summary[:200] if summary else None),
                                                details=summary,
                                                actual_weight=payload['actual_weight'],
                                                predicted_weight=payload['predicted_weight'],
                                                deviation_pct=payload['deviation_pct'],
                                                record_date=payload['record_date'],
                                                model_name=payload['model_name'],
                                            )
                                            db.session.add(alert)
                                            # 仍保留一筆事件，供舊 UI 顯示
                                            db.session.add(SheepEvent(
                                                user_id=current_user.id,
                                                sheep_id=sheep.id,
                                                event_date=record_date_obj.strftime('%Y-%m-%d'),
                                                event_type='健康警示',
                                                description=f"[警示] 體重低於預測 {payload['deviation_pct']}%"
                                            ))
                                except Exception as _e:
                                    current_app.logger.warning(f"健康警示流程失敗: {_e}", exc_info=True)
                        except (ValueError, TypeError) as date_err:
                            current_app.logger.warning(f"更新羊隻歷史數據時，日期格式錯誤: {record_date}, 錯誤: {date_err}")
                            pass 

                setattr(sheep, key, new_value)
        
        sheep.last_updated = datetime.utcnow()
        db.session.commit()
        return jsonify(
            success=True, 
            message="羊隻資料更新成功，並已自動記錄歷史數據。", 
            sheep=sheep.to_dict()
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新羊隻 {ear_num} 失敗: {e}", exc_info=True)
        return jsonify(error=f"更新羊隻失敗: {str(e)}"), 500

@bp.route('/<string:ear_num>', methods=['DELETE'])
@login_required
def delete_sheep(ear_num):
    """刪除羊隻"""
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first()
    if not sheep:
        return jsonify(error="找不到該耳號的羊隻或您沒有權限"), 404
    try:
        db.session.delete(sheep)
        db.session.commit()
        return jsonify(success=True, message="羊隻資料刪除成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"刪除羊隻 {ear_num} 失敗: {e}")
        return jsonify(error=f"刪除羊隻失敗: {str(e)}"), 500


# --- SheepEvent (事件) API Endpoints ---

@bp.route('/<string:ear_num>/events', methods=['GET'])
@login_required
def get_sheep_events(ear_num):
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first_or_404()
    events = SheepEvent.query.filter_by(sheep_id=sheep.id).order_by(SheepEvent.event_date.desc(), SheepEvent.id.desc()).all()
    return jsonify([e.to_dict() for e in events])

@bp.route('/<string:ear_num>/events', methods=['POST'])
@login_required
def add_sheep_event(ear_num):
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first_or_404()
    
    try:
        # 使用 Pydantic 驗證事件資料
        event_data = SheepEventCreateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response("事件資料驗證失敗", e.errors())), 400
    
    try:
        event_dict = event_data.model_dump(exclude_unset=True)
        new_event = SheepEvent(
            user_id=current_user.id, 
            sheep_id=sheep.id, 
            **event_dict
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify(success=True, message="羊隻事件新增成功", event=new_event.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"新增羊隻事件失敗: {e}")
        return jsonify(error=f"新增羊隻事件失敗: {str(e)}"), 500

@bp.route('/events/<int:event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    event = SheepEvent.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    
    data = request.get_json()
    if not data.get('event_date') or not data.get('event_type'):
        return jsonify(error="事件日期和類型為必填"), 400
        
    try:
        allowed_keys = SheepEvent.__table__.columns.keys()
        for key, value in data.items():
            if key in allowed_keys:
                setattr(event, key, value)
        db.session.commit()
        return jsonify(success=True, message="事件更新成功", event=event.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新事件 {event_id} 失敗: {e}")
        return jsonify(error=f"更新事件失敗: {str(e)}"), 500

@bp.route('/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    event = SheepEvent.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    
    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify(success=True, message="事件刪除成功")
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"刪除事件失敗: {str(e)}"), 500


# --- SheepHistoricalData (歷史數據) API Endpoints ---

@bp.route('/<string:ear_num>/history', methods=['GET'])
@login_required
def get_sheep_history(ear_num):
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first_or_404()
    history_data = SheepHistoricalData.query.filter_by(sheep_id=sheep.id).order_by(SheepHistoricalData.record_date.asc(), SheepHistoricalData.id.asc()).all()
    return jsonify([h.to_dict() for h in history_data])

@bp.route('/history/<int:record_id>', methods=['DELETE'])
@login_required
def delete_sheep_history(record_id):
    record = SheepHistoricalData.query.get_or_404(record_id)
    if record.user_id != current_user.id:
        return jsonify(error="您沒有權限刪除此記錄"), 403
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify(success=True, message="歷史數據刪除成功")
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"刪除歷史數據失敗: {str(e)}"), 500


# --- Health Alerts API ---

@bp.route('/<string:ear_num>/alerts', methods=['GET'])
@login_required
def list_health_alerts(ear_num):
    sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first_or_404()
    alerts = HealthAlert.query.filter_by(user_id=current_user.id, sheep_id=sheep.id).order_by(HealthAlert.created_at.desc()).all()
    return jsonify([a.to_dict() for a in alerts])


@bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_health_alert(alert_id):
    alert = HealthAlert.query.get_or_404(alert_id)
    if alert.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if alert.status == 'resolved':
        return jsonify(success=True, message='已處理過'), 200
    alert.status = 'resolved'
    alert.resolved_at = datetime.utcnow()
    try:
        db.session.commit()
        return jsonify(success=True, alert=alert.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"更新失敗: {str(e)}"), 500