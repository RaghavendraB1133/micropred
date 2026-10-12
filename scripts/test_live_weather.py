import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    print("=== Testing Live Internet Weather Sync (Open-Meteo) ===")
    
    # 1. Sync Live Weather for Zone 1
    req = urllib.request.Request(
        'http://127.0.0.1:5000/api/v1/zones/1/sync-live',
        data=b'{}',
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            details = res['sync_details']
            print(f"✅ Live Sync Message: {res['message']}")
            print(f"Source: {details['source']}")
            print(f"Hours Synced: {details['synced_hours']}")
            print(f"Live Weather Right Now: {details['latest_live_conditions']}\n")
    except urllib.error.HTTPError as e:
        print(f"HTTPError {e.code}: {e.read().decode('utf-8')}")
        return

    # 2. Run LSTM Prediction on this Live Data
    pred_req = urllib.request.Request(
        'http://127.0.0.1:5000/api/v1/predictions/run',
        data=json.dumps({'zone_id': 1, 'horizon_hours': 24}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(pred_req) as resp:
            pred_res = json.loads(resp.read().decode('utf-8'))
            pred = pred_res['prediction']
            print(f"✅ Prediction on Live Weather:")
            print(f"Zone: {pred['zone_code']} ({pred['zone_name']})")
            print(f"Risk Score: {pred['risk_score'] * 100:.1f}% -> Category: {pred['risk_category']}")
            print(f"Input Features: {pred['input_features_snapshot']}")
    except urllib.error.HTTPError as e:
        print(f"Pred HTTPError {e.code}: {e.read().decode('utf-8')}")

if __name__ == '__main__':
    main()
