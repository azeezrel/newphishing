import imaplib
import email
from email.header import decode_header
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup
import time
from datetime import datetime
import getpass
import ssl

class IMAPPhishingScanner:
    def __init__(self):
        print("🔧 Initializing IMAP Email Phishing Scanner...")
        
        # Load your trained model
        with open('models/phishing_detector.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        # Load vectorizer
        df = pd.read_csv('data/phishing_emails.csv')
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.vectorizer.fit(df['text'])
        
        self.mail = None
    
    def get_email_credentials(self):
        """Get email credentials from user"""
        print("\n" + "="*50)
        print("EMAIL SETUP")
        print("="*50)
        print("\nSupported email providers:")
        print("1. Gmail - imap.gmail.com:993")
        print("2. Outlook/Hotmail - outlook.office365.com:993")
        print("3. Yahoo - imap.mail.yahoo.com:993")
        print("4. Other - Ask your provider\n")
        
        # Get email settings
        self.email = input("Enter your email address: ").strip()
        
        print("\nSelect your email provider:")
        print("1. Gmail")
        print("2. Outlook/Hotmail")
        print("3. Yahoo")
        print("4. Other")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            self.imap_server = "imap.gmail.com"
            self.imap_port = 993
            print("\n⚠️ For Gmail, you need an App Password:")
            print("   1. Go to Google Account → Security")
            print("   2. Enable 2-Step Verification")
            print("   3. Generate App Password for 'Mail'")
            print("   4. Use that password here (not your regular password)\n")
        elif choice == '2':
            self.imap_server = "outlook.office365.com"
            self.imap_port = 993
        elif choice == '3':
            self.imap_server = "imap.mail.yahoo.com"
            self.imap_port = 993
            print("\n⚠️ For Yahoo, you need an App Password:")
            print("   1. Go to Yahoo Account Security")
            print("   2. Enable 2-Step Verification")
            print("   3. Generate App Password")
            print("   4. Use that password here\n")
        else:
            self.imap_server = input("Enter IMAP server address: ").strip()
            self.imap_port = int(input("Enter IMAP port (usually 993): ").strip() or "993")
        
        # Get password securely
        self.password = getpass.getpass("Enter your email password (or app password): ")
    
    def connect(self):
        """Connect to email server"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server
            print(f"\n🔄 Connecting to {self.imap_server}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context)
            self.mail.login(self.email, self.password)
            self.mail.select('INBOX')
            print("✅ Successfully connected to email server!\n")
            return True
        except imaplib.IMAP4.error as e:
            print(f"\n❌ Login failed: {e}")
            print("\nTroubleshooting:")
            if "gmail.com" in self.imap_server:
                print("- For Gmail: You NEED an App Password, not your regular password")
                print("- Enable 2-Step Verification in Google Account settings")
                print("- Then generate an App Password for 'Mail'")
            elif "yahoo" in self.imap_server:
                print("- For Yahoo: You NEED an App Password")
                print("- Generate it in Yahoo Account Security settings")
            else:
                print("- Check your password")
                print("- Verify IMAP is enabled in your email settings")
            return False
        except Exception as e:
            print(f"\n❌ Connection failed: {e}")
            return False
    
    def get_email_body(self, email_message):
        """Extract plain text from email body"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        body = BeautifulSoup(html, 'html.parser').get_text()
                    except:
                        continue
        else:
            # Not multipart
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = str(email_message.get_payload())
            elif content_type == "text/html":
                try:
                    html = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    body = BeautifulSoup(html, 'html.parser').get_text()
                except:
                    body = str(email_message.get_payload())
        
        return body[:3000]  # Limit length
    
    def decode_header_value(self, value):
        """Decode email header values"""
        if value:
            decoded_parts = decode_header(value)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    try:
                        decoded_string += part.decode(encoding if encoding else 'utf-8', errors='ignore')
                    except:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            return decoded_string
        return "No Subject"
    
    def scan_emails(self, max_emails=20, scan_unread_only=True):
        """Scan emails from inbox"""
        if not self.connect():
            return
        
        try:
            # Search for emails
            if scan_unread_only:
                result, data = self.mail.search(None, 'UNSEEN')
            else:
                result, data = self.mail.search(None, 'ALL')
            
            email_ids = data[0].split()
            
            if not email_ids:
                print("📭 No emails found.")
                return
            
            # Limit number of emails
            if len(email_ids) > max_emails:
                email_ids = email_ids[-max_emails:]
            
            print(f"📧 Found {len(email_ids)} emails to analyze...\n")
            print("="*60)
            
            phishing_count = 0
            safe_count = 0
            
            for email_id in reversed(email_ids):  # Newest first
                result, msg_data = self.mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # Get email details
                subject = self.decode_header_value(email_message['Subject'])
                sender = self.decode_header_value(email_message['From'])
                
                # Get email body
                body = self.get_email_body(email_message)
                
                if body and len(body) > 10:  # Only analyze if there's content
                    # Analyze with your model
                    try:
                        vec = self.vectorizer.transform([body[:2000]])
                        pred = self.model.predict(vec)[0]
                        
                        if pred == 1:
                            phishing_count += 1
                            status = "⚠️ PHISHING DETECTED"
                            print(f"\n🚨 {status}")
                            print(f"   From: {sender[:60]}")
                            print(f"   Subject: {subject[:70]}")
                            print(f"   ⚠️ DO NOT click any links or download attachments!")
                        else:
                            safe_count += 1
                            status = "✅ SAFE"
                            print(f"\n{status}")
                            print(f"   From: {sender[:60]}")
                            print(f"   Subject: {subject[:70]}")
                        print("-" * 60)
                    except Exception as e:
                        print(f"Error analyzing email: {e}")
            
            # Print summary
            print("\n" + "="*60)
            print("📊 SCAN SUMMARY")
            print("="*60)
            print(f"📧 Total emails analyzed: {phishing_count + safe_count}")
            print(f"⚠️ Phishing detected: {phishing_count}")
            print(f"✅ Safe emails: {safe_count}")
            
            if phishing_count > 0:
                print(f"\n🚨 WARNING: {phishing_count} suspicious email(s) found!")
                print("   Do not click any links or download attachments from them.")
            
            print("="*60)
            
        except Exception as e:
            print(f"Error scanning emails: {e}")
        
        finally:
            if self.mail:
                self.mail.close()
                self.mail.logout()
    
    def monitor_continuously(self, check_interval=60):
        """Monitor for new emails continuously"""
        print("\n" + "="*50)
        print("🔍 STARTING CONTINUOUS EMAIL MONITORING")
        print("="*50)
        print(f"Checking for new emails every {check_interval} seconds...")
        print("Press Ctrl+C to stop monitoring\n")
        
        processed_ids = set()
        
        if not self.connect():
            return
        
        try:
            while True:
                # Search for unread emails
                result, data = self.mail.search(None, 'UNSEEN')
                email_ids = data[0].split()
                
                for email_id in email_ids:
                    if email_id not in processed_ids:
                        processed_ids.add(email_id)
                        
                        # Fetch and analyze email
                        result, msg_data = self.mail.fetch(email_id, '(RFC822)')
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)
                        
                        subject = self.decode_header_value(email_message['Subject'])
                        sender = self.decode_header_value(email_message['From'])
                        body = self.get_email_body(email_message)
                        
                        if body and len(body) > 10:
                            try:
                                vec = self.vectorizer.transform([body[:2000]])
                                pred = self.model.predict(vec)[0]
                                
                                if pred == 1:
                                    print(f"\n🚨🚨🚨 PHISHING ALERT! 🚨🚨🚨")
                                    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                    print(f"   From: {sender[:60]}")
                                    print(f"   Subject: {subject[:70]}")
                                    print(f"   ⚠️ DANGER: This email appears to be phishing!")
                                    print(f"   ⚠️ DO NOT click any links or download attachments!")
                                    print("-" * 60)
                            except Exception as e:
                                print(f"Error: {e}")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped.")
            print(f"📊 Total unique emails processed: {len(processed_ids)}")
        
        finally:
            if self.mail:
                self.mail.close()
                self.mail.logout()

if __name__ == "__main__":
    print("\n" + "🛡️"*25)
    print("EMAIL PHISHING DETECTOR - IMAP SCANNER")
    print("🛡️"*25 + "\n")
    
    scanner = IMAPPhishingScanner()
    scanner.get_email_credentials()
    
    print("\n" + "="*50)
    print("CHOOSE AN OPTION")
    print("="*50)
    print("1. Scan recent unread emails (last 20)")
    print("2. Continuous monitoring (checks every minute)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        scanner.scan_emails(max_emails=20, scan_unread_only=True)
    elif choice == '2':
        interval = input("Check interval in seconds (default 60): ").strip()
        interval = int(interval) if interval else 60
        scanner.monitor_continuously(check_interval=interval)
    else:
        print("Goodbye!")