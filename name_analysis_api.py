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
from openai import OpenAI
import json

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

def send_email(full_name, chinese_name, gender, dob, age,
               phone, email, country, referrer,
               analysis, metrics):
    subject = "New KataChatBot Submission"
    # Build the email body with form fields + fenced JSON block
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

📊 Analysis:
{analysis}

📈 Metrics (raw JSON):
```json
{json.dumps(metrics, ensure_ascii=False, indent=2)}
