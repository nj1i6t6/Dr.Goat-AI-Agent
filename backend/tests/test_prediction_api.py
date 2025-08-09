import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, date

class TestPredictionAPI:
    """羊隻生長預測 API 測試類別"""

    def test_get_prediction_success(self, authenticated_client, app, sheep_with_weight_data, mock_gemini_api):
        """測試成功獲取預測結果"""
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['ear_tag'] == ear_tag
        assert data['target_days'] == 30
        assert 'predicted_weight' in data
        assert 'average_daily_gain' in data
        assert 'data_quality_report' in data
        assert 'ai_analysis' in data

    def test_get_prediction_sheep_not_found(self, authenticated_client):
        """測試羊隻不存在的情況"""
        response = authenticated_client.get(
            '/api/prediction/goats/NON_EXIST/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert '找不到' in data['error']

    def test_get_prediction_insufficient_data(self, authenticated_client, sheep_insufficient_data):
        """測試數據不足的情況"""
        ear_tag = sheep_insufficient_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '數據不足' in data['error']

    def test_get_prediction_invalid_target_days(self, authenticated_client, sheep_with_weight_data):
        """測試無效的預測天數"""
        ear_tag = sheep_with_weight_data.EarNum
        
        # 測試過小的天數
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=5',
            headers={'X-Api-Key': 'test-api-key'}
        )
        assert response.status_code == 400
        
        # 測試過大的天數
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=400',
            headers={'X-Api-Key': 'test-api-key'}
        )
        assert response.status_code == 400

    def test_get_chart_data_success(self, authenticated_client, sheep_with_weight_data):
        """測試成功獲取圖表數據"""
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction/chart-data?target_days=30'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'historical_points' in data
        assert 'trend_line' in data
        assert 'prediction_point' in data
        assert isinstance(data['historical_points'], list)
        assert isinstance(data['trend_line'], list)

    def test_data_quality_check_functions(self, app):
        """測試數據品質檢查函式"""
        from app.api.prediction import data_quality_check
        
        # 測試空數據
        result = data_quality_check([])
        assert result['status'] == 'Error'
        assert '無體重記錄' in result['message']
        
        # 測試數據不足
        insufficient_data = [
            {'record_date': '2024-01-01', 'value': 10.0},
            {'record_date': '2024-01-02', 'value': 10.5}
        ]
        result = data_quality_check(insufficient_data)
        assert result['status'] == 'Error'
        assert '數據點不足' in result['message']
        
        # 測試良好數據
        good_data = [
            {'record_date': '2024-01-01', 'value': 10.0},
            {'record_date': '2024-01-15', 'value': 11.0},
            {'record_date': '2024-01-30', 'value': 12.0},
            {'record_date': '2024-02-15', 'value': 13.0}
        ]
        result = data_quality_check(good_data)
        assert result['status'] in ['Good', 'Warning']
        assert result['details']['record_count'] == 4

    def test_breed_reference_ranges(self, app):
        """測試品種參考範圍函式"""
        from app.api.prediction import get_breed_reference_ranges
        
        # 測試努比亞品種
        ranges = get_breed_reference_ranges('努比亞', 6)
        assert 'min' in ranges
        assert 'max' in ranges
        assert ranges['min'] > 0
        assert ranges['max'] > ranges['min']
        
        # 測試未知品種
        ranges = get_breed_reference_ranges('未知品種', 12)
        assert ranges['min'] == 0.07
        assert ranges['max'] == 0.14

    @patch('app.api.prediction.call_gemini_api')
    def test_ai_analysis_error_handling(self, mock_gemini, authenticated_client, sheep_with_weight_data):
        """測試 AI 分析錯誤處理"""
        mock_gemini.return_value = {"error": "API 錯誤"}
        ear_tag = sheep_with_weight_data.EarNum
        
        response = authenticated_client.get(
            f'/api/prediction/goats/{ear_tag}/prediction?target_days=30',
            headers={'X-Api-Key': 'test-api-key'}
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'AI 分析失敗' in data['error']
