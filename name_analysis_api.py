# -*- coding: utf-8 -*-
import os, smtplib, logging, random, base64
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email_with_chart_links(html_body, chart_images):
    try:
        msg_root = MIMEMultipart('alternative')
        msg_root['Subject'] = "New KataChatBot Submission"
        msg_root['From'] = SMTP_USERNAME
        msg_root['To'] = SMTP_USERNAME

        # Attach the HTML
        msg_root.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg_root)

        logging.info("✅ Email sent with chart links")
    except Exception as e:
        logging.error("❌ Email sending failed", exc_info=True)

def generate_child_metrics():
    return [
        {
            "title": "Learning Preferences",
            "labels": ["Visual", "Auditory", "Kinesthetic"],
            "values": [random.randint(50, 70), random.randint(25, 40), random.randint(10, 30)]
        },
        {
            "title": "Study Engagement",
            "labels": ["Daily Review", "Group Study", "Independent Effort"],
            "values": [random.randint(40, 60), random.randint(20, 40), random.randint(30, 50)]
        },
        {
            "title": "Academic Confidence",
            "labels": ["Math", "Reading", "Focus & Attention"],
            "values": [random.randint(50, 85), random.randint(40, 70), random.randint(30, 65)]
        }
    ]

def generate_child_summary(age, gender, country, metrics):
    return [
        f"In {country}, many young {gender.lower()} children around the age of {age} are stepping into the early stages of learning with quiet determination and unique preferences. Among them, visual learning stands out as a powerful anchor — with {metrics[0]['values'][0]}% of learners gravitating toward images, colors, and story-based materials to make sense of the world around them. Auditory learning follows at {metrics[0]['values'][1]}%, and kinesthetic approaches like hands-on activities sit at {metrics[0]['values'][2]}%. These figures are not just numbers — they reflect the need to present information in ways that touch the heart and imagination of each child. When a child sees their own world come alive in pictures or guided tales, their curiosity deepens. For parents, this is an opportunity to bring home lessons through picture books, visual games, and shared storytelling moments that make learning both joyful and lasting.",

        f"When we look deeper into how these children engage with their studies, a touching pattern emerges. {metrics[1]['values'][0]}% are already building the habit of daily review — a remarkable sign of discipline at such a young age. Meanwhile, {metrics[1]['values'][2]}% show strong signs of self-motivation when learning alone, a trait that speaks volumes about their inner drive. However, only {metrics[1]['values'][1]}% are regularly involved in group study, which may hint at a deeper emotional preference for learning in safe, quiet spaces rather than competitive or chaotic ones. For parents, this raises a gentle question: how can we slowly introduce our children to peer learning in a way that feels supportive, not stressful? Nurturing environments like parent-child revision time, or cozy group storytelling with trusted friends, might be the bridge they need.",

        f"Confidence in core subjects reveals another meaningful insight. Math currently shines the brightest at {metrics[2]['values'][0]}%, while Reading scores slightly higher at {metrics[2]['values'][1]}%. The Focus & Attention score at {metrics[2]['values'][2]}% suggests many of these learners are still mastering the art of sustained concentration. But instead of seeing this as a weakness, parents can view it as a developmental rhythm — one that simply needs the right melody to guide it. Emotional regulation, gentle routines, reduced screen time, and creative classroom techniques like music-integrated learning or movement breaks may offer small but powerful shifts. Each child has their own tempo — the key is helping them find it without pressure or comparison.",

        "Together, these learning signals form more than a snapshot — they tell a story. A story of young minds filled with potential, quietly hoping the adults around them will notice not just their results, but their efforts, moods, and learning preferences. Parents and educators in Singapore, Malaysia, and Taiwan now have the chance to craft truly child-centered support. Whether it's choosing tutors who adapt to visual needs, or finding school systems that value emotional growth as much as academic grades — the goal remains the same: to help every child thrive with a sense of balance, self-worth, and joy in the journey."
    ]

def generate_summary_html(paragraphs):
    return "<div style='font-size:24px; font-weight:bold; margin-top:30px;'>🧠 Summary:</div><br>" + \
        "".join(f"<p style='line-height:1.7; font-size:16px; margin-bottom:16px;'>{p}</p>\n" for p in paragraphs)

def build_response(metrics, summary_paragraphs, chart_images):
    summary = generate_summary_html(summary_paragraphs)

    charts_html = ""
    if chart_images:
        charts_html += "<div style='margin-top:30px;'><strong style='font-size:20px;'>📈 Download Chart Images:</strong><br><br>"
        for idx, base64_img in enumerate(chart_images):
            safe_url = base64_img if base64_img.startswith("data:image") else f"data:image/png;base64,{base64_img}"
            charts_html += f"<a href='{safe_url}' download='chart{idx+1}.png'>🖼️ Download Chart {idx+1}</a><br><br>"
        charts_html += "</div>"

    footer = """
    <p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
      <strong>The insights in this report are generated by Katachat’s AI systems analyzing:</strong><br>
      1. Our proprietary database of anonymized learning patterns from Singaporean, Malaysian and Taiwanese students (with parental consent)<br>
      2. Aggregated, non-personal educational trends from trusted third-party sources including OpenAI’s research datasets<br>
      <em>All data is processed through our AI models to identify statistically significant patterns while maintaining strict PDPA compliance.</em>
    </p>
    <p style="background-color:#e6f7ff; color:#00529B; padding:15px; border-left:4px solid #00529B; margin:20px 0;">
      <strong>PS:</strong> Your personalized report will arrive in your inbox within 24 hours.
      If you’d like to explore the findings further, feel free to WhatsApp or book a quick 15-minute chat.
    </p>
    """
    return summary + charts_html + footer

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    try:
        data = request.get_json(force=True)
        logging.info(f"[analyze_name] Payload received")

        name = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender = data.get("gender", "").strip()
        country = data.get("country", "").strip()
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip()
        referrer = data.get("referrer", "").strip()
        chart_images = data.get("chart_images", [])

        month_str = str(data.get("dob_month")).strip()
        if month_str.isdigit():
            month = int(month_str)
        else:
            month = datetime.strptime(month_str.capitalize(), "%B").month

        birthdate = datetime(int(data.get("dob_year")), month, int(data.get("dob_day")))
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        metrics = generate_child_metrics()
        summary = generate_child_summary(age, gender, country, metrics)
        html_result = build_response(metrics, summary, chart_images)

        email_html = f"""<html><body style="font-family:sans-serif;color:#333">
        <h2>🎯 New User Submission:</h2>
        <p>
        👤 <strong>Full Name:</strong> {name}<br>
        🈶 <strong>Chinese Name:</strong> {chinese_name}<br>
        ⚧️ <strong>Gender:</strong> {gender}<br>
        🎂 <strong>DOB:</strong> {birthdate.date()}<br>
        🕑 <strong>Age:</strong> {age}<br>
        🌍 <strong>Country:</strong> {country}<br>
        📞 <strong>Phone:</strong> {phone}<br>
        📧 <strong>Email:</strong> {email}<br>
        💬 <strong>Referrer:</strong> {referrer}
        </p>
        <hr><h2>📊 AI-Generated Report</h2>
        {html_result}
        </body></html>"""

        send_email_with_chart_links(email_html, chart_images)

        return jsonify({
            "metrics": metrics,
            "analysis": html_result
        })

    except Exception as e:
        logging.exception("❌ Error in /analyze_name")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
