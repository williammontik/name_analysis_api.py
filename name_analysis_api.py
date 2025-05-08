import os
import re
import smtplib
import random
import matplotlib.pyplot as plt
import numpy as np
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
from datetime import datetime

# ✅ Flask App
app = Flask(__name__)
CORS(app)

# ✅ OpenAI API Key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set.")
client = OpenAI(api_key=openai_api_key)

# ✅ Email settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# ✅ Email Function
def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    subject = "New KataChatBot User Submission"
    body = f"""
🎯 New User Submission:

👤 Full Legal Name: {full_name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 Date of Birth: {dob}
🎯 Age: {age} years old
🌍 Country: {country}

📞 Phone: {phone}
📧 Email: {email}
💬 Referrer: {referrer}
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = SMTP_USERNAME

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# ✅ System Instructions for OpenAI Assistant
system_message = """
You are an elite educational advisor AI trained on deep global datasets about children’s development and academic psychology. Speak warmly and emotionally, like a trusted friend who understands parental concerns. Mix data, storytelling, and practical advice.

Your responses should focus on helping parents navigate challenges and support their children's development. When giving advice, include actionable steps based on the child's profile, such as curiosity, structure, emotional coaching, and cultural insights.
"""

# ✅ API Endpoint
@app.route("/generate_learning_report", methods=["POST"])
def generate_learning_report():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    country = data.get("country", "").strip()
    age = data.get("age", "").strip()
    gender = data.get("gender", "").strip()

    if not country or not age or not gender:
        return jsonify({"error": "Missing data for country, age, or gender."}), 400

    # ✅ Geographical and Gender-Based Data Insights
    # Example: Data reflecting general trends for children in specific countries, age, and gender
    # This data can be replaced with actual statistics if available
    age_group = int(age)
    gender_group = gender.lower()
    
    # Simulating learning trends data in percentage for different countries
    if country == "USA":
        data_improve = {"male": 72, "female": 78}
        data_struggle = {"male": 28, "female": 22}
    elif country == "Singapore":
        data_improve = {"male": 75, "female": 80}
        data_struggle = {"male": 25, "female": 20}
    else:
        # Default case: Adjust for unknown countries
        data_improve = {"male": 70, "female": 76}
        data_struggle = {"male": 30, "female": 24}
    
    # Adjust data based on age group (you can fine-tune this)
    improvement_percent = data_improve[gender_group]
    struggle_percent = data_struggle[gender_group]

    # Simulate seasonal effects (learning improvement during exam season, summer breaks, etc.)
    seasonal_improvement = improvement_percent * 1.1  # 10% improvement during school months
    seasonal_struggle = struggle_percent * 0.9        # 10% less struggle during holiday breaks

    # Create a dynamic chart to represent the data
    categories = ['Improvement (%)', 'Struggle (%)', 'Seasonal Improvement', 'Seasonal Struggle']
    values = [improvement_percent, struggle_percent, seasonal_improvement, seasonal_struggle]

    # Plotting the bar chart
    fig, ax = plt.subplots()
    ax.bar(categories, values, color=['green', 'red', 'blue', 'orange'])
    ax.set_ylabel('Percentage (%)')
    ax.set_title(f'Learning Trends for Children in {country} (Age: {age}, Gender: {gender.capitalize()})')

    # Save the plot to a file and return the file path
    chart_file_path = "/mnt/data/learning_trends_chart.png"
    plt.savefig(chart_file_path)

    # ✅ OpenAI analysis (country-wide trends)
    prompt = f"""
    Learning trends for children aged {age} in {country}:

    In {country}, children of the age group {age_group} (gender: {gender_group}) experience varying learning outcomes based on educational support, cultural factors, and seasonal influences. Here's an overview of the trends:

    📊 **Improvement with proper guidance**:
    - Around {seasonal_improvement}% of children (gender: {gender_group}) improve their learning outcomes significantly with proper guidance and targeted support.

    📉 **Struggle due to lack of support**:
    - Approximately {seasonal_struggle}% of children in this age/gender group face challenges due to insufficient educational support or lack of engagement.

    🗓️ **Seasonal Learning Variations**:
    - During peak academic periods (such as exam seasons), learning improvement is observed to increase by around 10%.
    - During summer or holiday breaks, the rate of struggle decreases by around 10% as children typically have more time for personal development and relaxation.

    💡 **What can parents do?**
    1. Provide structured learning activities that can be adjusted throughout the year, focusing on curiosity and exploration.
    2. Encourage emotional coaching and regular engagement to ensure children stay motivated and focused.
    3. Utilize seasonal breaks for light but consistent learning to maintain their engagement without overloading them.

    **Final Advice**:
    The learning behavior of children in {country} varies significantly depending on the time of the year and the support they receive. Parents should adapt their approach accordingly and make use of peak learning seasons to maximize their child’s development.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Replace with your fine-tuned model if necessary
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ✅ Clean output
    clean = re.sub(r"<[^>]+>", "", analysis)

    # ✅ Return the final analysis and chart
    return jsonify({
        "analysis": clean,
        "chart_url": chart_file_path
    })

if __name__ == "__main__":
    app.run(debug=True)
