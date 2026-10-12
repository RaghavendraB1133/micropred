import urllib.request
import json
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def test():
    # 1. Trigger prediction for Zone 1 (Coastal zone)
    payload = json.dumps({'zone_id': 1, 'horizon_hours': 24}).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:5000/api/v1/predictions/run',
        data=payload,
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        pred = res['prediction']
        print(f"Prediction Generated: Zone {pred['zone_code']} ({pred['zone_name']})")
        print(f"Risk Score: {pred['risk_score'] * 100:.1f}% -> Category: {pred['risk_category']}")
        print(f"Snapshot Features (last 24h data): {pred['input_features_snapshot']}")
        print(f"Data Window: {pred['source_data_period']}")
    
    # 2. Check alerts generated for this prediction
    alerts_url = f"http://127.0.0.1:5000/api/v1/alerts?zone_id=1&per_page=4"
    with urllib.request.urlopen(alerts_url) as resp:
        alert_data = json.loads(resp.read().decode('utf-8'))
        print(f"\nTotal Authority Alerts Logged: {alert_data['pagination']['total']}")
        print("Latest Authority Dispatches:")
        for a in alert_data['alerts'][:4]:
            print(f"- Target: {a['authority_code']} ({a['authority_name']})")
            print(f"  Channel: {a['channel']} | Contact: {a['recipient_contact']}")
            print(f"  Severity: {a['severity']} | Status: {a['dispatch_status']}")
            print(f"  Message: {a['message_body'][:120]}...\n")

if __name__ == '__main__':
    test()
