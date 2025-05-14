import os
import logging
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

# ── Flask Setup ─────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  
app.logger.setLevel(logging.DEBUG)

# ── /analyze_name Endpoint ───────────────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[analyze_name] payload: {data}")

        # ... your existing name-analysis logic here ...
        # For brevity, we'll just echo back a dummy response:

        dummy_metrics = [{
            "title": "Learning Preferences",
            "labels": ["Visual", "Auditory", "Kinesthetic"],
            "values": [75, 50, 25]
        }]
        return jsonify({
            "metrics": dummy_metrics,
            "analysis": f"Hello {data.get('name')}, here is your child report."
        })

    except Exception as e:
        app.logger.exception("Error in /analyze_name")
        return jsonify({"error": str(e)}), 500


# ── /boss_analyze Endpoint ───────────────────────────────────────────────────
@app.route("/boss_analyze", methods=["POST"])
def boss_analyze():
    try:
        data = request.get_json(force=True)
        app.logger.info(f"[boss_analyze] payload: {data}")

        # TODO: replace the dummy logic below with your real OpenAI & chart calculations
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
            "- Team shows high Trust but needs more Collaboration."
        )

        return jsonify({
            "metrics": dummy_metrics,
            "analysis": dummy_analysis
        })

    except Exception as e:
        app.logger.exception("Error in /boss_analyze")
        return jsonify({"error": str(e)}), 500


# ── Run Locally ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
