import re
import json

@app.route("/boss_analyze", methods=["POST", "OPTIONS"])
@cross_origin()
def boss_analyze():
    data = request.get_json()
    app.logger.info(f"Boss payload: {data}")

    # 1) Build the coaching prompt
    prompt = f'''
You are a friendly leadership coach. Given the following data about a team member:
- Name: {data["memberName"]}
- Role: {data["position"]}
- Department: {data.get("department", "N/A")}
- Years of Experience: {data["experience"]}
- Key Challenge: {data["challenge"]}
- Preferred Focus: {data["focus"]}
- Country: {data["country"]}

Please output ONLY valid JSON with two fields:
1. "metrics": an array of objects, each with:
    - "title": one of ["Leadership","Collaboration","Decision-Making","Communication","Sales Acumen"]
    - "labels": [the same title as a list]
    - "values": [a single number between 0 and 100]
2. "analysis": a brief, friendly & motivating paragraph (2–3 sentences) praising strengths and suggesting one next step.
'''

    # 2) Call OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content
    app.logger.debug("Raw AI output (boss):\n" + raw)

    # 3) Clean and parse JSON
    #   Remove markdown fences and whitespace
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        result = json.loads(cleaned)
    except Exception as e:
        app.logger.error("Failed to parse boss JSON, falling back to dummy", exc_info=True)

        # 4) Dummy fallback
        result = {
            "metrics": [
                {"title":"Leadership","labels":["Leadership"],"values":[75]},
                {"title":"Collaboration","labels":["Collaboration"],"values":[70]},
                {"title":"Decision-Making","labels":["Decision-Making"],"values":[65]},
                {"title":"Communication","labels":["Communication"],"values":[80]},
                {"title":"Sales Acumen","labels":["Sales Acumen"],"values":[60]}
            ],
            "analysis": (
                f"Here’s a quick analysis for {data.get('memberName')}: "
                "Your Collaboration and Communication are strong. "
                "Next, focus on Decision-Making to take your team to the next level!"
            )
        }

    # 5) Return the (real or fallback) result
    return jsonify(result)
