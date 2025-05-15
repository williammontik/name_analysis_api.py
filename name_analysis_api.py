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

# ── Flask Setup ───────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Setup ───────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ─────────────────────────────────────────
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
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)

# ── CHILDREN ENDPOINT (Untouched) ─────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # ... your existing working children's logic ...
    pass

# ── BOSS ENDPOINT (Updated) ───────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # 1) Extract fields
        name       = data.get("memberName", "").strip()  # not used
        position   = data.get("position", "").strip()
        department = data.get("department", "").strip()
        experience = data.get("experience", "").strip()
        sector     = data.get("sector", "").strip()
        challenge  = data.get("challenge", "").strip()
        focus      = data.get("focus", "").strip()
        country    = data.get("country", "").strip()
        email      = data.get("email", "").strip()
        referrer   = data.get("referrer", "").strip()

        # 2) Parse DOB → compute age
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
        app.logger.debug(f"Computed age={age} from DOB={birthdate.date()}")

        # 3) Compose anonymized segment description
        segment = f"{age}-year-old {position} ({sector}) in {country}"

        # 4) Construct safe, anonymized GPT prompt
        prompt = f"""
You are an expert organizational psychologist.

Generate a performance insight report based on the following professional profile:

- Segment: {segment}
- Years of Experience: {experience}
- Department: {department}
- Reported Challenge: {challenge}
- Desired Development Focus: {focus}

Guidelines:
1. DO NOT use the individual’s name.
2. Speak from the perspective of trends among similar professionals.
3. Compare their segment vs. regional and global benchmarks.
4. Write a 150–200 word narrative including:
   - Top strength
   - Primary weakness
   - Three practical next steps
5. Also include 3 bar chart metric items in JSON like:
   {{
     "title": "Leadership",
     "labels": ["Segment Avg", "Regional Avg", "Global Avg"],
     "values": [72, 65, 70]
   }}

Return a single JSON object with:
- \"metrics\": [ ... ]
- \"analysis\": \"...narrative...\"
"""

        # 5) GPT-3.5 Call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        app.logger.debug(f"[boss_analyze] GPT raw: {raw}")

        # 6) Parse response
        report = json.loads(raw)

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# ── APP RUN (for local test) ──────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
