import os
import re
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
import openai
from flask_cors import CORS
from datetime import datetime

# ✅ Flask App
app = Flask(__name__)
CORS(app)

# ✅ OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    # ✅ Calculate Age
    try:
        day, month_str, year = dob.split()
        month = datetime.strptime(month_str, "%B").month
        birthdate = datetime(int(year), month, int(day))
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except Exception as e:
        print(f"❌ Error calculating age: {e}")
        age = "Unknown"

    # ✅ Send Email
    try:
        send_email(name, chinese_name, gender, dob, age, phone, email, country)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    # ✅ OpenAI Prompt
    prompt = f"""
You are an educational advisor AI trained on global child development data. Generate a warm and insightful learning advice message for a parent.

👤 Full Legal Name (English): {name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 Date of Birth: {dob}
📞 Parent's Phone: {phone}
📧 Parent's Email: {email}
🌍 Country: {country}

🎉 Your Personalized AI Analysis:

Based on AI geographical insights and developmental trends among {age}-year-old {gender.lower()} children in {country}, our system identified key learning approaches that resonate with similar profiles in your area.

Please include:
- Age-appropriate advice
- Localized and cultural recommendations
- Suggestions for creativity, focus, and cognitive growth

🪄 Final Advice:
✨ If you’d like a very tailored and updated approach for how your child can improve even better — including spotting the right tutor who matches your child’s evolving character and age band — we strongly recommend speaking with our real human support team.

Children’s personalities shift over time, and so should their learning methods. For highly personalized and insightful guidance, chat with us directly on Telegram at @katachat007.

Let’s help your child shine in the most precise and creative way possible. 🌟
"""

    # ✅ OpenAI API Call with Traceback Logging
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content.strip()
        if not analysis:
            print("❌ GPT response was empty.")
            analysis = "⚠️ No analysis could be generated at this time."
    except Exception as e:
        import traceback
        print("❌ OpenAI error:", e)
        traceback.print_exc()
        analysis = f"⚠️ OpenAI system error: {str(e)}"

    clean = re.sub(r"<[^>]+>", "", analysis)
    return jsonify({"analysis": clean})
