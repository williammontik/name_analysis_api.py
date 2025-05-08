# ... (Previous imports remain the same)

# —–––––––––––––––––––––––––––––––––––––––––––––
# Updated Configuration for Matplotlib
# —–––––––––––––––––––––––––––––––––––––––––––––
plt.style.use('seaborn')
matplotlib.rcParams['font.family'] = 'Roboto'
matplotlib.rcParams['axes.titlepad'] = 20
COLOR_PALETTE = ['#2980b9', '#2ecc71', '#e74c3c', '#9b59b6']

# —–––––––––––––––––––––––––––––––––––––––––––––
# Enhanced Chart Generation Functions
# —–––––––––––––––––––––––––––––––––––––––––––––

def create_bar_chart(data, title):
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(data.keys(), data.values(), color=COLOR_PALETTE, edgecolor='none')
    ax.set_title(title, fontsize=16, fontweight='bold', color='#2c3e50')
    ax.set_ylabel("Percentage (%)", fontsize=12)
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height}%', ha='center', va='bottom',
                fontsize=10, color='#2c3e50')
    
    return fig

def create_pie_chart(data, title):
    fig, ax = plt.subplots(figsize=(8, 5))
    wedges, texts, autotexts = ax.pie(
        data.values(), 
        labels=data.keys(), 
        autopct="%1.1f%%", 
        startangle=140,
        colors=COLOR_PALETTE,
        textprops={'fontsize': 12},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    ax.set_title(title, fontsize=16, fontweight='bold', color='#2c3e50', pad=20)
    plt.setp(autotexts, size=12, weight='bold', color='white')
    return fig

# —–––––––––––––––––––––––––––––––––––––––––––––
# Updated HTML Template with Modern Styling
# —–––––––––––––––––––––––––––––––––––––––––––––

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Learning Patterns Analysis | KataChatBot AI</title>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Condensed:wght@700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2980b9;
      --secondary: #2ecc71;
      --accent: #e74c3c;
      --dark: #2c3e50;
      --light: #ecf0f1;
    }
    
    body {
      font-family: 'Roboto', sans-serif;
      margin: 0;
      padding: 40px;
      color: #444;
      background: #f8f9fa;
      line-height: 1.6;
      animation: fadeIn 0.8s ease;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      padding: 40px;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    h1 {
      color: var(--dark);
      font-family: 'Roboto Condensed', sans-serif;
      font-size: 2.4em;
      margin-bottom: 10px;
      border-bottom: 3px solid var(--primary);
      padding-bottom: 15px;
    }
    
    h2 {
      color: var(--dark);
      font-family: 'Roboto Condensed', sans-serif;
      margin-top: 30px;
      padding-bottom: 10px;
      position: relative;
    }
    
    h2::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 60px;
      height: 3px;
      background: var(--primary);
    }
    
    .charts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 30px;
      margin: 40px 0;
    }
    
    .charts img {
      width: 100%;
      border-radius: 12px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.1);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .charts img:hover {
      transform: translateY(-5px);
      box-shadow: 0 12px 25px rgba(0,0,0,0.15);
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 25px 0;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 15px rgba(0,0,0,0.1);
      animation: slideIn 0.6s ease;
    }
    
    th, td {
      padding: 15px 20px;
      text-align: left;
      border-bottom: 1px solid #eee;
    }
    
    th {
      background: var(--primary);
      color: white;
      font-weight: 500;
      text-transform: uppercase;
      font-size: 0.9em;
    }
    
    tr:nth-child(even) {
      background: #f8fafb;
    }
    
    tr:hover {
      background: #f1f8ff;
      transform: scale(1.02);
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      transition: all 0.2s ease;
    }
    
    .analysis-box {
      background: linear-gradient(145deg, #f8f9fa, #ffffff);
      padding: 25px;
      border-radius: 12px;
      border-left: 4px solid var(--primary);
      margin: 30px 0;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .analysis-text {
      white-space: pre-wrap;
      font-family: 'Roboto Mono', monospace;
      line-height: 1.8;
      color: #2c3e50;
      font-size: 0.95em;
    }
    
    footer {
      margin-top: 50px;
      text-align: center;
      color: #666;
      font-size: 0.9em;
      padding: 20px;
      border-top: 1px solid #eee;
    }
    
    @keyframes slideIn {
      from { opacity: 0; transform: translateX(-20px); }
      to { opacity: 1; transform: translateX(0); }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>📊 Learning Patterns Analysis</h1>
    <div class="header-info">
      <p><strong>Subject:</strong> {{ age }}-year-old in {{ country }} &bull; 
         <strong>Date:</strong> {{ today }}</p>
    </div>

    {% if chart1 and chart2 %}
    <div class="charts">
      <img src="{{ chart1 }}" alt="Learning Preferences">
      <img src="{{ chart2 }}" alt="Study Habits">
    </div>
    {% endif %}

    <!-- Rest of the template sections remain similar but use updated classes -->
    
    <h2>6. AI Analysis</h2>
    <div class="analysis-box">
      <pre class="analysis-text">{{ analysis }}</pre>
    </div>

    <footer>
      Report generated by KataChatBot AI • Confidential & Proprietary • {{ today }}
    </footer>
  </div>
</body>
</html>
"""

# —–––––––––––––––––––––––––––––––––––––––––––––
# Updated Analyze Endpoint with New Charts
# —–––––––––––––––––––––––––––––––––––––––––––––

@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    # ... (Previous processing code remains the same)
    
    # Updated chart generation section
    try:
        chart1 = encode_fig_to_base64(create_bar_chart(prefs, "Learning Preferences"))
        chart2 = encode_fig_to_base64(create_pie_chart(habits, "Study Habits"))
    except Exception as e:
        app.logger.error(f"Chart generation failed: {str(e)}", exc_info=True)
        chart1 = chart2 = None

    # ... (Rest of the endpoint code remains the same)

    return render_template_string(HTML_TEMPLATE, ...)  # Use updated template

# ... (Rest of the code remains the same)
