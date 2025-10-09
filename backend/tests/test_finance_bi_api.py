from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import CostEntry, RevenueEntry


@pytest.fixture
def finance_seed(app, test_user):
    with app.app_context():
        db.session.query(CostEntry).delete()
        db.session.query(RevenueEntry).delete()
        today = datetime.utcnow()
        entries = [
            CostEntry(
                user_id=test_user.id,
                category='飼料',
                subcategory='日糧',
                amount=Decimal('1200.50'),
                recorded_at=today - timedelta(days=10),
                breed='撒能',
                age_group='小羊 (0-6個月)',
                parity=0,
            ),
            CostEntry(
                user_id=test_user.id,
                category='保健',
                subcategory='疫苗',
                amount=Decimal('800.00'),
                recorded_at=today - timedelta(days=5),
                breed='波爾羊',
                age_group='青年 (6-12個月)',
                parity=1,
            ),
            RevenueEntry(
                user_id=test_user.id,
                category='乳品',
                subcategory='鮮乳',
                amount=Decimal('3200.75'),
                recorded_at=today - timedelta(days=4),
                breed='撒能',
                age_group='成羊 (12-36個月)',
                parity=2,
            ),
            RevenueEntry(
                user_id=test_user.id,
                category='肉品',
                subcategory='羔羊',
                amount=Decimal('2600.00'),
                recorded_at=today - timedelta(days=2),
                breed='波爾羊',
                age_group='青年 (6-12個月)',
                parity=1,
            ),
        ]
        db.session.add_all(entries)
        db.session.commit()
        return entries


def clear_bi_cache(app):
    client = app.extensions['redis_client']
    for key in client.keys('bi-cache:*'):
        client.delete(key)
    for key in client.keys('bi-rate:*'):
        client.delete(key)


def test_cost_entry_crud(authenticated_client):
    clear_bi_cache(authenticated_client.application)
    payload = {
        'category': '飼料',
        'amount': 1500,
        'recorded_at': datetime.utcnow().isoformat(),
    }
    resp = authenticated_client.post('/api/finance/costs', json=payload)
    assert resp.status_code == 201
    cost_id = resp.get_json()['id']

    resp = authenticated_client.get('/api/finance/costs')
    assert resp.status_code == 200
    assert any(entry['id'] == cost_id for entry in resp.get_json())

    resp = authenticated_client.put(f'/api/finance/costs/{cost_id}', json={'notes': '調整後'})
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == '調整後'

    resp = authenticated_client.delete(f'/api/finance/costs/{cost_id}')
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_revenue_bulk_import(authenticated_client):
    clear_bi_cache(authenticated_client.application)
    payload = {
        'entries': [
            {
                'category': '乳品',
                'amount': 2800,
                'recorded_at': datetime.utcnow().isoformat(),
            },
            {
                'category': '肉品',
                'amount': 3300,
                'recorded_at': datetime.utcnow().isoformat(),
            },
        ]
    }
    resp = authenticated_client.post('/api/finance/revenues/bulk', json=payload)
    assert resp.status_code == 201
    assert len(resp.get_json()) == 2


def test_cohort_analysis_endpoint(authenticated_client, finance_seed):
    clear_bi_cache(authenticated_client.application)
    payload = {
        'dimensions': ['breed'],
        'metrics': ['total_cost', 'total_revenue', 'net_income'],
        'time_range': {
            'start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'end': datetime.utcnow().isoformat(),
        },
    }
    resp = authenticated_client.post('/api/bi/cohort-analysis', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['dimensions'] == ['breed']
    assert 'rows' in data and len(data['rows']) >= 1
    assert 'metrics' in data['rows'][0]


def test_cost_benefit_rate_limit(authenticated_client, finance_seed, monkeypatch):
    clear_bi_cache(authenticated_client.application)
    from app import cache as cache_module

    monkeypatch.setattr(cache_module, 'BI_RATE_LIMIT_PER_MINUTE', 1)
    payload = {
        'metrics': ['total_cost', 'total_revenue'],
        'granularity': 'day',
    }
    first = authenticated_client.post('/api/bi/cost-benefit', json=payload)
    assert first.status_code == 200
    second = authenticated_client.post('/api/bi/cost-benefit', json=payload)
    assert second.status_code == 429


def test_ai_report_generation(authenticated_client, finance_seed, monkeypatch):
    clear_bi_cache(authenticated_client.application)

    def fake_call_gemini(prompt, api_key, generation_config_override=None):
        return {'text': '## 測試報告\n- 指標一\n- 指標二'}

    from app.api import bi as bi_module

    monkeypatch.setattr(bi_module, 'call_gemini_api', fake_call_gemini)

    payload = {
        'api_key': 'test-api-key-1234567890',
        'metrics': ['total_cost', 'total_revenue'],
        'aggregates': {'total_cost': 1000, 'total_revenue': 2000},
    }
    resp = authenticated_client.post('/api/bi/ai-report', json=payload, headers={'X-Api-Key': 'test-api-key-1234567890'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'report_markdown' in data and 'report_html' in data
    assert '測試報告' in data['report_markdown']
