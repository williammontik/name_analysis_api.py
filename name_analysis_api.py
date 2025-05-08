import os
import io
import base64
import logging
from datetime import datetime

from flask import Flask, request, render_template_string
from flask_cors import CORS
from dateutil import parser

# 1) Force Agg backend for headless servers
import matplotlib
matplotlib.use("Agg")

# 2) Import pyplot and set style to ggplot
import matplotlib.pyplot as plt
plt.style.use("ggplot")

# (Optional) OpenAI import
from openai import OpenAI

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

# — Configuration —
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# — Helper to encode figures —
def encode_fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{data}"

# — Main endpoint —
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    payload = request.form if request.form else (request.get_json() or {})
    name     = payload.get("name", "").strip() or "Unknown"
    country  = payload.get("country", "").strip() or "Singapore"

    # Build & parse DOB
    dob_raw = payload.get("dob", "").strip()
    if not dob_raw:
        d = payload.get("dob_day","").strip()
        m = payload.get("dob_month","").strip()
        y = payload.get("dob_year","").strip()
        dob_raw = f"{d} {m} {y}".strip()

    try:
        parts = dob_raw.split()
        if len(parts) == 3:
            dd, mon_str, yy = parts
            mon_idx = datetime.strptime(mon_str, "%B").month
            bd = datetime(int(yy), mon_idx, int(dd))
        else:
            bd = parser.parse(dob_raw, dayfirst=True)
        today = datetime.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except Exception:
        app.logger.warning(f"Failed to parse DOB '{dob_raw}'", exc_info=True)
        age = "Unknown"

    # Synthetic data
    prefs = {"Auditory": 50, "Visual": 35, "Reading & Writing": 15}
    habits= {"Studying Alone": 45, "Group Study": 30, "Online Study": 25}
    math  = {
      "Algebra":  {"local":70, "regional":60, "global":None},
      "Calculus": {"local":65, "regional":None, "global":55}
    }
    regional = {
      "Weekly Study Hours":    {"SG":15, "Other":10},
      "Homework Completion %": {"SG":85, "Other":75}
    }
    findings = [
      f"{prefs['Auditory']}% prefer auditory learning.",
      f"Algebra local score: {math['Algebra']['local']}% vs regional {math['Algebra']['regional']}%.",
      f"Singaporeans study {regional['Weekly Study Hours']['SG']} hrs/week vs {regional['Weekly Study Hours']['Other']} hrs regional."
    ]

    # Generate charts
    chart1 = chart2 = None
    try:
        fig1, ax1 = plt.subplots()
        ax1.bar(prefs.keys(), prefs.values())
        ax1.set_title("Learning Preferences")
        ax1.set_ylabel("Percentage (%)")
        chart1 = encode_fig_to_base64(fig1)

        fig2, ax2 = plt.subplots()
        ax2.pie(habits.values(), labels=habits.keys(), autopct="%1.1f%%", startangle=140)
        ax2.set_title("Study Habits")
        chart2 = encode_fig_to_base64(fig2)
    except Exception:
        app.logger.error("Chart generation failed", exc_info=True)

    # Optional AI analysis with graceful fallback
    analysis = "⚠️ AI analysis currently unavailable."
    if client:
        try:
            prompt = f"Generate a concise data report for a {age}-year-old male in {country}."
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"user","content":prompt}]
            )
            analysis = resp.choices[0].message.content.strip()
        except Exception:
            app.logger.warning("OpenAI call failed; using fallback.", exc_info=True)

    # Render the final HTML
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
    table { width:100%; border-collapse:collapse; margin-bottom:20px; }
    th,td { padding:8px; text-align:left; }
    th { background:#2980b9; color:#fff; }
    tr:nth-child(even){ background:#f9f9f9; }
    .charts { display:flex; gap:20px; margin-bottom:20px; }
    .charts img{ max-width:45%; border:1px solid #ccc; padding:5px; }
    .findings { background:#ecf0f1; padding:15px; border-radius:5px; }
    .analysis { background:#fff3cd; padding:15px; border-radius:5px; margin-bottom:20px; }
  </style>
</head>
<body>
  <h1>🎯 Learning Patterns Analysis</h1>
  <p><strong>Subject:</strong> 20-year-old Male in {{ country }} &bull;
     <strong>Date:</strong> {{ today }}</p>

  <h2>Executive Summary</h2>
  <p>This report provides a data-driven overview of learning preferences, study habits,
     mathematics proficiency, and regional benchmarks.</p>

  {% if chart1 and chart2 %}
  <div class="charts">
    <img src="{{ chart1 }}" alt="Learning Preferences">
    <img src="{{ chart2 }}" alt="Study Habits">
  </div>
  {% endif %}

  <h2>1. Learning Preferences</h2>
  <table>
    <tr><th>Mode</th><th>Percentage</th></tr>
    {% for m,p in prefs.items() %}
      <tr><td>{{ m }}</td><td>{{ p }}%</td></tr>
    {% endfor %}
  </table>

  <h2>2. Study Habits</h2>
  <table>
    <tr><th>Habit</th><th>Percentage</th></tr>
    {% for h,p in habits.items() %}
      <tr><td>{{ h }}</td><td>{{ p }}%</td></tr>
    {% endfor %}
  </table>

  <h2>3. Mathematics Proficiency</h2>
  <table>
    <tr><th>Topic</th><th>Local</th><th>Regional</th><th>Global</th></tr>
    {% for topic, vals in math.items() %}
      <tr>
        <td>{{ topic }}</td>
        <td>{{ vals.local }}%</td>
        <td>{{ vals.regional or '–' }}</td>
        <td>{{ vals.global    or '–' }}</td>
      </tr>
    {% endfor %}
  </table>

  <h2>4. Regional Comparisons</h2>
  <table>
    <tr><th>Metric</th><th>SG</th><th>Other</th></tr>
    {% for metric, vals in regional.items() %}
      <tr><td>{{ metric }}</td><td>{{ vals.SG }}</td><td>{{ vals.Other }}</td></tr>
    {% endfor %}
  </table>

  <h2>5. Top 3 Findings</h2>
  <div class="findings">
    <ol>{% for f in findings %}<li>{{ f }}</li>{% endfor %}</ol>
  </div>

  <h2>6. AI Analysis</h2>
  <div class="analysis"><pre style="margin:0">{{ analysis }}</pre></div>

  <footer style="margin-top:30px;font-size:0.8em;color:#777;">
    Report generated by KataChatBot AI • Confidential & Proprietary
  </footer>
</body>
</html>
""",
        today=datetime.today().strftime("%Y-%m-%d"),
        country=country,
        prefs=prefs,
        habits=habits,
        math=math,
        regional=regional,
        findings=findings,
        chart1=chart1,
        chart2=chart2,
        analysis=analysis
    )

    return html, 200, {"Content-Type": "text/html"}

if __name__ == "__main__":
    app.run(debug=True)
