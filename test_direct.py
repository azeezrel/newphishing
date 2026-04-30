import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Load model and vectorizer
print("Loading model and vectorizer...")
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)

with open('models/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

print(f"Model type: {type(model)}")
print(f"Model expects: {model.n_features_in_} features")
print(f"Vectorizer has: {len(vectorizer.get_feature_names_out())} features")

# Test emails
test_emails = [
    "Your Bank of America account has been suspended. Click here to verify: http://fake-bank.com",
    "Meeting tomorrow at 10am in conference room",
    "Your account has been compromised, click here to reset your password"
]

print("\n" + "="*50)
for email in test_emails:
    try:
        vec = vectorizer.transform([email])
        print(f"Vector shape: {vec.shape}")
        pred = model.predict(vec)[0]
        result = "PHISHING" if pred == 1 else "SAFE"
        print(f"{result}: {email[:60]}...")
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Email: {email[:60]}...")