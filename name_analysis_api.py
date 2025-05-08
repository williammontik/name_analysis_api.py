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

# set logging level to DEBUG
import logging
app.logger.setLevel(logging.DEBUG)

# OpenAI client setup (if you use it)
from openai import OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set.")
client = OpenAI(api_key=openai_api_key)

# SMTP setup
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
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
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception as e:
        app.logger.error("❌ EMAIL ERROR:", exc_info=e)

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    # collect fields
    name         = data.get("name", "").strip()
    chinese_name = data.get("chinese_name", "").strip()
    gender       = data.get("gender", "").strip()
    phone        = data.get("phone", "").strip()
    email        = data.get("email", "").strip()
    country      = data.get("country", "").strip()
    referrer     = data.get("referrer", "").strip()

    # build dob input from either combined or separate fields
    day   = data.get("dob_day")
    mon   = data.get("dob_month")
    year  = data.get("dob_year")
    if day and mon and year:
        dob_input = f"{day} {mon} {year}"
    else:
        dob_input = data.get("dob", "").strip()

    app.logger.debug(f"Raw DOB input: {dob_input!r}")

    # parse and compute age
    try:
        # try strict "DD Month YYYY" first
        parts = dob_input.split()
        if len(parts) == 3:
            d, mon_str, y = parts
            month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(y), month, int(d))
        else:
            # fallback to dateutil parser for more flexibility
            birthdate = parser.parse(dob_input, dayfirst=True)

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed age: {age!r}")
    except Exception as e:
        app.logger.error(f"Error calculating age from {dob_input!r}", exc_info=e)
        age = "Unknown"

    # send notification email
    try:
        send_email(name, chinese_name, gender, dob_input, age, phone, email, country, referrer)
    except Exception as e:
        app.logger.error("❌ Failed to send email:", exc_info=e)

    # prepare prompt and call OpenAI
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

1. [First Metric Name]:
[Category 1] |||||||| XX%
[Category 2] |||||||||||| YY%
[Category 3] |||| ZZ%

2. [Second Metric Name]:
- Item A: XX%
- Item B: YY%
- Item C: ZZ%

3. [Third Metric Name]:
{gender} performance in [subject]:
- Area 1: XX% (Regional: YY%)
- Area 2: XX% (Global: YY%)

Regional Comparisons:
- Metric A: {country} XX% vs Region YY%
- Metric B: {country} XX% vs Global YY%

Top 3 Statistical Findings:
1. Finding 1 (data-supported)
2. Finding 2 (data-supported)
3. Finding 3 (data-supported)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        app.logger.error("OpenAI error", exc_info=e)
        return jsonify({"error": str(e)}), 500

    clean = re.sub(r"<[^>]+>", "", analysis)

    return jsonify({
        "age_computed": age,
        "analysis": clean
    })

if __name__ == "__main__":
    app.run(debug=True)
