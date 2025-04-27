import os
import re
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)

# ✅ OpenAI API Key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set in environment variables.")
client = OpenAI(api_key=openai_api_key)

# ✅ Email SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"  # Your Gmail
SMTP_PASSWORD = "haywkvoyoaykvkul"         # Your App Password (no spaces)

# ✅ Function to send email
def send_email(full_name, phone, email, address):
    subject = "New User Submission from KataChatBot"
    body = f"""
New User Submission:

👤 Full Name: {full_name}
📞 Phone: {phone}
📧 Email: {email}
🏠 Address: {address}
"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# ✅ Main Route
@app.route('/analyze_name', methods=['POST'])
def analyze_name():
    """Endpoint to analyze a name and email user data."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    address = data.get('address', '').strip()

    if not name:
        return jsonify({"error": "No name provided"}), 400

    # ✅ Start sending email in background (no user wait)
    try:
        send_email(name, phone, email, address)
    except Exception as e:
        print(f"Failed to send email: {e}")

    # ✅ Prepare OpenAI prompt
    user_message = f"Please provide professional educational advice based on internal assessment results for a child profile. (Background information only, not for direct analysis): {name}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        analysis_text = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ✅ Clean up AI output
    clean_text = re.sub(r'(?i)<br\s*/?>', '\n', analysis_text)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)

    return jsonify({"analysis": clean_text})
