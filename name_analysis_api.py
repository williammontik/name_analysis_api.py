import os
import re
import smtplib
import logging
import json
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ── Flask Setup ─────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Setup ─────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    subject = "New KataChatBot Submission"
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
        app.logger.error("❌ Email sending failed.", exc_info=True)

# ── /boss_analyze Endpoint (Managers) ───────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # 1) Extract form fields
        name       = data.get("memberName", "Unknown").strip()
        position   = data.get("position", "").strip()
        department = data.get("department", "").strip()
        experience = data.get("experience", "").strip()
        sector     = data.get("sector", "").strip()
        challenge  = data.get("challenge", "").strip()
        focus      = data.get("focus", "").strip()
        country    = data.get("country", "").strip()
        email      = data.get("email", "").strip()
        referrer   = data.get("referrer", "").strip()

        # 2) Parse DOB → compute age
        day_str  = data.get("dob_day", "")
        mon_str  = data.get("dob_month", "")
        year_str = data.get("dob_year", "")
        month_map = {
            "January":1, "February":2, "March":3, "April":4, "May":5, "June":6,
            "July":7, "August":8, "September":9, "October":10, "November":11, "December":12
        }
        month = month_map.get(mon_str, 1)
        birthdate = datetime(int(year_str), int(month), int(day_str))
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        # 3) Build GPT Prompt with structured markdown instruction
        prompt = f"""
You are an expert organizational psychologist.

Generate a workplace development report for the following anonymous segment:

- Segment Description: {age}-year-old {position} in {country}
- Department: {department}
- Sector: {sector}
- Years of Experience: {experience}
- Reported Challenge: {challenge}
- Desired Focus Area: {focus}

🔐 Guidelines:
- DO NOT mention the individual's name.
- Speak about trends for people with similar age, role, experience, and sector.
- Use a structured, professional format in markdown.

📄 Return the following sections in clear Markdown:

# Statistical Report on Workplace Patterns for {age}-year-old {sector} Professionals in {country}

## Introduction
Explain the goal of the report and how the data was generated (e.g. AI benchmarks, segment trends, regional/global analysis).

## Workplace Patterns
List 3 labeled comparisons (e.g. Communication, Problem Solving, Collaboration).
For each, include:
- Segment Average
- Regional Average
- Global Average

## Comparison Insights
Compare the group's strengths and weaknesses with benchmarks.
Describe what stands out.

## Key Findings
Write 3 specific observations about the segment’s behavior, performance, or mindset.

## Suggested Next Steps
List 3 practical recommendations based on the challenge and desired focus area.

💡 Format all % comparisons as:
- Communication:
  - Segment: 75%
  - Regional: 68%
  - Global: 72%

Return only a valid JSON object like:
{
  "metrics": [
    {
      "title": "Communication",
      "labels": ["Segment Avg", "Regional Avg", "Global Avg"],
      "values": [75, 68, 72]
    },
    {
      "title": "Problem Solving",
      "labels": ["Segment Avg", "Regional Avg", "Global Avg"],
      "values": [60, 65, 70]
    }
  ],
  "analysis": "markdown report text here"
}

Do not include any explanation or markdown outside this JSON object.
"""

        # 4) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        app.logger.debug(f"[boss_analyze] GPT raw: {raw}")

        # 5) Parse as JSON with comma-fix fallback
        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            app.logger.warning("Initial JSON parsing failed. Attempting auto-fix...")
            json_start = raw.find("{")
            json_end = raw.rfind("}")
            if json_start != -1 and json_end != -1:
                safe_json = raw[json_start:json_end+1]
                fixed_json = re.sub(r"\}\s*\{", "},{", safe_json)
                try:
                    report = json.loads(fixed_json)
                except Exception as fix_err:
                    app.logger.error("Auto-fix failed to decode JSON.", exc_info=True)
                    return jsonify({"error": "AI response is not valid JSON after auto-fix."}), 500
            else:
                return jsonify({"error": "AI response did not contain valid JSON block."}), 500

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# ── Run App Locally ─────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
