from flask import Flask, render_template_string, request, jsonify
import pickle
import time
import os
from datetime import datetime
from flask_cors import CORS
import re
import requests

app = Flask(__name__)
CORS(app)

print("="*60)
print("PHISHING DETECTOR WITH PHISHTANK API")
print("="*60)

# Load or create models
if not os.path.exists('models/phishing_detector.pkl'):
    print("Creating ML models...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing_emails = [
        "urgent click link verify account suspended",
        "your account has been compromised click here",
        "verify your account immediately or it will be closed",
        "congratulations you won a million dollars click to claim",
        "your paypal account has been limited verify now",
        "irs tax refund waiting click here to claim",
        "http://fake-bank.com/verify click to secure your account",
        "netflix subscription expired update payment http://fake-netflix.com"
    ]
    safe_emails = [
        "meeting tomorrow at 10am in conference room",
        "project deadline is friday please submit your work",
        "team lunch at 12pm today in the cafeteria",
        "can you review this document when you have time",
        "weekly report attached please find the details",
        "reminder about the training session tomorrow",
        "github repository updated please pull latest changes",
        "slack channel created for project discussion"
    ]
    
    all_emails = phishing_emails + safe_emails
    labels = [1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0]
    
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

# PhishTank URL checker without library (to avoid timeout)
def check_url_phishtank_simple(url):
    """Check URL against PhishTank API - Simple version"""
    try:
        # PhishTank check endpoint
        check_url = "https://check.phishtank.com/checkurl/"
        headers = {
            'User-Agent': 'PhishingDetector/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'url': url,
            'format': 'json'
        }
        
        response = requests.post(check_url, data=data, headers=headers, timeout=5)
        if response.status_code == 200:
            result = response.json()
            if 'results' in result and 'in_database' in result['results']:
                return result['results']['in_database']
        return False
    except Exception as e:
        print(f"PhishTank error for {url}: {e}")
        return False

def extract_urls_from_email(email_text):
    """Extract all URLs from email"""
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s<>"{}|\\^`\[\]]*'
    urls = re.findall(url_pattern, email_text)
    return urls

def check_urls_for_phishing(email_text):
    """Check all URLs in email against PhishTank"""
    urls = extract_urls_from_email(email_text)
    if not urls:
        return {'has_suspicious_urls': False, 'checked_urls': [], 'phishing_urls': []}
    
    results = []
    phishing_urls = []
    
    for url in urls:
        is_phish = check_url_phishtank_simple(url)
        results.append({
            'url': url,
            'is_phishing': is_phish
        })
        if is_phish:
            phishing_urls.append(url)
    
    return {
        'has_suspicious_urls': len(phishing_urls) > 0,
        'checked_urls': results,
        'phishing_urls': phishing_urls
    }

# Store data
scan_data = {
    'total': 0,
    'phishing': 0,
    'phishing_with_api': 0,
    'history': [],
    'recent': []
}

MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector with API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            font-family: monospace;
            resize: vertical;
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
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            animation: fadeIn 0.5s;
        }
        .phishing { background: #fee; border-left: 4px solid #e74c3c; color: #c0392b; }
        .safe { background: #e8f5e9; border-left: 4px solid #27ae60; color: #2e7d32; }
        .warning { background: #fff3e0; border-left: 4px solid #f39c12; color: #e65100; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .dashboard-link {
            text-align: center;
            margin-top: 20px;
        }
        .dashboard-link a {
            color: white;
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            display: inline-block;
        }
        .example-btn {
            background: #ecf0f1;
            color: #333;
            padding: 5px 10px;
            font-size: 12px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .api-badge {
            background: #27ae60;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
            display: inline-block;
            margin-left: 10px;
        }
        .url-list {
            margin-top: 10px;
            font-size: 12px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI Phishing Detector <span class="api-badge">Powered by PhishTank API</span></h1>
            <p>ML Model + URL Database Checking</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <textarea name="email" rows="8" placeholder="Paste email content here..."></textarea>
                <br>
                <button type="submit">🔍 Analyze with ML + API</button>
            </form>
            
            <div style="margin-top: 10px;">
                <small>Test samples:</small>
                <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Phishing URL Sample</button>
                <button type="button" class="example-btn" onclick="fillSafe()">✅ Safe Email</button>
            </div>
            
            <div id="resultArea">
                {% if result %}
                <div class="result {{ result_class }}">
                    <h3>{{ result_title }}</h3>
                    <p>{{ result_message }}</p>
                    {% if api_results %}
                    <div class="url-list">
                        <strong>📎 Checked URLs:</strong><br>
                        {% for url_check in api_results.checked_urls %}
                        • {{ url_check.url }} - 
                        {% if url_check.is_phishing %}
                        <span style="color:#e74c3c;">⚠️ PHISHING URL DETECTED!</span>
                        {% else %}
                        <span style="color:#27ae60;">✓ Safe (not in database)</span>
                        {% endif %}
                        <br>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            
            <div class="dashboard-link">
                <a href="/dashboard" target="_blank">📊 Open Dashboard with Live Stats →</a>
            </div>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.querySelector('textarea[name="email"]').value = "URGENT: Your PayPal account has been limited!\n\nVerify your account now: http://fake-paypal-verify.com/secure\n\nIf not verified within 24 hours, your account will be suspended.";
        }
        function fillSafe() {
            document.querySelector('textarea[name="email"]').value = "Subject: Team Meeting Tomorrow\n\nHi Team,\n\nJust a reminder about our meeting at 10 AM in Conference Room B.\n\nAgenda:\n- Project updates\n- Q3 planning\n\nBest regards,\nManager";
        }
    </script>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 { color: white; text-align: center; margin-bottom: 20px; }
        .live-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            animation: pulse 1s infinite;
            margin-bottom: 20px;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-top: 10px;
        }
        .phishing { color: #e74c3c; }
        .safe { color: #27ae60; }
        .total { color: #3498db; }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
        }
        .chart-card h3 {
            text-align: center;
            margin-bottom: 15px;
        }
        canvas {
            max-height: 300px;
            width: 100% !important;
        }
        .recent-list {
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
        .badge-phish {
            background: #e74c3c;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 12px;
        }
        .badge-safe {
            background: #27ae60;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 12px;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px;
        }
        .center { text-align: center; }
        .timestamp { color: #999; font-size: 12px; }
        .api-badge { background: #9b59b6; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="center">
            <span class="live-badge">🔴 LIVE - ML + PhishTank API</span>
        </div>
        
        <h1>📊 Phishing Detection Dashboard <span class="api-badge">API Enhanced</span></h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 Total Scans</h3>
                <div class="stat-number total" id="total">0</div>
            </div>
            <div class="stat-card">
                <h3>⚠️ Phishing</h3>
                <div class="stat-number phishing" id="phishing">0</div>
            </div>
            <div class="stat-card">
                <h3>✅ Safe</h3>
                <div class="stat-number safe" id="safe">0</div>
            </div>
            <div class="stat-card">
                <h3>🎯 Threat Rate</h3>
                <div class="stat-number phishing" id="rate">0%</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 Phishing vs Safe (Pie Chart)</h3>
                <canvas id="pieChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📈 Detection Trend</h3>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="recent-list">
            <h3>📋 Recent Scans</h3>
            <div id="recentScans" style="max-height: 300px; overflow-y: auto;">
                <p style="text-align: center; color: #999;">No scans yet</p>
            </div>
        </div>
        
        <div class="center">
            <button onclick="location.reload()">🔄 Refresh</button>
            <button onclick="window.location.href='/'">← Back to Scanner</button>
        </div>
        
        <p class="center timestamp" style="color: white; margin-top: 20px;">
            Last updated: <span id="updateTime">Never</span>
        </p>
    </div>
    
    <script>
        let pieChart, trendChart;
        
        async function fetchData() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('total').innerText = data.total;
                document.getElementById('phishing').innerText = data.phishing;
                document.getElementById('safe').innerText = data.total - data.phishing;
                const rate = data.total > 0 ? ((data.phishing / data.total) * 100).toFixed(1) : 0;
                document.getElementById('rate').innerText = rate + '%';
                document.getElementById('updateTime').innerText = new Date().toLocaleTimeString();
                
                // Pie Chart
                const pieCtx = document.getElementById('pieChart').getContext('2d');
                if (pieChart) pieChart.destroy();
                pieChart = new Chart(pieCtx, {
                    type: 'pie',
                    data: {
                        labels: ['Phishing', 'Safe'],
                        datasets: [{
                            data: [data.phishing, data.total - data.phishing],
                            backgroundColor: ['#e74c3c', '#27ae60']
                        }]
                    }
                });
                
                // Trend Chart
                const trendCtx = document.getElementById('trendChart').getContext('2d');
                if (trendChart) trendChart.destroy();
                const history = data.history.length ? data.history : [0];
                trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: history.map((_, i) => '#' + (i+1)),
                        datasets: [{
                            label: 'Phishing (1) / Safe (0)',
                            data: history,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            fill: true
                        }]
                    },
                    options: {
                        scales: { y: { beginAtZero: true, max: 1 } }
                    }
                });
                
                // Recent scans
                const recentDiv = document.getElementById('recentScans');
                if (data.recent && data.recent.length > 0) {
                    recentDiv.innerHTML = data.recent.map(item => `
                        <div class="scan-item">
                            <div>
                                <span class="${item.is_phishing ? 'badge-phish' : 'badge-safe'}">
                                    ${item.is_phishing ? '⚠️ PHISHING' : '✅ SAFE'}
                                </span>
                                <span style="margin-left: 10px;">${item.preview}</span>
                            </div>
                            <div class="timestamp">${item.time}</div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        fetchData();
        setInterval(fetchData, 2000);
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    result_class = None
    result_title = None
    result_message = None
    api_results = None
    
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email and email.strip():
            # 1. ML Model Detection
            vec = vectorizer.transform([email])
            ml_pred = model.predict(vec)[0]
            
            # 2. URL PhishTank Check
            url_check = check_urls_for_phishing(email)
            
            # 3. Combined verdict (if ANY malicious URL found, it's phishing)
            is_phishing = ml_pred == 1 or url_check['has_suspicious_urls']
            
            # Determine detection method
            detection_method = []
            if ml_pred == 1:
                detection_method.append("ML Model")
            if url_check['has_suspicious_urls']:
                detection_method.append("PhishTank URL Database")
            
            # Update stats
            scan_data['total'] += 1
            if is_phishing:
                scan_data['phishing'] += 1
            
            scan_data['history'].append(1 if is_phishing else 0)
            if len(scan_data['history']) > 10:
                scan_data['history'].pop(0)
            
            scan_data['recent'].insert(0, {
                'is_phishing': is_phishing,
                'preview': email[:60] + '...' if len(email) > 60 else email,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            if len(scan_data['recent']) > 10:
                scan_data['recent'].pop()
            
            # Prepare result for display
            if is_phishing:
                result_class = 'phishing'
                result_title = '⚠️ PHISHING DETECTED!'
                result_message = f"This email was flagged as phishing by: {', '.join(detection_method)}"
            else:
                result_class = 'safe'
                result_title = '✅ SAFE EMAIL'
                result_message = "This email appears legitimate (checked by ML model and URL database)"
            
            api_results = url_check
            print(f"✅ Analyzed - ML: {ml_pred}, URL Phish: {url_check['has_suspicious_urls']}, Final: {is_phishing}")
    
    return render_template_string(MAIN_PAGE, result=is_phishing if request.method == 'POST' else None, 
                                 result_class=result_class, result_title=result_title, 
                                 result_message=result_message, api_results=api_results)

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_PAGE)

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'total': scan_data['total'],
        'phishing': scan_data['phishing'],
        'history': scan_data['history'],
        'recent': scan_data['recent']
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 PHISHING DETECTOR WITH PHISHTANK API")
    print("="*60)
    print("📧 Main App: http://127.0.0.1:5000")
    print("📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("="*60)
    print("\n✅ Features:")
    print("   • ML Model Detection (Random Forest)")
    print("   • PhishTank URL Database Check")
    print("   • Combined Detection Logic")
    print("   • Live Dashboard with Graphs")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
