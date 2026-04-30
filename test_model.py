import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the trained model
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)

# Since vectorizer isn't saved separately, let's recreate it
# First, load the preprocessed data to get the vectorizer
import joblib

# Try loading vectorizer if it exists in different format
try:
    vectorizer = joblib.load('models/vectorizer.joblib')
    print("Loaded vectorizer from models/vectorizer.joblib")
except:
    try:
        # Load from preprocessed data
        data = pd.read_pickle('data/preprocessed_data.pkl')
        # Recreate vectorizer from the preprocessed data
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=5000)
        
        # Load original data to fit vectorizer
        df = pd.read_csv('data/phishing_emails.csv')
        vectorizer.fit(df['text'])
        print("Recreated vectorizer from original data")
    except Exception as e:
        print(f"Error: {e}")
        print("Creating new vectorizer...")
        # Create new vectorizer
        df = pd.read_csv('data/phishing_emails.csv')
        vectorizer = TfidfVectorizer(max_features=5000)
        vectorizer.fit(df['text'])
        print("Created new vectorizer")

# Test emails
test_emails = [
    'Your account has been compromised, click here to reset your password',
    'Meeting tomorrow at 10am in conference room',
    'Congratulations! You won a $1000 Amazon gift card, claim now',
    'Please find attached the quarterly report for review',
    'Dear customer, your PayPal account has been limited, verify now',
    'Team lunch on Friday, please RSVP'
]

print("\n" + "="*60)
print("PHISHING DETECTION RESULTS")
print("="*60)

for email in test_emails:
    vec = vectorizer.transform([email])
    pred = model.predict(vec)[0]
    result = "🔴 PHISHING" if pred == 1 else "🟢 SAFE"
    print(f"{result}: {email[:60]}...")

print("="*60)