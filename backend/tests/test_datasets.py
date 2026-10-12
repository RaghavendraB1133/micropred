import io

def test_dataset_status(client):
    response = client.get('/api/v1/datasets/status')
    assert response.status_code == 200
    data = response.get_json()
    assert 'datasets' in data
    assert 'total_observations' in data

def test_dataset_validate_endpoint_valid_csv(client):
    csv_content = (
        "timestamp,zone_code,latitude,longitude,rainfall_mm,temperature_c,humidity_pct,wind_speed_kmh,pressure_hpa,soil_moisture_pct,disaster_occurrence\n"
        "2026-01-01 00:00:00,Z1,13.0,80.0,15.0,28.0,75.0,20.0,1010.0,40.0,0\n"
    )
    data = {
        'file': (io.BytesIO(csv_content.encode('utf-8')), 'test_upload.csv')
    }
    response = client.post('/api/v1/datasets/validate', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    res = response.get_json()
    assert res['validation_report']['is_valid'] is True

def test_dataset_validate_missing_file(client):
    response = client.post('/api/v1/datasets/validate', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
