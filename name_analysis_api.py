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

# ✅ Email Function (Updated to include Referrer)
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
    chinese_name = data.get("chinese_name", "").strip()
    gender = data.get("gender", "").strip()
    dob = data.get("dob", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    country = data.get("country", "").strip()
    referrer = data.get("referrer", "").strip()

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

    # ✅ Send email with the referrer included
    try:
        send_email(name, chinese_name, gender, dob, age, phone, email, country, referrer)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    # ✅ Smarter randomized stats
    base_improve = random.randint(65, 80)
    base_struggle = random.randint(30, 45)
    if base_struggle >= base_improve - 5:
        base_struggle = base_improve - random.randint(10, 15)
    improved_percent = round(base_improve / 5) * 5
    struggle_percent = round(base_struggle / 5) * 5

    # ✅ OpenAI analysis
    prompt = f"""
You are an elite educational advisor AI trained on deep global datasets about children’s development and academic psychology. Speak warmly and emotionally — like a trusted friend who understands parental concerns. Mix data, storytelling, and practical advice.

Child Profile:
- Full Name: {name}
- Chinese Name: {chinese_name}
- Gender: {gender}
- Date of Birth: {dob}
- Parent's Phone: {phone}
- Parent's Email: {email}
- Country: {country}
- Age: {age}

AI Insight:
Children aged {age} in {country} often face invisible crossroads — some grow curious and focused, while others start showing signs of detachment or learning fatigue.

📊 Our AI has identified that:
- Around {improved_percent}% of children in this age/gender/location profile who got timely, personalized help experienced a transformation: greater confidence, better attention span, and joyful participation in school.
- But about {struggle_percent}% of children who didn’t get targeted support slipped into patterns of frustration, resistance to learning, emotional withdrawal — sometimes unnoticed until it became serious.

💡 This is not fear — it’s foresight.

Advice:
1. Spark Curiosity: Let them explore through art, music, nature, or experiments — things that make them ask more questions.
2. Give Structure: Routine builds safety. Focus games, light challenges, and time-blocked play can reshape attention span.
3. Emotional Coaching: Teach naming feelings, and encourage expression — children who feel seen will stay open to learning.

In {country}, we’ve also seen cultural tools (like traditional stories, values of diligence and filial piety, or expressive arts) play a major role in turning kids around. Use what’s already meaningful in your community.

Final Advice:
Your child’s character today is only one version of their future. The biggest danger is assuming things will fix themselves.

That’s why we strongly recommend you speak directly to one of our real human learning specialists at @katachat007 (Telegram). We’ll zoom into your child’s specific personality, recommend the right type of tutor, and guide you through this age band with precision and heart.

Your child deserves more than average answers. Let’s build the learning path that fits them best — together.
"""

    try:
        response = client.chat.completions.create(
            model="childpp2",  # Use your fine-tuned model here
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ✅ Clean output
    clean = re.sub(r"<[^>]+>", "", analysis)
    return jsonify({"analysis": clean})

if __name__ == "__main__":
    app.run(debug=True)
