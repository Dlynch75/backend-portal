import smtplib
from email.mime.text import MIMEText

EMAIL_HOST = "smtp.office365.com"
EMAIL_PORT = 587
EMAIL_HOST_USER="connect@gulfteachers.com"
EMAIL_HOST_PASSWORD="Gulfteachers99!"


msg = MIMEText("This is a test email.")
msg["Subject"] = "SMTP Test"
msg["From"] = EMAIL_HOST_USER
msg["To"] = "shahabmughal766@gmail.com"

try:
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    server.sendmail(EMAIL_HOST_USER, ["recipient@example.com"], msg.as_string())
    server.quit()
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
