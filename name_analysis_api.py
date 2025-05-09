import os
import re
import smtplib
import random
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from dateutil import parser

app = Flask(__name__)
CORS(app)

# Logging setup
import logging
app.logger.setLevel(logging.DEBUG)

# OpenAI client setup
from openai import OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set.")
client = OpenAI(api_key=openai_api_key)

# SMTP setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
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
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception as e:
        app.logger.error("❌ EMAIL ERROR:", exc_info=e)

# Proper indentation starts here
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    # [Keep the rest of your existing analyze_name function code unchanged]
    # ... (rest of your code) ...

if __name__ == "__main__":
    app.run(debug=True)
