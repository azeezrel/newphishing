import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

print("="*50)
print("IMPROVING MODEL WITH MORE DATA")
print("="*50)

# Load existing data
df_existing = pd.read_csv('data/phishing_emails.csv')
print(f"Existing data: {len(df_existing)} emails")

# Create additional synthetic training data (expansion)
additional_data = []

# More phishing patterns
phishing_extras = [
    ("Your Apple ID has been locked. Verify now: http://apple-id.com", 1),
    ("FedEx: Your package cannot be delivered. Update address: http://fedex.com", 1),
    ("Netflix: Your membership expired. Update payment: http://netflix.com", 1),
    ("IRS: You have a tax refund pending. Claim: http://irs.gov", 1),
    ("Your WhatsApp account will expire. Verify: http://whatsapp.com", 1),
    ("LinkedIn: Someone viewed your profile. See who: http://linkedin.com", 1),
    ("Spotify: Your premium trial ends today. Renew: http://spotify.com", 1),
    ("Amazon: Your order is on hold. Confirm: http://amazon.com", 1),
]

# More safe patterns
safe_extras = [
    ("Project deadline extended to next Friday", 0),
    ("Lunch and learn session tomorrow at noon", 0),
    ("Your timesheet has been approved", 0),
    ("New feature release notes attached", 0),
    ("Company holiday party RSVP", 0),
    ("Conference call dial-in details", 0),
    ("Employee of the month announcement", 0),
    ("Office closed for maintenance", 0),
]

# Add variations of each pattern
for i in range(50):
    for text, label in phishing_extras:
        varied_text = text + f" variant_{i}"
        additional_data.append([varied_text, label])
    
    for text, label in safe_extras:
        varied_text = text + f" ref_{i}"
        additional_data.append([varied_text, label])

# Combine datasets
df_additional = pd.DataFrame(additional_data, columns=['text', 'label'])
df_combined = pd.concat([df_existing, df_additional], ignore_index=True)
df_combined = df_combined.sample(frac=1).reset_index(drop=True)  # Shuffle

print(f"New dataset: {len(df_combined)} emails")
print(f"Phishing: {(df_combined.label == 1).sum()}")
print(f"Safe: {(df_combined.label == 0).sum()}")

# Train improved model
print("\nTraining improved model...")
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
X = vectorizer.fit_transform(df_combined['text'])
y = df_combined['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"\n✅ Improved Model Accuracy: {accuracy:.2%}")

# Save improved model
with open('models/phishing_detector.pkl', 'wb') as f:
    pickle.dump(model, f)

# Also save vectorizer separately for future use
with open('models/vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

print("\n✅ Improved model saved to models/phishing_detector.pkl")
print("="*50)