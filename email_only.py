from flask import Flask, render_template_string, request, jsonify
import pickle
import os
from datetime import datetime
import re

app = Flask(__name__)

print("="*60)
print("PHISHING DETECTOR - EMAIL ONLY (NO URL TAB)")
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
    ]
    safe_emails = [
        "meeting tomorrow at 10am in conference room",
        "project deadline is friday please submit",
        "team lunch at 12pm today",
        "can you review this document",
        "weekly report attached",
    ]
    
    all_emails = phishing_emails + safe_emails
    labels = [1,1,1,1,1,0,0,0,0,0]
    
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

# Store data
scan_data = {
    'total': 0,
    'phishing': 0,
    'history': [],
    'recent': []
}

# Clean HTML - NO URL TAB, NO PhishTank badge
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Email Detector</title>
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
        .header p { font-size: 1.1em; opacity: 0.9; }
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
            margin: 10px 0;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            animation: slideIn 0.5s;
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
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .example-section {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        .example-btn {
            background: #ecf0f1;
            color: #333;
            padding: 8px 15px;
            font-size: 13px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .example-btn:hover {
            background: #d5dbdb;
            transform: none;
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
            transition: background 0.3s;
        }
        .dashboard-link a:hover {
            background: rgba(255,255,255,0.3);
        }
        .badge-ml {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 11px;
            margin-left: 10px;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI Phishing Email Detector <span class="badge-ml">ML Model</span></h1>
            <p>Paste an email to detect if it's a phishing attempt</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <textarea name="email" rows="10" placeholder="Paste email content here..."></textarea>
                <br>
                <button type="submit">🔍 Analyze Email</button>
            </form>
            
            <div class="example-section">
                <strong>📝 Quick test examples:</strong><br>
                <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Phishing Email</button>
                <button type="button" class="example-btn" onclick="fillSafe()">✅ Safe Email</button>
            </div>
            
            {% if result %}
                <div class="result {{ 'phishing' if 'PHISHING' in result else 'safe' }}">
                    <h3>{{ result }}</h3>
                    {% if 'PHISHING' in result %}
                        <p>⚠️ Do NOT click any links or reply to this email.</p>
                        <p>🔐 Report this to your IT security team.</p>
                    {% else %}
                        <p>✅ This email appears legitimate.</p>
                        <p>💡 Always remain vigilant with unexpected emails.</p>
                    {% endif %}
                </div>
            {% endif %}
        </div>
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 Open Live Dashboard →</a>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.querySelector('textarea').value = "URGENT: Your PayPal account has been limited!\\n\\nVerify your account now: http://fake-paypal-verify.com/secure\\n\\nIf not verified within 24 hours, your account will be suspended.";
        }
        function fillSafe() {
            document.querySelector('textarea').value = "Subject: Team Meeting Tomorrow\\n\\nHi Team,\\n\\nJust a reminder about our meeting at 10 AM in Conference Room B.\\n\\nAgenda:\\n- Project updates\\n- Q3 planning\\n\\nBest regards,\\nManager";
        }
    </script>
</body>
</html>
"""

# Dashboard Page
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
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
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
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
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
            <span class="live-badge">🔴 LIVE DASHBOARD - Auto Refreshes Every 3 Seconds</span>
        </div>
        
        <h1>📊 Phishing Detection Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card"><h3>📊 Total Scans</h3><div class="stat-number total" id="total">0</div></div>
            <div class="stat-card"><h3>⚠️ Phishing Detected</h3><div class="stat-number phishing" id="phishing">0</div></div>
            <div class="stat-card"><h3>✅ Safe Emails</h3><div class="stat-number safe" id="safe">0</div></div>
            <div class="stat-card"><h3>🎯 Threat Rate</h3><div class="stat-number phishing" id="rate">0%</div></div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card"><h3>📊 Phishing vs Safe Distribution</h3><canvas id="pieChart"></canvas></div>
            <div class="chart-card"><h3>📈 Detection Trend (Last 10 Scans)</h3><canvas id="trendChart"></canvas></div>
        </div>
        
        <div class="recent-list">
            <h3>📋 Recent Scans</h3>
            <div id="recentScans" style="max-height: 300px; overflow-y: auto;">
                <p style="text-align: center; color: #999;">No scans yet. Test some emails below!</p>
            </div>
        </div>
        
        <div class="center">
            <button onclick="location.reload()">🔄 Refresh Page</button>
            <button onclick="window.location.href='/'">← Back to Email Scanner</button>
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
                    data: {
                        labels: ['Phishing (' + data.phishing + ')', 'Safe (' + (data.total - data.phishing) + ')'],
                        datasets: [{
                            data: [data.phishing, data.total - data.phishing],
                            backgroundColor: ['#e74c3c', '#27ae60'],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'bottom' } }
                    }
                });
                
                const trendCtx = document.getElementById('trendChart').getContext('2d');
                if (trendChart) trendChart.destroy();
                const history = data.history.length ? data.history : [0];
                trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: history.map((_, i) => 'Scan ' + (i+1)),
                        datasets: [{
                            label: 'Threat Level (1=Phishing, 0=Safe)',
                            data: history,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            borderWidth: 3,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1,
                                ticks: {
                                    callback: function(value) {
                                        return value === 1 ? '⚠️ Phishing' : '✅ Safe';
                                    }
                                }
                            }
                        }
                    }
                });
                
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
                } else {
                    recentDiv.innerHTML = '<p style="text-align: center; color: #999;">📭 No scans yet. Go back and test some emails!</p>';
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        fetchData();
        setInterval(fetchData, 3000);
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email and email.strip():
            # ML Prediction
            vec = vectorizer.transform([email])
            pred = model.predict(vec)[0]
            is_phishing = pred == 1
            
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
            
            result = "⚠️ PHISHING DETECTED!" if is_phishing else "✅ SAFE EMAIL"
            print(f"📧 Analyzed: {result} | Total: {scan_data['total']} | Phishing: {scan_data['phishing']}")
    
    return render_template_string(MAIN_PAGE, result=result)

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
    print("🚀 PHISHING DETECTOR - EMAIL ONLY")
    print("="*60)
    print("📧 Main App: http://127.0.0.1:5000")
    print("📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("="*60)
    print("\n✅ Features:")
    print("   • Test emails with ML model")
    print("   • Live dashboard with pie chart")
    print("   • Detection trend graph")
    print("   • Recent scan history")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
