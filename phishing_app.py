from flask import Flask, render_template_string, request, jsonify
import pickle
import time
import os
from datetime import datetime

app = Flask(__name__)

print("="*50)
print("Starting Phishing Detector WITH WORKING GRAPHS")
print("="*50)

# Create simple models if they don't exist
if not os.path.exists('models/phishing_detector.pkl'):
    print("Creating models...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing_emails = [
        "urgent click link verify account suspended",
        "your account has been compromised click here",
        "verify your account immediately",
        "congratulations you won a prize click to claim",
        "your paypal account has been limited"
    ]
    safe_emails = [
        "meeting tomorrow at 10am in conference room",
        "project deadline is friday please submit",
        "team lunch at 12pm today",
        "can you review this document",
        "weekly report attached"
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
counters = {'total': 0, 'phishing': 0}
scan_history = []
recent_scans = []

# Main page HTML
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        h1 { color: #333; text-align: center; }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-family: monospace;
            margin: 10px 0;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
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
        .dashboard-link {
            text-align: center;
            margin-top: 20px;
        }
        .dashboard-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Phishing Email Detector</h1>
        
        <form method="POST">
            <textarea name="email" rows="8" placeholder="Paste email content here..."></textarea><br>
            <button type="submit">🔍 Analyze Email</button>
        </form>
        
        <div style="margin-top: 10px;">
            <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Test Phishing</button>
            <button type="button" class="example-btn" onclick="fillSafe()">✅ Test Safe</button>
        </div>
        
        {% if result %}
            <div class="result {{ 'phishing' if 'PHISHING' in result else 'safe' }}">
                <h3>{{ result }}</h3>
            </div>
        {% endif %}
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 View Dashboard with Graphs →</a>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.querySelector('textarea[name="email"]').value = "URGENT: Your account has been compromised! Click here to verify: http://fake-bank.com";
        }
        function fillSafe() {
            document.querySelector('textarea[name="email"]').value = "Meeting reminder: Project review at 2pm tomorrow";
        }
    </script>
</body>
</html>
"""

# Dashboard with working graphs
DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            margin: 0;
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
            font-size: 2em;
            font-weight: bold;
            margin-top: 10px;
        }
        .phishing { color: #e74c3c; }
        .safe { color: #27ae60; }
        .total { color: #3498db; }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin-bottom: 30px;
        }
        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .chart-card h3 {
            text-align: center;
            margin-bottom: 20px;
            color: #333;
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
        }
        .badge-phishing {
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
        .live-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 20px;
            text-align: center;
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
        .back-link {
            background: #95a5a6;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .center {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="center">
            <span class="live-badge">🔴 LIVE DASHBOARD - Auto Refreshes Every 3 Seconds</span>
        </div>
        
        <h1>📊 Phishing Detection Analytics</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Scans</h3>
                <div class="stat-number total" id="total">0</div>
            </div>
            <div class="stat-card">
                <h3>Phishing</h3>
                <div class="stat-number phishing" id="phishing">0</div>
            </div>
            <div class="stat-card">
                <h3>Safe</h3>
                <div class="stat-number safe" id="safe">0</div>
            </div>
            <div class="stat-card">
                <h3>Phishing Rate</h3>
                <div class="stat-number phishing" id="rate">0%</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 Distribution (Pie Chart)</h3>
                <canvas id="pieChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📈 Scan Trend (Line Graph)</h3>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>⚠️ Threat Level Gauge</h3>
                <canvas id="gaugeChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📋 Recent Activity</h3>
                <div id="recentList" style="max-height: 250px; overflow-y: auto;">
                    <p style="color: #999; text-align: center;">No scans yet</p>
                </div>
            </div>
        </div>
        
        <div class="center">
            <button onclick="refreshData()">🔄 Refresh Now</button>
            <a href="/" class="back-link">← Back to Scanner</a>
        </div>
        
        <p class="center" style="color: white; margin-top: 20px;">
            Last Updated: <span id="updateTime">Never</span>
        </p>
    </div>
    
    <script>
        let pieChart, trendChart, gaugeChart;
        
        function refreshData() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    // Update numbers
                    document.getElementById('total').innerText = data.total;
                    document.getElementById('phishing').innerText = data.phishing;
                    document.getElementById('safe').innerText = data.total - data.phishing;
                    const rate = data.total > 0 ? ((data.phishing / data.total) * 100).toFixed(1) : 0;
                    document.getElementById('rate').innerText = rate + '%';
                    document.getElementById('updateTime').innerText = new Date().toLocaleTimeString();
                    
                    // Update Pie Chart
                    if (pieChart) pieChart.destroy();
                    const pieCtx = document.getElementById('pieChart').getContext('2d');
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
                            maintainAspectRatio: true,
                            plugins: {
                                legend: { position: 'bottom' }
                            }
                        }
                    });
                    
                    // Update Trend Chart
                    if (trendChart) trendChart.destroy();
                    const trendCtx = document.getElementById('trendChart').getContext('2d');
                    const trendData = data.recent_scans.length > 0 ? data.recent_scans : [0];
                    const trendLabels = data.recent_scans.map((_, i) => '#' + (i+1));
                    
                    trendChart = new Chart(trendCtx, {
                        type: 'line',
                        data: {
                            labels: trendLabels.length ? trendLabels : ['No Data'],
                            datasets: [{
                                label: 'Threat Level (1=Phishing, 0=Safe)',
                                data: trendData,
                                borderColor: '#e74c3c',
                                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                                borderWidth: 3,
                                pointRadius: 5,
                                pointBackgroundColor: '#e74c3c',
                                tension: 0.3,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 1,
                                    ticks: {
                                        callback: function(value) {
                                            return value === 1 ? 'Phishing' : 'Safe';
                                        }
                                    }
                                }
                            },
                            plugins: {
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return context.parsed.y === 1 ? '⚠️ Phishing Detected' : '✅ Safe Email';
                                        }
                                    }
                                }
                            }
                        }
                    });
                    
                    // Update Gauge Chart
                    if (gaugeChart) gaugeChart.destroy();
                    const gaugeCtx = document.getElementById('gaugeChart').getContext('2d');
                    const threatPercent = data.total > 0 ? (data.phishing / data.total) * 100 : 0;
                    
                    gaugeChart = new Chart(gaugeCtx, {
                        type: 'doughnut',
                        data: {
                            labels: ['Threat (' + threatPercent.toFixed(1) + '%)', 'Safe (' + (100-threatPercent).toFixed(1) + '%)'],
                            datasets: [{
                                data: [threatPercent, 100 - threatPercent],
                                backgroundColor: ['#e74c3c', '#27ae60'],
                                borderWidth: 3,
                                borderColor: '#fff'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            cutout: '65%',
                            plugins: {
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return context.parsed.toFixed(1) + '%';
                                        }
                                    }
                                }
                            }
                        }
                    });
                    
                    // Add center text to gauge
                    const gaugeContainer = document.getElementById('gaugeChart').parentElement;
                    let centerText = gaugeContainer.querySelector('.gauge-center-text');
                    if (!centerText) {
                        centerText = document.createElement('div');
                        centerText.className = 'gauge-center-text';
                        centerText.style.position = 'absolute';
                        centerText.style.top = '50%';
                        centerText.style.left = '50%';
                        centerText.style.transform = 'translate(-50%, -50%)';
                        centerText.style.textAlign = 'center';
                        centerText.style.fontSize = '24px';
                        centerText.style.fontWeight = 'bold';
                        gaugeContainer.style.position = 'relative';
                        gaugeContainer.appendChild(centerText);
                    }
                    centerText.innerHTML = threatPercent.toFixed(0) + '%<br><span style="font-size: 12px;">Threat</span>';
                    centerText.style.color = threatPercent > 50 ? '#e74c3c' : '#27ae60';
                    
                    // Update recent scans
                    const recentDiv = document.getElementById('recentList');
                    if (data.recent_scans_list && data.recent_scans_list.length > 0) {
                        recentDiv.innerHTML = data.recent_scans_list.map(item => `
                            <div class="scan-item">
                                <div>
                                    <span class="${item.is_phishing ? 'badge-phishing' : 'badge-safe'}">
                                        ${item.is_phishing ? '⚠️ PHISHING' : '✅ SAFE'}
                                    </span>
                                    <span style="margin-left: 10px;">${item.preview}</span>
                                </div>
                                <div style="color: #999; font-size: 12px;">${item.time}</div>
                            </div>
                        `).join('');
                    } else {
                        recentDiv.innerHTML = '<p style="color: #999; text-align: center;">No scans yet. Test some emails!</p>';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('recentList').innerHTML = '<p style="color: red; text-align: center;">Error loading data. Make sure the server is running.</p>';
                });
        }
        
        // Refresh every 3 seconds
        refreshData();
        setInterval(refreshData, 3000);
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
            vec = vectorizer.transform([email])
            pred = model.predict(vec)[0]
            
            counters['total'] += 1
            if pred == 1:
                counters['phishing'] += 1
            
            # Store in history (keep last 10)
            scan_history.append(1 if pred == 1 else 0)
            if len(scan_history) > 10:
                scan_history.pop(0)
            
            # Store recent scans
            recent_scans.insert(0, {
                'is_phishing': pred == 1,
                'preview': email[:80] + '...' if len(email) > 80 else email,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            if len(recent_scans) > 20:
                recent_scans.pop()
            
            result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
            print(f"Analyzed: {result} (Total: {counters['total']})")
    
    return render_template_string(MAIN_PAGE, result=result)

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_PAGE)

@app.route('/api/stats')
def api_stats():
    total = counters['total']
    phishing = counters['phishing']
    
    return {
        'time': datetime.now().strftime('%H:%M:%S'),
        'total': total,
        'phishing': phishing,
        'recent_scans': scan_history,
        'recent_scans_list': recent_scans[:10]
    }

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 PHISHING DETECTOR WITH WORKING GRAPHS")
    print("="*60)
    print("📍 Main Web App: http://127.0.0.1:5000")
    print("📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("="*60)
    print("\n✅ Features:")
    print("   • Pie Chart - Shows phishing vs safe distribution")
    print("   • Line Graph - Shows trend of last 10 scans")
    print("   • Threat Gauge - Donut chart with threat percentage")
    print("   • Auto-refreshes every 3 seconds")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
