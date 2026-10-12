import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    print("=== Testing Human Behavior Aware Disaster Email Dispatch ===")
    
    # 1. Fetch Email Preview with Human Behavior Awareness Guidelines
    preview_url = 'http://127.0.0.1:5000/api/v1/alerts/email-preview?zone_id=1'
    with urllib.request.urlopen(preview_url) as resp:
        preview = json.loads(resp.read().decode('utf-8'))
        guide = preview['human_awareness_guide']
        print(f"Target Sector: {preview['zone_name']} ({preview['zone_code']})")
        print(f"Risk Score   : {preview['risk_score'] * 100:.1f}% -> Category: {preview['risk_category']}")
        print(f"Email Subject: {preview['email_subject']}\n")
        
        print("🧠 [Human Behavior Awareness Guidelines in Email]:")
        print("1. Immediate Safety Actions:")
        for act in guide['immediate_actions'][:2]:
            print(f"   • {act}")
        print("2. Emergency Kit Checklist:")
        for kit in guide['emergency_kit_checklist'][:2]:
            print(f"   • {kit}")
        print("3. Community Behavioral Guidance:")
        for b in guide['community_behavioral_advisory'][:2]:
            print(f"   • {b}\n")

    # 2. Dispatch Email
    send_payload = json.dumps({
        'zone_id': 1,
        'recipient_email': 'disaster.collector@state.gov.in'
    }).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:5000/api/v1/alerts/send-email',
        data=send_payload,
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        alert = res['alert']
        print(f"✅ {res['message']}")
        print(f"Alert ID: {alert['id']} | Channel: {alert['channel']}")
        print(f"Recipient Contact: {alert['recipient_contact']}")
        print(f"Delivery Status  : {alert['dispatch_status']}")

if __name__ == '__main__':
    main()
