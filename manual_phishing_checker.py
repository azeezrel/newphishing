import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import getpass

class ManualPhishingChecker:
    def __init__(self):
        print("🔧 Loading Phishing Detection Model...")
        
        # Load model
        with open('models/phishing_detector.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        # Load vectorizer
        df = pd.read_csv('data/phishing_emails.csv')
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.vectorizer.fit(df['text'])
        
        print("✅ Model loaded successfully!\n")
    
    def check_email(self, email_text, sender="Unknown", subject="Unknown"):
        """Check if an email is phishing"""
        vec = self.vectorizer.transform([email_text[:2000]])
        pred = self.model.predict(vec)[0]
        return pred == 1  # True if phishing
    
    def send_alert(self, alert_email, alert_password, sender, subject, confidence="High"):
        """Send alert email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = alert_email
            msg['To'] = alert_email
            msg['Subject'] = f"🚨 PHISHING ALERT - {subject[:40]}"
            
            body = f"""
╔══════════════════════════════════════════════════════════╗
║     🚨 PHISHING DETECTION ALERT 🚨                        ║
╚══════════════════════════════════════════════════════════╝

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Confidence: {confidence}

SUSPICIOUS EMAIL DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From: {sender}
Subject: {subject}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ ACTION REQUIRED:
• DO NOT click any links in this email
• DO NOT download any attachments
• DO NOT reply to the email
• Report as phishing in your email client
• Delete the email immediately

🔒 This is an automated alert from your Phishing Detection System.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Determine SMTP server based on email
            if '@gmail.com' in alert_email:
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
            elif '@outlook.com' in alert_email or '@hotmail.com' in alert_email:
                smtp_server = "smtp-mail.outlook.com"
                smtp_port = 587
            else:
                print("Unknown email provider. Please use Gmail or Outlook for alerts.")
                return False
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(alert_email, alert_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send alert: {e}")
            return False
    
    def interactive_mode(self):
        """Manually check emails"""
        print("\n" + "="*50)
        print("MANUAL PHISHING CHECKER")
        print("="*50)
        print("Paste an email to check if it's phishing.")
        print("Type 'quit' to exit.\n")
        
        while True:
            print("\n📧 " + "-"*40)
            email_text = input("Paste email content (or 'quit'): ").strip()
            
            if email_text.lower() == 'quit':
                break
            
            if not email_text:
                print("Please enter some text.")
                continue
            
            is_phishing = self.check_email(email_text)
            
            if is_phishing:
                print("\n" + "🚨"*20)
                print("⚠️  PHISHING EMAIL DETECTED!  ⚠️")
                print("🚨"*20)
                print("\nDO NOT click any links or download attachments!\n")
                
                # Ask if they want to send an alert
                send_alert = input("Send alert email? (yes/no): ").strip().lower()
                if send_alert == 'yes':
                    alert_email = input("Your email for alerts: ").strip()
                    alert_password = getpass.getpass("Email password: ")
                    
                    if self.send_alert(alert_email, alert_password, "Manual Entry", email_text[:50]):
                        print("✅ Alert sent successfully!")
                    else:
                        print("❌ Failed to send alert")
            else:
                print("\n✅ SAFE EMAIL ✅")
                print("This email appears legitimate.\n")
    
    def auto_mode_with_forwarding(self):
        """Instructions for auto-forwarding emails"""
        print("\n" + "="*60)
        print("📧 SETUP AUTOMATIC EMAIL FORWARDING")
        print("="*60)
        print("""
To automatically check emails without storing passwords:

1. Create a new Gmail account (e.g., phishingchecker@gmail.com)
2. Enable 2-Step Verification on that account
3. Generate an App Password for that account
4. Forward suspicious emails from your main account to this checker account
5. This script can monitor the checker account

OR use this web-based approach:

1. Keep your web app running: python app.py
2. Manually copy/paste suspicious emails to http://127.0.0.1:5000
3. Get instant results

Would you like to set up a dedicated checker email account?""")
        
        choice = input("\nSet up checker email? (yes/no): ").strip().lower()
        
        if choice == 'yes':
            print("\n📧 Create a new Gmail account at: https://mail.google.com")
            print("Then come back here and I'll help you configure it.")
        else:
            print("\n✅ Use the web app at http://127.0.0.1:5000 for manual checking.")

if __name__ == "__main__":
    print("\n" + "🛡️"*25)
    print("PHISHING DETECTION SYSTEM")
    print("🛡️"*25)
    
    checker = ManualPhishingChecker()
    
    print("\nChoose mode:")
    print("1. Interactive Mode (paste emails to check)")
    print("2. Web App Mode (use browser interface)")
    print("3. Auto-Forwarding Setup Instructions")
    
    choice = input("\nChoice (1/2/3): ").strip()
    
    if choice == '1':
        checker.interactive_mode()
    elif choice == '2':
        print("\nStarting web app...")
        import subprocess
        import sys
        subprocess.Popen([sys.executable, 'app.py'])
        print("\n✅ Web app started! Open http://127.0.0.1:5000 in your browser")
    elif choice == '3':
        checker.auto_mode_with_forwarding()
    else:
        print("Goodbye!")