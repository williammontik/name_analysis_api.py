import os
import io
import base64
import logging
import random
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dateutil import parser
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI setup ────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set.")
client = OpenAI(api_key=OPENAI_API_KEY)

# ── SMTP setup ──────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    subject = "New KataChatBot User Submission"
    body = f"""
🎯 New User Submission:

👤 Full Legal Name: {full_name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 Date of Birth: {dob}
🎯 Age: {age} years old
🌍 Country: {country}

📞 Phone: {phone}
📧 Email: {email}
💬 Referrer: {referrer}
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]   = SMTP_USERNAME
    msg["To"]     = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.error("❌ EMAIL ERROR", exc_info=True)

# ── Simple SVG animation stub ───────────────────────────────
def generate_animation(data):
    """
    Returns an inline SVG animation (pulsing circle) as a string.
    You can replace this with any SVG/GIF/HTML5 <canvas> animation you like.
    """
    svg = """
<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="20" fill="#3498db">
    <animate attributeName="r"
             from="20" to="50"
             dur="1.5s"
             repeatCount="indefinite"
             values="20;50;20"
             keyTimes="0;0.5;1" />
  </circle>
</svg>
"""
    return svg.strip()

# ── Main endpoint ───────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # 1) Parse input
    data = request.get_json() if request.is_json else request.form
    name         = data.get("name","").strip()
    chinese_name = data.get("chinese_name","").strip()
    gender       = data.get("gender","").strip()
    phone        = data.get("phone","").strip()
    email_addr   = data.get("email","").strip()
    country      = data.get("country","").strip()
    referrer     = data.get("referrer","").strip()

    # 2) Build & parse DOB
    day, mon, year = data.get("dob_day"), data.get("dob_month"), data.get("dob_year")
    if day and mon and year:
        dob_raw = f"{day} {mon} {year}"
    else:
        dob_raw = data.get("dob","").strip()

    try:
        parts = dob_raw.split()
        if len(parts) == 3:
            d, m_str, y = parts
            m = datetime.strptime(m_str, "%B").month
            bd = datetime(int(y), m, int(d))
        else:
            bd = parser.parse(dob_raw, dayfirst=True)
        today = datetime.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        app.logger.error(f"Error calculating age from {dob_raw!r}", exc_info=True)
        age = "Unknown"

    # 3) Send email
    send_email(name, chinese_name, gender, dob_raw, age, phone, email_addr, country, referrer)

    # 4) AI analysis
    prompt = f"Generate a concise statistical report for a {age}-year-old {gender} in {country}."
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        analysis = resp.choices[0].message.content
    except Exception:
        app.logger.error("OpenAI error", exc_info=True)
        analysis = "⚠️ AI analysis currently unavailable."

    clean = re.sub(r"<[^>]+>", "", analysis)

    # 5) Generate animation safely
    try:
        animation = generate_animation(data)
    except Exception:
        app.logger.error("Animation generation failed", exc_info=True)
        animation = None

    # 6) Return JSON
    return jsonify({
        "age_computed": age,
        "analysis": clean,
        "animation": animation
    })

if __name__ == "__main__":
    app.run(debug=True)
