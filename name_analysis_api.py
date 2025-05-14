import os
import re
import smtplib
import random
import logging
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
import json

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from openai import OpenAI

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client ────────────────────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, chinese_name, gender, dob, age, phone, email_addr, country, referrer):
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
📧 Email: {email_addr}
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

# ── Children Analysis Endpoint ────────────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    try:
        # 1) Collect fields
        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email_addr   = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()
        lang         = data.get("lang", "en").lower()

        # 2) Parse DOB
        day_str  = data.get("dob_day")
        mon_str  = data.get("dob_month")
        year_str = data.get("dob_year")
        if day_str and mon_str and year_str:
            chinese_months = {
                "一月":1, "二月":2, "三月":3, "四月":4,
                "五月":5, "六月":6, "七月":7, "八月":8,
                "九月":9, "十月":10, "十一月":11,"十二月":12
            }
            if mon_str.isdigit():
                month = int(mon_str)
            elif mon_str in chinese_months:
                month = chinese_months[mon_str]
            else:
                month = datetime.strptime(mon_str, "%B").month

            day  = int(day_str)
            year = int(year_str)
            birthdate = datetime(year, month, day)
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        # 3) Compute age
        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed birthdate={birthdate.date()}, age={age}")

        # 4) Email notification
        send_email(name, chinese_name, gender, birthdate.date(), age, phone, email_addr, country, referrer)

        # 5) Build prompt for children (existing logic)…
        #    [Your existing prompt construction and OpenAI call here]

        # 6) Call OpenAI & parse metrics (existing logic)…
        #    [Your existing code that returns JSON]

        # For brevity, returning a simple placeholder here:
        return jsonify({
            "age_computed": age,
            "analysis":     "Original children analysis output",
            "metrics":      []
        })

    except Exception as e:
        app.logger.error("❌ Exception in /analyze_name", exc_info=True)
        return jsonify({ "error": str(e) }), 500

# ── Boss Analysis Endpoint ──────────────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST", "OPTIONS"])
@cross_origin()
def boss_analyze():
    data = request.get_json()
    app.logger.info(f"Boss payload: {data}")

    # 1) Build the coaching prompt
    prompt = f'''
You are a friendly leadership coach. Given the following data about a team member:
- Name: {data["memberName"]}
- Role: {data["position"]}
- Department: {data.get("department", "N/A")}
- Years of Experience: {data["experience"]}
- Key Challenge: {data["challenge"]}
- Preferred Focus: {data["focus"]}
- Country: {data["country"]}

Please output ONLY valid JSON with two fields:
1. "metrics": an array of objects. Each object must have:
    - "title": one of ["Leadership","Collaboration","Decision-Making","Communication","Sales Acumen"]
    - "labels": identical to title in a list
    - "values": a single number (0–100)

2. "analysis": a brief, friendly & motivating paragraph (2–3 sentences) praising strengths and suggesting one next step.
'''

    # 2) Call OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content

    # 3) Parse the JSON the model returned
    try:
        result = json.loads(content)
    except Exception:
        app.logger.error("Failed to parse JSON from OpenAI:", exc_info=True)
        return jsonify({"error": "Invalid JSON from AI"}), 500

    # 4) Return the AI’s metrics + analysis
    return jsonify(result)

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
