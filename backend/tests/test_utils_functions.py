"""
工具功能測試
測試 utils.py 中的功能函數
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.utils import call_gemini_api, get_sheep_info_for_context


class TestUtilsFunctions:
    """工具功能測試類別"""

    @patch('app.utils.requests.post')
    def test_call_gemini_api_success(self, mock_post):
        """測試成功調用 Gemini API"""
        # 設置模擬回應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "這是一個關於羊隻管理的測試回應"}]
                },
                "finishReason": "STOP"
            }]
        }
        mock_post.return_value = mock_response
        
        prompt_text = "如何照顧羊隻？"
        api_key = "test_api_key"
        result = call_gemini_api(prompt_text, api_key)
        
        assert result["text"] == "這是一個關於羊隻管理的測試回應"
        assert result["finish_reason"] == "STOP"
        mock_post.assert_called_once()

    @patch('app.utils.requests.post')
    def test_call_gemini_api_with_list_prompt(self, mock_post):
        """測試使用列表格式的提示詞"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "回應列表格式的提示"}]
                },
                "finishReason": "STOP"
            }]
        }
        mock_post.return_value = mock_response
        
        prompt_text = [{"role": "user", "parts": [{"text": "測試問題"}]}]
        api_key = "test_api_key"
        result = call_gemini_api(prompt_text, api_key)
        
        assert result["text"] == "回應列表格式的提示"
        assert result["finish_reason"] == "STOP"

    @patch('app.utils.requests.post')
    def test_call_gemini_api_http_error(self, mock_post):
        """測試 HTTP 錯誤處理"""
        import requests
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "API 金鑰無效"}
        }
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        result = call_gemini_api("測試", "invalid_key")
        
        assert "error" in result
        assert "API 金鑰無效" in result["error"]

    @patch('app.utils.requests.post')
    def test_call_gemini_api_request_exception(self, mock_post):
        """測試網路請求異常"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("網路連接錯誤")
        
        result = call_gemini_api("測試", "test_key")
        
        assert "error" in result
        assert "網路或請求錯誤" in result["error"]

    @patch('app.utils.requests.post')
    def test_call_gemini_api_prompt_blocked(self, mock_post):
        """測試提示詞被封鎖"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "promptFeedback": {
                "blockReason": "SAFETY",
                "safetyRatings": [{"category": "HARM_CATEGORY_HARASSMENT", "probability": "HIGH"}]
            }
        }
        mock_post.return_value = mock_response
        
        result = call_gemini_api("不當內容", "test_key")
        
        assert "error" in result
        assert "提示詞被拒絕" in result["error"]
        assert "SAFETY" in result["error"]

    @patch('app.utils.requests.post')
    def test_call_gemini_api_unexpected_response(self, mock_post):
        """測試意外的 API 回應格式"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value = mock_response
        
        result = call_gemini_api("測試", "test_key")
        
        assert "error" in result
        assert "API 回應格式不符合預期" in result["error"]

    @patch('app.utils.requests.post')
    def test_call_gemini_api_with_custom_config(self, mock_post):
        """測試自訂配置參數"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "自訂配置回應"}]
                },
                "finishReason": "STOP"
            }]
        }
        mock_post.return_value = mock_response
        
        generation_config_override = {"temperature": 0.8}
        safety_settings_override = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"}]
        
        result = call_gemini_api("測試", "test_key", generation_config_override, safety_settings_override)
        
        assert result["text"] == "自訂配置回應"
        # 驗證配置被正確使用
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        assert payload['generationConfig']['temperature'] == 0.8
        assert payload['safetySettings'] == safety_settings_override

    def test_get_sheep_info_for_context_no_ear_num(self):
        """測試沒有耳號的情況"""
        result = get_sheep_info_for_context("", 1)
        assert result is None
        
        result = get_sheep_info_for_context(None, 1)
        assert result is None

    def test_get_sheep_info_for_context_sheep_not_found(self, app):
        """測試找不到羊隻的情況"""
        with app.app_context():
            result = get_sheep_info_for_context("NONEXISTENT", 1)
            assert result is None

    def test_get_sheep_info_for_context_success(self, test_sheep, app):
        """測試成功獲取羊隻資訊"""
        with app.app_context():
            # 添加一些事件和歷史記錄
            from app.models import SheepEvent, SheepHistoricalData, db
            
            event = SheepEvent(
                user_id=1,
                sheep_id=test_sheep.id,
                event_date='2024-01-15',
                event_type='疫苗接種',
                description='接種測試疫苗'
            )
            db.session.add(event)
            
            history = SheepHistoricalData(
                user_id=1,
                sheep_id=test_sheep.id,
                record_date='2024-01-15',
                record_type='Body_Weight_kg',
                value=45.0
            )
            db.session.add(history)
            db.session.commit()
            
            result = get_sheep_info_for_context(test_sheep.EarNum, 1)
            
            assert result is not None
            assert result['EarNum'] == test_sheep.EarNum
            assert 'recent_events' in result
            assert 'history_records' in result
            assert len(result['recent_events']) >= 1
            assert len(result['history_records']) >= 1

    def test_call_gemini_api_general_exception(self, mock_post, app):
        """測試一般異常處理"""
        mock_post.side_effect = Exception("未知錯誤")
        
        with app.app_context():
            result = call_gemini_api("測試", "test_key")
            
            assert "error" in result
            assert "處理 API 請求時發生未知錯誤" in result["error"]

    @patch('app.utils.requests.post')
    def test_call_gemini_api_timeout(self, mock_post):
        """測試超時處理"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("請求超時")
        
        result = call_gemini_api("測試", "test_key")
        
        assert "error" in result
        assert "網路或請求錯誤" in result["error"]

    @patch('app.utils.requests.post')
    def test_call_gemini_api_empty_text_response(self, mock_post):
        """測試空回應文本"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": ""}]
                },
                "finishReason": "STOP"
            }]
        }
        mock_post.return_value = mock_response
        
        result = call_gemini_api("測試", "test_key")
        
        assert result["text"] == ""
        assert result["finish_reason"] == "STOP"
