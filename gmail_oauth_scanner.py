import pickle
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email import message_from_bytes
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

# Gmail API scope - read only
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailOAuthScanner:
    def __init__(self):
        print("🔧 Initializing Gmail OAuth Scanner...")
        
        # Load your trained model
        with open('models/phishing_detector.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        # Load vectorizer
        df = pd.read_csv('data/phishing_emails.csv')
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.vectorizer.fit(df['text'])
        
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API using OAuth"""
        creds = None
        
        # Token file stores user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("\n" + "="*50)
                print("GMAIL AUTHENTICATION REQUIRED")
                print("="*50)
                print("You need to create credentials in Google Cloud Console:")
                print("1. Go to: https://console.cloud.google.com/")
                print("2. Create new project or select existing")
                print("3. Enable Gmail API")
                print("4. Create OAuth 2.0 Client ID (Desktop app)")
                print("5. Download as 'credentials.json'")
                print("="*50)
                
                input("\nPress Enter after you have credentials.json file...")
                
                if not os.path.exists('credentials.json'):
                    print("❌ credentials.json not found! Please download it first.")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail authentication successful!")
    
    def get_email_body(self, msg_id):
        """Extract text from email"""
        try:
            message = self.service.users().messages().get(
                userId='me', id=msg_id, format='raw'
            ).execute()
            
            msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
            mime_msg = message_from_bytes(msg_str)
            
            text = ""
            if mime_msg.is_multipart():
                for part in mime_msg.walk():
                    if part.get_content_type() == "text/plain":
                        text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    elif part.get_content_type() == "text/html":
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        text = BeautifulSoup(html, 'html.parser').get_text()
                        break
            else:
                if mime_msg.get_content_type() == "text/plain":
                    text = mime_msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            return text[:3000]
        except Exception as e:
            print(f"Error: {e}")
            return ""
    
    def scan_recent_emails(self, max_emails=10):
        """Scan recent emails"""
        if not self.service:
            print("Not authenticated!")
            return
        
        results = self.service.users().messages().list(
            userId='me', maxResults=max_emails, labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("No emails found.")
            return
        
        print(f"\n📧 Found {len(messages)} emails to analyze...\n")
        print("="*60)
        
        for msg in messages:
            msg_data = self.service.users().messages().get(
                userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()
            
            headers = msg_data.get('payload', {}).get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            
            body = self.get_email_body(msg['id'])
            
            if body:
                vec = self.vectorizer.transform([body[:2000]])
                pred = self.model.predict(vec)[0]
                status = "⚠️ PHISHING" if pred == 1 else "✅ SAFE"
                
                print(f"\n{status}")
                print(f"   From: {sender[:60]}")
                print(f"   Subject: {subject[:70]}")
                print("-" * 60)

if __name__ == "__main__":
    scanner = GmailOAuthScanner()
    scanner.scan_recent_emails()