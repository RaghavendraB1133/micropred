import json

def test_get_predictions_empty(client):
    response = client.get('/api/v1/predictions')
    assert response.status_code == 200
    data = response.get_json()
    assert 'predictions' in data
    assert 'pagination' in data

def test_run_prediction_invalid_zone(client):
    response = client.post('/api/v1/predictions/run', json={'zone_id': 9999})
    assert response.status_code in (400, 422, 503)

def test_run_prediction_validation_failure(client):
    # Missing zone_id
    response = client.post('/api/v1/predictions/run', json={'horizon_hours': 24})
    assert response.status_code == 422
