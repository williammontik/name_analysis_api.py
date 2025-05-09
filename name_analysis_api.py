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

# ── Flask & Logging Setup ────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client Setup ─────────────────────────────────────────────────
from openai import OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ────────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; email sending may fail.")

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    """Send a notification email to yourself with the submission details."""
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
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.error("❌ Failed to send email:", exc_info=True)


# ── Name Analysis Endpoint ────────────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    try:
        # 1) Collect fields
        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email        = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()

        # 2) Reconstruct DOB string
        day  = data.get("dob_day")
        mon  = data.get("dob_month")
        year = data.get("dob_year")
        if day and mon and year:
            dob_input = f"{day} {mon} {year}"
        else:
            dob_input = data.get("dob", "").strip()

        app.logger.debug(f"Raw DOB input: {dob_input!r}")

        # 3) Parse birthdate & calculate age
        parts = dob_input.split()
        if len(parts) == 3:
            d, mon_str, y = parts
            month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(y), month, int(d))
        else:
            birthdate = parser.parse(dob_input, dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed age: {age!r}")

        # 4) Send email notification (optional)
        send_email(name, chinese_name, gender, dob_input, age, phone, email, country, referrer)

        # 5) Build your prompt
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {gender} in {country}.

Requirements:
1. Present only factual data in percentage/numerical form
2. Include 3 text-based bar charts using markdown
3. Compare with regional/global averages
4. Highlight 3 key statistical findings
5. No personalized advice or recommendations
6. Use academic, data-focused language

Format:
**Learning Patterns Analysis for {age}-year-old {gender}s in {country}**

1. Learning Preferences:
Visual |||||| {improved_percent}%
Auditory |||||||||| {struggle_percent}%
Kinesthetic |||| 5%

2. Study Habits:
- Regular Study Hours: 70%
- Group Study Sessions: 30%
- Prefer Studying Alone: 60%

3. STEM Learning:
{gender} performance in Mathematics:
- Algebra: {improved_percent}% (Regional: 75%)
- Geometry: 70% (Global: 60%)

Regional Comparisons:
- Study Hours: {country} 70% vs Region 60%
- Group Study: {country} 30% vs Global 40%

Top 3 Statistical Findings:
1. 55% of {age}-year-old {gender}s in {country} prefer auditory learning, above global 45%.
2. Singaporean females outperform averages in Algebra ({improved_percent}% vs 75% vs 60%).
3. 70% maintain regular study hours, showing strong commitment.
"""

        # 6) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content

        # 7) Clean HTML tags and return
        clean = re.sub(r"<[^>]+>", "", analysis)
        return jsonify({"age_computed": age, "analysis": clean})

    except Exception as e:
        # Log full traceback to your Render logs
        app.logger.error("❌ Exception in /analyze_name", exc_info=True)
        # Return the error message as JSON
        return jsonify({"error": str(e)}), 500


# ── Run the App Locally ───────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
