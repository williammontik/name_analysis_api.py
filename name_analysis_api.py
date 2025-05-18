import os
import re
import smtplib
import random
import logging
import io
import base64
import numpy as np
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import matplotlib.pyplot as plt
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

def send_email(full_name, chinese_name, gender, dob, age,
               phone, email_addr, country, referrer,
               report_html, chart_images):
    """
    Sends a multipart HTML email with embedded chart images.
    """
    subject = "New KataChatBot Submission"
    msg = MIMEMultipart('related')
    msg["Subject"] = subject
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME

    # Build HTML body
    html = f"""
    <html><body>
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
      <h3>📊 Charts</h3>
    """
    # Attach each chart inline
    for img_b64 in chart_images:
        html += f'<img src="data:image/png;base64,{img_b64}" style="max-width:600px; margin-bottom:20px;"><br>\n'
    html += "</body></html>"

    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ HTML email with charts sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)

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

        # 3) Build prompt
        if lang == "zh":
            prompt = f"请用简体中文生成一份学习模式统计报告，面向年龄 {age}、性别 {gender}、地区 {country} 的孩子。"
        elif lang == "tw":
            prompt = f"請用繁體中文生成一份學習模式統計報告，面向年齡 {age}、性別 {gender}、地區 {country} 的孩子。"
        else:
            prompt = f"Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}."

        # 4) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        raw_report = response.choices[0].message.content
        analysis   = re.sub(r"<[^>]+>", "", raw_report)

        # 5) Metrics (unchanged)
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        metrics = [
            {
                "title": "Learning Preferences" if lang=="en" else "學習偏好",
                "labels": ["Visual","Auditory","Kinesthetic"] if lang=="en" else ["視覺","聽覺","動手"],
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
                "values": [improved_percent,70]
            }
        ]

        # 6) Generate chart images with front-end palette & gradient mimic
        palette = [
            (94/255,156/255,160/255,0.8),
            (255/255,159/255,64/255,0.8),
            (153/255,102/255,255/255,0.8),
            (75/255,192/255,192/255,0.8),
            (255/255,99/255,132/255,0.8),
            (54/255,162/255,235/255,0.8),
            (255/255,206/255,86/255,0.8),
            (201/255,203/255,207/255,0.8),
        ]
        chart_images = []
        for m in metrics:
            bar_colors = [palette[i % len(palette)] for i in range(len(m["values"]))]
            fig, ax = plt.subplots(figsize=(6,4))
            bars = ax.bar(
                m["labels"],
                m["values"],
                color=bar_colors,
                edgecolor=[(r, g, b, 1) for (r, g, b, a) in bar_colors],
                linewidth=1.5,
                width=0.6
            )
            ax.set_title(m["title"], fontsize=16)
            ax.set_ylim(0, 100)
            ax.set_ylabel("Percent")
            ax.grid(axis='y', color='#f0f0f0')
            ax.set_axisbelow(True)

            # overlay light vertical gradient
            for bar in bars:
                x, y = bar.get_x(), bar.get_height()
                w = bar.get_width()
                grad = np.linspace(0,1,256).reshape(256,1)
                ax.imshow(
                    np.concatenate([grad,grad,grad,np.zeros_like(grad)], axis=1),
                    extent=(x, x+w, 0, y),
                    aspect='auto',
                    cmap='Greys',
                    alpha=0.15,
                    origin='lower'
                )

            buf = io.BytesIO()
            fig.tight_layout()
            fig.savefig(buf, format="png", dpi=100)
            plt.close(fig)
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            chart_images.append(img_b64)

        # 7) Prepare report HTML
        report_html = f"<div style='font-family:Arial; font-size:14px;'><pre style='white-space:pre-wrap;'>{analysis}</pre></div>"

        # 8) Send email with charts
        send_email(
            name, chinese_name, gender, birthdate.date(),
            age, phone, email_addr, country, referrer,
            report_html, chart_images
        )

        # 9) Return JSON response
        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500

@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    # Unchanged boss_analyze implementation
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")
        # ... existing logic ...
    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
