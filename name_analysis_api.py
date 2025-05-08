import os
import re
import io
import base64
import smtplib
import random
import logging
from email.mime.text import MIMEText
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from dateutil import parser
from openai import OpenAI
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# — Configuration (same as before) —
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key not set.")
client = OpenAI(api_key=OPENAI_API_KEY)

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# — Helpers (same encode + email as before) —
def encode_fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

def send_email(**kw):
    # … your existing email code …
    pass

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    # 1) Required fields
    name = data.get("name","").strip()
    dob_raw = data.get("dob","").strip() or \
              " ".join([data.get("dob_day",""), data.get("dob_month",""), data.get("dob_year","")]).strip()
    if not name or not dob_raw:
        return jsonify({"error":"Name and DOB are required"}), 400

    # 2) Compute age
    try:
        parts = dob_raw.split()
        if len(parts)==3:
            d, m_str, y = parts
            m = datetime.strptime(m_str, "%B").month
            bd = datetime(int(y),m,int(d))
        else:
            bd = parser.parse(dob_raw, dayfirst=True)
        today = datetime.today()
        age = today.year - bd.year - ((today.month, today.day)<(bd.month, bd.day))
    except Exception as e:
        app.logger.error("DOB parse error", exc_info=e)
        age = None

    # 3) Notify by email
    send_email(full_name=name, chinese_name=data.get("chinese_name",""),
               gender=data.get("gender","Unknown"), dob=dob_raw,
               age=age or "Unknown", phone=data.get("phone",""),
               email=data.get("email",""), country=data.get("country","Unknown"),
               referrer=data.get("referrer",""))

    # 4) Assemble your synthetic stats
    prefs = {"Auditory":50, "Visual":35, "Reading & Writing":15}
    habits= {"Studying Alone":45, "Group Study":30, "Online Study":25}
    regional = {
      "Weekly Study Hours":    {"SG":15, "Region":10},
      "Homework Completion %":{"SG":85, "Global":75}
    }

    # 5) Generate charts (always executed)
    fig1, ax1 = plt.subplots()
    ax1.bar(prefs.keys(), prefs.values())
    ax1.set_title("Learning Preferences")
    chart1 = encode_fig_to_base64(fig1)

    fig2, ax2 = plt.subplots()
    ax2.pie(habits.values(), labels=habits.keys(),
            autopct="%1.1f%%", startangle=140)
    ax2.set_title("Study Habits")
    chart2 = encode_fig_to_base64(fig2)

    # 6) Call OpenAI safely
    analysis = None
    try:
        prompt = f"""
Generate a statistical report on learning patterns for children aged {age}, gender {data.get('gender',"Unknown")} in {data.get('country',"Unknown")}.
… (your full prompt here) …
"""
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        raw = resp.choices[0].message.content
        analysis = re.sub(r"<[^>]+>", "", raw).strip()
    except Exception as e:
        app.logger.error("OpenAI error", exc_info=e)
        analysis = (
            "⚠️ Unable to generate AI analysis at this time. "
            "Please try again later."
        )

    # 7) Build final JSON
    return jsonify({
        "age": age,
        "data": {
            "learning_preferences": prefs,
            "study_habits": habits,
            "regional_comparisons": regional
        },
        "charts": {
            "learning_preferences_bar": chart1,
            "study_habits_pie": chart2
        },
        "analysis": analysis
    })

if __name__=="__main__":
    app.run(debug=True)
