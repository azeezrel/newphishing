from flask import Flask, render_template_string, request, jsonify
import pickle
import time
import os

app = Flask(__name__)

print("="*50)
print("Starting Phishing Detector Web App")
print("="*50)

# Check if models exist
if not os.path.exists('models/phishing_detector.pkl'):
    print("❌ Models not found! Creating sample models...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing = ["urgent click link verify account suspended", "your account has been compromised"]
    safe = ["meeting tomorrow at 10am", "project deadline friday"]
    all_text = phishing + safe
    labels = [1, 1, 0, 0]
    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(all_text)
    model = RandomForestClassifier()
    model.fit(X, labels)
    
    os.makedirs('models', exist_ok=True)
    with open('models/phishing_detector.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    print("✅ Sample models created!")
else:
    print("Loading existing models...")
    with open('models/phishing_detector.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("✅ Models loaded!")

# Simple counters
counters = {'total': 0, 'phishing': 0}

# Simple HTML interface
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            font-family: monospace;
            box-sizing: border-box;
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
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            animation: fadeIn 0.5s;
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
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .dashboard-link {
            text-align: center;
            margin-top: 20px;
        }
        .dashboard-link a {
            color: #667eea;
            text-decoration: none;
        }
        .example-btn {
            background: #ecf0f1;
            color: #333;
            padding: 5px 10px;
            font-size: 12px;
            margin: 5px;
            cursor: pointer;
            border: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Phishing Email Detector</h1>
        
        <form method="POST">
            <textarea name="email" rows="8" placeholder="Paste email content here..."></textarea>
            <br>
            <button type="submit">🔍 Analyze Email</button>
        </form>
        
        <div style="margin-top: 10px;">
            <small>Test examples:</small>
            <button type="button" class="example-btn" onclick="fillPhishing()">Phishing Example</button>
            <button type="button" class="example-btn" onclick="fillSafe()">Safe Example</button>
        </div>
        
        {% if result %}
            <div class="result {{ 'phishing' if 'PHISHING' in result else 'safe' }}">
                <h3>{{ result }}</h3>
                {% if 'PHISHING' in result %}
                    <p>⚠️ Do not click any links or reply to this email!</p>
                {% else %}
                    <p>✅ This email appears to be legitimate.</p>
                {% endif %}
            </div>
        {% endif %}
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 Open Live Dashboard →</a>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.querySelector('textarea[name="email"]').value = "URGENT: Your account has been compromised! Click here to verify immediately: http://fake-bank.com/verify";
        }
        function fillSafe() {
            document.querySelector('textarea[name="email"]').value = "Meeting reminder: Project review at 2pm in Conference Room A";
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
            vec = vectorizer.transform([email])
            pred = model.predict(vec)[0]
            counters['total'] += 1
            if pred == 1:
                counters['phishing'] += 1
            result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
            print(f"✅ Analyzed: {result} (Total: {counters['total']})")
    
    return render_template_string(HTML, result=result)

@app.route('/dashboard')
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Dashboard</title>
        <style>
            body {
                font-family: Arial;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
            }
            h1 { text-align: center; }
            .stat-card {
                background: #f8f9fa;
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                text-align: center;
            }
            .stat-number {
                font-size: 3em;
                font-weight: bold;
                margin: 10px 0;
            }
            .phishing { color: #e74c3c; }
            .safe { color: #27ae60; }
            .total { color: #3498db; }
            .live-badge {
                background: #e74c3c;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                display: inline-block;
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.6; }
                100% { opacity: 1; }
            }
            button {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Live Detection Dashboard</h1>
            <div style="text-align: center;">
                <span class="live-badge">🔴 LIVE UPDATES</span>
            </div>
            
            <div class="stat-card">
                <h3>Total Scans</h3>
                <div class="stat-number total" id="total">0</div>
            </div>
            
            <div class="stat-card">
                <h3>Phishing Detected</h3>
                <div class="stat-number phishing" id="phishing">0</div>
            </div>
            
            <div class="stat-card">
                <h3>Safe Emails</h3>
                <div class="stat-number safe" id="safe">0</div>
            </div>
            
            <div class="stat-card">
                <h3>Phishing Rate</h3>
                <div class="stat-number phishing" id="rate">0%</div>
            </div>
            
            <div style="text-align: center;">
                <button onclick="refreshData()">🔄 Refresh</button>
            </div>
            
            <p style="text-align: center; margin-top: 20px; color: #999;">
                Last updated: <span id="time">Never</span>
            </p>
        </div>
        
        <script>
            function refreshData() {
                fetch('/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('total').innerText = data.total;
                        document.getElementById('phishing').innerText = data.phishing;
                        document.getElementById('safe').innerText = data.total - data.phishing;
                        document.getElementById('rate').innerText = (data.phishing_rate * 100).toFixed(1) + '%';
                        document.getElementById('time').innerText = data.time;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('total').innerText = 'Error';
                    });
            }
            
            refreshData();
            setInterval(refreshData, 3000);
        </script>
    </body>
    </html>
    ''')

@app.route('/stats')
def stats():
    total = counters['total']
    phishing = counters['phishing']
    rate = (phishing / total) if total > 0 else 0
    return jsonify({
        'time': time.strftime('%H:%M:%S'),
        'total': total,
        'phishing': phishing,
        'phishing_rate': round(rate, 4)
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 STARTING WEB APP ON PORT 5000")
    print("="*50)
    print("📍 Open your browser and go to:")
    print("   http://127.0.0.1:5000")
    print("")
    print("📊 Dashboard will be at:")
    print("   http://127.0.0.1:5000/dashboard")
    print("")
    print("⚠️  Press CTRL+C to stop the server")
    print("="*50 + "\n")
    
    try:
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
