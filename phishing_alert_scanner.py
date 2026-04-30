import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup
import time
from datetime import datetime
import getpass
import ssl
import smtplib

class PhishingAlertScanner:
    def __init__(self):
        print("🔧 Initializing Phishing Alert Scanner...")
        
        # Load your trained model
        with open('models/phishing_detector.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        # Load vectorizer
        df = pd.read_csv('data/phishing_emails.csv')
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.vectorizer.fit(df['text'])
        
        self.mail = None
        self.alert_email = None
        self.alert_password = None
        self.smtp_server = None
        
    def setup_alerts(self):
        """Setup email alerts"""
        print("\n" + "="*50)
        print("📧 EMAIL ALERT SETUP")
        print("="*50)
        print("Enter the email address where you want to receive phishing alerts:")
        self.alert_email = input("Alert email: ").strip()
        
        print("\nSelect your alert email provider:")
        print("1. Gmail")
        print("2. Outlook/Hotmail")
        print("3. Other")
        choice = input("Choice (1-3): ").strip()
        
        if choice == '1':
            self.smtp_server = "smtp.gmail.com"
            self.smtp_port = 587
            print("\n⚠️ For Gmail alerts, you need an App Password")
        elif choice == '2':
            self.smtp_server = "smtp-mail.outlook.com"
            self.smtp_port = 587
        else:
            self.smtp_server = input("SMTP server: ").strip()
            self.smtp_port = int(input("SMTP port: ").strip())
        
        self.alert_password = getpass.getpass("Email password (or app password): ")
        
        # Test alert connection
        print("\n📧 Sending test alert...")
        if self.send_alert("Test", "✅ Phishing Alert System is now active!", "test@system.com", "Test Alert"):
            print("✅ Alert system configured successfully!")
        else:
            print("❌ Failed to send test alert. Check your credentials.")
    
    def send_alert(self, alert_type, message, sender, subject):
        """Send email alert"""
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.alert_email
            msg['To'] = self.alert_email
            msg['Subject'] = f"🚨 PHISHING ALERT: {subject[:50]}"
            
            body = f"""
            ╔══════════════════════════════════════════════════════════╗
            ║     🚨 PHISHING DETECTION ALERT 🚨                        ║
            ╚══════════════════════════════════════════════════════════╝
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Alert Type: {alert_type}
            
            Suspicious Email Details:
            ────────────────────────────────────────────────────────────
            From: {sender}
            Subject: {subject}
            ────────────────────────────────────────────────────────────
            
            Risk Assessment: {message}
            
            ⚠️ WHAT TO DO:
            1. DO NOT click any links in the suspicious email
            2. DO NOT download any attachments
            3. DO NOT reply to the email
            4. Mark it as spam/phishing in your email client
            5. Delete the email
            
            🔒 This alert was generated automatically by your Phishing Detection System.
            
            Stay safe!
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.alert_email, self.alert_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send alert: {e}")
            return False
    
    def get_email_credentials(self):
        """Get email credentials for scanning"""
        print("\n" + "="*50)
        print("EMAIL SCANNING SETUP")
        print("="*50)
        
        self.email = input("Enter email address to scan: ").strip()
        
        print("\nSelect your email provider:")
        print("1. Gmail")
        print("2. Outlook/Hotmail")
        print("3. Yahoo")
        print("4. Other")
        
        choice = input("Choice (1-4): ").strip()
        
        if choice == '1':
            self.imap_server = "imap.gmail.com"
            self.imap_port = 993
        elif choice == '2':
            self.imap_server = "outlook.office365.com"
            self.imap_port = 993
        elif choice == '3':
            self.imap_server = "imap.mail.yahoo.com"
            self.imap_port = 993
        else:
            self.imap_server = input("IMAP server: ").strip()
            self.imap_port = int(input("IMAP port (993): ").strip() or "993")
        
        self.password = getpass.getpass("Email password (or app password): ")
    
    def connect(self):
        """Connect to email server"""
        try:
            context = ssl.create_default_context()
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context)
            self.mail.login(self.email, self.password)
            self.mail.select('INBOX')
            print("✅ Connected to email server!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_email_body(self, email_message):
        """Extract email body"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(email_message.get_payload())
        return body[:3000]
    
    def decode_header_value(self, value):
        """Decode email headers"""
        if value:
            decoded_parts = decode_header(value)
            result = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        result += part.decode(encoding if encoding else 'utf-8', errors='ignore')
                    except:
                        result += part.decode('utf-8', errors='ignore')
                else:
                    result += str(part)
            return result
        return "No Subject"
    
    def scan_and_alert(self, max_emails=20):
        """Scan emails and send alerts for phishing"""
        if not self.connect():
            return
        
        try:
            result, data = self.mail.search(None, 'UNSEEN')
            email_ids = data[0].split()
            
            if not email_ids:
                print("📭 No new emails found.")
                return
            
            if len(email_ids) > max_emails:
                email_ids = email_ids[-max_emails:]
            
            print(f"\n📧 Scanning {len(email_ids)} emails...\n")
            
            phishing_found = False
            
            for email_id in email_ids:
                result, msg_data = self.mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                subject = self.decode_header_value(email_message['Subject'])
                sender = self.decode_header_value(email_message['From'])
                body = self.get_email_body(email_message)
                
                if body and len(body) > 10:
                    vec = self.vectorizer.transform([body[:2000]])
                    pred = self.model.predict(vec)[0]
                    
                    if pred == 1:  # PHISHING DETECTED
                        phishing_found = True
                        print(f"\n🚨 PHISHING DETECTED!")
                        print(f"   From: {sender[:60]}")
                        print(f"   Subject: {subject[:70]}")
                        print(f"   📧 Sending alert to {self.alert_email}...")
                        
                        # Send email alert
                        alert_message = "⚠️ PHISHING EMAIL DETECTED - Do not interact with this email!"
                        self.send_alert("Immediate Action Required", alert_message, sender, subject)
                        print("   ✅ Alert sent!")
            
            if not phishing_found:
                print("\n✅ No phishing emails detected in this scan.")
                print(f"   Checked {len(email_ids)} emails, all appear safe.")
            
        except Exception as e:
            print(f"Error scanning: {e}")
        finally:
            if self.mail:
                self.mail.close()
                self.mail.logout()
    
    def continuous_monitor(self, check_interval=60):
        """Continuously monitor for phishing emails"""
        print("\n" + "="*50)
        print("🔍 STARTING CONTINUOUS MONITORING")
        print("="*50)
        print(f"Checking for new emails every {check_interval} seconds...")
        print(f"Alerts will be sent to: {self.alert_email}")
        print("Press Ctrl+C to stop\n")
        
        processed_ids = set()
        
        if not self.connect():
            return
        
        try:
            while True:
                result, data = self.mail.search(None, 'UNSEEN')
                email_ids = data[0].split()
                
                for email_id in email_ids:
                    if email_id not in processed_ids:
                        processed_ids.add(email_id)
                        
                        result, msg_data = self.mail.fetch(email_id, '(RFC822)')
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)
                        
                        subject = self.decode_header_value(email_message['Subject'])
                        sender = self.decode_header_value(email_message['From'])
                        body = self.get_email_body(email_message)
                        
                        if body and len(body) > 10:
                            vec = self.vectorizer.transform([body[:2000]])
                            pred = self.model.predict(vec)[0]
                            
                            if pred == 1:
                                print(f"\n🚨🚨🚨 PHISHING ALERT! 🚨🚨🚨")
                                print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                print(f"   From: {sender[:60]}")
                                print(f"   Subject: {subject[:70]}")
                                print(f"   📧 Alert sent to {self.alert_email}")
                                
                                self.send_alert("URGENT", "Phishing email detected in your inbox!", sender, subject)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped.")
            print(f"📊 Monitored {len(processed_ids)} emails")

if __name__ == "__main__":
    print("\n" + "🛡️"*25)
    print("PHISHING DETECTOR WITH EMAIL ALERTS")
    print("🛡️"*25 + "\n")
    
    scanner = PhishingAlertScanner()
    
    print("\nFirst, let's set up where to send alerts:")
    scanner.setup_alerts()
    
    print("\nNow, let's set up which inbox to scan:")
    scanner.get_email_credentials()
    
    print("\n" + "="*50)
    print("CHOOSE MONITORING MODE")
    print("="*50)
    print("1. Scan once and send alerts")
    print("2. Continuous monitoring (sends alerts automatically)")
    print("3. Exit")
    
    choice = input("\nChoice (1/2/3): ").strip()
    
    if choice == '1':
        scanner.scan_and_alert(max_emails=20)
    elif choice == '2':
        interval = input("Check interval in seconds (default 60): ").strip()
        interval = int(interval) if interval else 60
        scanner.continuous_monitor(check_interval=interval)
    else:
        print("Goodbye!")