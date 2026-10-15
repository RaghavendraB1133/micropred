import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from flask import current_app
from app.extensions import db
from app.models.alert import AlertNotification
from app.models.zone import Zone
from app.models.prediction import Prediction
from app.utils.logger import logger

class EmailService:
    @classmethod
    def generate_human_awareness_guide(cls, zone: Zone, risk_score: float) -> Dict[str, Any]:
        """
        Generates structured human behavior awareness guidelines tailored
        to disaster mitigation and public safety.
        """
        score_pct = round(risk_score * 100, 1)
        return {
            'risk_level': 'CRITICAL HIGH' if risk_score >= 0.70 else ('MODERATE' if risk_score >= 0.35 else 'LOW'),
            'score_pct': score_pct,
            'zone_name': zone.name,
            'zone_code': zone.zone_code,
            'topography': zone.topography,
            'immediate_actions': [
                "Move immediately to designated municipal relief shelters or elevated ground.",
                "Turn off main electrical circuit breakers and LPG gas cylinders to prevent post-disaster fires.",
                "Never walk, swim, or drive through flowing water — 15cm of rapid water can knock an adult down.",
                "Keep battery-powered radios tuned to State Disaster Management Authority broadcasts."
            ],
            'emergency_kit_checklist': [
                "3-day supply of clean drinking water (3 liters per person per day)",
                "Non-perishable ready-to-eat dry rations and baby food if needed",
                "Essential prescription medicines, first-aid kit, and antiseptic wipes",
                "Battery-operated LED flashlight with spare batteries and power bank",
                "Identification papers, insurance documents, and cash sealed in waterproof bags"
            ],
            'community_behavioral_advisory': [
                "Assist vulnerable neighbors: Check on elderly residents, pregnant women, and disabled citizens.",
                "Do not panic or circulate unverified WhatsApp/social media rumors.",
                "Keep emergency phone lines clear for rescue teams; communicate via short SMS where possible.",
                "Secure outdoor items (metal sheets, plastic drums) that could become hazardous projectiles in high winds."
            ],
            'emergency_contacts': [
                {"agency": "District Disaster Management (DDMA)", "phone": "1077"},
                {"agency": "State Emergency Operations Centre (SEOC)", "phone": "1070"},
                {"agency": "NDRF Flood Rescue Command", "phone": "044-27473000"},
                {"agency": "Municipal Emergency Response", "phone": "1913"}
            ]
        }

    @classmethod
    def format_email_content(cls, zone: Zone, prediction: Prediction) -> Tuple[str, str, str]:
        """
        Formats email Subject, Plain Text body, and responsive HTML body.
        """
        guide = cls.generate_human_awareness_guide(zone, prediction.risk_score)
        snap = prediction.input_features_snapshot or {}
        rain = snap.get('rainfall_mm', 'N/A')
        wind = snap.get('wind_speed_kmh', 'N/A')
        press = snap.get('pressure_hpa', 'N/A')
        
        subject = f"🚨 [DISASTER ALERT] High Risk Predicted for {zone.name} ({zone.zone_code}) - Immediate Human Awareness Advisory"

        # Plain text version
        plain_text = f"""
================================================================================
🚨 HUMAN BEHAVIOR AWARE MICRO-ZONE DISASTER ALERT
================================================================================
Target Sector : {zone.name} ({zone.zone_code})
Coordinates   : Lat {zone.latitude:.3f}, Lon {zone.longitude:.3f}
Risk Status   : {guide['risk_level']} ({guide['score_pct']}% Probability)
Forecast Window: Next {prediction.prediction_horizon_hours} Hours
Weather Snapshot: Rainfall: {rain}mm | Wind Speed: {wind}km/h | Pressure: {press}hPa
Timestamp     : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

--------------------------------------------------------------------------------
1. IMMEDIATE HUMAN SAFETY ACTIONS:
--------------------------------------------------------------------------------
{chr(10).join(f"- {act}" for act in guide['immediate_actions'])}

--------------------------------------------------------------------------------
2. EMERGENCY KIT CHECKLIST:
--------------------------------------------------------------------------------
{chr(10).join(f"- {kit}" for kit in guide['emergency_kit_checklist'])}

--------------------------------------------------------------------------------
3. COMMUNITY & BEHAVIORAL SAFETY:
--------------------------------------------------------------------------------
{chr(10).join(f"- {b}" for b in guide['community_behavioral_advisory'])}

--------------------------------------------------------------------------------
4. EMERGENCY HELPLINES:
--------------------------------------------------------------------------------
- DDMA Control : 1077
- State SEOC   : 1070
- NDRF Rescue  : 044-27473000
- Municipal Help: 1913

This alert was generated automatically by the AI Micro-Zone Disaster Early Warning System
based on 5-year historical disaster patterns.
================================================================================
"""

        # HTML Version
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
    .container {{ max-width: 650px; margin: 0 auto; background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }}
    .header {{ background: #dc2626; color: white; padding: 24px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.95; }}
    .badge {{ display: inline-block; background: #7f1d1d; color: #fecaca; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-top: 10px; border: 1px solid #ef4444; }}
    .content {{ padding: 24px; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0 20px; }}
    .metric-card {{ background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; }}
    .metric-title {{ font-size: 10px; color: #94a3b8; text-transform: uppercase; }}
    .metric-val {{ font-size: 16px; font-weight: bold; color: #38bdf8; margin-top: 4px; }}
    .section-title {{ font-size: 14px; font-weight: bold; color: #f87171; text-transform: uppercase; margin: 20px 0 10px; border-bottom: 1px solid #334155; padding-bottom: 6px; }}
    ul {{ margin: 0; padding-left: 20px; font-size: 13px; color: #cbd5e1; line-height: 1.6; }}
    li {{ margin-bottom: 6px; }}
    .contact-box {{ background: #0f172a; padding: 12px 16px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #38bdf8; }}
    .footer {{ background: #0f172a; padding: 16px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid #334155; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🚨 Micro-Zone Disaster Early Warning</h1>
      <p>Human Behavior Aware Emergency Alert & Public Safety Notice</p>
      <div class="badge">{guide['risk_level']} HAZARD — {guide['score_pct']}% PROBABILITY</div>
    </div>
    <div class="content">
      <p style="font-size: 14px; color: #e2e8f0; margin-top: 0;">
        An automated AI assessment based on 5-year historical disaster observations has flagged 
        <strong>{zone.name} ({zone.zone_code})</strong> for high disaster probability in the upcoming 
        <strong>{prediction.prediction_horizon_hours} hours</strong>.
      </p>

      <div class="metric-grid">
        <div class="metric-card">
          <div class="metric-title">Rainfall</div>
          <div class="metric-val">{rain} mm</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">Wind Speed</div>
          <div class="metric-val">{wind} km/h</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">Pressure</div>
          <div class="metric-val">{press} hPa</div>
        </div>
      </div>

      <div class="section-title">🏃 1. Immediate Human Safety Actions</div>
      <ul>
        {''.join(f'<li>{act}</li>' for act in guide['immediate_actions'])}
      </ul>

      <div class="section-title">🎒 2. Emergency Kit Checklist</div>
      <ul>
        {''.join(f'<li>{kit}</li>' for kit in guide['emergency_kit_checklist'])}
      </ul>

      <div class="section-title">🤝 3. Community & Behavioral Advisory</div>
      <ul>
        {''.join(f'<li>{b}</li>' for b in guide['community_behavioral_advisory'])}
      </ul>

      <div class="section-title">📞 4. Emergency Contacts & Shelters</div>
      <div class="contact-box">
        <p style="margin: 0; font-size: 13px; color: #94a3b8;">
          • <strong>DDMA Control:</strong> 1077<br>
          • <strong>State SEOC:</strong> 1070<br>
          • <strong>NDRF Command:</strong> 044-27473000<br>
          • <strong>Municipal Emergency:</strong> 1913
        </p>
      </div>
    </div>
    <div class="footer">
      Generated automatically by the AI Micro-Zone Disaster Prediction System.<br>
      Trained on 5-Year Historical Hydro-Meteorological Disaster Records.
    </div>
  </div>
</body>
</html>"""

        return subject, plain_text, html_content

    @classmethod
    def get_smtp_config(cls) -> Dict[str, Any]:
        server = os.getenv("MAIL_SERVER", "")
        port = int(os.getenv("MAIL_PORT", 587))
        username = os.getenv("MAIL_USERNAME", "")
        sender = os.getenv("MAIL_DEFAULT_SENDER", "")
        password = os.getenv("MAIL_PASSWORD", "")
        has_password = bool(password and password.strip())

        return {
            "server": server,
            "port": port,
            "username": username,
            "sender": sender or username,
            "is_configured": bool(server and username and has_password),
            "masked_password": "••••••••••••••••" if has_password else ""
        }

    @classmethod
    def save_smtp_config(
        cls,
        server: str,
        port: int,
        username: str,
        password: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        sender = sender or username
        clean_pass = password.replace(" ", "").strip() if password else ""
        os.environ["MAIL_SERVER"] = server.strip()
        os.environ["MAIL_PORT"] = str(port)
        os.environ["MAIL_USERNAME"] = username.strip()
        if clean_pass:
            os.environ["MAIL_PASSWORD"] = clean_pass
        elif not username.strip():
            os.environ["MAIL_PASSWORD"] = ""
        os.environ["MAIL_DEFAULT_SENDER"] = sender.strip()

        # Update .env file on disk if available
        try:
            from pathlib import Path
            env_file = Path(current_app.root_path).parent / ".env"
            lines = []
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            keys_to_update = {
                "MAIL_SERVER": server.strip(),
                "MAIL_PORT": str(port),
                "MAIL_USERNAME": username.strip(),
                "MAIL_PASSWORD": password.strip() if password else os.getenv("MAIL_PASSWORD", ""),
                "MAIL_DEFAULT_SENDER": sender.strip()
            }

            updated_lines = []
            seen_keys = set()
            for line in lines:
                matched = False
                for k, v in keys_to_update.items():
                    if line.startswith(f"{k}="):
                        updated_lines.append(f"{k}={v}\n")
                        seen_keys.add(k)
                        matched = True
                        break
                if not matched:
                    updated_lines.append(line)

            for k, v in keys_to_update.items():
                if k not in seen_keys:
                    updated_lines.append(f"{k}={v}\n")

            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            logger.info("Saved SMTP configuration to backend/.env successfully.")
        except Exception as e:
            logger.warning(f"Could not persist SMTP config to .env: {str(e)}")

        return cls.get_smtp_config()

    @classmethod
    def test_smtp_connection(
        cls,
        server: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        recipient_test: str
    ) -> Dict[str, Any]:
        """
        Attempts a live SMTP connection and transmits a test probe email.
        Raises RuntimeError with specific error descriptions if it fails.
        """
        # Sanitize app password spaces
        password = password.replace(" ", "").strip() if password else ""
        subject = "✅ [MICRO-ZONE DISASTER PREDICTION SYSTEM] Live SMTP Email Gateway Test Successful"
        body = f"""
================================================================================
✅ LIVE SMTP DISASTER ALERT GATEWAY VERIFIED
================================================================================
Hello,

This is a test notification from the Human Behavior Aware Micro-Zone Disaster Prediction System.
Your SMTP Email gateway is functioning properly and ready to deliver real-time disaster alerts!

Configured Server : {server}:{port}
Authenticated User: {username}
Sender Address    : {sender}
Test Recipient    : {recipient_test}
Timestamp         : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Disaster warning emails with Human Safety Guidelines will now be delivered live to this inbox.
================================================================================
"""
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient_test

        try:
            if port == 465:
                with smtplib.SMTP_SSL(server, port, timeout=15) as smtp:
                    smtp.login(username, password)
                    smtp.sendmail(sender, [recipient_test], msg.as_string())
            else:
                with smtplib.SMTP(server, port, timeout=15) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(username, password)
                    smtp.sendmail(sender, [recipient_test], msg.as_string())

            logger.info(f"Test SMTP probe sent to {recipient_test} via {server}:{port}")
            return {
                "success": True,
                "message": f"Test email successfully delivered to {recipient_test} via {server}:{port}!"
            }
        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(
                f"Authentication failed: {str(e)}. "
                "For Gmail, please use an App Password (16 characters) generated from Google Account > Security > 2-Step Verification > App passwords."
            )
        except smtplib.SMTPConnectError as e:
            raise RuntimeError(f"Could not connect to SMTP server {server}:{port}. Check host and port.")
        except Exception as e:
            raise RuntimeError(f"SMTP connection error ({type(e).__name__}): {str(e)}")

    @classmethod
    def send_alert_email(
        cls,
        to_email: str,
        zone: Zone,
        prediction: Prediction,
        authority_name: str = "Disaster Management Authority & Citizens"
    ) -> AlertNotification:
        """
        Dispatches an emergency email alert.
        If SMTP credentials are configured, sends live email via SMTP.
        Otherwise, provides informative simulation and stores in database.
        """
        subject, plain_text, html_content = cls.format_email_content(zone, prediction)
        now = datetime.now(timezone.utc)

        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        smtp_user = os.getenv("MAIL_USERNAME")
        smtp_pass = (os.getenv("MAIL_PASSWORD") or "").replace(" ", "").strip()
        sender_email = os.getenv("MAIL_DEFAULT_SENDER", smtp_user or "alerts@micropredict.local")

        delivery_status = "DELIVERED"
        error_msg = None

        if smtp_server and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = to_email
                msg.attach(MIMEText(plain_text, "plain", "utf-8"))
                msg.attach(MIMEText(html_content, "html", "utf-8"))

                if smtp_port == 465:
                    with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
                        server.login(smtp_user, smtp_pass)
                        server.sendmail(sender_email, [to_email], msg.as_string())
                else:
                    with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(smtp_user, smtp_pass)
                        server.sendmail(sender_email, [to_email], msg.as_string())

                delivery_status = f"DELIVERED_VIA_SMTP ({smtp_server})"
                logger.info(f"[LIVE SMTP EMAIL SENT] Successfully delivered to {to_email}")
            except Exception as e:
                delivery_status = f"SMTP_FAILED: {str(e)[:80]}"
                error_msg = str(e)
                logger.warning(f"Live SMTP email delivery failed (recorded in log): {error_msg}")
        else:
            delivery_status = "SIMULATED_DELIVERED (SMTP Credentials Not Set)"
            logger.info(f"[EMAIL SIMULATION] SMTP not configured. Simulated delivery for {to_email}")

        # Save to database alert_notifications
        alert = AlertNotification(
            zone_id=zone.id,
            prediction_id=prediction.id,
            authority_name=authority_name,
            authority_code="EMAIL_ALERT",
            channel="EMAIL_DISPATCH",
            severity="CRITICAL_HIGH",
            risk_score=prediction.risk_score,
            message_body=plain_text,
            recipient_contact=to_email,
            dispatch_status=delivery_status,
            dispatched_at=now
        )
        db.session.add(alert)
        db.session.commit()
        return alert
