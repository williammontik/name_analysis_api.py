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

# ── Flask App Setup ───────────────────────────────
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Setup ──────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Email Setup ──────────────────────────────
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
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception:
        app.logger.error("❌ Email sending failed.", exc_info=True)

# ── CHILDREN ENDPOINT (/analyze_name) ─────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json(force=True)
    try:
        app.logger.info(f"[analyze_name] payload: {data}")

        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email        = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()
        lang         = data.get("lang", "en").lower()

        day_str  = data.get("dob_day")
        mon_str  = data.get("dob_month")
        year_str = data.get("dob_year")

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
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        send_email(name, chinese_name, gender, birthdate.date(), age, phone, email, country, referrer)

        if lang == "zh":
            prompt = f"""请用简体中文生成一份学习模式统计报告，面向年龄 {age}、性别 {gender}、地区 {country} 的孩子。
要求：
1. 只给出百分比数据
2. 在文本中用 Markdown 语法给出 3 个“柱状图”示例
3. 对比区域/全球趋势
4. 突出 3 个关键发现
5. 不要个性化建议
6. 学术风格"""
        elif lang == "tw":
            prompt = f"""請用繁體中文生成一份學習模式統計報告，面向年齡 {age}、性別 {gender}、地區 {country} 的孩子。
要求：
1. 只給出百分比數據
2. 在文本中用 Markdown 语法給出 3 個「柱狀圖」示例
3. 比較區域／全球趨勢
4. 突出 3 個關鍵發現
5. 不要個性化建議
6. 學術風格"""
        else:
            prompt = f"""Generate a statistical report on learning patterns for children aged {age}, gender {gender}, in {country}.
Requirements:
1. Only factual percentages
2. Include 3 markdown bar‐charts
3. Compare regional/global
4. Highlight 3 key findings
5. No personalized advice
6. Academic style"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = re.sub(r"<[^>]+>", "", response.choices[0].message.content)

        base_improve  = 70
        base_struggle = 40

        metrics = [
            {
                "title": "Learning Preferences" if lang=="en" else "學習偏好",
                "labels": ["Visual", "Auditory", "Kinesthetic"] if lang=="en" else ["視覺","聽覺","動手"],
                "values": [base_improve, base_struggle, 100 - base_improve - base_struggle]
            },
            {
                "title": "Study Habits" if lang=="en" else "學習習慣",
                "labels": ["Regular Study", "Group Study", "Solo Study"] if lang=="en" else ["定期學習","小組學習","獨自學習"],
                "values": [70, 30, 60]
            },
            {
                "title": "Math Performance" if lang=="en" else "數學表現",
                "labels": ["Algebra", "Geometry"] if lang=="en" else ["代數","幾何"],
                "values": [base_improve, 70]
            }
        ]

        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500

# ── BOSS ENDPOINT (/boss_analyze) ────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        name       = data.get("memberName", "").strip()
        position   = data.get("position", "").strip()
        department = data.get("department", "").strip()
        experience = data.get("experience", "").strip()
        sector     = data.get("sector", "").strip()
        challenge  = data.get("challenge", "").strip()
        focus      = data.get("focus", "").strip()
        country    = data.get("country", "").strip()
        email      = data.get("email", "").strip()
        referrer   = data.get("referrer", "").strip()

        # Age from DOB
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

Return only a valid JSON object structured like:
{{
  "metrics": [...],
  "analysis": "markdown report text here"
}}
Do not include any explanation or text outside the JSON object.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content.strip()
        app.logger.debug(f"[boss_analyze] GPT raw: {raw}")

        # Safe fallback JSON decoding
        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            json_start = raw.find("{")
            json_end = raw.rfind("}")
            if json_start != -1 and json_end != -1:
                safe_json = raw[json_start:json_end+1]
                report = json.loads(safe_json)
            else:
                raise ValueError("GPT response is not a valid JSON block.")

        return jsonify(report)

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500

# ── Run App Locally ───────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
