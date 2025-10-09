from app import db
from app.services.verifiable_log_service import append_event


def _event(summary: str):
    return {
        'action': 'create',
        'summary': summary,
        'metadata': {'summary': summary},
    }


def test_verify_chain_endpoint_returns_ok(authenticated_client, app):
    with app.app_context():
        append_event(entity_type='batch', entity_id=1, event=_event('first'))
        db.session.commit()
        append_event(entity_type='batch', entity_id=1, event=_event('second'))
        db.session.commit()

    response = authenticated_client.get('/api/verify/chain')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['integrity'] == 'OK'
    assert payload['checked'] >= 2

    response_with_entries = authenticated_client.get('/api/verify/chain?include_entries=true&limit=1')
    assert response_with_entries.status_code == 200
    data = response_with_entries.get_json()
    assert isinstance(data.get('entries'), list)
    assert data['entries']
