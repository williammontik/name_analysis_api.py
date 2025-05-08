# ✅ API Endpoint
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    name = data.get("name", "").strip()
    chinese_name = data.get("chineseName", "").strip()
    gender = data.get("gender", "").strip()
    dob_day = data.get("dob_day", "").strip()
    dob_month = data.get("dob_month", "").strip()
    dob_year = data.get("dob_year", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    country = data.get("country", "").strip()

    if not name:
        return jsonify({"error": "No name provided"}), 400

    # ✅ Combine dob_day, dob_month, dob_year into a single dob
    try:
        dob = f"{dob_day} {dob_month} {dob_year}"
        # Calculate age
        month = datetime.strptime(dob_month, "%B").month
        birthdate = datetime(int(dob_year), month, int(dob_day))
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except Exception as e:
        print(f"❌ Error calculating age: {e}")
        dob = "Unknown"
        age = "Unknown"

    # ✅ Send email
    try:
        send_email(name, chinese_name, gender, dob, age, phone, email, country)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    # ✅ Smarter randomized stats
    base_improve = random.randint(65, 80)
    base_struggle = random.randint(30, 45)
    if base_struggle >= base_improve - 5:
        base_struggle = base_improve - random.randint(10, 15)
    improved_percent = round(base_improve / 5) * 5
    struggle_percent = round(base_struggle / 5) * 5

    # ✅ OpenAI analysis
    prompt = f"""
You are an elite educational advisor AI trained on deep global datasets about children’s development and academic psychology. Speak warmly and emotionally — like a trusted friend who understands parental concerns. Mix data, storytelling, and practical advice.

Child Profile:
- Full Name: {name}
- Chinese Name: {chinese_name}
- Gender: {gender}
- Date of Birth: {dob}
- Parent's Phone: {phone}
- Parent's Email: {email}
- Country: {country}
- Age: {age}

AI Insight:
Children aged {age} in {country} often face invisible crossroads — some grow curious and focused, while others start showing signs of detachment or learning fatigue.

📊 Our AI has identified that:
- Around {improved_percent}% of children in this age/gender/location profile who got timely, personalized help experienced a transformation: greater confidence, better attention span, and joyful participation in school.
- But about {struggle_percent}% of children who didn’t get targeted support slipped into patterns of frustration, resistance to learning, emotional withdrawal — sometimes unnoticed until it became serious.

💡 This is not fear — it’s foresight.

Advice:
1. Spark Curiosity: Let them explore through art, music, nature, or experiments — things that make them ask more questions.
2. Give Structure: Routine builds safety. Focus games, light challenges, and time-blocked play can reshape attention span.
3. Emotional Coaching: Teach naming feelings, and encourage expression — children who feel seen will stay open to learning.

In {country}, we’ve also seen cultural tools (like traditional stories, values of diligence and filial piety, or expressive arts) play a major role in turning kids around. Use what’s already meaningful in your community.

Final Advice:
Your child’s character today is only one version of their future. The biggest danger is assuming things will fix themselves.

That’s why we strongly recommend you speak directly to one of our real human learning specialists at @katachat007 (Telegram). We’ll zoom into your child’s specific personality, recommend the right type of tutor, and guide you through this age band with precision and heart.

Your child deserves more than average answers. Let’s build the learning path that fits them best — together.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ✅ Clean output
    clean = re.sub(r"<[^>]+>", "", analysis)
    return jsonify({"analysis": clean})
