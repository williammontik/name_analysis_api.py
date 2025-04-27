import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅
from openai import OpenAI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # ✅ ALLOW ALL ORIGINS

# Initialize OpenAI API client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set in environment variables.")
client = OpenAI(api_key=openai_api_key)

@app.route('/analyze_name', methods=['POST'])
def analyze_name():
    """Endpoint to analyze a name using OpenAI."""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    name = data.get('name', '')
    if not name:
        return jsonify({"error": "No name provided"}), 400

    user_message = f"Please provide a detailed analysis of the name '{name}'."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        analysis_text = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    clean_text = re.sub(r'(?i)<br\s*/?>', '\n', analysis_text)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)

    return jsonify({"analysis": clean_text})
