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

# ✅ OpenAI v1.x Client Setup
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
You are an expert educational advisor AI trained on global child development data. Use deep emotional tone, vivid storytelling, and motivational reasoning to give personalized learning advice for a parent.

Use this information:
👤 Full Name: {name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 Date of Birth: {dob}
📞 Parent's Phone: {phone}
📧 Parent's Email: {email}
🌍 Country: {country}
🎯 Age: {age}

🎉 Your Personalized AI Analysis:

---

💡 **Local Insight:**

Based on educational data and developmental trends among {age}-year-old {gender.lower()} children in {country}, we found patterns that show how your child compares to others in the same age, gender, and cultural environment.

📊 Among children with a similar profile:
- ✅ Over 68% who received early, tailored support experienced major boosts in confidence, focus, and creativity within 3 to 6 months.
- ⚠️ However, around 42% of children without this guidance showed signs of emotional withdrawal, learning fatigue, and even behavioral friction — especially during key transition phases like age {age - 1} to {age}.

These aren’t just numbers — they reflect real children’s struggles. Often, the difference is whether someone cared enough to act early.

---

🎨 **Creative & Cognitive Growth Suggestions:**

Your child needs more than general schooling. Consider:
- 🎨 Exploring expressive outlets (music, storytelling, visual arts)
- 🔍 Introducing small research tasks or challenges to sharpen focus
- 🧘 Practicing mindfulness or light physical activities to improve discipline and emotional clarity

If you're in {country}, it's also meaningful to weave local culture into their learning. For example:
- Philippine children often thrive through cultural music, traditional stories, and local values of resilience
- In Taiwan or Singapore, dual-language storytelling and community projects have shown excellent developmental benefits

---

🪄 **Final Advice:**

Every child is a moving star. Their personality, talents, and motivation evolve with age.

✨ To make sure you're not relying on guesswork, we strongly recommend chatting with a real human mentor who understands education deeply. Our team is on Telegram at @katachat007, ready to give pinpoint suggestions — including finding the **right tutor match** for your child’s current (and future) learning profile.

Let’s not leave your child’s potential to chance. Together, we can build a plan that truly fits — and makes them shine in the most precise, joyful way possible. 🌱
"""

    # ✅ OpenAI API Call with Error Trace
    try:
        response = client.chat.completions.create(
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
