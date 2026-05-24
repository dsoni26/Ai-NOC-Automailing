import os
import smtplib
from email.message import EmailMessage


def send_email(subject: str, body: str, recipient: str, sender: str = None, password: str = None):
    sender_email = (sender or os.getenv("GMAIL_EMAIL", "")).strip()
    raw_password = password or os.getenv("GMAIL_APP_PASSWORD", "")
    app_password = "".join(raw_password.split())

    if not sender_email or not app_password:
        return False, "Gmail credentials are missing. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env."
    if not recipient:
        return False, "Recipient email is required."

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(message)
        return True, f"Email sent successfully to {recipient}."
    except Exception as exc:
        error_text = str(exc)
        if "5.7.8" in error_text or "Username and Password not accepted" in error_text:
            return (
                False,
                "Email sending failed: Gmail rejected the login. Confirm that "
                "2-Step Verification is enabled and that GMAIL_APP_PASSWORD is a valid 16-character "
                "Google App Password. If you pasted it with spaces, the app now removes them automatically."
            )
        return False, f"Email sending failed: {exc}"
