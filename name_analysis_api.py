# ✅ OpenAI Prompt
prompt = f"""
You are an educational advisor AI trained on global child development data. Generate a warm and insightful learning advice message for a parent.

👤 Full Legal Name (English): {name}
🈶 Chinese Name: {chinese_name}
⚧️ Gender: {gender}
🎂 Date of Birth: {dob}
📞 Parent's Phone: {phone}
📧 Parent's Email: {email}
🌍 Country: {country}

🎉 Your Personalized AI Analysis:

Based on AI geographical insights and developmental trends among {age_str} {gender.lower()} children in {country}, our system identified key learning approaches that resonate with similar profiles in your area.

Please include:
- Age-appropriate educational advice
- Localized and cultural recommendations
- Suggestions for creativity, focus, and cognitive growth

📊 Important AI Insight from Similar Profiles:

Our AI analyzed developmental trends among children in the same age group, gender, and region as {name}. It uncovered patterns that show how early support can shape outcomes dramatically.

- ✅ A significant proportion of children who received timely, personalized learning support demonstrated noticeable gains in confidence, creativity, and attention span within just a few months.
- ⚠️ On the other hand, a worrying percentage of children who lacked targeted help showed declining interest in learning, especially during key transition years like {age_range}.

These insights reflect the reality of many families — where delayed action led to unnecessary academic or emotional struggles.

🎯 Every child is unique, but trends like these remind us how much timely care can influence a child's long-term growth.

🪄 Final Advice:
✨ That’s why we strongly encourage you to take one more step — talk to a real human from our educational team on Telegram at @katachat007.

Let’s zoom in on your child’s character and evolving needs. Together, we’ll help them thrive with precise strategies, the right tutor, and tools designed just for them.

Your child deserves this clarity — and we’re here to walk that journey with you. 🌱
"""

# ✅ DEBUG Prompt Output
print("📝 Prompt sent to OpenAI:")
print(prompt)

# ✅ OpenAI API Call + Safe Output Handling
try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.9,
        messages=[{"role": "user", "content": prompt}]
    )
    message = response.choices[0].message.content.strip()
    if not message:
        print("❌ GPT response is empty.")
        message = "⚠️ No analysis could be generated at this time."
except Exception as e:
    print("❌ OpenAI error:", e)
    message = "⚠️ No analysis could be generated due to a system error."

# ✅ Final Cleaned Return
clean = re.sub(r"<[^>]+>", "", message)
return jsonify({"analysis": clean})
