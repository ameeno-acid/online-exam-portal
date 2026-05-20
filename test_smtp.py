import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def test_email():
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    
    print(f"User: {email_user}")
    print(f"Pass: {email_pass}")
    print(f"Server: {smtp_server}:{smtp_port}")

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_user
    msg['Subject'] = "Test Email"
    msg.attach(MIMEText("This is a test email.", 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_email()
