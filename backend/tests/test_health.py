def test_health_endpoint(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'dependencies' in data
    assert data['dependencies']['database']['status'] == 'CONNECTED'
    assert 'version' in data
