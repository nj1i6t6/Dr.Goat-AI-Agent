import pytest
import json
from datetime import date, timedelta
from app.models import Sheep, SheepEvent, SheepHistoricalData, EventTypeOption, EventDescriptionOption


class TestDashboardAPI:
    """測試儀表板 API 端點"""

    def test_get_dashboard_data(self, authenticated_client):
        """測試獲取儀表板數據"""
        response = authenticated_client.get('/api/dashboard/data')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'reminders' in data
        assert 'health_alerts' in data
        assert 'flock_status_summary' in data
        assert 'esg_metrics' in data

    def test_get_farm_report(self, authenticated_client):
        """測試獲取牧場報告"""
        response = authenticated_client.get('/api/dashboard/farm_report')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'flock_composition' in data
        assert 'production_summary' in data
        assert 'health_summary' in data
        
        # 檢查報告結構
        assert 'by_breed' in data['flock_composition']
        assert 'by_sex' in data['flock_composition']
        assert 'total' in data['flock_composition']

    def test_get_event_options(self, authenticated_client):
        """測試獲取事件選項"""
        response = authenticated_client.get('/api/dashboard/event_options')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_add_event_type_success(self, authenticated_client):
        """測試成功添加事件類型"""
        event_data = {'name': '自定義事件類型'}
        
        response = authenticated_client.post('/api/dashboard/event_types', json=event_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['name'] == '自定義事件類型'
        assert data['is_default'] is False

    def test_add_event_type_duplicate(self, authenticated_client):
        """測試添加重複事件類型"""
        # 先創建一個事件類型
        authenticated_client.post('/api/dashboard/event_types', json={'name': '已存在類型'})

        # 嘗試創建重複的
        response = authenticated_client.post('/api/dashboard/event_types', json={'name': '已存在類型'})
        assert response.status_code == 409
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_add_event_type_missing_name(self, authenticated_client):
        """測試添加事件類型缺少名稱"""
        response = authenticated_client.post('/api/dashboard/event_types', json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_delete_event_type_success(self, authenticated_client):
        """測試成功刪除事件類型"""
        # 先創建一個事件類型
        response = authenticated_client.post('/api/dashboard/event_types', json={'name': '要刪除的類型'})
        event_type = json.loads(response.data)

        response = authenticated_client.delete(f'/api/dashboard/event_types/{event_type["id"]}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True

    def test_add_event_description_success(self, authenticated_client):
        """測試成功添加事件描述"""
        # 先創建一個事件類型
        type_response = authenticated_client.post('/api/dashboard/event_types', json={'name': '測試類型'})
        event_type = json.loads(type_response.data)

        desc_data = {
            'event_type_option_id': event_type['id'],
            'description': '測試描述'
        }
        
        response = authenticated_client.post('/api/dashboard/event_descriptions', json=desc_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['description'] == '測試描述'

    def test_add_event_description_missing_params(self, authenticated_client):
        """測試添加事件描述缺少參數"""
        response = authenticated_client.post('/api/dashboard/event_descriptions', json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_delete_event_description_success(self, authenticated_client):
        """測試成功刪除事件描述"""
        # 先創建一個事件類型和描述
        type_response = authenticated_client.post('/api/dashboard/event_types', json={'name': '測試類型'})
        event_type = json.loads(type_response.data)

        desc_response = authenticated_client.post('/api/dashboard/event_descriptions', json={
            'event_type_option_id': event_type['id'],
            'description': '要刪除的描述'
        })
        desc = json.loads(desc_response.data)

        response = authenticated_client.delete(f'/api/dashboard/event_descriptions/{desc["id"]}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True

    def test_dashboard_unauthenticated_access(self, client):
        """測試未認證用戶訪問儀表板 API"""
        endpoints = [
            '/api/dashboard/data',
            '/api/dashboard/farm_report',
            '/api/dashboard/event_options'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # 應該返回未授權
