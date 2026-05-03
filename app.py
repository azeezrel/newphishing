from flask import Flask, render_template, render_template_string, request, jsonify
import pickle
import time
import os

app = Flask(__name__)

# Load model and vectorizer with error handling
try:
    print("Loading models...")
    with open('models/phishing_detector.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("✅ Models loaded successfully!")
except FileNotFoundError as e:
    print(f"❌ Error: {e}")
    print("Please run 'python create_models.py' first to create the models")
    exit(1)

# In-memory counters for simple live stats (persist only while app runs)
counters = { 'total': 0, 'phishing': 0 }

# Beautiful HTML for main page
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phishing Email Detector</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            font-family: monospace;
            resize: vertical;
            transition: border-color 0.3s;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 15px;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            animation: slideIn 0.5s ease;
        }
        
        .phishing {
            background: #fee;
            border-left: 4px solid #e74c3c;
            color: #c0392b;
        }
        
        .safe {
            background: #e8f5e9;
            border-left: 4px solid #27ae60;
            color: #2e7d32;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .dashboard-link {
            text-align: center;
            margin-top: 20px;
        }
        
        .dashboard-link a {
            color: white;
            text-decoration: none;
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            transition: background 0.3s;
        }
        
        .dashboard-link a:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .example-section {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .example-btn {
            background: #ecf0f1;
            color: #2c3e50;
            padding: 8px 15px;
            font-size: 12px;
            margin: 5px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
        }
        
        .example-btn:hover {
            background: #d5dbdb;
            transform: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI Phishing Email Detector</h1>
            <p>Paste an email to detect if it's a phishing attempt</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <textarea name="email" rows="10" placeholder="Paste the email content here..."></textarea>
                <br>
                <button type="submit">🔍 Analyze Email</button>
            </form>
            
            <div class="example-section">
                <small>📝 Quick test examples:</small><br>
                <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Phishing Example</button>
                <button type="button" class="example-btn" onclick="fillSafe()">✅ Safe Example</button>
            </div>
            
            {% if result %}
                <div class="result {% if 'PHISHING' in result %}phishing{% else %}safe{% endif %}">
                    <h3>{{ result }}</h3>
                    {% if 'PHISHING' in result %}
                        <p>⚠️ Do not click any links or reply to this email.</p>
                        <p>🔐 Report this to your IT security team immediately.</p>
                    {% else %}
                        <p>✅ This email appears to be legitimate.</p>
                        <p>💡 Always remain vigilant with unexpected emails.</p>
                    {% endif %}
                </div>
            {% endif %}
        </div>
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 View Live Dashboard →</a>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.querySelector('textarea[name="email"]').value = `URGENT: Your Account Has Been Compromised!

Dear Valued Customer,

We detected suspicious activity on your account. To prevent permanent closure, you must verify your identity immediately.

Click here to verify: http://fake-security-verify.com/account

Failure to verify within 24 hours will result in account suspension.

Sincerely,
Security Department`;
        }
        
        function fillSafe() {
            document.querySelector('textarea[name="email"]').value = `Weekly Team Meeting - Tomorrow at 10AM

Hi Team,

Just a reminder about our meeting tomorrow at 10 AM in Conference Room B.

Agenda:
- Project updates
- Q3 planning
- Team building discussion

Please come prepared with your updates.

Best regards,
Manager`;
        }
    </script>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email and email.strip():
            try:
                # Transform and predict
                vec = vectorizer.transform([email])
                pred = model.predict(vec)[0]
                
                # Update counters
                counters['total'] += 1
                if int(pred) == 1:
                    counters['phishing'] += 1
                
                result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
                print(f"✅ Analyzed email - Result: {result} (Total: {counters['total']}, Phishing: {counters['phishing']})")
            except Exception as e:
                print(f"Error analyzing email: {e}")
                result = "❌ Error analyzing email. Please try again."
        else:
            result = "⚠️ Please paste an email to analyze."
    
    return render_template_string(HTML, result=result)


@app.route('/dashboard')
def dashboard():
    # Make sure templates folder exists
    return render_template('dashboard.html')


@app.route('/stats')
def stats():
    total = counters.get('total', 0)
    phishing = counters.get('phishing', 0)
    safe = total - phishing
    rate = (phishing / total) if total > 0 else 0.0
    return jsonify({
        'time': time.strftime('%H:%M:%S'),
        'total': total,
        'phishing': phishing,
        'safe': safe,
        'phishing_rate': round(rate, 4)
    })


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🛡️ PHISHING DETECTION WEB APP")
    print("="*50)
    print(f"✅ Models loaded successfully!")
    print(f"📧 Web App: http://127.0.0.1:5000")
    print(f"📊 Dashboard: http://127.0.0.1:5001")
    print("="*50)
    print("\n⚠️  Make sure dashboard.py is running in another terminal!")
    print("   Command: python dashboard.py")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)