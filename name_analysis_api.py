import os
import io
import base64
import re
import smtplib
import random
from datetime import datetime
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dateutil import parser

app = Flask(__name__)
CORS(app)

# Logging setup
import logging
app.logger.setLevel(logging.DEBUG)

# OpenAI client setup
from openai import OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(full_name, chinese_name, gender, dob, age, phone, email, country, referrer):
    # ... (keep your existing email function unchanged) ...

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # ... (keep your existing data parsing and age calculation) ...

    # Modified prompt section
    prompt = f"""
Generate a statistical report for {age}-year-old {gender}s in {country} using EXACTLY this format:

**Learning Patterns Analysis for {age}-year-old {gender}s in {country}**

1. Learning Preferences:  
- Visual |{'|' * 4}    |  {random.randint(35,45)}%  
- Auditory |{'|' * 5}   |  {random.randint(50,60)}%  
- Kinesthetic |{'|' * 0}  |  {random.randint(0,10)}%  

2. Study Habits:  
- Regular Study Hours: {random.randint(65,75)}%  
- Group Study Sessions: {random.randint(25,35)}%  
- Prefer Studying Alone: {random.randint(55,65)}%  

3. STEM Learning:  
{gender} performance in Mathematics:  
- Algebra: {random.randint(80,90)}% (Regional: 75%)  
- Geometry: {random.randint(65,75)}% (Global: 60%)  

Regional Comparisons:  
- Study Hours: {country} {random.randint(65,75)}% vs Region 60%  
- Group Study: {country} {random.randint(25,35)}% vs Global 40%  

Top 3 Statistical Findings:
1. {random.randint(50,60)}% prefer auditory learning (+{random.randint(5,15)}% vs global)
2. Algebra scores lead region by {random.randint(10,15)}%
3. {random.randint(65,75)}% maintain regular study hours

Formatting rules:
- Use pipe characters for progress bars
- Align percentages to right
- Keep regional comparisons in parentheses
- Bold section headers only
- No markdown tables
"""

    # ... (keep remaining OpenAI API call and response handling) ...

if __name__ == "__main__":
    app.run(debug=True)
