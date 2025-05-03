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
        age_str = f"{age}-year-old"
        age_range = f"{age - 1} to {age}"
    except Exception as e:
        print(f"❌ Error calculating age: {e}")
        age = "Unknown"
        age_str = "children"
        age_range = "early childhood"

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

Based on AI geographical insights and developmental trends among {age_str} {gender.lower()} children in {country}, our system identified key learning approaches that resonate with similar profiles in your area.

Please include:
- Age-appropriate educational advice
- Localized and cultural recommendations
- Suggestions for creativity, focus, and cognitive growth

📊 Important AI Insight from Similar Profiles:

Our AI analyzed developmental trends among children in the same age group, gender, and region as {name}. It uncovered patterns that show how early support can shape outcomes dramatically.

- ✅ A significant proportion of children who received timely, personalized learning support demonstrated noticeable gains in confidence, creativity, and attention span within just a few months.
- ⚠️ On the other hand, a worrying percentage of children who lacked targeted help showed declining interest in learning, especially during key transition years like {age_range}.

These insights reflect the reality of many families — where delayed action led to unnecessary academic or emotional struggles.

🎯 Every child is unique, but trends like these remind us how much timely care can influence a child's long-term growth.

🪄 Final Advice:
✨ That’s why we strongly encourage you to take one more step — talk to a real human from our educational team on Telegram at @katachat007.

Let’s zoom in on your child’s character and evolving needs. Together, we’ll help them thrive with precise strategies, the right tutor, and tools designed just for them.

Your child deserves this clarity — and we’re here to walk that journey with you. 🌱
"""

    # ✅ DEBUG Prompt Output
    print("📝 Prompt sent to OpenAI:")
    print(prompt)

    # ✅ OpenAI API Call + Safe Output Handling
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.9,
            messages=[{"role": "user", "content": prompt}]
        )
        message = response.choices[0].message.content.strip()
        if not message:
            print("❌ GPT response is empty.")
            message = "⚠️ No analysis could be generated at this time."
    except Exception as e:
        print("❌ OpenAI error:", e)
        message = "⚠️ No analysis could be generated due to a system error."

    clean = re.sub(r"<[^>]+>", "", message)
    return jsonify({"analysis": clean})
