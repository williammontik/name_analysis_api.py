import os
import re
import smtplib
import random
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
from datetime import datetime

# ✅ Flask App
app = Flask(__name__)
CORS(app)

# ✅ OpenAI API Key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set.")
client = OpenAI(api_key=openai_api_key)

# ✅ Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ✅ Email Function
def send_email(full_name, chinese_name, gender, dob, age, phone, email, country):
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
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# ✅ API Endpoint
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
        day, month_str, year = dob.split()
        month = datetime.strptime(month_str, "%B").month
        birthdate = datetime(int(year), month, int(day))
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except Exception as e:
        print(f"❌ Error calculating age: {e}")
        age = "Unknown"

    # ✅ Send email
    try:
        send_email(name, chinese_name, gender, dob, age, phone, email, country)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    # ✅ Randomized stats
    improved_percent = random.randint(65, 78)
    struggle_percent = random.randint(37, 48)

    # ✅ OpenAI analysis prompt
    prompt = f"""
You are an educational advisor AI trained on global child development data. Generate a warm and insightful learning advice message for a parent.

Child Profile:
- Full Name: {name}
- Chinese Name: {chinese_name}
- Gender: {gender}
- Date of Birth: {dob}
- Parent's Phone: {phone}
- Parent's Email: {email}
- Country: {country}
- Age: {age}

Based on developmental patterns among {age}-year-old {gender.lower()} children in {country}, AI analysis suggests:

📊 Insights from similar profiles:
- About {improved_percent}% of children with personalized early support saw major improvements in focus, creativity, and emotional wellbeing.
- However, nearly {struggle_percent}% of children without tailored help struggled with learning fatigue and declining motivation—especially during age shifts like {age - 1} to {age}.

Recommendations:
- Provide hands-on learning experiences
- Encourage expressive outlets like storytelling, music, or drawing
- Reinforce focus through daily routines and play-based challenges
- Introduce cultural learning based on {country}'s traditions

Final Tip:
To get highly personalized strategies and a spot-on tutor for your child’s evolving character, connect with a real human from our team. Chat with us on Telegram at @katachat007. A precise plan today can shape a confident learner tomorrow.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ✅ Clean output
    clean = re.sub(r"<[^>]+>", "", analysis)
    return jsonify({"analysis": clean})
