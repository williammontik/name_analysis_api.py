import os
import re
import smtplib
import random
import logging
import json
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

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
        # … (your full existing children logic here, unchanged) …
        # At the end:
        return jsonify({
            "age_computed": age,
            "analysis":     analysis,
            "metrics":      metrics
        })
    except Exception as e:
        app.logger.error("❌ Exception in /analyze_name", exc_info=True)
        return jsonify({"error": str(e)}), 500

# ── Boss Analysis Endpoint ──────────────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST", "OPTIONS"])
@cross_origin()
def boss_analyze():
