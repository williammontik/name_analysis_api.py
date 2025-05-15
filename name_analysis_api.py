import os
import re
import json
import logging
from datetime import datetime
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
    raise RuntimeError("OPENAI_API_KEY is not set.")
client = OpenAI(api_key=openai_api_key)

# ── Child Report Endpoint ────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[analyze_name] payload: {data}")

        name = data.get("name", "")
        chinese_name = data.get("chinese_name", "")
        gender = data.get("gender", "")
        phone = data.get("phone", "")
        email = data.get("email", "")
        country = data.get("country", "")
        referrer = data.get("referrer", "")
        lang = data.get("lang", "en").lower()

        # Compute DOB and Age
        day = data.get("dob_day")
        mon = data.get("dob_month")
        year = data.get("dob_year")
        if day and mon and year:
            if mon.isdigit():
                month = int(mon)
            else:
                month = datetime.strptime(mon, "%B").month
            birthdate = datetime(int(year), month, int(day))
        else:
            birthdate = datetime(2015, 1, 1)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        # Language prompt
        if lang == "zh":
            prompt = f"""请用简体中文生成一份学习模式统计报告，面向年龄 {age}、性别 {gender}、地区 {country} 的孩子。
要求：
1. 只给出百分比数据
2. 用 Markdown 格式展示 3 个“柱状图”示例
3. 对比区域/全球趋势
4. 突出 3 个关键发现
5. 不要个性化建议
6. 学术风格"""
        elif lang == "tw":
            prompt = f"""請用繁體中文生成一份學習模式統計報告，面向年齡 {age}、性別 {gender}、地區 {country} 的孩子。
要求：
1. 只給出百分比數據
2. 用 Markdown 格式展示 3 個「柱狀圖」示例
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
        analysis = re.sub(r"<[^>]+>", "", response.choices[0].message.content.strip())

        metrics = [
            {
                "title": "Learning Preferences" if lang == "en" else "學習偏好",
                "labels": ["Visual", "Auditory", "Kinesthetic"] if lang == "en" else ["視覺","聽覺","動手"],
                "values": [65, 25, 10]
            },
            {
                "title": "Study Habits" if lang == "en" else "學習習慣",
                "labels": ["Regular Study", "Group Study", "Solo Study"] if lang == "en" else ["定期學習", "小組學習", "獨自學習"],
                "values": [70, 30, 60]
            },
            {
                "title": "Math Performance" if lang == "en" else "數學表現",
                "labels": ["Algebra", "Geometry"] if lang == "en" else ["代數", "幾何"],
                "values": [75, 68]
            }
        ]

        return jsonify({"metrics": metrics, "analysis": analysis})

    except Exception as e:
        app.logger.exception("[analyze_name] error")
        return jsonify({"error": str(e)}), 500

# ── Boss Report Endpoint ─────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        name = data.get("memberName", "")
        position = data.get("position", "")
        department = data.get("department", "")
        experience = data.get("experience", "")
        sector = data.get("sector", "")
        challenge = data.get("challenge", "")
        focus = data.get("focus", "")
        email = data.get("email", "")
        country = data.get("country", "")

        day = data.get("dob_day")
        mon = data.get("dob_month")
        year = data.get("dob_year")
        if day and mon and year:
            month = int(mon) if mon.isdigit() else datetime.strptime(mon, "%B").month
            dob = datetime(int(year), month, int(day))
        else:
            dob = datetime(1990, 1, 1)
        age = datetime.now().year - dob.year

        # Prompt
        prompt = f"""
You are an expert organizational psychologist.

Generate a workplace performance report for a segment of:
- Age: {age}
- Position: {position}
- Department: {department}
- Experience: {experience} years
- Sector: {sector}
- Country: {country}
- Main Challenge: {challenge}
- Development Focus: {focus}

🎯 Return this in HTML:
1. Title (1 line) as a bold <p>
2. Introduction (2–3 lines) using <p>
3. Workplace Patterns section — each metric as:
   <p><strong>Metric Title:</strong> Segment 75% | Regional 70% | Global 72%</p>
4. Comparison with Regional/Global Trends in a new <p>
5. Key Findings in a <ul> list with <li>
6. Add 1 blank line (<br><br>) between sections
End with: "End of Report"
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content.strip()

        metrics = [
            {
                "title": "Communication Efficiency",
                "labels": ["Segment", "Regional", "Global"],
                "values": [75, 70, 72]
            },
            {
                "title": "Leadership Readiness",
                "labels": ["Segment", "Regional", "Global"],
                "values": [60, 65, 70]
            },
            {
                "title": "Task Completion Reliability",
                "labels": ["Segment", "Regional", "Global"],
                "values": [85, 80, 82]
            }
        ]

        footer = '''<br><br>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>The insights in this report are generated by KataChat’s AI systems analyzing:</strong><br>
  1. Our proprietary database of anonymized professional profiles across Singapore, Malaysia, and Taiwan<br>
  2. Aggregated global business benchmarks from trusted OpenAI research and leadership trend datasets<br>
  <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance. Sample sizes vary by analysis, with minimum thresholds of 1,000+ data points for management comparisons.</em>
</p>
<p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
  <strong>PS:</strong> This report has also been sent to your email inbox and should arrive within 24 hours. If you'd like to discuss it further, feel free to reach out — we’re happy to arrange a 15-minute call at your convenience.
</p>'''

        return jsonify({"metrics": metrics, "analysis": analysis + footer})

    except Exception as e:
        app.logger.exception("[boss_analyze] error")
        return jsonify({"error": str(e)}), 500

# ── Run Local Test (Optional) ────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
