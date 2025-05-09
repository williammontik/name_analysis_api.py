# app.py

import os
import io
import base64
from datetime import datetime

from flask import Flask, request, render_template_string
from flask_cors import CORS
from dateutil import parser

# Force Matplotlib to use Agg for server rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("ggplot")

app = Flask(__name__)
CORS(app)

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{data}"

@app.route("/", methods=["GET"])
def form():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>KataChatBot Analysis Form</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    label { display: block; margin-top: 10px; }
    select, input { padding: 5px; width: 200px; }
    button { margin-top: 15px; padding: 10px 20px; }
  </style>
</head>
<body>
  <h1>KataChatBot Analysis</h1>
  <form action="/analyze_name" method="post" target="_blank">
    <label>
      Full Legal Name:
      <input type="text" name="name" required>
    </label>
    <label>
      Date of Birth:
      <input type="date" name="dob" required>
    </label>
    <label>
      Gender:
      <select name="gender">
        <option value="Female">Female</option>
        <option value="Male">Male</option>
        <option value="Other">Other</option>
      </select>
    </label>
    <label>
      Country:
      <input type="text" name="country" value="Singapore" required>
    </label>
    <button type="submit">Analyze</button>
  </form>
</body>
</html>
    """)

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # 1) Parse inputs
    name    = request.form.get("name", "Unknown")
    dob_str = request.form.get("dob", "")
    gender  = request.form.get("gender", "Unknown")
    country = request.form.get("country", "Unknown")

    # 2) Compute age
    try:
        dt = parser.parse(dob_str)
        today = datetime.today()
        age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except Exception:
        age = "Unknown"

    # 3) Generate a bar chart (learning preferences)
    prefs = {"Auditory":50, "Visual":35, "Reading & Writing":15}
    fig, ax = plt.subplots()
    ax.bar(prefs.keys(), prefs.values())
    ax.set_title("Learning Preferences")
    chart1 = fig_to_base64(fig)

    # 4) Inline SVG animation (pulsing circle)
    svg_anim = """
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

    # 5) Render the full HTML report
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Learning Patterns Analysis for {{ name }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Roboto', sans-serif; margin:20px; color:#333; }
    h1 { color:#2c3e50; }
    .animation { margin:20px 0; }
    .chart { margin:20px 0; }
    .chart img { max-width:60%; border:1px solid #ccc; padding:5px; }
    .info { margin-bottom:20px; }
  </style>
</head>
<body>
  <h1>🎯 Learning Patterns Analysis</h1>
  <div class="info">
    <p><strong>Name:</strong> {{ name }}</p>
    <p><strong>Age:</strong> {{ age }}</p>
    <p><strong>Gender:</strong> {{ gender }}</p>
    <p><strong>Country:</strong> {{ country }}</p>
  </div>

  <div class="animation">
    {{ svg_anim | safe }}
  </div>

  <div class="chart">
    <h2>Learning Preferences</h2>
    <img src="{{ chart1 }}" alt="Learning Preferences Chart">
  </div>
</body>
</html>
    """,
    name=name, age=age, gender=gender, country=country,
    chart1=chart1, svg_anim=svg_anim)

if __name__ == "__main__":
    app.run(debug=True)
