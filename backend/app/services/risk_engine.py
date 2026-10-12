from typing import Dict, Any

class MicroZoneRiskEngine:
    """
    Categorizes predicted quantitative risk scores into standard academic decision-support tiers:
    LOW: [0.00, 0.35)
    MEDIUM: [0.35, 0.70)
    HIGH: [0.70, 1.00]
    """
    THRESHOLD_LOW = 0.35
    THRESHOLD_HIGH = 0.70

    @classmethod
    def calibrate_score(cls, raw_prob: float) -> float:
        """
        Calibrates raw neural network probability from imbalanced time-series training
        (where positive disaster occurrences comprise ~17% base rate) into an intuitive,
        standardized hazard risk index in [0.0, 1.0].
        - Calm baseline (p < 0.15) -> [0.01, 0.30] (LOW RISK)
        - Moderate hazard (0.15 <= p < 0.45) -> [0.35, 0.68] (MEDIUM RISK)
        - Severe storm / flood hazard (p >= 0.45) -> [0.70, 0.98] (HIGH RISK)
        """
        p = max(0.0, min(1.0, float(raw_prob)))
        if p < 0.15:
            score = (p / 0.15) * 0.30
        elif p < 0.45:
            score = 0.35 + ((p - 0.15) / (0.45 - 0.15)) * 0.33
        else:
            score = 0.70 + (min(p - 0.45, 0.15) / 0.15) * 0.28
        return round(float(max(0.01, min(0.99, score))), 4)

    @classmethod
    def classify(cls, score: float) -> str:
        score = float(score)
        if score < cls.THRESHOLD_LOW:
            return "LOW"
        elif score < cls.THRESHOLD_HIGH:
            return "MEDIUM"
        else:
            return "HIGH"

    @classmethod
    def get_risk_details(cls, score: float) -> Dict[str, Any]:
        category = cls.classify(score)
        color_map = {
            "LOW": "#10b981",     # Emerald Green
            "MEDIUM": "#f59e0b",  # Amber / Warning Yellow
            "HIGH": "#ef4444",    # Crimson Red
        }
        action_map = {
            "LOW": "Normal meteorological status. Routine environmental surveillance.",
            "MEDIUM": "Elevated hydro-meteorological indicators. Decision-makers should review drainage and drainage assets.",
            "HIGH": "Critical hazard signature. Pre-deployment of local mitigation teams advised."
        }
        return {
            "risk_score": round(float(score), 4),
            "risk_category": category,
            "badge_color": color_map[category],
            "thresholds": {
                "low_upper": cls.THRESHOLD_LOW,
                "high_lower": cls.THRESHOLD_HIGH
            },
            "advisory": action_map[category],
            "scientific_note": "Probabilistic estimate based on sequential weather observations. Calibrated for 24h forecasting window."
        }
