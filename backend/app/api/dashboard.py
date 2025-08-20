from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models import db, Sheep, SheepEvent, SheepHistoricalData, EventTypeOption, EventDescriptionOption
from sqlalchemy import func, case
from sqlalchemy.orm import aliased
from datetime import datetime, date, timedelta

bp = Blueprint('dashboard', __name__)


@bp.route('/data', methods=['GET'])
@login_required
def get_dashboard_data():
    """獲取儀表板所需的聚合數據"""
    try:
        user_id = current_user.id
        today = date.today()
        seven_days_later = today + timedelta(days=7)
        
        # 1. 常規提醒事項
        reminders = []
        reminder_fields = {
            "next_vaccination_due_date": "疫苗接種",
            "next_deworming_due_date": "驅蟲",
            "expected_lambing_date": "預產期"
        }
        
        # 查詢所有有設定提醒日期的羊隻
        reminder_sheep = db.session.query(
            Sheep.EarNum,
            Sheep.next_vaccination_due_date,
            Sheep.next_deworming_due_date,
            Sheep.expected_lambing_date
        ).filter(
            Sheep.user_id == user_id,
            (Sheep.next_vaccination_due_date != None) |
            (Sheep.next_deworming_due_date != None) |
            (Sheep.expected_lambing_date != None)
        ).all()

        for s in reminder_sheep:
            for field, type_name in reminder_fields.items():
                due_date_str = getattr(s, field)
                if due_date_str:
                    due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    if due_date_obj <= seven_days_later:
                        status = "即將到期"
                        if due_date_obj < today: status = "已過期"
                        reminders.append({"ear_num": s.EarNum, "type": type_name, "due_date": due_date_str, "status": status})

        # 2. 停藥期提醒
        medication_events = db.session.query(
            Sheep.EarNum, SheepEvent.event_date, SheepEvent.medication, SheepEvent.withdrawal_days
        ).join(Sheep, Sheep.id == SheepEvent.sheep_id)\
         .filter(Sheep.user_id == user_id, SheepEvent.withdrawal_days != None, SheepEvent.withdrawal_days > 0).all()

        for event in medication_events:
            event_date_obj = datetime.strptime(event.event_date, '%Y-%m-%d').date()
            end_date = event_date_obj + timedelta(days=event.withdrawal_days)
            if end_date >= today:
                reminders.append({
                    "ear_num": event.EarNum,
                    "type": f"停藥期 ({event.medication or '未指定藥品'})",
                    "due_date": end_date.strftime('%Y-%m-%d'),
                    "status": "停藥中"
                })

        # 3. 羊群狀態摘要
        flock_status_summary = db.session.query(
            Sheep.status, func.count(Sheep.id)
        ).filter(Sheep.user_id == user_id, Sheep.status != None, Sheep.status != '').group_by(Sheep.status).all()
        flock_summary_list = [{"status": status, "count": count} for status, count in flock_status_summary]

        # 4. 健康與福利警示
        health_alerts = []
        # (此處的健康警示邏輯與原專案保持一致，未來可進一步優化)
        
        # 5. ESG 指標模擬
        fcr_value = 4.5 # 簡化模擬值

        return jsonify({
            "reminders": sorted(reminders, key=lambda x: (x.get("due_date", "9999-99-99"))),
            "health_alerts": health_alerts,
            "flock_status_summary": flock_summary_list,
            "esg_metrics": {"fcr": fcr_value}
        })
        
    except Exception as e:
        current_app.logger.error(f"獲取儀表板數據時發生錯誤: {e}", exc_info=True)
        return jsonify(error=f"伺服器內部錯誤，無法生成儀表板數據: {str(e)}"), 500

@bp.route('/farm_report', methods=['GET'])
@login_required
def get_farm_report():
    """生成牧場報告"""
    try:
        user_id = current_user.id
        
        flock_composition = {
            'by_breed': db.session.query(Sheep.Breed, func.count(Sheep.id)).filter(Sheep.user_id == user_id, Sheep.Breed != None).group_by(Sheep.Breed).all(),
            'by_sex': db.session.query(Sheep.Sex, func.count(Sheep.id)).filter(Sheep.user_id == user_id, Sheep.Sex != None).group_by(Sheep.Sex).all()
        }
        
        production_summary = {
            'avg_birth_weight': db.session.query(func.avg(Sheep.BirWei)).filter(Sheep.user_id == user_id, Sheep.BirWei != None).scalar(),
            'avg_litter_size': db.session.query(func.avg(Sheep.LittleSize)).filter(Sheep.user_id == user_id, Sheep.LittleSize != None).scalar(),
            'avg_milk_yield': db.session.query(func.avg(SheepHistoricalData.value)).filter(SheepHistoricalData.user_id == user_id, SheepHistoricalData.record_type == 'milk_yield_kg_day').scalar()
        }
        
        disease_stats = db.session.query(
            SheepEvent.description, func.count(SheepEvent.id)
        ).filter(SheepEvent.user_id == user_id, SheepEvent.event_type == '疾病治療', SheepEvent.description != None)\
         .group_by(SheepEvent.description).order_by(func.count(SheepEvent.id).desc()).limit(5).all()

        report = {
            "flock_composition": {
                "by_breed": [{"name": item[0] or "未分類", "count": item[1]} for item in flock_composition['by_breed']],
                "by_sex": [{"name": item[0] or "未分類", "count": item[1]} for item in flock_composition['by_sex']],
                "total": db.session.query(func.count(Sheep.id)).filter(Sheep.user_id == user_id).scalar() or 0
            },
            "production_summary": {
                "avg_birth_weight": round(p, 2) if (p := production_summary['avg_birth_weight']) else None,
                "avg_litter_size": round(p, 1) if (p := production_summary['avg_litter_size']) else None,
                "avg_milk_yield": round(p, 2) if (p := production_summary['avg_milk_yield']) else None,
            },
            "health_summary": {
                "top_diseases": [{"name": item[0] or "未指定描述", "count": item[1]} for item in disease_stats]
            }
        }
        
        return jsonify(report)

    except Exception as e:
        current_app.logger.error(f"生成牧場報告時發生錯誤: {e}", exc_info=True)
        return jsonify(error=f"伺服器內部錯誤，無法生成報告: {str(e)}"), 500

# --- 事件選項自訂 API ---

@bp.route('/event_options', methods=['GET'])
@login_required
def get_event_options():
    """取得用戶所有自訂與預設的事件選項"""
    types = EventTypeOption.query.filter_by(user_id=current_user.id).order_by(EventTypeOption.is_default.desc(), EventTypeOption.name).all()
    # 使用 to_dict 方法來序列化，它會自動處理關聯的 descriptions
    return jsonify([t.to_dict() for t in types])

@bp.route('/event_types', methods=['POST'])
@login_required
def add_event_type():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify(error="類型名稱為必填"), 400
    if EventTypeOption.query.filter_by(user_id=current_user.id, name=name).first():
        return jsonify(error=f"類型 '{name}' 已存在"), 409
    try:
        new_type = EventTypeOption(user_id=current_user.id, name=name, is_default=False)
        db.session.add(new_type)
        db.session.commit()
        return jsonify(new_type.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"新增失敗: {str(e)}"), 500

@bp.route('/event_types/<int:type_id>', methods=['DELETE'])
@login_required
def delete_event_type(type_id):
    option = EventTypeOption.query.get_or_404(type_id)
    if option.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if option.is_default:
        return jsonify(error="不能刪除預設的事件類型"), 400
    try:
        db.session.delete(option)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"刪除失敗: {str(e)}"), 500

@bp.route('/event_descriptions', methods=['POST'])
@login_required
def add_event_description():
    data = request.get_json()
    type_id = data.get('event_type_option_id')
    description_text = data.get('description')
    if not all([type_id, description_text]):
        return jsonify(error="缺少必要參數"), 400
    
    parent_type = EventTypeOption.query.get_or_404(type_id)
    if parent_type.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if EventDescriptionOption.query.filter_by(event_type_option_id=type_id, description=description_text).first():
        return jsonify(error=f"描述 '{description_text}' 已存在於此類型中"), 409
        
    try:
        new_desc = EventDescriptionOption(
            user_id=current_user.id,
            event_type_option_id=type_id,
            description=description_text,
            is_default=False
        )
        db.session.add(new_desc)
        db.session.commit()
        return jsonify(new_desc.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"新增失敗: {str(e)}"), 500

@bp.route('/event_descriptions/<int:desc_id>', methods=['DELETE'])
@login_required
def delete_event_description(desc_id):
    option = EventDescriptionOption.query.get_or_404(desc_id)
    if option.user_id != current_user.id:
        return jsonify(error="權限不足"), 403
    if option.is_default:
        return jsonify(error="不能刪除預設的簡要描述"), 400
    try:
        db.session.delete(option)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"刪除失敗: {str(e)}"), 500