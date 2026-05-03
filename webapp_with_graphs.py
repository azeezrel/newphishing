from flask import Flask, render_template_string, request, jsonify
import pickle
import time
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

print("="*50)
print("Starting Phishing Detector WITH GRAPHS")
print("="*50)

# Load or create models
if not os.path.exists('models/phishing_detector.pkl'):
    print("Creating models...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing = [
        "urgent click link verify account suspended",
        "your account has been compromised click here",
        "verify your account immediately or it will be closed",
        "congratulations you won a prize click to claim"
    ]
    safe = [
        "meeting tomorrow at 10am in conference room",
        "project deadline is friday please submit",
        "team lunch at 12pm today",
        "can you review this document"
    ]
    
    all_text = phishing + safe
    labels = [1, 1, 1, 1, 0, 0, 0, 0]
    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(all_text)
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

counters = {'total': 0, 'phishing': 0}
scan_history = []
recent_scans_list = []

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phishing Detector</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .main-card {
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
            animation: slideIn 0.5s;
        }
        .phishing { background: #fee; border-left: 4px solid #e74c3c; color: #c0392b; }
        .safe { background: #e8f5e9; border-left: 4px solid #27ae60; color: #2e7d32; }
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
            cursor: pointer;
            border: none;
            border-radius: 5px;
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI Phishing Email Detector</h1>
            <p>Paste an email to detect if it's a phishing attempt</p>
        </div>
        
        <div class="main-card">
            <form method="POST">
                <textarea name="email" rows="8" placeholder="Paste email content here..."></textarea>
                <br>
                <button type="submit">🔍 Analyze Email</button>
            </form>
            
            <div style="margin-top: 10px;">
                <small>Quick test:</small>
                <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Phishing Example</button>
                <button type="button" class="example-btn" onclick="fillSafe()">✅ Safe Example</button>
            </div>
            
            {% if result %}
                <div class="result {{ 'phishing' if 'PHISHING' in result else 'safe' }}">
                    <h3>{{ result }}</h3>
                    {% if 'PHISHING' in result %}
                        <p>⚠️ Do NOT click any links or reply to this email!</p>
                    {% else %}
                        <p>✅ This email appears legitimate.</p>
                    {% endif %}
                </div>
            {% endif %}
        </div>
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 Open Interactive Dashboard with Graphs →</a>
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

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phishing Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; font-size: 2.5em; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2.5em; font-weight: bold; margin-top: 10px; }
        .phishing { color: #e74c3c; }
        .safe { color: #27ae60; }
        .total { color: #3498db; }
        .live-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            animation: pulse 1.5s infinite;
            margin-bottom: 20px;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .chart-card h3 { margin-bottom: 20px; color: #333; text-align: center; }
        canvas { max-height: 300px; }
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
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .timestamp { color: #999; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Live Phishing Detection Dashboard</h1>
        
        <div style="text-align: center;">
            <span class="live-badge">🔴 LIVE UPDATES EVERY 3 SECONDS</span>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📧 Total Scans</h3>
                <div class="stat-number total" id="totalCount">0</div>
            </div>
            <div class="stat-card">
                <h3>⚠️ Phishing Detected</h3>
                <div class="stat-number phishing" id="phishingCount">0</div>
            </div>
            <div class="stat-card">
                <h3>✅ Safe Emails</h3>
                <div class="stat-number safe" id="safeCount">0</div>
            </div>
            <div class="stat-card">
                <h3>🎯 Phishing Rate</h3>
                <div class="stat-number phishing" id="rateCount">0%</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📈 Phishing vs Safe (Pie Chart)</h3>
                <canvas id="pieChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📊 Scan Trends (Last 10 Scans)</h3>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>🎯 Threat Level Gauge</h3>
                <canvas id="gaugeChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📋 Recent Activity</h3>
                <div id="recentScans" style="max-height: 250px; overflow-y: auto;">
                    <p style="text-align: center; color: #999;">No scans yet...</p>
                </div>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <button class="refresh-btn" onclick="refreshAllData()">🔄 Refresh Now</button>
            <a href="/" style="background: #95a5a6; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; margin-left: 10px;">
                ← Back to Scanner
            </a>
        </div>
        
        <p style="text-align: center; color: white; margin-top: 20px;">
            Last updated: <span id="lastUpdate">Never</span>
        </p>
    </div>
    
    <script>
        let pieChart, trendChart, gaugeChart;
        
        function refreshAllData() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalCount').innerText = data.total;
                    document.getElementById('phishingCount').innerText = data.phishing;
                    document.getElementById('safeCount').innerText = data.total - data.phishing;
                    const rate = data.total > 0 ? ((data.phishing / data.total) * 100).toFixed(1) : 0;
                    document.getElementById('rateCount').innerText = rate + '%';
                    document.getElementById('lastUpdate').innerText = new Date().toLocaleTimeString();
                    
                    if (pieChart) pieChart.destroy();
                    pieChart = new Chart(document.getElementById('pieChart'), {
                        type: 'pie',
                        data: {
                            labels: ['Phishing', 'Safe'],
                            datasets: [{
                                data: [data.phishing, data.total - data.phishing],
                                backgroundColor: ['#e74c3c', '#27ae60']
                            }]
                        }
                    });
                    
                    if (trendChart) trendChart.destroy();
                    trendChart = new Chart(document.getElementById('trendChart'), {
                        type: 'line',
                        data: {
                            labels: data.recent_labels || ['No Data'],
                            datasets: [{
                                label: 'Scan Results (1=Phishing, 0=Safe)',
                                data: data.recent_scans || [0],
                                borderColor: '#e74c3c',
                                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            scales: { y: { beginAtZero: true, max: 1 } }
                        }
                    });
                    
                    if (gaugeChart) gaugeChart.destroy();
                    const threatPercent = data.total > 0 ? (data.phishing / data.total) * 100 : 0;
                    gaugeChart = new Chart(document.getElementById('gaugeChart'), {
                        type: 'doughnut',
                        data: {
                            labels: ['Threat Level', 'Safe Level'],
                            datasets: [{
                                data: [threatPercent, 100 - threatPercent],
                                backgroundColor: ['#e74c3c', '#27ae60']
                            }]
                        },
                        options: { cutout: '70%' }
                    });
                    
                    const recentDiv = document.getElementById('recentScans');
                    if (data.recent_items && data.recent_items.length > 0) {
                        recentDiv.innerHTML = data.recent_items.map(item => `
                            <div class="scan-item">
                                <div>
                                    <span class="${item.is_phishing ? 'phishing-badge' : 'safe-badge'}">
                                        ${item.is_phishing ? '⚠️ PHISHING' : '✅ SAFE'}
                                    </span>
                                    <span style="margin-left: 10px;">${item.preview}</span>
                                </div>
                                <div class="timestamp">${item.time}</div>
                            </div>
                        `).join('');
                    }
                })
                .catch(error => console.error('Error:', error));
        }
        
        refreshAllData();
        setInterval(refreshAllData, 3000);
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
            
            scan_history.append(1 if pred == 1 else 0)
            if len(scan_history) > 10:
                scan_history.pop(0)
            
            recent_scans_list.insert(0, {
                'is_phishing': pred == 1,
                'preview': email[:80] + '...' if len(email) > 80 else email,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            if len(recent_scans_list) > 20:
                recent_scans_list.pop()
            
            result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
            print(f"✅ Analyzed: {result}")
    
    return render_template_string(HTML, result=result)

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def api_stats():
    total = counters['total']
    phishing = counters['phishing']
    rate = (phishing / total) if total > 0 else 0
    
    trend_labels = [f"Scan {i+1}" for i in range(len(scan_history))]
    
    return jsonify({
        'time': datetime.now().strftime('%H:%M:%S'),
        'total': total,
        'phishing': phishing,
        'phishing_rate': round(rate, 4),
        'recent_scans': scan_history,
        'recent_labels': trend_labels,
        'recent_items': recent_scans_list[:10]
    })

if __name__ == '__main__':
    print("\\n" + "="*50)
    print("🚀 PHISHING DETECTOR WITH GRAPHS")
    print("="*50)
    print("📍 Main Web App: http://127.0.0.1:5000")
    print("📊 Dashboard with Graphs: http://127.0.0.1:5000/dashboard")
    print("="*50)
    print("\\n✅ Features: Pie Chart, Trend Line, Threat Gauge")
    print("="*50 + "\\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
