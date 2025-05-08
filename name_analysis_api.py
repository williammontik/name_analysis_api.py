import os
import io
import base64
import random
import logging
from datetime import datetime

from flask import Flask, request, render_template_string
from flask_cors import CORS
from dateutil import parser
from openai import OpenAI
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# —— Configuration ——  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key not set.")
client = OpenAI(api_key=OPENAI_API_KEY)

# —— Helpers ——  
def encode_fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

# —— Route ——  
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.form or request.get_json()
    # --- 1) Extract & parse DOB ---
    name   = data.get("name","").strip() or "Unknown"
    dob_raw= data.get("dob","").strip()
    if not dob_raw:
        d = data.get("dob_day"); m = data.get("dob_month"); y = data.get("dob_year")
        dob_raw = f"{d} {m} {y}".strip()
    try:
        parts = dob_raw.split()
        if len(parts)==3:
            d, m_str, y = parts
            m = datetime.strptime(m_str, "%B").month
            bd = datetime(int(y), m, int(d))
        else:
            bd = parser.parse(dob_raw, dayfirst=True)
        today = datetime.today()
        age = today.year - bd.year - ((today.month, today.day)<(bd.month, bd.day))
    except:
        age = "Unknown"

    # --- 2) Build synthetic data ---
    prefs = {"Auditory":50, "Visual":35, "Reading & Writing":15}
    habits= {"Studying Alone":45, "Group Study":30, "Online Study":25}
    math  = {
        "Algebra":       {"local":70, "regional":60, "global":None},
        "Calculus":      {"local":65, "regional":None, "global":55}
    }
    regional = {
        "Weekly Study Hours":    {"SG":15, "Other":10},
        "Homework Completion %":{"SG":85, "Other":75}
    }
    findings = [
        "50% of 20-year-old males in Singapore prefer auditory learning.",
        "Algebra performance (70%) exceeds the regional average by 10 pp.",
        "Average study time (15 hrs/week) outpaces regional norms by 50%."
    ]

    # --- 3) Generate charts ---
    # Learning Preferences bar
    fig1, ax1 = plt.subplots()
    ax1.bar(prefs.keys(), prefs.values(), edgecolor="white")
    ax1.set_title("Learning Preferences")
    ax1.set_ylabel("Percentage (%)")
    chart1 = encode_fig_to_base64(fig1)
    # Study Habits pie
    fig2, ax2 = plt.subplots()
    ax2.pie(habits.values(), labels=habits.keys(), autopct="%1.1f%%", startangle=140)
    ax2.set_title("Study Habits")
    chart2 = encode_fig_to_base64(fig2)

    # --- 4) Render HTML ---
    html = render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Learning Patterns Analysis</title>
  <style>
    body { font-family: Arial, sans-serif; margin:20px; color:#333; }
    h1 { color:#2c3e50; }
    h2 { border-bottom:2px solid #ddd; padding-bottom:5px; color:#34495e; }
    table { width:100%; border-collapse: collapse; margin-bottom:20px; }
    th,td { text-align:left; padding:8px; }
    th { background:#2980b9; color:#fff; }
    tr:nth-child(even) { background:#f2f2f2; }
    .charts { display:flex; gap:20px; margin-bottom:20px; }
    .charts img { max-width:45%; border:1px solid #ccc; padding:5px; }
    .findings { background:#ecf0f1; padding:15px; border-radius:5px; }
  </style>
</head>
<body>
  <h1>🎯 Learning Patterns Analysis</h1>
  <p><strong>Subject:</strong> 20-year-old Male (Singapore) &bull; <strong>Date:</strong> {{today}}</p>

  <h2>Executive Summary</h2>
  <p>This report provides a data-focused overview of learning modes, study habits, mathematics proficiency, and regional benchmarks for 20-year-old males in Singapore.</p>

  <h2>Charts</h2>
  <div class="charts">
    <img src="{{chart1}}" alt="Learning Preferences">
    <img src="{{chart2}}" alt="Study Habits">
  </div>

  <h2>1. Learning Preferences</h2>
  <table>
    <tr><th>Mode</th><th>Percentage</th></tr>
    {% for mode, pct in prefs.items() %}
    <tr><td>{{mode}}</td><td>{{pct}}%</td></tr>
    {% endfor %}
  </table>

  <h2>2. Study Habits</h2>
  <table>
    <tr><th>Habit</th><th>Percentage</th></tr>
    {% for habit, pct in habits.items() %}
    <tr><td>{{habit}}</td><td>{{pct}}%</td></tr>
    {% endfor %}
  </table>

  <h2>3. Mathematics Proficiency</h2>
  <table>
    <tr><th>Topic</th><th>Local (%)</th><th>Regional (%)</th><th>Global (%)</th></tr>
    {% for topic, vals in math.items() %}
    <tr>
      <td>{{topic}}</td>
      <td>{{vals.local}}%</td>
      <td>{{vals.regional if vals.regional is not none else '–' }}</td>
      <td>{{vals.global    if vals.global    is not none else '–' }}</td>
    </tr>
    {% endfor %}
  </table>

  <h2>4. Regional Comparisons</h2>
  <table>
    <tr><th>Metric</th><th>Singapore</th><th>Other</th></tr>
    {% for metric, vals in regional.items() %}
    <tr><td>{{metric}}</td><td>{{vals.SG}}</td><td>{{vals.Other}}</td></tr>
    {% endfor %}
  </table>

  <h2>5. Top 3 Findings</h2>
  <div class="findings">
    <ol>
      {% for f in findings %}
      <li>{{f}}</li>
      {% endfor %}
    </ol>
  </div>

  <footer style="margin-top:30px; font-size:0.9em; color:#777;">
    Report generated by KataChatBot AI • Confidential & Proprietary
  </footer>
</body>
</html>
    """,
    today=datetime.today().strftime("%Y-%m-%d"),
    chart1=chart1, chart2=chart2,
    prefs=prefs, habits=habits,
    math=math, regional=regional,
    findings=findings
    )

    return html, 200, {"Content-Type":"text/html"}

if __name__ == "__main__":
    app.run(debug=True)
