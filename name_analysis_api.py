import os
import re
import smtplib
import random
import logging
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client ────────────────────────────────────────────────────────────
from openai import OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup (for your notification email) ─────────────────────────────────
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

# ── Analysis Endpoint ────────────────────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    try:
        # 1) Collect fields
        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email        = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()

        # 2) Reconstruct DOB
        day  = data.get("dob_day")
        mon  = data.get("dob_month")
        year = data.get("dob_year")
        if day and mon and year:
            dob_input = f"{day} {mon} {year}"
        else:
            dob_input = data.get("dob", "").strip()

        app.logger.debug(f"DOB input: {dob_input!r}")

        # 3) Parse birthdate & compute age
        parts = dob_input.split()
        if len(parts) == 3:
            d, mon_str, y = parts
            month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(y), month, int(d))
        else:
            birthdate = parser.parse(dob_input, dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed age: {age}")

        # 4) Notify by email (optional)
        send_email(name, chinese_name, gender, dob_input, age, phone, email, country, referrer)

        # 5) Generate percentages for charts
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        # 6) Build your AI prompt
        prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}.
Requirements:
1. Only factual percentages
2. Include 3 markdown bar‐charts
3. Compare regional/global
4. Highlight 3 key findings
5. No personalized advice
6. Academic style
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content
        clean = re.sub(r"<[^>]+>", "", analysis)

        # 7) Build structured metrics for Chart.js
        metrics = [
            {
                "title":  "Learning Preferences",
                "labels": ["Visual", "Auditory", "Kinesthetic"],
                "values": [improved_percent, struggle_percent, 5]
            },
            {
                "title":  "Study Habits",
                "labels": ["Regular Study", "Group Study", "Alone"],
                "values": [70, 30, 60]
            },
            {
                "title":  "Math Performance",
                "labels": ["Algebra", "Geometry"],
                "values": [improved_percent, 70]
            }
        ]

        # 8) Return combined JSON
        return jsonify({
            "age_computed": age,
            "analysis":     clean,
            "metrics":      metrics
        })

    except Exception as e:
        app.logger.error("❌ Exception in /analyze_name", exc_info=True)
        return jsonify({ "error": str(e) }), 500

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
