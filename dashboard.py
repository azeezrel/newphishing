from flask import Flask, render_template_string, request, jsonify
import pickle
from datetime import datetime
import os

app = Flask(__name__)

print("Loading model...")

# Load model
if not os.path.exists('models/phishing_detector.pkl'):
    print("❌ Model not found! Please run the web app first to create models.")
    print("Run: py -3.11 connected_webapp.py")
    exit(1)

with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)

with open('models/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

print("✅ Model loaded!")

# Statistics storage
stats = {
    'total_scans': 0,
    'phishing_detected': 0,
    'safe_emails': 0,
    'recent_scans': [],
    'hourly_data': {}
}

def analyze_email(email_text):
    vec = vectorizer.transform([email_text[:2000]])
    pred = model.predict(vec)[0]
    is_phishing = pred == 1
    
    stats['total_scans'] += 1
    if is_phishing:
        stats['phishing_detected'] += 1
    else:
        stats['safe_emails'] += 1
    
    scan_record = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_phishing': is_phishing,
        'email_preview': email_text[:100] + '...' if len(email_text) > 100 else email_text
    }
    stats['recent_scans'].insert(0, scan_record)
    stats['recent_scans'] = stats['recent_scans'][:50]
    
    hour = datetime.now().strftime('%Y-%m-%d %H:00')
    stats['hourly_data'][hour] = stats['hourly_data'].get(hour, 0) + 1
    
    return is_phishing

# HTML Dashboard
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-top: 10px;
        }
        .phishing { color: #e74c3c; }
        .safe { color: #27ae60; }
        .total { color: #3498db; }
        .scans-list {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        .scan-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .phishing-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
        }
        .safe-badge {
            background: #27ae60;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
        }
        .timestamp {
            color: #999;
            font-size: 0.8em;
        }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #2980b9;
        }
        .status {
            text-align: center;
            color: white;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Phishing Detection Dashboard</h1>
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 Total Scans</h3>
                <div class="stat-number total">{{ stats.total_scans }}</div>
            </div>
            <div class="stat-card">
                <h3>⚠️ Phishing Detected</h3>
                <div class="stat-number phishing">{{ stats.phishing_detected }}</div>
            </div>
            <div class="stat-card">
                <h3>✅ Safe Emails</h3>
                <div class="stat-number safe">{{ stats.safe_emails }}</div>
            </div>
            <div class="stat-card">
                <h3>🎯 Threat Rate</h3>
                <div class="stat-number {% if threat_rate > 30 %}phishing{% else %}safe{% endif %}">
                    {{ "%.1f"|format(threat_rate) }}%
                </div>
            </div>
        </div>
        
        <div class="scans-list">
            <h2>📋 Recent Scans</h2>
            {% for scan in stats.recent_scans[:20] %}
            <div class="scan-item">
                <div>
                    <span class="{% if scan.is_phishing %}phishing-badge{% else %}safe-badge{% endif %}">
                        {% if scan.is_phishing %}⚠️ PHISHING{% else %}✅ SAFE{% endif %}
                    </span>
                    <span style="margin-left: 10px;">{{ scan.email_preview }}</span>
                </div>
                <div class="timestamp">{{ scan.timestamp }}</div>
            </div>
            {% endfor %}
            {% if stats.recent_scans|length == 0 %}
            <p style="text-align: center; color: #999;">No scans yet. Test some emails in the web app!</p>
            {% endif %}
        </div>
        
        <div class="status">
            <p>💡 Use the web app at http://127.0.0.1:5000 to test emails</p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    threat_rate = (stats['phishing_detected'] / stats['total_scans'] * 100) if stats['total_scans'] > 0 else 0
    return render_template_string(HTML, stats=stats, threat_rate=threat_rate)

@app.route('/analyze', methods=['POST'])
def analyze():
    email_text = request.json.get('email', '')
    if email_text:
        is_phishing = analyze_email(email_text)
        return jsonify({'is_phishing': is_phishing})
    return jsonify({'error': 'No email provided'})

if __name__ == '__main__':
    print("\\n" + "="*50)
    print("📊 PHISHING DETECTION DASHBOARD")
    print("="*50)
    print("Dashboard: http://127.0.0.1:5001")
    print("Web App: http://127.0.0.1:5000")
    print("="*50 + "\\n")
    app.run(debug=True, host='127.0.0.1', port=5001)
