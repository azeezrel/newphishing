import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import os

print("="*60)
print("FIXING MODEL AND VECTORIZER")
print("="*60)

# Load your data
print("\n1. Loading email data...")
df = pd.read_csv('data/phishing_emails.csv')
print(f"   Loaded {len(df)} emails")

# Display data info
print(f"   Columns: {df.columns.tolist()}")
print(f"   Label distribution:\n{df['label'].value_counts()}")

# Create vectorizer with fixed parameters
print("\n2. Creating vectorizer...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english'
)

# Transform the text data
print("3. Transforming text data...")
X = vectorizer.fit_transform(df['text'])
y = df['label'].values

print(f"   Feature matrix shape: {X.shape}")
print(f"   Number of features: {X.shape[1]}")

# Split data
print("\n4. Splitting data for training...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"   Training samples: {X_train.shape[0]}")
print(f"   Testing samples: {X_test.shape[0]}")

# Train model
print("\n5. Training Random Forest model...")
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"   Model Accuracy: {accuracy:.2%}")

# Save model and vectorizer
print("\n6. Saving model and vectorizer...")
with open('models/phishing_detector.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('models/vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

print("   ✓ Model saved to models/phishing_detector.pkl")
print("   ✓ Vectorizer saved to models/vectorizer.pkl")

# Test the saved model
print("\n7. Testing saved model...")
with open('models/phishing_detector.pkl', 'rb') as f:
    test_model = pickle.load(f)
with open('models/vectorizer.pkl', 'rb') as f:
    test_vectorizer = pickle.load(f)

# Test with sample emails
test_emails = [
    "Your account has been compromised, click here to reset your password",
    "Meeting tomorrow at 10am in conference room",
    "Congratulations! You won a $1000 gift card, claim now"
]

print("\n8. Testing with sample emails:")
for email in test_emails:
    vec = test_vectorizer.transform([email])
    pred = test_model.predict(vec)[0]
    result = "PHISHING" if pred == 1 else "SAFE"
    print(f"   {result}: {email[:50]}...")

print("\n" + "="*60)
print("✅ FIX COMPLETE! Model and vectorizer are now synchronized.")
print("="*60)