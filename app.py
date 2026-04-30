from flask import Flask, render_template, render_template_string, request, jsonify
import pickle
import time

app = Flask(__name__)

# Load model and vectorizer
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)
with open('models/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

# In-memory counters for simple live stats (persist only while app runs)
counters = { 'total': 0, 'phishing': 0 }

# Simple HTML for main page (kept inline for convenience)
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Phishing Detector</title>
</head>
<body>
    <h1>🛡️ Phishing Email Detector</h1>
    <form method="POST">
        <textarea name="email" rows="8" cols="60" placeholder="Paste email here..."></textarea>
        <br>
        <button type="submit">Analyze</button>
    </form>
    {% if result %}
        <h2>{{ result }}</h2>
    {% endif %}
    <p><a href="/dashboard">Open live dashboard</a></p>
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        if email:
            vec = vectorizer.transform([email])
            pred = model.predict(vec)[0]
            # update simple counters
            counters['total'] += 1
            if int(pred) == 1:
                counters['phishing'] += 1
            result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
    return render_template_string(HTML, result=result)


@app.route('/dashboard')
def dashboard():
    # Renders a simple dashboard that polls `/stats` for live numbers
    return render_template('dashboard.html')


@app.route('/stats')
def stats():
    total = counters.get('total', 0)
    phishing = counters.get('phishing', 0)
    rate = (phishing / total) if total > 0 else 0.0
    return jsonify({
        'time': time.strftime('%H:%M:%S'),
        'total': total,
        'phishing': phishing,
        'phishing_rate': round(rate, 4)
    })


if __name__ == '__main__':
    app.run(debug=True)