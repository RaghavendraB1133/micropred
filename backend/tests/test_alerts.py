def test_get_authorities_directory(client):
    response = client.get('/api/v1/alerts/authorities')
    assert response.status_code == 200
    data = response.get_json()
    assert 'authorities' in data
    assert len(data['authorities']) >= 4
    codes = [a['code'] for a in data['authorities']]
    assert 'DDMA' in codes
    assert 'NDRF' in codes
    assert 'SEOC' in codes

def test_get_alerts_list(client):
    response = client.get('/api/v1/alerts')
    assert response.status_code == 200
    data = response.get_json()
    assert 'alerts' in data
    assert 'pagination' in data

def test_alerts_summary(client):
    response = client.get('/api/v1/alerts/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_dispatched' in data
    assert 'registered_agencies_count' in data

def test_broadcast_drill_valid_zone(client, sample_zone):
    response = client.post('/api/v1/alerts/broadcast', json={'zone_id': sample_zone.id})
    assert response.status_code == 201
    data = response.get_json()
    assert data['count'] >= 4
    assert len(data['alerts']) >= 4

def test_broadcast_drill_missing_zone(client):
    response = client.post('/api/v1/alerts/broadcast', json={})
    assert response.status_code == 400

def test_send_email_alert(client, sample_zone):
    response = client.post('/api/v1/alerts/send-email', json={
        'zone_id': sample_zone.id,
        'recipient_email': 'test-collector@state.gov.in'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'alert' in data
    assert data['alert']['channel'] == 'EMAIL_DISPATCH'
    assert data['alert']['recipient_contact'] == 'test-collector@state.gov.in'

def test_get_email_preview(client, sample_zone):
    response = client.get(f'/api/v1/alerts/email-preview?zone_id={sample_zone.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'email_subject' in data
    assert 'human_awareness_guide' in data
    assert 'immediate_actions' in data['human_awareness_guide']
    assert len(data['human_awareness_guide']['immediate_actions']) > 0

def test_smtp_config_endpoints(client):
    # GET smtp config
    get_res = client.get('/api/v1/alerts/smtp-config')
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert 'server' in data
    assert 'port' in data
    assert 'is_configured' in data

    # POST smtp config
    post_res = client.post('/api/v1/alerts/smtp-config', json={
        'server': 'smtp.gmail.com',
        'port': 587,
        'username': 'alert-test@disaster.gov.in',
        'password': 'test-app-password',
        'sender': 'Disaster Alerts <alert-test@disaster.gov.in>'
    })
    assert post_res.status_code == 200
    pdata = post_res.get_json()
    assert 'config' in pdata
    assert pdata['config']['is_configured'] is True

def test_test_smtp_endpoint(client, monkeypatch):
    from app.services.email_service import EmailService
    monkeypatch.setattr(
        EmailService, 
        'test_smtp_connection', 
        lambda *args, **kwargs: {'status': 'SUCCESS', 'message': 'Handshake OK', 'server': 'smtp.gmail.com', 'port': 587}
    )
    res = client.post('/api/v1/alerts/test-smtp', json={
        'server': 'smtp.gmail.com',
        'port': 587,
        'username': 'test@gmail.com',
        'password': 'password123'
    })
    assert res.status_code == 200
    assert res.get_json()['status'] == 'SUCCESS'

