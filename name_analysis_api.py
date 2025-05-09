import os
import io
import base64
import logging
from datetime import datetime

from flask import Flask, request, render_template_string
from flask_cors import CORS
from dateutil import parser

# Force Matplotlib to use the Agg backend on servers
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("ggplot")

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{data}"

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # 1) Parse date of birth → compute age
    dob = request.form.get("dob") or (
        f"{request.form.get('dob_day','')} "
        f"{request.form.get('dob_month','')} "
        f"{request.form.get('dob_year','')}"
    ).strip()
    try:
        dt = parser.parse(dob, dayfirst=True)
        today = datetime.today()
        age = today.year - dt.year - (
            (today.month, today.day) < (dt.month, dt.day)
        )
    except Exception:
        age = "Unknown"

    # 2) Generate a sample bar chart for learning preferences
    prefs = {"Auditory": 50, "Visual": 35, "Reading & Writing": 15}
    fig1, ax1 = plt.subplots()
    ax1.bar(prefs.keys(), prefs.values())
    ax1.set_title("Learning Preferences")
    chart1 = fig_to_base64(fig1)

    # 3) Inline SVG animation (pulsing circle)
    svg_animation = """
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
""".strip()

    # 4) Render a full HTML report
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Learning Patterns Analysis</title>
  <!-- Load a clean font -->
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Roboto', sans-serif; padding:20px; color:#333; }
    h1 { font-weight:700; color:#2c3e50; }
    .charts { display:flex; gap:20px; margin:20px 0; }
    .charts img { max-width:45%; border:1px solid #ccc; padding:5px; }
    .animation { margin:20px 0; }
  </style>
</head>
<body>
  <h1>🎯 Learning Patterns Analysis</h1>
  <p><strong>Age:</strong> {{ age }}</p>

  <div class="animation">
    {{ svg_animation | safe }}
  </div>

  <div class="charts">
    <img src="{{ chart1 }}" alt="Learning Preferences Chart">
  </div>
</body>
</html>
    """,
    age=age,
    chart1=chart1,
    svg_animation=svg_animation
    ), 200, {"Content-Type": "text/html"}

if __name__ == "__main__":
    app.run(debug=True)
