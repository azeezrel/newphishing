import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

print("="*60)
print("COMPLETE RETRAINING FROM SCRATCH")
print("="*60)

# Load data
print("\n1. Loading data...")
df = pd.read_csv('data/phishing_emails.csv')
print(f"   Loaded {len(df)} emails")

# Create features and labels
print("\n2. Creating features...")
vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(df['text'])
y = df['label']

print(f"   Features shape: {X.shape}")

# Split data
print("\n3. Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
print("\n4. Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Test accuracy
accuracy = model.score(X_test, y_test)
print(f"   Accuracy: {accuracy:.2%}")

# Save
print("\n5. Saving files...")
with open('models/phishing_detector.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('models/vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

print("   ✓ Model saved")
print("   ✓ Vectorizer saved")

# Test with new emails
print("\n6. Testing with examples...")
test_emails = [
    "Your account has been compromised! Click here: http://fake.com",
    "Meeting tomorrow at 10am in conference room"
]

for email in test_emails:
    vec = vectorizer.transform([email])
    pred = model.predict(vec)[0]
    result = "⚠️ PHISHING" if pred == 1 else "✅ SAFE"
    print(f"   {result}: {email[:50]}")

print("\n" + "="*60)
print("✅ RETRAINING COMPLETE!")
print("="*60)