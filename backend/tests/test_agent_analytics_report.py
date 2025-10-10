from datetime import datetime


def test_generate_analytics_report(authenticated_client, mock_gemini_api):
    payload = {
        'filters': {'breed': ['波爾羊'], 'period': '2024-01'},
        'cohort': [
            {
                'breed': '波爾羊',
                'metrics': {
                    'sheep_count': 12,
                    'total_cost': 5400.0,
                    'total_revenue': 7800.0,
                    'net_profit': 2400.0,
                }
            }
        ],
        'cost_benefit': {
            'summary': {
                'total_cost': 5400.0,
                'total_revenue': 7800.0,
                'net_profit': 2400.0,
            },
            'items': [
                {
                    'group': '2024-01',
                    'metrics': {
                        'total_cost': 5400.0,
                        'total_revenue': 7800.0,
                        'net_profit': 2400.0,
                        'avg_cost_per_head': 450.0,
                    }
                }
            ]
        },
        'insights': ['泌乳期飼料成本較預期高 8%。']
    }

    resp = authenticated_client.post(
        '/api/agent/analytics-report', json=payload, headers={'X-Api-Key': 'fake-key'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'report_html' in data
    assert 'report_markdown' in data
    assert 'AI 回應內容' in data['report_markdown']
