import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from hangout.config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT, BUSINESS_NAME


def send_email(subject, html_body, recipient=None, sender=None, password=None):
    """Send an HTML email via Gmail SMTP with App Password."""
    sender = sender or GMAIL_SENDER
    password = password or GMAIL_APP_PASSWORD
    recipient = recipient or GMAIL_RECIPIENT

    if not all([sender, password, recipient]):
        raise ValueError(
            "Gmail credentials not configured. Set environment variables:\n"
            "  HANGOUT_GMAIL_SENDER=your.email@gmail.com\n"
            "  HANGOUT_GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx\n"
            "  HANGOUT_GMAIL_RECIPIENT=recipient@email.com"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{BUSINESS_NAME} <{sender}>"
    msg["To"] = recipient

    # Plain text fallback
    plain = f"{subject}\n\nView this email in an HTML-capable client for the full report."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent to {recipient}")
