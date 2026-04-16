import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASS")

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASS)

    server.sendmail(
        EMAIL,
        EMAIL,
        "Subject: Test Email\n\nThis is a test email"
    )

    print("Email sent successfully")

    server.quit()

except Exception as e:
    print("ERROR:", e)