from flask import Flask, render_template_string, request, jsonify
import pickle
import time
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

print("="*60)
print("STARTING PHISHING DETECTOR - FIXED VERSION")
print("="*60)

# Create simple models
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
        "irs tax refund waiting click here to claim"
    ]
    safe_emails = [
        "meeting tomorrow at 10am in conference room",
        "project deadline is friday please submit your work",
        "team lunch at 12pm today in the cafeteria",
        "can you review this document when you have time",
        "weekly report attached please find the details",
        "reminder about the training session tomorrow"
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
    print("✅ Models created successfully!")
else:
    with open('models/phishing_detector.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('models/vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("✅ Models loaded successfully!")

# Store data
scan_data = {
    'total': 0,
    'phishing': 0,
    'history': [],  # Last 10 scans (1=phishing, 0=safe)
    'recent': []    # Last 10 scans with details
}

# Main HTML page
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
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
        .status {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI Phishing Email Detector</h1>
            <p>Paste an email to detect phishing attempts</p>
        </div>
        
        <div class="card">
            <form method="POST" id="scanForm">
                <textarea name="email" id="emailInput" rows="8" placeholder="Paste email content here..."></textarea>
                <br>
                <button type="submit">🔍 Analyze Email</button>
            </form>
            
            <div style="margin-top: 10px;">
                <small>Quick test:</small>
                <button type="button" class="example-btn" onclick="fillPhishing()">⚠️ Phishing Example</button>
                <button type="button" class="example-btn" onclick="fillSafe()">✅ Safe Example</button>
            </div>
            
            <div id="resultArea"></div>
            
            <div class="status" id="statusMsg">
                📊 Ready to scan. Dashboard will update automatically.
            </div>
        </div>
        
        <div class="dashboard-link">
            <a href="/dashboard" target="_blank">📊 Open Live Dashboard with Graphs →</a>
        </div>
    </div>
    
    <script>
        function fillPhishing() {
            document.getElementById('emailInput').value = "URGENT: Your account has been compromised! Click here to verify immediately: http://fake-bank.com/verify";
        }
        function fillSafe() {
            document.getElementById('emailInput').value = "Meeting reminder: Project review tomorrow at 2pm in Conference Room A";
        }
        
        // Check if form was submitted
        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const result = urlParams.get('result');
            if (result) {
                const resultDiv = document.getElementById('resultArea');
                if (result === 'phishing') {
                    resultDiv.innerHTML = `<div class="result phishing"><h3>⚠️ PHISHING DETECTED!</h3><p>Do not click any links or reply to this email!</p></div>`;
                } else if (result === 'safe') {
                    resultDiv.innerHTML = `<div class="result safe"><h3>✅ SAFE EMAIL</h3><p>This email appears legitimate.</p></div>`;
                }
                document.getElementById('statusMsg').innerHTML = '✅ Email analyzed! Check the dashboard for updated graphs.';
            }
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
    <title>Live Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
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
        .error-msg {
            background: #fee;
            color: #c0392b;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="center">
            <span class="live-badge">🔴 LIVE UPDATES - Refreshes every 2 seconds</span>
        </div>
        
        <h1>📊 Phishing Detection Dashboard</h1>
        
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
                <h3>📈 Scan Trend (Last 10 Scans)</h3>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>⚠️ Threat Level Gauge</h3>
                <canvas id="gaugeChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📋 Recent Scans</h3>
                <div id="recentScans" style="max-height: 300px; overflow-y: auto;">
                    <p style="text-align: center; color: #999;">No scans yet. Test some emails in the main app!</p>
                </div>
            </div>
        </div>
        
        <div class="center">
            <button onclick="location.reload()">🔄 Refresh Page</button>
            <button onclick="window.location.href='/'">← Back to Scanner</button>
        </div>
        
        <p class="center timestamp" style="color: white; margin-top: 20px;">
            Last updated: <span id="updateTime">Never</span>
        </p>
    </div>
    
    <script>
        let pieChart, trendChart, gaugeChart;
        
        async function fetchData() {
            try {
                const response = await fetch('/api/stats');
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                
                // Update stats
                document.getElementById('total').innerText = data.total;
                document.getElementById('phishing').innerText = data.phishing;
                document.getElementById('safe').innerText = data.total - data.phishing;
                const rate = data.total > 0 ? ((data.phishing / data.total) * 100).toFixed(1) : 0;
                document.getElementById('rate').innerText = rate + '%';
                document.getElementById('updateTime').innerText = new Date().toLocaleTimeString();
                
                // Update Pie Chart
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
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
                
                // Update Trend Chart
                const trendCtx = document.getElementById('trendChart').getContext('2d');
                if (trendChart) trendChart.destroy();
                const historyData = data.history.length > 0 ? data.history : [0];
                const labels = data.history.map((_, i) => '#' + (i + 1));
                trendChart = new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: labels.length ? labels : ['No Data'],
                        datasets: [{
                            label: 'Threat Level (1=Phishing, 0=Safe)',
                            data: historyData,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            borderWidth: 3,
                            pointRadius: 6,
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
                                        return value === 1 ? '⚠️ Phishing' : '✅ Safe';
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
                const gaugeCtx = document.getElementById('gaugeChart').getContext('2d');
                if (gaugeChart) gaugeChart.destroy();
                gaugeChart = new Chart(gaugeCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Threat Level (' + rate + '%)', 'Safe Level'],
                        datasets: [{
                            data: [rate, 100 - rate],
                            backgroundColor: ['#e74c3c', '#27ae60'],
                            borderWidth: 3
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
                
                // Update recent scans list
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
                    recentDiv.innerHTML = '<p style="text-align: center; color: #999;">📭 No scans yet. Go to the main app and test some emails!</p>';
                }
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('recentScans').innerHTML = '<div class="error-msg">❌ Error connecting to server. Make sure the app is running on port 5000</div>';
            }
        }
        
        // Fetch data immediately and every 2 seconds
        fetchData();
        setInterval(fetchData, 2000);
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result_param = None
    
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email and email.strip():
            # Analyze
            vec = vectorizer.transform([email])
            pred = model.predict(vec)[0]
            is_phishing = bool(pred == 1)
            
            # Update data
            scan_data['total'] += 1
            if is_phishing:
                scan_data['phishing'] += 1
            
            # Update history (keep last 10)
            scan_data['history'].append(1 if is_phishing else 0)
            if len(scan_data['history']) > 10:
                scan_data['history'].pop(0)
            
            # Update recent scans
            scan_data['recent'].insert(0, {
                'is_phishing': is_phishing,
                'preview': email[:70] + '...' if len(email) > 70 else email,
                'time': datetime.now().strftime('%H:%M:%S')
            })
            if len(scan_data['recent']) > 10:
                scan_data['recent'].pop()
            
            result_param = 'phishing' if is_phishing else 'safe'
            print(f"✅ Analyzed - Result: {'PHISHING' if is_phishing else 'SAFE'} | Total: {scan_data['total']} | Phishing: {scan_data['phishing']}")
    
    # Pass result as query parameter
    if result_param:
        return render_template_string(MAIN_PAGE) + f'<script>window.onload=function(){{const d=document.getElementById("resultArea");if(d)d.innerHTML=`<div class="result {result_param}"><h3>{"⚠️ PHISHING DETECTED!" if result_param=="phishing" else "✅ SAFE EMAIL"}</h3><p>{"Do not click any links!" if result_param=="phishing" else "This email appears legitimate."}</p></div>`;document.getElementById("statusMsg").innerHTML="✅ Email analyzed! Check the dashboard for updated graphs.";}}</script>'
    
    return render_template_string(MAIN_PAGE)

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
    print("✅ PHISHING DETECTOR IS RUNNING")
    print("="*60)
    print("📧 Main App: http://127.0.0.1:5000")
    print("📊 Dashboard: http://127.0.0.1:5000/dashboard")
    print("="*60)
    print("\n🎯 INSTRUCTIONS:")
    print("1. Open the Main App and paste an email")
    print("2. Click 'Analyze Email'")
    print("3. Open the Dashboard to see graphs update")
    print("4. Dashboard auto-refreshes every 2 seconds")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
