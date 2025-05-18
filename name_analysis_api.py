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
from openai import OpenAI
import json

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client ────────────────────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, chinese_name, gender, dob, age, phone, email_addr, country, referrer, report_html):
    """
    Sends an HTML email containing both the submission data and the generated report.
    """
    subject = "New KataChatBot Submission"
    # Build HTML message body
    html_content = f"""
    <html>
      <body>
        <h2>🎯 New User Submission:</h2>
        <p>
          <strong>👤 Full Name:</strong> {full_name}<br>
          <strong>🈶 Chinese Name:</strong> {chinese_name}<br>
          <strong>⚧️ Gender:</strong> {gender}<br>
          <strong>🎂 DOB:</strong> {dob}<br>
          <strong>🕑 Age:</strong> {age}<br>
          <strong>🌍 Country:</strong> {country}
        </p>
        <p>
          <strong>📞 Phone:</strong> {phone}<br>
          <strong>📧 Email:</strong> {email_addr}<br>
          <strong>💬 Referrer:</strong> {referrer}
        </p>
        <hr>
        <h2>📄 Personalized AI-Generated Report</h2>
        {report_html}
      </body>
    </html>
    """
    msg = MIMEText(html_content, 'html')
    msg["Subject"] = subject
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ HTML email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)

# ── /analyze_name Endpoint (Children) ─────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json(force=True)
    try:
        app.logger.info(f"[analyze_name] payload: {data}")

        # 1) Collect fields
        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email_addr   = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()
        lang         = data.get("lang", "en").lower()

        # 2) Parse DOB
        day_str   = data.get("dob_day")
        mon_str   = data.get("dob_month")
        year_str  = data.get("dob_year")
        if day_str and mon_str and year_str:
            chinese_months = {
                "一月":1, "二月":2, "三月":3, "四月":4,
                "五月":5, "六月":6, "七月":7, "八月":8,
                "九月":9, "十月":10, "十一月":11, "十二月":12
            }
            if mon_str.isdigit():
                month = int(mon_str)
            elif mon_str in chinese_months:
                month = chinese_months[mon_str]
            else:
                month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        # compute age
        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed birthdate={birthdate.date()}, age={age}")

        # 3) Build prompt based on lang
        if lang == "zh":
            prompt = f"""
请用简体中文生成一份学习模式统计报告，面向年龄 {age}、性别 {gender}、地区 {country} 的孩子。
"""
        elif lang == "tw":
            prompt = f"""
請用繁體中文生成一份學習模式統計報告，面向年齡 {age}、性別 {gender}、地區 {country} 的孩子。
"""
        else:
            prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}.
"""

        # 4) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        raw_report = response.choices[0].message.content
        analysis   = re.sub(r"<[^>]+>", "", raw_report)

        # 5) Metrics for charts (unchanged)
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        metrics = [
            {
                "title": "Learning Preferences" if lang=="en" else "學習偏好",
                "labels": ["Visual", "Auditory", "Kinesthetic"] if lang=="en" else ["視覺","聽覺","動手"],
                "values": [improved_percent, struggle_percent, 100 - improved_percent - struggle_percent]
            },
            {
                "title": "Study Habits" if lang=="en" else "學習習慣",
                "labels": ["Regular Study","Group Study","Solo Study"] if lang=="en" else ["定期學習","小組學習","獨自學習"],
                "values": [70,30,60]
            },
            {
                "title": "Math Performance" if lang=="en" else "數學表現",
                "labels": ["Algebra","Geometry"] if lang=="en" else ["代數","幾何"],
                "values": [improved_percent, 70]
            }
        ]

        # 6) Prepare HTML snippet of the report for email
        report_html = f"""
        <div style='font-family:Arial, sans-serif; font-size:14px;'>
          <pre style='white-space:pre-wrap;'>{analysis}</pre>
        </div>
        """

        # 7) Send notification email with report attached
        send_email(
            name, chinese_name, gender, birthdate.date(),
            age, phone, email_addr, country, referrer, report_html
        )

        # 8) Return API response (unchanged)
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500

# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        # ... (unchanged boss_analyze implementation) ...
        pass
    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
