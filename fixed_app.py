from flask import Flask, render_template_string, request, jsonify
import pickle
import time
import os
from datetime import datetime

app = Flask(__name__)

# Create simple models if they don't exist
if not os.path.exists('models/phishing_detector.pkl'):
    print("Creating models...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    
    phishing_emails = [
        "urgent click link verify account",
        "your account has been compromised",
        "verify your account immediately",
        "congratulations you won a prize"
    ]
    safe_emails = [
        "meeting tomorrow at 10am",
        "project deadline is friday",
        "team lunch at 12pm today",
        "can you review this document"
    ]
    
    all_emails = phishing_emails + safe_emails
    labels = [1,1,1,1,0,0,0,0]
    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(all_emails)
    model = RandomForestClassifier()
    model.fit(X, labels)
    
    os.makedirs('models', exist_ok=True)
    with open('models/phishing_detector.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    print("Models created!")
else:
    with open('models/phishing_detector.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("Models loaded!")

# Store data
counters = {'total': 0, 'phishing': 0}
scan_history = []
recent_scans = []

# Main page
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector</title>
    <style>
        body {
            font-family: Arial;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        textarea {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 10px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
        }
        .phishing { background: #fee; border-left: 4px solid red; }
        .safe { background: #e8f5e9; border-left: 4px solid green; }
        .dashboard-link {
            text-align: center;
            margin-top: 20px;
        }
        a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Phishing Email Detector</h1>
        
        <form method="POST">
            <textarea name="email" rows="8" placeholder="Paste email here..."></textarea><br>
            <button type="submit">Analyze</button>
        </form>
        
        {% if result %}
            <div class="result {{ 'phishing' if 'PHISHING' in result else 'safe' }}">
                <h3>{{ result }}</h3>
            </div>
        {% endif %}
        
        <div class="dashboard-link">
            <a href="/dashboard">📊 View Dashboard with Graphs</a>
        </div>
    </div>
</body>
</html>
"""

# Simple dashboard with graphs
DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {
            font-family: Arial;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2 {
            color: white;
            text-align: center;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 20px 0;
        }
        .stat {
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .charts {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }
        .chart-box {
            background: white;
            padding: 20px;
            border-radius: 15px;
        }
        canvas {
            max-height: 300px;
            width: 100%;
        }
        .recent {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
        }
        .scan-item {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
        }
        .badge-phish {
            background: #e74c3c;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
        }
        .badge-safe {
            background: #27ae60;
            color: white;
            padding: 3px 10px;
            border-radius: 15px;
        }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px;
        }
        .center {
            text-align: center;
        }
        .live {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="center">
            <span class="live">🔴 LIVE - Refreshes every 3 seconds</span>
        </div>
        
        <h1>📊 Phishing Detection Dashboard</h1>
        
        <div class="stats">
            <div class="stat">
                <h3>Total Scans</h3>
                <div class="stat-number" id="total">0</div>
            </div>
            <div class="stat">
                <h3>Phishing</h3>
                <div class="stat-number" id="phishing" style="color:#e74c3c;">0</div>
            </div>
            <div class="stat">
                <h3>Safe</h3>
                <div class="stat-number" id="safe" style="color:#27ae60;">0</div>
            </div>
            <div class="stat">
                <h3>Threat Rate</h3>
                <div class="stat-number" id="rate" style="color:#e74c3c;">0%</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-box">
                <h2 style="color:#333;">Pie Chart</h2>
                <canvas id="pieChart"></canvas>
            </div>
            <div class="chart-box">
                <h2 style="color:#333;">Trend Line</h2>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-box">
                <h2 style="color:#333;">Threat Gauge</h2>
                <canvas id="gaugeChart"></canvas>
            </div>
            <div class="chart-box">
                <h2 style="color:#333;">Recent Scans</h2>
                <div id="recent" style="max-height: 250px; overflow-y: auto;">
                    <p>No scans yet</p>
                </div>
            </div>
        </div>
        
        <div class="center">
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh</button>
            <button class="refresh-btn" onclick="window.location.href='/'">← Back</button>
        </div>
        
        <p class="center" style="color:white;">Last updated: <span id="timestamp">Never</span></p>
    </div>
    
    <script>
        let pieChart, trendChart, gaugeChart;
        
        async function loadData() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                // Update stats
                document.getElementById('total').innerText = data.total;
                document.getElementById('phishing').innerText = data.phishing;
                document.getElementById('safe').innerText = data.total - data.phishing;
                const rate = data.total > 0 ? ((data.phishing / data.total) * 100).toFixed(1) : 0;
                document.getElementById('rate').innerText = rate + '%';
                document.getElementById('timestamp').innerText = new Date().toLocaleTimeString();
                
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
                const trendData = data.recent_scans.length > 0 ? data.recent_scans : [0];
                trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: trendData.map((_, i) => 'Scan ' + (i+1)),
                        datasets: [{
                            label: 'Threat Level',
                            data: trendData,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            fill: true
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1,
                                ticks: {
                                    callback: (val) => val === 1 ? 'Phishing' : 'Safe'
                                }
                            }
                        }
                    }
                });
                
                // Gauge Chart
                const gaugeCtx = document.getElementById('gaugeChart').getContext('2d');
                if (gaugeChart) gaugeChart.destroy();
                gaugeChart = new Chart(gaugeCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Threat', 'Safe'],
                        datasets: [{
                            data: [rate, 100 - rate],
                            backgroundColor: ['#e74c3c', '#27ae60']
                        }]
                    },
                    options: {
                        cutout: '65%'
                    }
                });
                
                // Recent scans
                const recentDiv = document.getElementById('recent');
                if (data.recent_list && data.recent_list.length > 0) {
                    recentDiv.innerHTML = data.recent_list.map(item => `
                        <div class="scan-item">
                            <div>
                                <span class="${item.is_phishing ? 'badge-phish' : 'badge-safe'}">
                                    ${item.is_phishing ? '⚠️ PHISHING' : '✅ SAFE'}
                                </span>
                                <span style="margin-left: 10px;">${item.preview}</span>
                            </div>
                            <div>${item.time}</div>
                        </div>
                    `).join('');
                } else {
                    recentDiv.innerHTML = '<p style="text-align:center;color:#999;">No scans yet. Test some emails first!</p>';
                }
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('recent').innerHTML = '<p style="color:red;">Error loading data. Make sure server is running.</p>';
            }
        }
        
        // Load data immediately and every 3 seconds
        loadData();
        setInterval(loadData, 3000);
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
            
            # Store history (last 10)
            scan_history.append(1 if pred == 1 else 0)
            if len(scan_history) > 10:
                scan_history.pop(0)
            
            # Store recent scans
            recent_scans.insert(0, {
                'is_phishing': pred == 1,
                'preview': email[:60] + '...' if len(email) > 60 else email,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            if len(recent_scans) > 10:
                recent_scans.pop()
            
            result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
            print(f"✅ Analyzed - Total: {counters['total']}, Phishing: {counters['phishing']}")
    
    return render_template_string(MAIN_PAGE, result=result)

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD_PAGE)

@app.route('/api/stats')
def stats():
    return {
        'total': counters['total'],
        'phishing': counters['phishing'],
        'recent_scans': scan_history,
        'recent_list': recent_scans[:10]
    }

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 STARTING PHISHING DETECTOR")
    print("="*50)
    print("Main App: http://127.0.0.1:5000")
    print("Dashboard: http://127.0.0.1:5000/dashboard")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
