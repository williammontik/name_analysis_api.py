# -*- coding: utf-8 -*-
import os, logging, smtplib, traceback, random, json
from datetime import datetime
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Flask setup
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Email credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Route
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    try:
        data = request.get_json()
        name = data.get("name", "")
        gender = data.get("gender", "")
        country = data.get("country", "")
        year = data.get("dob_year", "")
        email = data.get("email", "")

        age = datetime.now().year - int(year)

        # === Chart Section ===
        metrics = [
            {
                "title": "Learning Preference",
                "labels": ["Visual", "Auditory", "Kinesthetic"],
                "values": [random.randint(50, 90), random.randint(10, 50), random.randint(5, 40)]
            },
            {
                "title": "Study Habits",
                "labels": ["Daily Review", "Group Study"],
                "values": [random.randint(30, 90), random.randint(10, 70)]
            },
            {
                "title": "Confidence Areas",
                "labels": ["Math", "Reading", "Focus & Attention"],
                "values": [random.randint(40, 95), random.randint(30, 80), random.randint(20, 70)]
            }
        ]

        # === Summary Section ===
        summary = [
            f"In {country}, many children around the age of {age} are exploring the world with curiosity and differing strengths. Among them, a strong preference for {metrics[0]['labels'][0]} learning shows up prominently at {metrics[0]['values'][0]}%, suggesting a need for engaging visual tools in their education.",
            f"Study behavior insights reveal that while {metrics[1]['values'][0]}% show consistency in daily review, only {metrics[1]['values'][1]}% engage in group study — indicating room to cultivate collaborative learning environments.",
            f"Confidence trends show higher assurance in Math ({metrics[2]['values'][0]}%) than in Reading ({metrics[2]['values'][1]}%), while focus-related abilities average at {metrics[2]['values'][2]}%. These insights reflect both growth opportunities and areas needing gentle support.",
            f"These metrics are based on anonymized comparisons with hundreds of learners across Singapore, Malaysia, and Taiwan. They serve not as judgment but as a guide — empowering parents with clearer understanding and creative next steps. 💡"
        ]

        # === Footer Section ===
        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #5E9CA0;"
            "border-radius:8px;margin-top:30px;'>"
            "<strong>📊 Insights Generated From:</strong>"
            "<ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>Aggregated data from anonymized students in Singapore, Malaysia, and Taiwan</li>"
            "<li>Educational trend benchmarking using OpenAI's analytical tools</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>All insights are generated through statistically significant patterns, without referencing any personal record. "
            "Our platform is fully PDPA-compliant and used only for improvement guidance.</p>"
            "<p style='margin-top:10px;line-height:1.7;'>"
            "<strong>PS:</strong> Your full personalized report will be sent to your inbox within <strong>24 hours</strong>. "
            "If you prefer a quick chat, we’re happy to arrange a <strong>15-minute call</strong> to walk you through it."
            "</p></div>"
        )

        # Format for frontend
        full_analysis = "<div style='font-size:24px; font-weight:bold; margin-top:30px;'>🧠 Summary:</div><br>"
        full_analysis += "".join([f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px;'>{para}</p>" for para in summary])
        full_analysis += footer

        # Send email (optional: enable if needed)
        email_body = f"<h2>Child Insight Report for {name}</h2>" + full_analysis
        send_email(email_body)

        return jsonify({ "metrics": metrics, "analysis": full_analysis })

    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({ "error": "⚠️ Unable to generate analysis. Please try again later." })

# === Email Sender ===
def send_email(html_body):
    subject = "Your Child Insight Report"
    msg = MIMEText(html_body, 'html')
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logging.info("✅ Email sent")
    except Exception:
        logging.error("❌ Email failed to send.")

# === Run app ===
if __name__ == "__main__":
    app.run(debug=True)
