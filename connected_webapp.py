from flask import Flask, render_template_string, request, jsonify
import pickle
import os
from datetime import datetime
from flask_cors import CORS
import re
import requests

app = Flask(__name__)
CORS(app)

print("="*60)
print("PHISHING DETECTOR - CONNECTED TO DASHBOARD")
print("="*60)

# Load models
if not os.path.exists('models/phishing_detector.pkl'):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing = ["urgent click link verify account", "your account has been compromised", "verify your account immediately"]
    safe = ["meeting tomorrow at 10am", "project deadline is friday", "team lunch at 12pm"]
    
    all_emails = phishing + safe
    labels = [1,1,1,0,0,0]
    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(all_emails)
    model = RandomForestClassifier()
    model.fit(X, labels)
    
    os.makedirs('models', exist_ok=True)
    with open('models/phishing_detector.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    print("✅ Models created!")
else:
    with open('models/phishing_detector.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("✅ Models loaded!")

def extract_urls(email_text):
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, email_text)

def check_url_phishtank(url):
    try:
        response = requests.post("https://check.phishtank.com/checkurl/", 
                                data={'url': url, 'format': 'json'},
                                headers={'User-Agent': 'PhishingDetector/1.0'},
                                timeout=5)
        if response.status_code == 200:
            return response.json().get('results', {}).get('in_database', False)
    except:
        pass
    return False

# Store local data
scan_data = {'total': 0, 'phishing': 0, 'history': [], 'recent': []}

# HTML
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 20px; padding: 30px; }
        h1 { text-align: center; color: #333; }
        textarea { width: 100%; padding: 15px; border: 2px solid #ddd; border-radius: 10px; margin: 10px 0; font-family: monospace; }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; }
        .result { margin-top: 20px; padding: 20px; border-radius: 10px; }
        .phishing { background: #fee; border-left: 4px solid #e74c3c; color: #c0392b; }
        .safe { background: #e8f5e9; border-left: 4px solid #27ae60; color: #2e7d32; }
        .dashboard-link { text-align: center; margin-top: 20px; }
        .dashboard-link a { color: white; background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 25px; text-decoration: none; display: inline-block; }
        .example-btn { background: #ecf0f1; color: #333; padding: 5px 10px; font-size: 12px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ AI Phishing Detector</h1>
        
        <form method="POST">
            <textarea name="email" rows="8" placeholder="Paste email content here..."></textarea><br>
            <button type="submit">🔍 Analyze Email</button>
        </form>
        
        <div style="margin-top: 10px;">
            <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Phishing Email</button>
            <button type="button" class="example-btn" onclick="fillSafe()">✅ Safe Email</button>
        </div>
        
        {% if result %}
            <div class="result {{ 'phishing' if 'PHISHING' in result else 'safe' }}">
                <h3>{{ result }}</h3>
            </div>
        {% endif %}
        
        <div class="dashboard-link">
            <a href="http://127.0.0.1:5001" target="_blank">📊 Open Dashboard (Port 5001) →</a>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.querySelector('textarea').value = "URGENT: Your PayPal account has been limited! Verify now: http://fake-paypal-verify.com/secure";
        }
        function fillSafe() {
            document.querySelector('textarea').value = "Meeting reminder: Project review tomorrow at 2pm";
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email:
            vec = vectorizer.transform([email])
            pred = model.predict(vec)[0]
            is_phishing = pred == 1
            
            # Update local stats
            scan_data['total'] += 1
            if is_phishing:
                scan_data['phishing'] += 1
            
            # SEND TO DASHBOARD ON PORT 5001
            try:
                dashboard_response = requests.post('http://127.0.0.1:5001/analyze', 
                                                   json={'email': email},
                                                   timeout=2)
                print(f"✅ Sent to dashboard: {dashboard_response.status_code}")
            except Exception as e:
                print(f"⚠️ Dashboard not running on port 5001: {e}")
            
            result = "⚠️ PHISHING DETECTED!" if is_phishing else "✅ SAFE EMAIL"
    
    return render_template_string(MAIN_PAGE, result=result)

@app.route('/api/stats')
def get_stats():
    return jsonify(scan_data)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 WEB APP RUNNING")
    print("="*60)
    print("Web App: http://127.0.0.1:5000")
    print("Dashboard: http://127.0.0.1:5001 (must be running)")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
