import os
import re
import smtplib
import logging
import json
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ── Flask Setup ─────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Setup ─────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    subject = "New KataChatBot Submission"
    body = f"""
🎯 New User Submission:

👤 Full Name: {full_name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 DOB: {dob}
🕑 Age: {age}
🌍 Country: {country}

📞 Phone: {phone}
📧 Email: {email}
💬 Referrer: {referrer}
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)

# ── /boss_analyze Endpoint ─────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        name       = data.get("memberName", "").strip()
        position   = data.get("position", "").strip()
        department = data.get("department", "").strip()
        experience = data.get("experience", "").strip()
        sector     = data.get("sector", "").strip()
        challenge  = data.get("challenge", "").strip()
        focus      = data.get("focus", "").strip()
        country    = data.get("country", "").strip()
        email      = data.get("email", "").strip()
        referrer   = data.get("referrer", "").strip()

        # Age from DOB
        day_str  = data.get("dob_day", "")
        mon_str  = data.get("dob_month", "")
        year_str = data.get("dob_year", "")
        month_map = {
            "January":1, "February":2, "March":3, "April":4, "May":5, "June":6,
            "July":7, "August":8, "September":9, "October":10, "November":11, "December":12
        }
        month = month_map.get(mon_str, 1)
        birthdate = datetime(int(year_str), int(month), int(day_str))
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        # GPT Prompt matching cee.pdf format
        prompt = f"""
You are an expert organizational psychologist.

Generate a workplace performance report for a segment of:
- Age: {age}
- Position: {position}
- Department: {department}
- Experience: {experience} years
- Sector: {sector}
- Country: {country}
- Main Challenge: {challenge}
- Development Focus: {focus}

🎯 Return the following in plain text:
1. Title (one line)
2. Introduction (2–3 lines)
3. Workplace Patterns section — show 3 areas, each with:
   - Segment %
   - Regional %
   - Global %
4. Comparison with Regional/Global Trends (2–3 lines)
5. Key Findings (3 bullet points)
6. Bar Chart style using text (e.g. █ and % labels)
7. No headings in markdown, just plain line breaks and section labels

🧠 End your response with: “End of Report.”

ALSO return a separate metrics array with 3 chart blocks:
- Each has: title, labels, values (3 items: Segment, Regional, Global)

Return ONLY the following JSON:
{{
  "analysis": "your plain report string here...",
  "metrics": [
    {{
      "title": "Communication Efficiency",
      "labels": ["Segment", "Regional", "Global"],
      "values": [75, 70, 72]
    }},
    {{
      "title": "Leadership Readiness",
      "labels": ["Segment", "Regional", "Global"],
      "values": [60, 65, 70]
    }},
    {{
      "title": "Task Completion Reliability",
      "labels": ["Segment", "Regional", "Global"],
      "values": [85, 80, 82]
    }}
  ]
}}
"""

        # GPT Call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        app.logger.debug(f"[boss_analyze] GPT raw:\n{raw}")

        # Parse safely (with fallback for comma issues)
        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            app.logger.warning("Initial JSON parsing failed. Attempting comma fix.")
            json_start = raw.find("{")
            json_end = raw.rfind("}")
            safe_json = raw[json_start:json_end+1]
            fixed_json = re.sub(r"\}\s*\{", "},{", safe_json)
            report = json.loads(fixed_json)

        # Append footer directly to the analysis field
        footer = """

<p style=\"background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;\">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.<br>
  Report results may vary even for similar profiles, as the analysis is based on live data.</em>
</p>

<p style=\"background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;\">
  <strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.
</p>
"""
        report["analysis"] += footer

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# ── Run App Locally ─────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
