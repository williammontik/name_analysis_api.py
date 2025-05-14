import os
import re
import smtplib
import random
import logging
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin        # ← imported cross_origin
from openai import OpenAI

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # allows CORS for all routes
app.logger.setLevel(logging.DEBUG)

# ── OpenAI Client ────────────────────────────────────────────────────────────
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
client = OpenAI(api_key=openai_api_key)

# ── SMTP Setup ───────────────────────────────────────────────────────────────
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
if not SMTP_PASSWORD:
    app.logger.warning("SMTP_PASSWORD is not set; emails may fail.")

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    # … your existing send_email implementation …

# ── Children Analysis Endpoint ───────────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # … your existing analyze_name logic …
    # returns jsonify({ "age_computed": age, "analysis": analysis, "metrics": metrics })

# ── Boss Analysis Endpoint ──────────────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST", "OPTIONS"])
@cross_origin()  # handles the OPTIONS preflight and adds CORS headers
def boss_analyze():
    data = request.get_json()
    app.logger.info(f"Boss payload: {data}")

    # Dummy metrics & analysis—replace later with real logic
    dummy_metrics = [
        {
            "title": "Leadership Effectiveness",
            "labels": ["Vision", "Execution", "Empathy"],
            "values": [75, 60, 85]
        },
        {
            "title": "Team Engagement",
            "labels": ["Motivation", "Collaboration", "Trust"],
            "values": [70, 65, 80]
        }
    ]
    dummy_analysis = (
        f"Here’s a quick analysis for {data.get('memberName')}:\n\n"
        "- Strong Vision and Empathy; consider boosting Execution.\n"
        "- Team shows high Trust but needs more Collaboration.\n"
    )

    return jsonify({
        "metrics": dummy_metrics,
        "analysis": dummy_analysis
    })

# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
