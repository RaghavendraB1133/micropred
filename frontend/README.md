# HUMAN BEHAVIOR AWARE MICRO-ZONE DISASTER PREDICTION SYSTEM USING AI

> **Final-Year Project Overview**: A simple, clear AI disaster early-warning system that predicts localized disasters from 5 years of historical data, makes people aware through human safety guidance, and sends automated email alert notifications.

---

## 🌟 The 4 Core Steps of the Project

```
1. 5 YEARS HISTORICAL DATA  ──►  2. AI DISASTER PREDICTION
   (Weather & past disaster         (Predicts Low, Medium, or High
    records from 2021-2026)          hazard for each micro-zone)
                                              │
                                              ▼
4. EMAIL ALERT NOTIFICATION ◄──  3. HUMAN BEHAVIOR AWARENESS
   (Automated warning email         (Actionable safety instructions:
    sent to people & authorities)    evacuation, kits, dos and don'ts)
```

---

## 1. Previous 5 Years Historical Data
- The system is trained on **5 years of historical hydro-meteorological and disaster observations** (rainfall, temperature, humidity, wind speed, atmospheric pressure, and soil moisture).
- The AI model studies these past 5 years to recognize the exact weather patterns that caused past floods and cyclones.

## 2. Micro-Zone Disaster Prediction
- Instead of issuing broad, inaccurate alerts for an entire state, the region is divided into discrete **Micro-Zones** (e.g. *Coastal Lowland, River Basin, Urban Metro*).
- For each zone, the AI assesses conditions and assigns a clear risk tier:
  - **🟢 LOW RISK (< 35%):** Safe, routine weather.
  - **🟡 MEDIUM RISK (35% – 70%):** Elevated weather activity; watch advisory.
  - **🔴 HIGH RISK (≥ 70%):** Critical disaster hazard detected!

## 3. Human Behavior Awareness ("How Humans Become Aware")
When a disaster is predicted, the system provides practical, life-saving guidance so people know exactly how to react:
- 🏃 **Immediate Human Actions:** Evacuate to higher municipal relief shelters; turn off electrical mains and LPG gas.
- 🎒 **Essential Emergency Kit:** 3-day drinking water, non-perishable rations, flashlight, medicines, and waterproof documents.
- 🤝 **Community & Behavioral Support:** Stay calm, do not spread unverified rumors, assist elderly neighbors and children.
- 📞 **Emergency Helplines:** DDMA (1077), State SEOC (1070), NDRF Command (044-27473000), Municipal Help (1913).

## 4. Automated Email Alert Notification
- Whenever **HIGH RISK** is predicted, the system **automatically dispatches an Email Alert** to registered authorities and citizens.
- The email includes the exact hazard prediction details, weather triggers, and the full Human Behavior Safety Guide.

---

## 🚀 How to Run the Project for Viva / Demo

```powershell
# 1. Start the system:
.\scripts\run_system.ps1 -All

# 2. Test Email Alerts & Human Awareness dispatch:
.\scripts\run_system.ps1 -EmailTest

# 3. Run all automated tests:
.\scripts\run_system.ps1 -Test
```

- **Frontend URL:** [http://localhost:5173](http://localhost:5173)
- **Email Alerts & Awareness Tab:** [http://localhost:5173/alerts](http://localhost:5173/alerts)
