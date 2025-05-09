import os, re, random, smtplib
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)
app.logger.setLevel("DEBUG")

# ─── OpenAI client ─────────────────────────────────────────────────────────────
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")
client = OpenAI(api_key=OPENAI_KEY)

# ─── SMTP settings ─────────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "kata.chatbot@gmail.com"
SMTP_PASS     = os.getenv("SMTP_PASSWORD") or ""

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    subject = "🔔 New KataChatBot Submission"
    body = f"""
🎯 New Submission:

👤 Full Name: {full_name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 DOB: {dob}  (Age: {age})
🌍 Country: {country}

📞 Phone: {phone}
📧 Email: {email}
🔗 Referrer: {referrer}
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = SMTP_USER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        app.logger.info("✅ Email sent")
    except Exception:
        app.logger.exception("❌ SMTP error")

# ─── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() or {}
    # collect fields
    name         = data.get("name","").strip()
    chinese_name = data.get("chinese_name","").strip()
    gender       = data.get("gender","").strip()
    phone        = data.get("phone","").strip()
    email        = data.get("email","").strip()
    country      = data.get("country","").strip()
    referrer     = data.get("referrer","").strip()

    # parse DOB + age
    dob_input = ""
    if data.get("dob_day") and data.get("dob_month") and data.get("dob_year"):
        dob_input = f"{data['dob_day']} {data['dob_month']} {data['dob_year']}"
    else:
        dob_input = data.get("dob","").strip()

    try:
        parts = dob_input.split()
        if len(parts)==3:
            d, mon_str, y = parts
            month = datetime.strptime(mon_str, "%B").month
            birthdate = datetime(int(y), month, int(d))
        else:
            birthdate = parser.parse(dob_input, dayfirst=True)
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except Exception:
        app.logger.exception("DOB parse error")
        age = None

    # email notification
    send_email(name, chinese_name, gender, dob_input, age, phone, email, country, referrer)

    # --- Generate dummy stats (or call OpenAI here if you prefer) ---
    # For demo, we hard-code the same buckets you showed.
    result = {
      "age": age,
      "demographic": {"age":age,"gender":gender,"country":country},
      "metrics": {
        "study_time":   {"labels":["< 5 hrs","5–10 hrs","> 10 hrs"], "values":[35,55,10]},
        "learning_styles": {"labels":["Visual","Auditory","Kinesthetic"], "values":[40,30,30]},
        "math_performance": {
          "subjects":["Algebra","Geometry"],
          "local":[75,80],
          "regional":[70,None],
          "global":[None,75]
        }
      },
      "regional_comparison":{
        "study_time":{"local":55,"regional":45},
        "visual_learners":{"local":40,"global":35}
      },
      "top_findings":[
        f"{55}% of {age}-year-old {gender}s in {country} study 5–10hrs/week (above regional).",
        "Learning methods split evenly: Visual, Auditory, Kinesthetic.",
        "Singaporean females hit 80% in geometry (vs 75% global)."
      ]
    }

    return jsonify(result)

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0")
