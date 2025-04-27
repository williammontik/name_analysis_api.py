import os
import re
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI API client using the key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OpenAI API key not set in environment variables.")
client = OpenAI(api_key=openai_api_key)

@app.route('/analyze_name', methods=['POST'])
def analyze_name():
    """Endpoint to analyze a name using OpenAI."""
    # Retrieve the 'name' parameter from JSON body or form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    name = data.get('name', '')
    if not name:
        return jsonify({"error": "No name provided"}), 400

    # Prepare the prompt/message for the OpenAI API
    user_message = f"Please provide a detailed analysis of the name '{name}'."

    try:
        # Call the OpenAI Chat Completion API (GPT-3.5-turbo or GPT-4)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        # Extract the content of the AI's reply
        analysis_text = response.choices[0].message.content
    except Exception as e:
        # Handle any errors (e.g., API errors or timeouts)
        return jsonify({"error": str(e)}), 500

    # Clean HTML tags from the response (e.g., replace <br> with newline)
    clean_text = re.sub(r'(?i)<br\s*/?>', '\n', analysis_text)  # `<br>` -> newline
    clean_text = re.sub(r'<[^>]+>', '', clean_text)             # remove any other HTML tags

    # Return the analysis as plain text in JSON
    return jsonify({"analysis": clean_text})
