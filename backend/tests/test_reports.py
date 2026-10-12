def test_reports_summary(client):
    response = client.get('/api/v1/reports/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert 'zone_statistics' in data

def test_reports_export_csv(client):
    response = client.get('/api/v1/reports/export')
    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/csv')
    assert b'Prediction ID' in response.data
