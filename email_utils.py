import smtplib
from email.mime.text import MIMEText

SENDER_EMAIL = "akulanavyasahithi@gmail.com"
APP_PASSWORD = "yxnzcvapamnyosuh"

WEBSITE_LINK = "http://localhost:8501"


def send_email(to_email, subject, message):

    body = f"""
Hello,

{message}

---------------------------------------
🔗 Login to Food Donation Portal:
{WEBSITE_LINK}

Please login to take action.

Thank you,
Food Donation System
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully")

    except Exception as e:
        print("Email error:", e)