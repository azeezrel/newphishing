import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the model
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)

# Load the original data to fit a vectorizer
df = pd.read_csv('data/phishing_emails.csv')

# Create and fit vectorizer
vectorizer = TfidfVectorizer(max_features=5000)
vectorizer.fit(df['text'])

# Test different emails
test_emails = [
    "Your account has been compromised. Click here to reset your password.",
    "Meeting tomorrow at 10am in the conference room.",
    "Congratulations! You've won a $1000 gift card. Claim now!",
    "Please find attached the quarterly report for your review.",
    "URGENT: Your PayPal account has been limited. Verify your identity now.",
    "Team lunch on Friday at 12pm. Please let me know if you can attend.",
    "Bank alert: Unusual activity detected. Login to confirm your identity.",
    "HR Update: New holiday schedule for next month attached."
]

print("\n" + "="*70)
print("PHISHING EMAIL DETECTION SYSTEM - RESULTS")
print("="*70)

for email in test_emails:
    vec = vectorizer.transform([email])
    pred = model.predict(vec)[0]
    result = "⚠️ PHISHING DETECTED" if pred == 1 else "✅ SAFE EMAIL"
    print(f"{result}: {email[:50]}...")

print("="*70)