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

def send_email(html_body):
    """
    Sends an HTML email containing the full submission and report.
    """
    subject = "New KataChatBot Submission"
    msg = MIMEText(html_body, 'html')
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

        # 3) Build prompt (unchanged) …
        # 4) Call OpenAI & strip HTML tags to get `analysis` (unchanged) …
        # 5) Generate metrics (unchanged) …
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        if lang == "en":
            titles = ["Learning Preferences", "Study Habits", "Math Performance"]
            labels = [
                ["Visual","Auditory","Kinesthetic"],
                ["Regular Study","Group Study","Solo Study"],
                ["Algebra","Geometry"]
            ]
        elif lang == "zh":
            titles = ["学习偏好", "学习习惯", "数学表现"]
            labels = [
                ["视觉","听觉","动手"],
                ["定期学习","小组学习","独自学习"],
                ["代数","几何"]
            ]
        else:  # tw
            titles = ["學習偏好", "學習習慣", "數學表現"]
            labels = [
                ["視覺","聽覺","動手"],
                ["定期學習","小組學習","獨自學習"],
                ["代數","幾何"]
            ]

        metrics = [
            {"title": titles[0], "labels": labels[0],
             "values": [improved_percent, struggle_percent, 100 - improved_percent - struggle_percent]},
            {"title": titles[1], "labels": labels[1], "values": [70,30,60]},
            {"title": titles[2], "labels": labels[2], "values": [improved_percent,70]}
        ]

        # 6) Build the HTML email body with inline‐CSS bar charts
        palette = ["#5E9CA0","#FF9F40","#9966FF","#4BC0C0","#FF6384","#36A2EB","#FFCE56","#C9CBCF"]
        html = [f"""<html><body style="font-family:sans-serif;color:#333">
<h2>🎯 New User Submission:</h2>
<p>
👤 <strong>Full Name:</strong> {name}<br>
🈶 <strong>Chinese Name:</strong> {chinese_name}<br>
⚧️ <strong>Gender:</strong> {gender}<br>
🎂 <strong>DOB:</strong> {birthdate.date()}<br>
🕑 <strong>Age:</strong> {age}<br>
🌍 <strong>Country:</strong> {country}<br>
📞 <strong>Phone:</strong> {phone}<br>
📧 <strong>Email:</strong> {email_addr}<br>
💬 <strong>Referrer:</strong> {referrer}
</p>
<hr>
<h2>📊 AI-Generated Report</h2>
<pre style="font-size:14px;white-space:pre-wrap">{analysis}</pre>
<hr>
<h2>📈 Metrics</h2>
"""]
        for m in metrics:
            html.append(f"<h3>{m['title']}</h3>")
            for i, (lbl, val) in enumerate(zip(m["labels"], m["values"])):
                color = palette[i % len(palette)]
                html.append(f"""
<div style="margin:4px 0; line-height:1.4">
  {lbl}: 
  <span style="
    display:inline-block;
    width:{max(val,0)}%;
    height:12px;
    background:{color};
    border-radius:4px;
    vertical-align:middle;
  "></span>
  &nbsp;{val}%
</div>
""")
        html.append("</body></html>")
        email_html = "".join(html)

        # 7) Send HTML email
        send_email(email_html)

        # 8) Return the same JSON response you already had
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500


# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    # unchanged boss_analyze…
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")
        # … your existing boss_analyze logic …
    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
