import os
import re
import random
import logging
from datetime import datetime
from dateutil import parser
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

# ── Helper: send email (unchanged from your children code) ────────────────────
def send_email(*args, **kwargs):
    # your existing send_email implementation here
    pass

# ── /analyze_name Endpoint (Children) ─────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[analyze_name] payload: {data}")

        # 1) parse DOB & compute age (your existing logic)
        day_str  = data.get("dob_day")
        mon_str  = data.get("dob_month")
        year_str = data.get("dob_year")
        if day_str and mon_str and year_str:
            month = int(mon_str) if mon_str.isdigit() else datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(year_str), month, int(day_str))
        else:
            birthdate = parser.parse(data.get("dob", ""), dayfirst=True)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        # 2) send email (optional)
        # send_email(...)

        # 3) build prompt & call OpenAI
        gender  = data.get("gender", "")
        country = data.get("country", "")
        prompt = (
            f"Generate a statistical report on learning patterns for children aged {age}, "
            f"gender {gender}, in {country}.\n"
            "Requirements:\n"
            "1. Only factual percentages\n"
            "2. Include 3 markdown bar‐charts\n"
            "3. Compare regional/global\n"
            "4. Highlight 3 key findings\n"
            "5. No personalized advice\n"
            "6. Academic style\n"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        analysis = re.sub(r"<[^>]+>", "", response.choices[0].message.content)

        # 4) dummy metrics (or your real stats)
        base_ok  = random.randint(65, 80)
        base_bad = max(0, random.randint(30, 45))
        ok_pct    = round(base_ok/5)*5
        bad_pct   = round(base_bad/5)*5
        metrics = [
            {
                "title":  "Learning Preferences",
                "labels": ["Visual", "Auditory", "Kinesthetic"],
                "values": [ok_pct, bad_pct, 100 - ok_pct - bad_pct]
            },
            {
                "title":  "Study Habits",
                "labels": ["Regular Study", "Group Study", "Solo Study"],
                "values": [70, 30, 60]
            },
            {
                "title":  "Math Performance",
                "labels": ["Algebra", "Geometry"],
                "values": [ok_pct, 70]
            }
        ]

        return jsonify({
            "metrics": metrics,
            "analysis": analysis
        })

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500


# ── /boss_analyze Endpoint (Managers) ─────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # You can replace this with a real OpenAI prompt like above,
        # but for now we return matching dummy data:
        dummy_metrics = [
            {
                "title":  "Leadership Effectiveness",
                "labels": ["Vision", "Execution", "Empathy"],
                "values": [75, 60, 85]
            },
            {
                "title":  "Team Engagement",
                "labels": ["Motivation", "Collaboration", "Trust"],
                "values": [70, 65, 80]
            },
            {
                "title":  "Communication Skills",
                "labels": ["Clarity", "Listening", "Feedback"],
                "values": [80, 70, 75]
            }
        ]
        dummy_analysis = (
            f"Here’s a quick analysis for {data.get('memberName')} ({data.get('position')}):\n\n"
            "- Strong Vision and Empathy; consider boosting Execution.\n"
            "- Team shows high Trust but needs more Collaboration.\n"
            "- Communication is solid, with room to improve Feedback."
        )

        return jsonify({
            "metrics": dummy_metrics,
            "analysis": dummy_analysis
        })

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
