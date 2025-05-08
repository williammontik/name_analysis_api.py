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

# —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# Configuration
# —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

# OpenAI  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  
if not OPENAI_API_KEY:  
    raise RuntimeError("OpenAI API key not set.")  
client = OpenAI(api_key=OPENAI_API_KEY)

# SMTP  
SMTP_SERVER   = "smtp.gmail.com"  
SMTP_PORT     = 587  
SMTP_USERNAME = "kata.chatbot@gmail.com"  
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# Helpers
# —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

def encode_fig_to_base64(fig):
    """Encode a matplotlib figure as a base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

def send_email(**kwargs):
    """Dispatch summary email."""
    body = f"""
🎯 New User Submission:

👤 Full Legal Name: {kwargs['full_name']}
🈶 Chinese Name: {kwargs['chinese_name']}
⚧️ Gender: {kwargs['gender']}
🎂 Date of Birth: {kwargs['dob']}
🎯 Age: {kwargs['age']} years old
🌍 Country: {kwargs['country']}

📞 Phone: {kwargs['phone']}
📧 Email: {kwargs['email']}
💬 Referrer: {kwargs['referrer']}
"""
    msg = MIMEText(body)
    msg["Subject"] = "New KataChatBot User Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("✅ Email sent successfully.")
    except Exception as e:
        app.logger.error("❌ Email error:", exc_info=e)

# —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# Endpoint
# —–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # 1) Parse incoming form/json
    data = request.get_json() if request.is_json else request.form
    name         = data.get("name", "").strip()
    chinese_name = data.get("chinese_name", "").strip()
    gender       = data.get("gender", "").strip() or "Unknown"
    country      = data.get("country", "").strip() or "Unknown"
    phone        = data.get("phone", "").strip()
    email        = data.get("email", "").strip()
    referrer     = data.get("referrer", "").strip()

    # 2) Construct DOB input
    day  = data.get("dob_day")
    mon  = data.get("dob_month")
    year = data.get("dob_year")
    if day and mon and year:
        dob_input = f"{day} {mon} {year}"
    else:
        dob_input = data.get("dob", "").strip()

    if not name or not dob_input:
        return jsonify({"error": "Name and date of birth are required."}), 400

    app.logger.debug(f"Raw DOB input: {dob_input!r}")

    # 3) Compute age
    try:
        parts = dob_input.split()
        if len(parts) == 3:
            d, mon_str, y = parts
            mon_idx = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(y), mon_idx, int(d))
        else:
            birthdate = parser.parse(dob_input, dayfirst=True)
        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
    except Exception as e:
        app.logger.error("Error calculating age", exc_info=e)
        age = None

    # 4) Email notification
    send_email(
        full_name   = name,
        chinese_name= chinese_name,
        gender      = gender,
        dob         = dob_input,
        age         = age if age is not None else "Unknown",
        phone       = phone,
        email       = email,
        country     = country,
        referrer    = referrer
    )

    # 5) Generate synthetic stats
    prefs = {"Auditory": 50, "Visual": 35, "Reading & Writing": 15}
    habits= {"Studying Alone": 45, "Group Study": 30, "Online Study": 25}
    math  = {"Algebra": (70, 60, None), "Calculus": (65, None, 55)}
    regional = {
        "Weekly Study Hours":    {"SG":15, "Region/Global":10},
        "Homework Completion %":{"SG":85, "Region/Global":75}
    }

    # 6) Top findings
    findings = [
        "50% of 20-year-old males in Singapore prefer auditory learning.",
        "Singaporean males achieve 70% in Algebra—10 pp above regional average.",
        "Average study time (15 hrs/week) exceeds regional norms by 50%."
    ]

    # 7) Build OpenAI prompt & get analysis (if needed)
    # (– omitted here for brevity, reuse your existing prompt logic –)

    # 8) Build charts
    #   8a) Bar chart for prefs
    fig1, ax1 = plt.subplots()
    ax1.bar(prefs.keys(), prefs.values())
    ax1.set_title("Learning Preferences")
    ax1.set_ylabel("Percentage (%)")
    chart_prefs = encode_fig_to_base64(fig1)

    #   8b) Pie chart for habits
    fig2, ax2 = plt.subplots()
    ax2.pie(habits.values(), labels=habits.keys(), autopct="%1.1f%%", startangle=140)
    ax2.set_title("Study Habits")
    chart_habits = encode_fig_to_base64(fig2)

    # 9) Return structured JSON
    return jsonify({
        "age": age,
        "data": {
            "learning_preferences": prefs,
            "study_habits":        habits,
            "math_proficiency": {
                subject: {"local": v[0], "regional": v[1], "global": v[2]}
                for subject, v in math.items()
            },
            "regional_comparisons": regional,
            "top_findings":         findings
        },
        "charts": {
            "learning_preferences_bar": chart_prefs,
            "study_habits_pie":         chart_habits
        },
        # if you run the OpenAI step, you can also include:
        # "analysis": clean_text
    })

if __name__ == "__main__":
    app.run(debug=True)
