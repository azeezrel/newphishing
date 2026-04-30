from flask import Flask, render_template_string, request
import pickle

app = Flask(__name__)

# Load model and vectorizer
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)
with open('models/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

# Simple HTML
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
            result = "⚠️ PHISHING DETECTED!" if pred == 1 else "✅ SAFE EMAIL"
    return render_template_string(HTML, result=result)

if __name__ == '__main__':
    app.run(debug=True)