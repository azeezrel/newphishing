import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

print("Loading model...")

# Load model and vectorizer
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)

with open('models/vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

print(f"Model ready! Expects {model.n_features_in_} features\n")

print("="*50)
print("PHISHING EMAIL CHECKER")
print("="*50)
print("Paste an email and I'll tell you if it's phishing.")
print("Type 'quit' to exit.\n")

while True:
    print("\n📧 Enter email text:")
    email_text = input("> ").strip()
    
    if email_text.lower() == 'quit':
        print("Goodbye!")
        break
    
    if not email_text:
        print("Please enter some text.")
        continue
    
    try:
        # Transform and predict
        vec = vectorizer.transform([email_text])
        pred = model.predict(vec)[0]
        
        if pred == 1:
            print("\n" + "🚨" * 20)
            print("⚠️  PHISHING EMAIL DETECTED!  ⚠️")
            print("🚨" * 20)
            print("\n⚠️ DO NOT click any links or download attachments!\n")
        else:
            print("\n✅" * 20)
            print("✓ SAFE EMAIL ✓")
            print("✅" * 20)
            print("\nThis email appears legitimate.\n")
    except Exception as e:
        print(f"Error: {e}")