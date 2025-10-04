import json
import os
import sys
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import ProductBatch, BatchSheepAssociation


class TestTraceabilityAPI:
    def _create_batch(self, client, sheep=None, batch_number='BATCH-001'):
        payload = {
            'batch_number': batch_number,
            'product_name': '鮮羊乳 946ml',
            'product_type': '乳品',
            'production_date': date.today().isoformat(),
            'is_public': True,
        }
        if sheep is not None:
            payload['sheep_links'] = [
                {
                    'sheep_id': sheep.id,
                    'role': '乳源',
                    'contribution_type': '鮮乳',
                }
            ]
        response = client.post('/api/traceability/batches', json=payload)
        assert response.status_code == 201
        return json.loads(response.data)

    def test_create_batch_with_sheep(self, authenticated_client, test_sheep):
        data = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-100')
        assert data['batch_number'] == 'BATCH-100'
        assert data['sheep_links']
        assert data['sheep_links'][0]['sheep_id'] == test_sheep.id

    def test_update_batch_details(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-101')
        payload = {
            'product_name': '熟成羊乳酪',
            'esg_highlights': '採用牧草飼養，碳排放量低於業界平均。',
            'is_public': False,
        }
        response = authenticated_client.put(f"/api/traceability/batches/{batch['id']}", json=payload)
        assert response.status_code == 200
        updated = json.loads(response.data)
        assert updated['product_name'] == '熟成羊乳酪'
        assert updated['is_public'] is False

    def test_replace_sheep_links(self, authenticated_client, test_sheep, db_session, test_user):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-102')
        from app.models import Sheep
        new_sheep = Sheep(user_id=test_user.id, EarNum='TEST-S2', Breed='努比亞', Sex='母')
        db_session.add(new_sheep)
        db_session.commit()

        payload = {
            'sheep_links': [
                {
                    'sheep_id': new_sheep.id,
                    'role': '奶源',
                    'notes': '第二批次乳量',
                }
            ]
        }
        response = authenticated_client.post(f"/api/traceability/batches/{batch['id']}/sheep", json=payload)
        assert response.status_code == 200
        result = json.loads(response.data)
        assert len(result['sheep_links']) == 1
        assert result['sheep_links'][0]['sheep_id'] == new_sheep.id

    def test_public_trace_endpoint(self, authenticated_client, client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-103')
        response = client.get('/api/traceability/public/BATCH-103')
        assert response.status_code == 200
        story = json.loads(response.data)
        assert story['batch']['batch_number'] == 'BATCH-103'
        assert story['processing_timeline'] == []
        assert story['sheep_details']

    def test_access_control_on_batches(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-104')
        authenticated_client.post('/api/auth/logout')
        response = authenticated_client.get(f"/api/traceability/batches/{batch['id']}")
        assert response.status_code == 401

    def test_delete_batch(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-105')
        response = authenticated_client.delete(f"/api/traceability/batches/{batch['id']}")
        assert response.status_code == 200
        assert response.json['success'] is True
        assert ProductBatch.query.filter_by(id=batch['id']).first() is None
        assert BatchSheepAssociation.query.filter_by(batch_id=batch['id']).count() == 0
