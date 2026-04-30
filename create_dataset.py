import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Phishing email templates
phishing = [
    "Your account has been compromised, verify now",
    "Update your payment information immediately",
    "Congratulations! You have won $1000, claim your prize",
    "Your password expires today, click here to keep it",
    "Bank alert: Unusual activity detected on your account",
    "Your PayPal account has been limited, confirm your identity",
    "Urgent: Your account will be closed within 24 hours",
    "Tax refund pending: Process immediately to receive funds",
    "Your Netflix subscription has expired, update billing info",
    "Security alert: Someone logged into your account"
]

# Legitimate email templates
legitimate = [
    "Meeting agenda for tomorrow attached, please review",
    "Project update completed ahead of schedule",
    "Team lunch tomorrow at 12 PM in cafeteria",
    "Your timesheet has been approved",
    "Quarterly report ready for download",
    "Reminder: Department meeting at 2pm in conference room",
    "Thank you for your contribution to the project",
    "New hire announcement: Please welcome John to the team",
    "HR update: Holiday schedule for next month released",
    "Your request for time off has been approved"
]

# Generate 500 emails (250 phishing, 250 legitimate)
data = []
for i in range(250):
    text = np.random.choice(phishing) + f" (ref_{i})"
    data.append([text, 1])
    
for i in range(250):
    text = np.random.choice(legitimate) + f" (msg_{i})"
    data.append([text, 0])

# Create DataFrame and save
df = pd.DataFrame(data, columns=['text', 'label'])
df = df.sample(frac=1).reset_index(drop=True)  # Shuffle
df.to_csv('data/phishing_emails.csv', index=False)

print(f"SUCCESS! Created dataset with {len(df)} emails")
print(f"Phishing emails: {len(df[df.label==1])}")
print(f"Legitimate emails: {len(df[df.label==0])}")
print("Saved to: data/phishing_emails.csv")