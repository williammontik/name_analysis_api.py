import os
import re
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
from datetime import datetime

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)

# ✅ OpenAI API Key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set in environment variables.")
client = OpenAI(api_key=openai_api_key)

# ✅ Email SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # ✅ Secure method

# ✅ Function to send email
def send_email(full_name, chinese_name, gender, dob, age, phone, email, country):
    subject = "New KataChatBot User Submission"
    body = f"""
🎯 New User Submission:

👤 Full Legal Name of Child: {full_name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 Date of Birth: {dob}
🎯 Age: {age} years old
🌍 Country: {country}

📞 Parent's Phone Number: {phone}
📧 Parent's Email Address: {email}
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
    except Exception as e:
        print(f"Error sending email: {e}")

# ✅ Main API Endpoint
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    name = data.get("name", "").strip()
    chinese_name = data.get("chineseName", "").strip()
    gender = data.get("gender", "").strip()
    dob = data.get("dob", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    country = data.get("country", "").strip()

    if not name:
        return jsonify({"error": "No name provided"}), 400

    # ✅ Calculate age
    try:
        dob_parts = dob.split()
        day = int(dob_parts[0])
        month = datetime.strptime(dob_parts[1], "%B").month
        year = int(dob_parts[2])
        birthdate = datetime(year, month, day)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except Exception as e:
        print(f"Error parsing DOB: {e}")
        age = "Unknown"

    # ✅ Send email
    try:
        send_email(name, chinese_name, gender, dob, age, phone, email, country)
    except Exception as e:
        print(f"Failed to send email: {e}")

    # ✅ OpenAI advice (name only)
    user_message = (
        f"Please provide professional educational advice for a child named '{name}'. "
        f"This child is {age} years old and comes from {country}. "
        f"Only use this background information. Do not reference the name analysis directly."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        analysis_text = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    clean_text = re.sub(r"(?i)<br\s*/?>", "\n", analysis_text)
    clean_text = re.sub(r"<[^>]+>", "", clean_text)

    return jsonify({"analysis": clean_text})
