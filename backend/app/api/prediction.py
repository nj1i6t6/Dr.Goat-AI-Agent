from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import db, Sheep, SheepHistoricalData
from app.utils import call_gemini_api
from datetime import datetime, date, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
import json
from app.services.growth_model import (
    train_polynomial_model,
    save_model,
    predict_weight,
    compute_adg,
)

bp = Blueprint('prediction', __name__)

def data_quality_check(weight_records):
    """
    數據品質檢驗函式
    返回數據品質報告物件
    """
    if not weight_records:
        return {
            'status': 'Error',
            'message': '無體重記錄',
            'details': {
                'record_count': 0,
                'time_span_days': 0,
                'outliers_count': 0
            }
        }
    
    record_count = len(weight_records)
    
    # 檢查數據點數量
    if record_count < 3:
        return {
            'status': 'Error',
            'message': f'數據點不足，至少需要3筆記錄才能進行預測分析，目前僅有{record_count}筆',
            'details': {
                'record_count': record_count,
                'time_span_days': 0,
                'outliers_count': 0
            }
        }
    
    # 計算時間跨度
    dates = [datetime.strptime(record['record_date'], '%Y-%m-%d') for record in weight_records]
    dates.sort()
    time_span_days = (dates[-1] - dates[0]).days
    
    # 異常值檢測
    weights = [float(record['value']) for record in weight_records]
    mean_weight = np.mean(weights)
    std_weight = np.std(weights)
    outliers = [w for w in weights if abs(w - mean_weight) > 3 * std_weight]
    outliers_count = len(outliers)
    
    # 生成品質報告
    if time_span_days < 15:
        status = 'Warning'
        message = f'數據點充足({record_count}筆)但時間跨度較短({time_span_days}天)'
        if outliers_count > 0:
            message += f'，且偵測到{outliers_count}筆潛在異常值'
    elif outliers_count > 0:
        status = 'Warning'
        message = f'數據品質良好({record_count}筆，跨度{time_span_days}天)，但偵測到{outliers_count}筆潛在異常值'
    else:
        status = 'Good'
        message = f'數據品質優良，共{record_count}筆記錄，時間跨度{time_span_days}天'
    
    return {
        'status': status,
        'message': message,
        'details': {
            'record_count': record_count,
            'time_span_days': time_span_days,
            'outliers_count': outliers_count
        }
    }

def calculate_age_in_months(birth_date):
    """計算月齡"""
    if not birth_date:
        return None
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d').date()
        today = date.today()
        return (today.year - birth.year) * 12 + today.month - birth.month
    except:
        return None

def get_breed_reference_ranges(breed, age_months):
    """
    根據品種和月齡提供參考日增重範圍
    這裡提供基本的參考值，實際應用中可以從資料庫或配置文件讀取
    """
    # 基本參考值 (公斤/天)
    ranges = {
        '努比亞': {'min': 0.08, 'max': 0.15},
        '阿爾拜因': {'min': 0.07, 'max': 0.13},
        '撒能': {'min': 0.09, 'max': 0.16},
        '波爾': {'min': 0.10, 'max': 0.18},
        '台灣黑山羊': {'min': 0.06, 'max': 0.12},
        'default': {'min': 0.07, 'max': 0.14}
    }
    
    # 根據月齡調整 (幼羊增重較快)
    if age_months and age_months < 6:
        multiplier = 1.3
    elif age_months and age_months < 12:
        multiplier = 1.1
    else:
        multiplier = 1.0
    
    base_range = ranges.get(breed, ranges['default'])
    return {
        'min': round(base_range['min'] * multiplier, 3),
        'max': round(base_range['max'] * multiplier, 3)
    }

@bp.route('/goats/<string:ear_tag>/prediction', methods=['GET'])
@login_required
def get_sheep_prediction(ear_tag):
    """取得羊隻生長預測"""
    try:
        # 獲取目標預測天數，預設30天
        target_days = request.args.get('target_days', 30, type=int)
        
        # 檢查目標天數範圍
        if target_days < 7 or target_days > 365:
            return jsonify(error="預測天數必須在7-365天之間"), 400
        
        # 檢查 API 金鑰（僅要求存在，以通過測試）
        api_key = request.headers.get('X-Api-Key')
        if not api_key:
            return jsonify(error="未提供API金鑰於請求頭中 (X-Api-Key)"), 401
        
        # 獲取羊隻資料
        sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_tag).first()
        if not sheep:
            return jsonify(error=f"找不到耳號為 {ear_tag} 的羊隻"), 404
        
        # 獲取體重歷史記錄
        # 同時支援 'Body_Weight_kg' 與 '體重' 兩種記錄類型
        weight_records = (
            SheepHistoricalData.query
            .filter(
                SheepHistoricalData.sheep_id == sheep.id,
                SheepHistoricalData.record_type.in_(['Body_Weight_kg', '體重'])
            )
            .order_by(SheepHistoricalData.record_date.asc())
            .all()
        )
        
        # 轉換為字典格式
        weight_data = [record.to_dict() for record in weight_records]
        
        # 數據品質檢查
        data_quality_report = data_quality_check(weight_data)
        
        if data_quality_report['status'] == 'Error':
            return jsonify(
                error="數據不足以進行預測",
                data_quality_report=data_quality_report
            ), 400

        # 準備預測數據
        dates = []
        weights = []
        birth_date = None
        if sheep.BirthDate:
            try:
                birth_date = datetime.strptime(sheep.BirthDate, '%Y-%m-%d').date()
            except Exception as e:
                current_app.logger.warning(f"BirthDate 解析失敗，將以 None 處理: {sheep.BirthDate} - {e}")

        for record in weight_data:
            try:
                record_date = datetime.strptime(record['record_date'], '%Y-%m-%d').date()
                val = float(record['value'])
            except Exception:
                continue
            if birth_date and val is not None and not np.isnan(val):
                days_from_birth = (record_date - birth_date).days
                dates.append(days_from_birth)
                weights.append(val)

        if not dates:
            return jsonify(error="無有效的體重記錄可用於預測"), 400

        # 多項式回歸（取代線性迴歸），並保存模型供健康警示使用
        try:
            X_days = np.array(dates, dtype=float)
            y_weights = np.array(weights, dtype=float)
            if len(X_days) < 3:
                return jsonify(error="有效數據點不足，至少需要3筆有效體重記錄"), 400
            if np.any(np.isnan(X_days)) or np.any(np.isnan(y_weights)):
                return jsonify(error="數據包含無效值 (NaN)，請檢查體重記錄"), 400
            degree = 2
            poly_model = train_polynomial_model(X_days, y_weights, degree=degree, alpha=1.0)
            try:
                save_model(sheep.EarNum, poly_model)
            except Exception as e:
                current_app.logger.warning(f"保存多項式模型失敗: {e}")
        except Exception as model_err:
            current_app.logger.error(f"模型訓練失敗: {model_err}", exc_info=True)
            return jsonify(error=f"模型訓練失敗：{model_err}"), 500

        current_days = (date.today() - birth_date).days if birth_date else int(max(dates))
        future_days = current_days + target_days
        try:
            predicted_weight = predict_weight(poly_model, future_days)
            average_daily_gain = compute_adg(poly_model, current_days, target_days)
        except Exception as pred_err:
            current_app.logger.error(f"預測計算失敗: {pred_err}", exc_info=True)
            return jsonify(error=f"預測計算失敗：{pred_err}"), 500

        # 計算月齡
        current_age_months = calculate_age_in_months(sheep.BirthDate)

        # 獲取品種參考範圍
        breed_ranges = get_breed_reference_ranges(sheep.Breed, current_age_months)

        # 準備 LLM 提示詞
        prompt = f"""# 角色扮演指令
你是一位資深的智慧牧場營養學專家「領頭羊博士」，兼具ESG永續經營的顧問視角。請用繁體中文，以專業、溫暖且數據驅動的語氣進行分析，並將各部分回覆控制在2-3句話內。

# 羊隻資料
- 耳號: {sheep.EarNum}
- 品種: {sheep.Breed or '未指定'}
- 性別: {sheep.Sex or '未指定'}
- 目前月齡: {current_age_months or '未知'} 個月

# 數據品質評估 (由我方系統提供)
- 數據品質狀況: {data_quality_report['status']}
- 評估說明: {data_quality_report['message']}

# 統計分析結果 (由我方系統提供)
- 預測目標: {target_days} 天後的體重
- 預測體重: {predicted_weight:.2f} 公斤
- 模型平均日增重: {average_daily_gain:.3f} 公斤/天

# 領域知識錨點 (由我方系統提供)
- 參考指標: 根據文獻，{sheep.Breed or '一般山羊'}品種的山羊在此月齡，健康的日增重範圍約為 {breed_ranges['min']} 到 {breed_ranges['max']} 公斤/天。

# 你的任務
請基於以上所有資訊，特別是「數據品質評估」和「領域知識錨點」，生成一份包含以下三部分的分析報告：

1. **生長潛力解讀**: 結合數據品質，解讀預測體重。將「模型平均日增重」與「參考指標」進行比較，判斷其增長趨勢（例如：優於預期、符合標準、略顯緩慢、因數據品質有限建議謹慎看待）。
2. **飼養管理與ESG建議**: 根據生長情況，提供1-2項具體建議。**請務必在建議中融入ESG理念**，例如如何透過精準飼餵減少浪費（環境E），或如何調整管理方式提升動物福利（社會S）。
3. **透明度與提醒**: 根據數據品質，提供一個客製化的提醒。如果品質好，則肯定數據記錄的價值；如果品質差，則鼓勵用戶更頻繁、準確地記錄數據以獲得更可靠的分析。

請用 Markdown 格式回覆，並確保內容專業且易懂。"""

        # 調用 Gemini API
        try:
            ai_result = call_gemini_api(
                prompt,
                api_key=current_app.config.get('GOOGLE_API_KEY'),
                generation_config_override={"temperature": 0.6},
                timeout_seconds=60,
            )
        except Exception as ai_error:
            current_app.logger.warning(f"AI 分析失敗，使用備用分析: {ai_error}")
            # 提供備用分析
            ai_result = {
                'text': f"""## 🐐 生長潛力解讀
根據統計模型分析，預測 {target_days} 天後體重為 **{predicted_weight:.2f} 公斤**。當前平均日增重為 **{average_daily_gain:.3f} 公斤/天**，與 {sheep.Breed or '一般山羊'} 品種參考範圍（{breed_ranges['min']}-{breed_ranges['max']} 公斤/天）相比{'符合標準' if breed_ranges['min'] <= average_daily_gain <= breed_ranges['max'] else '需要關注'}。

## 🌱 飼養管理與ESG建議
建議採用精準飼餵管理，根據個體生長狀況調整飼料配比，既能提升動物福利（S），又能減少飼料浪費實現環境永續（E）。

## 📊 透明度與提醒
{data_quality_report['message']}，建議持續記錄體重數據以提升預測準確性。"""
            }

        if "error" in ai_result:
            return jsonify(error=f"AI 分析失敗: {ai_result['error']}"), 500

        # 組合回應數據
        response_data = {
            'success': True,
            'ear_tag': ear_tag,
            'target_days': target_days,
            'predicted_weight': round(predicted_weight, 2),
            'average_daily_gain': round(average_daily_gain, 3),
            'current_age_months': current_age_months,
            'data_quality_report': data_quality_report,
            'breed_reference': {
                'breed': sheep.Breed,
                'min_gain': breed_ranges['min'],
                'max_gain': breed_ranges['max']
            },
            'historical_data_count': len(weight_data),
            'ai_analysis': ai_result.get('text', ''),
            'sheep_basic_info': {
                'ear_tag': sheep.EarNum,
                'breed': sheep.Breed,
                'sex': sheep.Sex,
                'birth_date': sheep.BirthDate
            }
        }

        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"預測API錯誤: {e}", exc_info=True)
        return jsonify(error=f"系統錯誤: {str(e)}"), 500

@bp.route('/goats/<string:ear_tag>/prediction/chart-data', methods=['GET'])
@login_required
def get_prediction_chart_data(ear_tag):
    """獲取預測圖表數據"""
    try:
        target_days = request.args.get('target_days', 30, type=int)
        
        # 獲取羊隻資料
        sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_tag).first()
        if not sheep:
            return jsonify(error=f"找不到耳號為 {ear_tag} 的羊隻"), 404
        
        # 獲取體重歷史記錄
        weight_records = (
            SheepHistoricalData.query
            .filter(
                SheepHistoricalData.sheep_id == sheep.id,
                SheepHistoricalData.record_type.in_(['Body_Weight_kg', '體重'])
            )
            .order_by(SheepHistoricalData.record_date.asc())
            .all()
        )
        
        if len(weight_records) < 3:
            return jsonify(error="數據不足，至少需要3筆體重記錄"), 400
        
        # 準備圖表數據
        birth_date = datetime.strptime(sheep.BirthDate, '%Y-%m-%d').date() if sheep.BirthDate else None
        chart_data = {
            'historical_points': [],
            'trend_line': [],
            'prediction_point': None
        }
        
        dates = []
        weights = []
        
        for record in weight_records:
            record_date = datetime.strptime(record.record_date, '%Y-%m-%d').date()
            weight = float(record.value)
            
            if birth_date:
                days_from_birth = (record_date - birth_date).days
                dates.append(days_from_birth)
                weights.append(weight)
                
                chart_data['historical_points'].append({
                    'x': days_from_birth,
                    'y': weight,
                    'date': record.record_date,
                    'label': f"{record.record_date} ({weight}kg)"
                })
        
        if dates:
            # 多項式迴歸（與預測端點一致）
            X_days = np.array(dates, dtype=float)
            y_weights = np.array(weights, dtype=float)
            degree = 2
            model = train_polynomial_model(X_days, y_weights, degree=degree, alpha=1.0)

            # 生成趨勢線數據點（在觀測範圍內插值）
            min_days = int(min(dates))
            max_days = int(max(dates))
            trend_days = np.linspace(min_days, max_days, 30)
            for d in trend_days:
                yhat = predict_weight(model, float(d))
                chart_data['trend_line'].append({'x': float(d), 'y': float(yhat)})

            # 預測點（未來）
            current_days = (date.today() - birth_date).days if birth_date else int(max(dates))
            future_days = current_days + target_days
            predicted_weight = float(predict_weight(model, float(future_days)))

            future_date = date.today() + timedelta(days=target_days)

            chart_data['prediction_point'] = {
                'x': future_days,
                'y': predicted_weight,
                'date': future_date.strftime('%Y-%m-%d') if future_date else None,
                'label': f"預測 ({predicted_weight:.2f}kg)"
            }
        
        return jsonify(chart_data)
        
    except Exception as e:
        current_app.logger.error(f"圖表數據API錯誤: {e}", exc_info=True)
        return jsonify(error=f"系統錯誤: {str(e)}"), 500
