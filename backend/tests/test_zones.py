def test_get_zones(client, sample_zone):
    response = client.get('/api/v1/zones')
    assert response.status_code == 200
    data = response.get_json()
    assert 'zones' in data
    assert len(data['zones']) >= 1
    assert data['zones'][0]['zone_code'] == sample_zone.zone_code

def test_get_zone_by_id(client, sample_zone):
    response = client.get(f'/api/v1/zones/{sample_zone.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == sample_zone.id

def test_get_zone_by_id_not_found(client):
    response = client.get('/api/v1/zones/9999')
    assert response.status_code == 404

def test_get_zone_history(client, sample_zone, sample_weather):
    response = client.get(f'/api/v1/zones/{sample_zone.id}/history')
    assert response.status_code == 200
    data = response.get_json()
    assert 'weather_history' in data
    assert len(data['weather_history']) > 0

def test_sync_zone_live_weather(client, sample_zone, monkeypatch):
    from datetime import datetime, timezone
    mock_records = [
        {
            'timestamp': datetime.now(timezone.utc),
            'rainfall_mm': 12.5,
            'temperature_c': 29.0,
            'humidity_pct': 75.0,
            'wind_speed_kmh': 24.0,
            'pressure_hpa': 1008.0,
            'soil_moisture_pct': 42.0
        }
    ]
    from app.services.live_weather_service import LiveWeatherService
    monkeypatch.setattr(LiveWeatherService, 'fetch_live_weather_for_coords', lambda *args, **kwargs: mock_records)

    response = client.post(f'/api/v1/zones/{sample_zone.id}/sync-live')
    assert response.status_code == 200
    data = response.get_json()
    assert 'sync_details' in data
    assert data['sync_details']['zone_code'] == sample_zone.zone_code
    assert data['sync_details']['synced_hours'] == 1

def test_sync_zone_live_weather_not_found(client):
    response = client.post('/api/v1/zones/9999/sync-live')
    assert response.status_code == 404

def test_seed_pan_india_zones(client):
    response = client.post('/api/v1/zones/seed-pan-india')
    assert response.status_code in (200, 201)
    data = response.get_json()
    assert 'count' in data
    assert data['count'] >= 15
    assert 'zones' in data

def test_add_custom_location(client, monkeypatch):
    from datetime import datetime, timezone
    mock_records = [
        {
            'timestamp': datetime.now(timezone.utc),
            'rainfall_mm': 15.0,
            'temperature_c': 28.0,
            'humidity_pct': 70.0,
            'wind_speed_kmh': 20.0,
            'pressure_hpa': 1010.0,
            'soil_moisture_pct': 40.0
        }
    ]
    from app.services.live_weather_service import LiveWeatherService
    monkeypatch.setattr(LiveWeatherService, 'fetch_live_weather_for_coords', lambda *args, **kwargs: mock_records)

    response = client.post('/api/v1/zones/add-custom', json={
        'name': 'Bengaluru South Floodplain',
        'state': 'Karnataka',
        'latitude': 12.9716,
        'longitude': 77.5946,
        'elevation_m': 920,
        'population_estimate': 8400000,
        'topography': 'Urban Plateau Basin',
        'description': 'Rapidly urbanizing lake basin prone to flash waterlogging.'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'zone' in data
    assert data['zone']['name'] == 'Bengaluru South Floodplain, Karnataka'
    assert 'prediction' in data

