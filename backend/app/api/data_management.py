import pandas as pd
import json
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Sheep, SheepEvent, SheepHistoricalData, ChatHistory

bp = Blueprint('data_management', __name__)

@bp.route('/export_excel', methods=['GET'])
@login_required
def export_excel():
    """將用戶所有數據匯出為 Excel 檔案"""
    try:
        user_id = current_user.id
        db_engine = db.engine 

        # 準備查詢
        sheep_query = Sheep.query.filter_by(user_id=user_id).order_by(Sheep.EarNum)
        events_query = SheepEvent.query.join(Sheep).filter(Sheep.user_id==user_id).order_by(Sheep.EarNum, SheepEvent.event_date.desc())
        history_query = SheepHistoricalData.query.join(Sheep).filter(Sheep.user_id==user_id).order_by(Sheep.EarNum, SheepHistoricalData.record_date)
        chat_query = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp)

        # 讀取到 Pandas DataFrame
        df_sheep = pd.read_sql(sheep_query.statement, db_engine) if sheep_query.first() else pd.DataFrame()
        df_events = pd.read_sql(events_query.statement, db_engine) if events_query.first() else pd.DataFrame()
        df_history = pd.read_sql(history_query.statement, db_engine) if history_query.first() else pd.DataFrame()
        df_chat = pd.read_sql(chat_query.statement, db_engine) if chat_query.first() else pd.DataFrame()

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 確保至少有一個工作表
            has_data = False
            
            if not df_sheep.empty:
                df_sheep.to_excel(writer, sheet_name='Sheep_Basic_Info', index=False)
                has_data = True
            
            if not df_events.empty:
                # 建立羊隻 ID 到耳號的映射
                sheep_map = {s.id: s.EarNum for s in sheep_query.all()}
                df_events['EarNum'] = df_events['sheep_id'].map(sheep_map)
                # 重新排列欄位，將 EarNum 放在最前面
                cols = ['EarNum'] + [col for col in df_events.columns if col not in ['EarNum', 'sheep_id']]
                df_events[cols].to_excel(writer, sheet_name='Sheep_Events_Log', index=False)
                has_data = True

            if not df_history.empty:
                if 'sheep_map' not in locals():
                    sheep_map = {s.id: s.EarNum for s in sheep_query.all()}
                df_history['EarNum'] = df_history['sheep_id'].map(sheep_map)
                cols = ['EarNum'] + [col for col in df_history.columns if col not in ['EarNum', 'sheep_id']]
                df_history[cols].to_excel(writer, sheet_name='Sheep_Historical_Data', index=False)
                has_data = True
            
            if not df_chat.empty:
                df_chat.to_excel(writer, sheet_name='Chat_History', index=False)
                has_data = True
            
            # 如果沒有任何數據，創建一個空的工作表
            if not has_data:
                empty_df = pd.DataFrame({'說明': ['目前沒有數據可匯出']})
                empty_df.to_excel(writer, sheet_name='Empty_Export', index=False)

        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"goat_data_export_{timestamp}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        current_app.logger.error(f"匯出 Excel 失敗: {e}", exc_info=True)
        return jsonify(error=f"匯出 Excel 失敗: {str(e)}"), 500

@bp.route('/analyze_excel', methods=['POST'])
@login_required
def analyze_excel():
    """分析上傳的 Excel 檔案結構"""
    if 'file' not in request.files:
        return jsonify(error="沒有檔案被上傳"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="沒有選擇檔案"), 400
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify(error="不支援的檔案格式，請上傳 .xlsx 或 .xls 檔案"), 400
        
    try:
        xls = pd.ExcelFile(file)
        sheets_data = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            df = df.where(pd.notna(df), None) # 將 NaN 轉換為 None
            preview_data = df.head(3).to_dict(orient='records')
            sheets_data[sheet_name] = {
                "columns": list(df.columns),
                "rows": len(df),
                "preview": preview_data
            }
        return jsonify(success=True, sheets=sheets_data)

    except Exception as e:
        current_app.logger.error(f"分析 Excel 檔案失敗: {e}", exc_info=True)
        return jsonify(error=f"分析 Excel 檔案失敗: {str(e)}"), 500

@bp.route('/process_import', methods=['POST'])
@login_required
def process_import():
    """處理數據導入"""
    if 'file' not in request.files:
        return jsonify(error="請求缺少檔案參數"), 400
    
    file = request.files['file']
    is_default_mode = request.form.get('is_default_mode', 'false').lower() == 'true'

    if is_default_mode:
        # 內建的標準範本映射設定
        config = {
            "sheets": {
                "0009-0013A1_Basic": {"purpose": "basic_info", "columns": {"EarNum": "EarNum", "Breed": "Breed", "Sex": "Sex", "BirthDate": "BirthDate", "Sire": "Sire", "Dam": "Dam", "BirWei": "BirWei", "SireBre": "SireBre", "DamBre": "DamBre", "MoveCau": "MoveCau", "MoveDate": "MoveDate", "Class": "Class", "LittleSize": "LittleSize", "Lactation": "Lactation", "ManaClas": "ManaClas", "FarmNum": "FarmNum", "RUni": "RUni"}},
                "0009-0013A4_Kidding": {"purpose": "kidding_record", "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate", "KidNum": "KidNum", "KidSex": "KidSex"}},
                "0009-0013A2_PubMat": {"purpose": "mating_record", "columns": {"EarNum": "EarNum", "Mat_date": "Mat_date", "Mat_grouM_Sire": "Mat_grouM_Sire"}},
                "0009-0013A3_Yean": {"purpose": "yean_record", "columns": {"EarNum": "EarNum", "YeanDate": "YeanDate", "DryOffDate": "DryOffDate", "Lactation": "Lactation"}},
                "0009-0013A9_Milk": {"purpose": "milk_yield_record", "columns": {"EarNum": "EarNum", "MeaDate": "MeaDate", "Milk": "Milk"}},
                "0009-0013A11_MilkAnalysis": {"purpose": "milk_analysis_record", "columns": {"EarNum": "EarNum", "MeaDate": "MeaDate", "AMFat": "AMFat"}},
                "S2_Breed": {"purpose": "breed_mapping", "columns": {"Code": "Symbol", "Name": "Breed"}},
                "S7_Sex": {"purpose": "sex_mapping", "columns": {"Code": "Num", "Name": "Sex"}},
            }
        }
    else:
        if 'mapping_config' not in request.form:
            return jsonify(error="手動模式請求缺少映射設定參數"), 400
        try:
            config = json.loads(request.form['mapping_config'])
        except json.JSONDecodeError:
            return jsonify(error="映射設定格式錯誤"), 400

    try:
        xls = pd.ExcelFile(file)
        report_details = []
        
        def format_date(d):
            if pd.isna(d) or d is None: return None
            try:
                # 處理 '1900-01-01' 或 '1900/1/1' 這類代表空值的日期
                if '1900' in str(d): return None
                dt = pd.to_datetime(d)
                # 處理 excel 日期原點問題
                if dt.year < 1901: return None
                return dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                return None

        # --- 第一階段：讀取映射表並建立羊隻基礎資料 ---
        breed_map, sex_map = {}, {}
        sheets_to_process = config.get('sheets', {})

        # 優先處理映射表
        for sheet_name, sheet_config in sheets_to_process.items():
            if sheet_name not in xls.sheet_names: continue
            purpose = sheet_config.get('purpose')
            cols = sheet_config.get('columns', {})
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str).where(pd.notna, None)
            
            if purpose == 'breed_mapping' and cols.get('Code') and cols.get('Name'):
                for _, row in df.iterrows():
                    if row.get(cols['Code']): breed_map[str(row[cols['Code']])] = row[cols['Name']]
            elif purpose == 'sex_mapping' and cols.get('Code') and cols.get('Name'):
                for _, row in df.iterrows():
                    if row.get(cols['Code']): sex_map[str(row[cols['Code']])] = row[cols['Name']]

        # 處理基礎資料
        for sheet_name, sheet_config in sheets_to_process.items():
            if sheet_name not in xls.sheet_names or sheet_config.get('purpose') != 'basic_info': continue
            
            cols = sheet_config.get('columns', {})
            if 'EarNum' not in cols: continue
            
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str).where(pd.notna, None)
            created, updated = 0, 0
            for _, row in df.iterrows():
                ear_num = row.get(cols['EarNum'])
                if not ear_num: continue

                sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_num).first()
                if not sheep:
                    sheep = Sheep(user_id=current_user.id, EarNum=ear_num)
                    db.session.add(sheep)
                    created += 1
                else:
                    updated += 1
                
                for db_field, xls_col in cols.items():
                    if hasattr(sheep, db_field) and xls_col in row and row[xls_col] is not None:
                        value = row[xls_col]
                        if db_field == 'Breed': value = breed_map.get(str(value), value)
                        elif db_field == 'Sex': value = sex_map.get(str(value), value)
                        elif 'Date' in db_field: value = format_date(value)
                        setattr(sheep, db_field, value)
            
            db.session.commit() # 提交基礎資料變更
            report_details.append({"sheet": sheet_name, "message": f"處理完成。新增 {created} 筆，更新 {updated} 筆基礎資料。"})

        # --- 第二階段：處理事件和歷史數據 ---
        sheep_id_cache = {s.EarNum: s.id for s in Sheep.query.filter_by(user_id=current_user.id).all()}
        
        for sheet_name, sheet_config in sheets_to_process.items():
            if sheet_name not in xls.sheet_names or sheet_config.get('purpose') in ['ignore', 'basic_info', 'breed_mapping', 'sex_mapping']: continue

            cols = sheet_config.get('columns', {})
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str).where(pd.notna, None)
            count = 0
            
            for _, row in df.iterrows():
                ear_num = row.get(cols.get('EarNum'))
                sheep_id = sheep_id_cache.get(ear_num)
                if not sheep_id: continue
                
                # 初始化事件和歷史數據變數
                event_type, event_desc, event_date_val = None, None, None
                hist_type, hist_value, hist_date_val = None, None, None

                purpose = sheet_config.get('purpose')
                
                # 根據用途設定事件或歷史數據
                if purpose == 'kidding_record':
                    event_type, event_date_val = '產仔', row.get(cols.get('YeanDate'))
                    event_desc = f"產下仔羊: {row.get(cols.get('KidNum'))}" if cols.get('KidNum') in row else None
                
                elif purpose == 'mating_record':
                    event_type, event_date_val = '配種', row.get(cols.get('Mat_date'))
                    event_desc = f"配種公羊: {row.get(cols.get('Mat_grouM_Sire'))}" if cols.get('Mat_grouM_Sire') in row else None
                
                elif purpose == 'yean_record':
                    yean_date = format_date(row.get(cols.get('YeanDate')))
                    dry_off_date = format_date(row.get(cols.get('DryOffDate')))
                    lactation = row.get(cols.get('Lactation'))
                    if yean_date:
                        db.session.add(SheepEvent(user_id=current_user.id, sheep_id=sheep_id, event_date=yean_date, event_type='泌乳開始', description=f"第 {lactation} 胎次"))
                        count += 1
                    if dry_off_date:
                        db.session.add(SheepEvent(user_id=current_user.id, sheep_id=sheep_id, event_date=dry_off_date, event_type='乾乳', description=f"第 {lactation} 胎次結束"))
                        count += 1
                    continue
                
                elif purpose in ['weight_record', 'milk_yield_record', 'milk_analysis_record']:
                    if purpose == 'weight_record':
                        hist_type, hist_date_val, hist_value = 'Body_Weight_kg', row.get(cols.get('MeaDate')), row.get(cols.get('Weight'))
                    elif purpose == 'milk_yield_record':
                        hist_type, hist_date_val, hist_value = 'milk_yield_kg_day', row.get(cols.get('MeaDate')), row.get(cols.get('Milk'))
                    elif purpose == 'milk_analysis_record':
                        hist_type, hist_date_val, hist_value = 'milk_fat_percentage', row.get(cols.get('MeaDate')), row.get(cols.get('AMFat'))
                
                # 統一處理日期和數據寫入
                formatted_date = format_date(event_date_val or hist_date_val)
                if not formatted_date: continue

                if event_type:
                    db.session.add(SheepEvent(user_id=current_user.id, sheep_id=sheep_id, event_date=formatted_date, event_type=event_type, description=event_desc))
                    count += 1
                elif hist_type and hist_value is not None:
                    try:
                        db.session.add(SheepHistoricalData(user_id=current_user.id, sheep_id=sheep_id, record_date=formatted_date, record_type=hist_type, value=float(hist_value)))
                        count += 1
                    except (ValueError, TypeError):
                        continue

            if count > 0:
                report_details.append({"sheet": sheet_name, "message": f"成功導入 {count} 筆記錄。"})

        db.session.commit()
        return jsonify(success=True, message="數據導入已成功完成！", details=report_details)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"導入 Excel 數據失敗: {e}", exc_info=True)
        return jsonify(error=f"導入數據過程中發生錯誤: {str(e)}"), 500