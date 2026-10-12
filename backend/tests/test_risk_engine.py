from app.services.risk_engine import MicroZoneRiskEngine

def test_risk_classification_thresholds():
    # Low threshold < 0.35
    assert MicroZoneRiskEngine.classify(0.0) == "LOW"
    assert MicroZoneRiskEngine.classify(0.20) == "LOW"
    assert MicroZoneRiskEngine.classify(0.3499) == "LOW"

    # Medium threshold [0.35, 0.70)
    assert MicroZoneRiskEngine.classify(0.35) == "MEDIUM"
    assert MicroZoneRiskEngine.classify(0.50) == "MEDIUM"
    assert MicroZoneRiskEngine.classify(0.6999) == "MEDIUM"

    # High threshold >= 0.70
    assert MicroZoneRiskEngine.classify(0.70) == "HIGH"
    assert MicroZoneRiskEngine.classify(0.85) == "HIGH"
    assert MicroZoneRiskEngine.classify(1.00) == "HIGH"

def test_risk_details_payload():
    details = MicroZoneRiskEngine.get_risk_details(0.82)
    assert details['risk_category'] == 'HIGH'
    assert details['badge_color'] == '#ef4444'
    assert 'advisory' in details
    assert 'thresholds' in details
