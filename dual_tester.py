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
print("PHISHING DETECTOR - EMAIL + URL TESTER")
print("="*60)

# Load or create models
if not os.path.exists('models/phishing_detector.pkl'):
    print("Creating ML models...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing_emails = [
        "urgent click link verify account suspended",
        "your account has been compromised click here",
        "verify your account immediately",
        "congratulations you won a prize click to claim",
        "your paypal account has been limited verify now",
        "http://fake-bank.com/verify click to secure"
    ]
    safe_emails = [
        "meeting tomorrow at 10am in conference room",
        "project deadline is friday please submit",
        "team lunch at 12pm today",
        "can you review this document",
        "weekly report attached",
        "github repository updated"
    ]
    
    all_emails = phishing_emails + safe_emails
    labels = [1,1,1,1,1,1,0,0,0,0,0,0]
    
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

def check_url_phishtank(url):
    """Check URL against PhishTank"""
    try:
        check_url = "https://check.phishtank.com/checkurl/"
        headers = {'User-Agent': 'PhishingDetector/1.0'}
        data = {'url': url, 'format': 'json'}
        
        response = requests.post(check_url, data=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get('results', {}).get('in_database', False)
        return False
    except Exception as e:
        print(f"PhishTank error: {e}")
        return False

def extract_urls_from_email(email_text):
    """Extract all URLs from email"""
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s<>"{}|\\^`\[\]]*'
    return re.findall(url_pattern, email_text)

# Store data
scan_data = {
    'total': 0,
    'phishing': 0,
    'history': [],
    'recent': []
}

# HTML with Tabs for Email and URL testing
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector - Email & URL Tester</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        .tab-btn.active {
            background: white;
            color: #667eea;
        }
        .tab-content {
            display: none;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .tab-content.active {
            display: block;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        textarea, input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            margin: 10px 0;
        }
        input { font-family: monospace; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            animation: slideIn 0.5s;
        }
        .phishing { background: #fee; border-left: 4px solid #e74c3c; color: #c0392b; }
        .safe { background: #e8f5e9; border-left: 4px solid #27ae60; color: #2e7d32; }
        .warning { background: #fff3e0; border-left: 4px solid #f39c12; color: #e65100; }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
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
        .url-list {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
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
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
            margin-left: 10px;
        }
        .badge-api { background: #9b59b6; color: white; }
        .badge-ml { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI Phishing Detector <span class="badge badge-api">PhishTank API</span><span class="badge badge-ml">ML Model</span></h1>
            <p>Test emails OR URLs for phishing detection</p>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('email')">📧 Email Testing</button>
            <button class="tab-btn" onclick="switchTab('url')">🔗 URL Testing</button>
        </div>
        
        <!-- Email Tab -->
        <div id="emailTab" class="tab-content active">
            <form method="POST" action="/analyze_email">
                <textarea name="email" rows="8" placeholder="Paste email content here..."></textarea>
                <br>
                <button type="submit">🔍 Analyze Email with ML + API</button>
            </form>
            
            <div style="margin-top: 10px;">
                <small>Test samples:</small>
                <button type="button" class="example-btn" onclick="fillEmailPhishing()">⚠️ Phishing Email</button>
                <button type="button" class="example-btn" onclick="fillEmailSafe()">✅ Safe Email</button>
            </div>
            
            {% if email_result %}
            <div class="result {{ email_result_class }}">
                <h3>{{ email_result_title }}</h3>
                <p>{{ email_result_message }}</p>
                {% if email_api_results %}
                <div class="url-list">
                    <strong>📎 URLs found in email:</strong><br>
                    {% for url_check in email_api_results.checked_urls %}
                    • {{ url_check.url }} - 
                    {% if url_check.is_phishing %}
                    <span style="color:#e74c3c;">⚠️ PHISHING URL!</span>
                    {% else %}
                    <span style="color:#27ae60;">✓ Safe</span>
                    {% endif %}
                    <br>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
        
        <!-- URL Tab -->
        <div id="urlTab" class="tab-content">
            <input type="text" id="urlInput" placeholder="Enter URL to test (e.g., http://example.com)">
            <button onclick="checkURL()">🔍 Check URL with PhishTank API</button>
            
            <div style="margin-top: 10px;">
                <small>Test samples:</small>
                <button type="button" class="example-btn" onclick="setURL('http://fake-paypal-verify.com/secure')">⚠️ Phishing URL</button>
                <button type="button" class="example-btn" onclick="setURL('https://www.google.com')">✅ Safe URL</button>
                <button type="button" class="example-btn" onclick="setURL('http://fake-bank-verification.com/login')">⚠️ Suspicious URL</button>
                <button type="button" class="example-btn" onclick="setURL('https://github.com')">✅ GitHub</button>
            </div>
            
            <div id="urlResult"></div>
        </div>
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 Open Live Dashboard →</a>
        </div>
    </div>
    
    <script>
        function switchTab(tab) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // Update content
            document.getElementById('emailTab').classList.remove('active');
            document.getElementById('urlTab').classList.remove('active');
            
            if (tab === 'email') {
                document.getElementById('emailTab').classList.add('active');
            } else {
                document.getElementById('urlTab').classList.add('active');
            }
        }
        
        async function checkURL() {
            const url = document.getElementById('urlInput').value;
            const resultDiv = document.getElementById('urlResult');
            
            if (!url) {
                resultDiv.innerHTML = '<div class="result warning"><h3>⚠️ Please enter a URL</h3></div>';
                return;
            }
            
            resultDiv.innerHTML = '<div style="text-align: center;">🔄 Checking URL against PhishTank database...</div>';
            
            try {
                const response = await fetch('/check_url', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                const data = await response.json();
                
                if (data.is_phishing) {
                    resultDiv.innerHTML = `
                        <div class="result phishing">
                            <h3>⚠️ PHISHING URL DETECTED!</h3>
                            <p>This URL has been reported as a phishing site in the PhishTank database.</p>
                            <div class="url-list">
                                <strong>🔗 URL:</strong> ${url}<br>
                                <strong>📊 Status:</strong> In PhishTank Database<br>
                                <strong>⚠️ Risk:</strong> High - Do NOT open this link<br>
                                <strong>🕒 Checked:</strong> ${new Date().toLocaleTimeString()}
                            </div>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result safe">
                            <h3>✅ URL APPEARS SAFE</h3>
                            <p>This URL was not found in the PhishTank phishing database.</p>
                            <div class="url-list">
                                <strong>🔗 URL:</strong> ${url}<br>
                                <strong>📊 Status:</strong> Not in phishing database<br>
                                <strong>✅ Risk:</strong> Low - Still be cautious<br>
                                <strong>🕒 Checked:</strong> ${new Date().toLocaleTimeString()}
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result warning"><h3>❌ Error</h3><p>${error.message}</p></div>`;
            }
        }
        
        function setURL(url) {
            document.getElementById('urlInput').value = url;
            checkURL();
        }
        
        function fillEmailPhishing() {
            document.querySelector('textarea[name="email"]').value = "URGENT: Your PayPal account has been limited!\n\nVerify your account now: http://fake-paypal-verify.com/secure\n\nIf not verified within 24 hours, your account will be suspended.";
            document.querySelector('form').submit();
        }
        
        function fillEmailSafe() {
            document.querySelector('textarea[name="email"]').value = "Subject: Team Meeting Tomorrow\n\nHi Team,\n\nJust a reminder about our meeting at 10 AM in Conference Room B.\n\nAgenda:\n- Project updates\n- Q3 planning\n\nBest regards,\nManager";
            document.querySelector('form').submit();
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
        .badge-phish { background: #e74c3c; color: white; padding: 3px 10px; border-radius: 15px; font-size: 12px; }
        .badge-safe { background: #27ae60; color: white; padding: 3px 10px; border-radius: 15px; font-size: 12px; }
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
    </style>
</head>
<body>
    <div class="container">
        <div class="center">
            <span class="live-badge">🔴 LIVE - Email & URL Testing</span>
        </div>
        
        <h1>📊 Detection Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card"><h3>Total Scans</h3><div class="stat-number total" id="total">0</div></div>
            <div class="stat-card"><h3>Phishing</h3><div class="stat-number phishing" id="phishing">0</div></div>
            <div class="stat-card"><h3>Safe</h3><div class="stat-number safe" id="safe">0</div></div>
            <div class="stat-card"><h3>Threat Rate</h3><div class="stat-number phishing" id="rate">0%</div></div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card"><h3>📊 Phishing vs Safe</h3><canvas id="pieChart"></canvas></div>
            <div class="chart-card"><h3>📈 Detection Trend</h3><canvas id="trendChart"></canvas></div>
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
                
                const pieCtx = document.getElementById('pieChart').getContext('2d');
                if (pieChart) pieChart.destroy();
                pieChart = new Chart(pieCtx, {
                    type: 'pie',
                    data: { labels: ['Phishing', 'Safe'], datasets: [{ data: [data.phishing, data.total - data.phishing], backgroundColor: ['#e74c3c', '#27ae60'] }] }
                });
                
                const trendCtx = document.getElementById('trendChart').getContext('2d');
                if (trendChart) trendChart.destroy();
                const history = data.history.length ? data.history : [0];
                trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: { labels: history.map((_, i) => '#' + (i+1)), datasets: [{ label: 'Threat Level', data: history, borderColor: '#e74c3c', fill: true }] },
                    options: { scales: { y: { beginAtZero: true, max: 1 } } }
                });
                
                const recentDiv = document.getElementById('recentScans');
                if (data.recent && data.recent.length > 0) {
                    recentDiv.innerHTML = data.recent.map(item => `<div class="scan-item"><div><span class="${item.is_phishing ? 'badge-phish' : 'badge-safe'}">${item.is_phishing ? '⚠️ PHISHING' : '✅ SAFE'}</span><span style="margin-left: 10px;">${item.preview}</span></div><div class="timestamp">${item.time}</div></div>`).join('');
                }
            } catch (error) { console.error('Error:', error); }
        }
        
        fetchData();
        setInterval(fetchData, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MAIN_PAGE)

@app.route('/analyze_email', methods=['POST'])
def analyze_email():
    email = request.form.get('email', '')
    result_class = None
    result_title = None
    result_message = None
    api_results = None
    
    if email and email.strip():
        # ML Detection
        vec = vectorizer.transform([email])
        ml_pred = model.predict(vec)[0]
        
        # URL Check
        urls = extract_urls_from_email(email)
        url_check = {'has_suspicious_urls': False, 'checked_urls': []}
        for url in urls:
            is_phish = check_url_phishtank(url)
            url_check['checked_urls'].append({'url': url, 'is_phishing': is_phish})
            if is_phish:
                url_check['has_suspicious_urls'] = True
        
        is_phishing = ml_pred == 1 or url_check['has_suspicious_urls']
        
        # Update stats
        scan_data['total'] += 1
        if is_phishing:
            scan_data['phishing'] += 1
        
        scan_data['history'].append(1 if is_phishing else 0)
        if len(scan_data['history']) > 10:
            scan_data['history'].pop(0)
        
        scan_data['recent'].insert(0, {
            'is_phishing': is_phishing,
            'preview': email[:50] + '...' if len(email) > 50 else email,
            'time': datetime.now().strftime('%H:%M:%S')
        })
        if len(scan_data['recent']) > 10:
            scan_data['recent'].pop()
        
        if is_phishing:
            result_class = 'phishing'
            result_title = '⚠️ PHISHING DETECTED!'
            result_message = f"This email was flagged as phishing"
        else:
            result_class = 'safe'
            result_title = '✅ SAFE EMAIL'
            result_message = "This email appears legitimate"
        
        api_results = url_check
    
    return render_template_string(MAIN_PAGE, email_result=True, email_result_class=result_class,
                                 email_result_title=result_title, email_result_message=result_message,
                                 email_api_results=api_results)

@app.route('/check_url', methods=['POST'])
def check_url():
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'})
    
    is_phishing = check_url_phishtank(url)
    return jsonify({'is_phishing': is_phishing, 'url': url})

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
    print("🚀 PHISHING DETECTOR - EMAIL + URL TESTER")
    print("="*60)
    print("📧 Main App: http://127.0.0.1:5000")
    print("📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("="*60)
    print("\n✅ Features:")
    print("   • Tab 1: Test Emails (ML + URL extraction)")
    print("   • Tab 2: Test URLs directly (PhishTank API)")
    print("   • Live Dashboard with graphs")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
