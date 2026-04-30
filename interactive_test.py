import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Load model and create vectorizer
with open('models/phishing_detector.pkl', 'rb') as f:
    model = pickle.load(f)

df = pd.read_csv('data/phishing_emails.csv')
vectorizer = TfidfVectorizer(max_features=5000)
vectorizer.fit(df['text'])

print("\n" + "="*50)
print("PHISHING EMAIL DETECTOR")
print("="*50)
print("Type an email to check if it's phishing or safe.")
print("Type 'quit' to exit.\n")

while True:
    email = input("Enter email text: ")
    if email.lower() == 'quit':
        print("Goodbye!")
        break
    
    if len(email.strip()) == 0:
        print("Please enter some text.\n")
        continue
    
    vec = vectorizer.transform([email])
    pred = model.predict(vec)[0]
    
    if pred == 1:
        print("⚠️  RESULT: PHISHING EMAIL - Be careful!\n")
    else:
        print("✅ RESULT: SAFE EMAIL\n")