import os
import pickle
import base64
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

# Authenticate and build Gmail service
def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

service = authenticate_gmail()

# Check for new emails
def check_emails(service):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=25).execute()
    messages = results.get('messages', [])
    summary = []
    if not messages:
        return "No new emails."
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            subject = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'), "No Subject Found")
            summary.append(f"Email {len(summary)+1}: {subject}")

    return "\n".join(summary)


# Read a specific email by number
def read_email(service, email_number):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])
    
    if len(messages) < email_number:
        return "Email not found."
    
    message_id = messages[email_number - 1]['id']
    msg = service.users().messages().get(userId='me', id=message_id).execute()
    
    # Handle different email formats (plain, multipart, etc.)
    if 'data' in msg['payload']['body']:
        # Simple plain text email
        message = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
    else:
        # Multipart email (with attachments or different parts)
        parts = msg['payload'].get('parts', [])
        for part in parts:
            if part['mimeType'] == 'text/plain':  # Look for the plain text part
                message = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
        else:
            message = "No plain text body found in this email."
    
    return message


# Send an email
def send_email(service, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    send_message = {'raw': raw_message}
    service.users().messages().send(userId='me', body=send_message).execute()
    return "Email sent successfully."

# Command processing for email actions
def process_email_command(command, service):
    if "check emails" in command:
        return check_emails(service)
    elif "read email" in command:
        email_number = int(command.split()[-1])
        return read_email(service, email_number)
    elif "send email" in command:
        to = command.split('to')[1].split()[0]
        subject = command.split('subject')[1].split()[0]
        body = command.split('body')[1]
        return send_email(service, to, subject, body)
    else:
        return "Command not recognized."
def get_important_unread_emails(service):
    # Search for unread and important emails
    results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD', 'IMPORTANT']).execute()
    messages = results.get('messages', [])
    
    if not messages:
        return "No important unread emails. You're all caught up! 🎉"
    
    summary = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        subject = next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject')
        summary.append(f"Important Email {len(summary) + 1}: {subject}")
    
    return "\n".join(summary)

summary = check_emails(service)
print(summary)
email_content = read_email(service, 1)  # Read the first unread email
print(email_content)
result = send_email(service, 'email@gmail.com', 'Test Subject', 'This is a test email.')
print(result)
important_emails = get_important_unread_emails(service)
print(important_emails)
