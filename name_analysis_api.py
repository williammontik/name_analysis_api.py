14th May afternoon GitHub 


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

# ── Analysis Endpoint ────────────────────────────────────────────────────────
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
        lang         = data.get("lang", "en").lower()

        # 2) Parse DOB
        day_str   = data.get("dob_day")
        mon_str   = data.get("dob_month")
        year_str  = data.get("dob_year")
        if day_str and mon_str and year_str:
            mon_key = mon_str.strip()
            chinese_months = {
                "一月":1, "二月":2, "三月":3, "四月":4,
                "五月":5, "六月":6, "七月":7, "八月":8,
                "九月":9, "十月":10, "十一月":11,"十二月":12
            }
            if mon_key.isdigit():
                month = int(mon_key)
            elif mon_key in chinese_months:
                month = chinese_months[mon_key]
            else:
                month = datetime.strptime(mon_key, "%B").month

            day  = int(day_str)
            year = int(year_str)
            birthdate = datetime(year, month, day)
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)

        # compute age
        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed birthdate={birthdate.date()}, age={age}")

        # 3) Email notification
        send_email(name, chinese_name, gender, birthdate.date(), age, phone, email, country, referrer)

        # 4) Build prompt based on lang
        if lang == "zh":
            prompt = f"""
请用简体中文生成一份学习模式统计报告，面向年龄 {age}、性别 {gender}、地区 {country} 的孩子。
要求：
1. 只给出百分比数据
2. 在文本中用 Markdown 语法给出 3 个“柱状图”示例
3. 对比区域/全球趋势
4. 突出 3 个关键发现
5. 不要个性化建议
6. 学术风格
"""
        elif lang == "tw":
            prompt = f"""
請用繁體中文生成一份學習模式統計報告，面向年齡 {age}、性別 {gender}、地區 {country} 的孩子。
要求：
1. 只給出百分比數據
2. 在文本中用 Markdown 語法給出 3 個「柱狀圖」示例
3. 比較區域／全球趨勢
4. 突出 3 個關鍵發現
5. 不要個性化建議
6. 學術風格
"""
        else:
            prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}.
Requirements:
1. Only factual percentages
2. Include 3 markdown bar‐charts
3. Compare regional/global
4. Highlight 3 key findings
5. No personalized advice
6. Academic style
"""

        # 5) Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = re.sub(r"<[^>]+>", "", response.choices[0].message.content)

        # 6) Metrics for charts
        base_improve  = random.randint(65, 80)
        base_struggle = random.randint(30, 45)
        if base_struggle >= base_improve - 5:
            base_struggle = base_improve - random.randint(10, 15)
        improved_percent  = round(base_improve / 5) * 5
        struggle_percent  = round(base_struggle / 5) * 5

        if lang == "tw":
            metrics = [
                {
                    "title":  "學習偏好",
                    "labels": ["視覺", "聽覺", "動手"],
                    "values": [improved_percent, struggle_percent, 5]
                },
                {
                    "title":  "學習習慣",
                    "labels": ["定期學習", "小組學習", "獨自學習"],
                    "values": [70, 30, 60]
                },
                {
                    "title":  "數學表現",
                    "labels": ["代數", "幾何"],
                    "values": [improved_percent, 70]
                }
            ]
        else:
            metrics = [
                {
                    "title":  "Learning Preferences",
                    "labels": ["Visual", "Auditory", "Kinesthetic"],
                    "values": [improved_percent, struggle_percent, 5]
                },
                {
                    "title":  "Study Habits",
                    "labels": ["Regular Study", "Group Study", "Alone"],
                    "values": [70, 30, 60]
                },
                {
                    "title":  "Math Performance",
                    "labels": ["Algebra", "Geometry"],
                    "values": [improved_percent, 70]
                }
            ]

        # 7) Return combined JSON
        return jsonify({
            "age_computed": age,
            "analysis":     analysis,
            "metrics":      metrics
        })

    except Exception as e:
        app.logger.error("❌ Exception in /analyze_name", exc_info=True)
        return jsonify({ "error": str(e) }), 500

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
