import os
import io
import base64
import logging
import random
from datetime import datetime

from flask import Flask, request, render_template_string
from flask_cors import CORS
from dateutil import parser

# Force Agg backend on the server
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("ggplot")

# (Optional) remove OpenAI entirely if you don’t need live AI text
from openai import OpenAI
from email.mime.text import MIMEText
import smtplib

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# —–––––––––––––––––––––
# SMTP (email) setup
# —–––––––––––––––––––––
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(full_name, dob, age, phone, email, country, referrer):
    msg = MIMEText(f"""
New Submission:
Name: {full_name}
DOB: {dob}
Age: {age}
Phone: {phone}
Email: {email}
Country: {country}
Referrer: {referrer}
""")
    msg["Subject"] = "KataChatBot Submission"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        app.logger.info("Email sent")
    except Exception:
        app.logger.error("Email failed", exc_info=True)

# —–––––––––––––––––––––
# Inline SVG animation
# —–––––––––––––––––––––
def get_svg_animation():
    return """
<svg width="120" height="120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="20" fill="#3498db">
    <animate attributeName="r"
             from="20" to="50"
             dur="1.5s"
             repeatCount="indefinite"
             values="20;50;20"
             keyTimes="0;0.5;1" />
  </circle>
</svg>
"""

# —–––––––––––––––––––––
# Helper: Matplotlib → Base64
# —–––––––––––––––––––––
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{data}"

# —–––––––––––––––––––––
# Main route
# —–––––––––––––––––––––
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    form = request.form

    # 1) Parse
    name     = form.get("name", "") or "Unknown"
    phone    = form.get("phone", "")
    email    = form.get("email", "")
    country  = form.get("country", "Singapore")
    referrer = form.get("referrer", "")

    # 2) DOB → age
    dob = form.get("dob") or f"{form.get('dob_day','')} {form.get('dob_month','')} {form.get('dob_year','')}"
    try:
        parts = dob.split()
        if len(parts)==3:
            d, m, y = parts
            m_idx = datetime.strptime(m, "%B").month
            bd = datetime(int(y), m_idx, int(d))
        else:
            bd = parser.parse(dob, dayfirst=True)
        today = datetime.today()
        age = today.year - bd.year - ((today.month, today.day)<(bd.month, bd.day))
    except Exception:
        age = "Unknown"

    # 3) Send email (optional)
    send_email(name, dob, age, phone, email, country, referrer)

    # 4) Synthetic data
    prefs = {"Auditory":50, "Visual":35, "Reading & Writing":15}
    habits= {"Alone":45, "Group":30, "Online":25}
    math  = {"Algebra":(70,60,None), "Calculus":(65,None,55)}
    regional = {"Study Hours":(15,10), "Homework %":(85,75)}
    findings = [
        f"{prefs['Auditory']}% prefer auditory learning.",
        f"Algebra: {math['Algebra'][0]}% vs regional {math['Algebra'][1]}%.",
        f"{regional['Study Hours'][0]} hrs/week vs {regional['Study Hours'][1]} regional."
    ]

    # 5) Charts
    fig1, ax1 = plt.subplots()
    ax1.bar(prefs.keys(), prefs.values())
    ax1.set_title("Learning Preferences")
    chart1 = fig_to_base64(fig1)

    fig2, ax2 = plt.subplots()
    ax2.pie(habits.values(), labels=habits.keys(), autopct="%1.1f%%", startangle=140)
    ax2.set_title("Study Habits")
    chart2 = fig_to_base64(fig2)

    # 6) SVG animation
    svg_anim = get_svg_animation()

    # 7) Render HTML
    return render_template_string("""
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Learning Patterns</title>
<style>
  body{font-family:Arial,sans-serif;margin:20px;color:#333}
  h1{color:#2c3e50} h2{border-bottom:2px solid #ddd;padding:5px;color:#34495e}
  table{width:100%;border-collapse:collapse;margin:10px 0}
  th,td{padding:8px;text-align:left} th{background:#2980b9;color:#fff}
  tr:nth-child(even){background:#f9f9f9}
  .charts{display:flex;gap:20px;margin:20px 0}
  .charts img{max-width:45%;border:1px solid #ccc;padding:5px}
  .anim{margin:20px 0}
  .findings{background:#ecf0f1;padding:15px;border-radius:5px}
</style>
</head><body>
  <h1>🎯 Learning Patterns Analysis</h1>
  <p><strong>Name:</strong> {{name}} • <strong>Age:</strong> {{age}} • 
     <strong>Country:</strong> {{country}}</p>

  <div class="anim">{{ svg_anim|safe }}</div>

  <div class="charts">
    <img src="{{chart1}}" alt="Prefs">
    <img src="{{chart2}}" alt="Habits">
  </div>

  <h2>1. Learning Preferences</h2>
  <table><tr><th>Mode</th><th>%</th></tr>
    {% for m,p in prefs.items() %}
      <tr><td>{{m}}</td><td>{{p}}%</td></tr>
    {% endfor %}
  </table>

  <h2>2. Study Habits</h2>
  <table><tr><th>Habit</th><th>%</th></tr>
    {% for h,p in habits.items() %}
      <tr><td>{{h}}</td><td>{{p}}%</td></tr>
    {% endfor %}
  </table>

  <h2>3. Math Proficiency</h2>
  <table><tr><th>Subject</th><th>Local</th><th>Regional</th><th>Global</th></tr>
    {% for sub,(l,r,g) in math.items() %}
      <tr><td>{{sub}}</td><td>{{l}}%</td><td>{{r or '–'}}%</td><td>{{g or '–'}}%</td></tr>
    {% endfor %}
  </table>

  <h2>4. Regional Comparisons</h2>
  <table><tr><th>Metric</th><th>SG</th><th>Other</th></tr>
    {% for m,(s,o) in regional.items() %}
      <tr><td>{{m}}</td><td>{{s}}</td><td>{{o}}</td></tr>
    {% endfor %}
  </table>

  <h2>5. Top Findings</h2>
  <div class="findings"><ol>
    {% for f in findings %}<li>{{f}}</li>{% endfor %}
  </ol></div>

  <footer style="margin-top:30px;font-size:0.8em;color:#777;">
    Generated by KataChatBot AI
  </footer>
</body></html>
""",
    name=name, age=age, country=country,
    prefs=prefs, habits=habits, math=math,
    regional=regional, findings=findings,
    chart1=chart1, chart2=chart2,
    svg_anim=svg_anim
)

if __name__ == "__main__":
    app.run(debug=True)
