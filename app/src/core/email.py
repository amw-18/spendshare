import logging
from typing import Optional
from pydantic import EmailStr

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def send_beta_interest_email(
    email_to: EmailStr,
    interested_email: EmailStr,
    description: Optional[str] = None
):
    """
    Sends an email notification about a new beta interest registration.
    For now, it logs the email content instead of sending via SMTP.
    """
    subject = f"New Beta Program Interest: {interested_email}"
    body_lines = [
        f"A new user has registered their interest in the beta program.",
        f"Email: {interested_email}",
    ]
    if description:
        body_lines.append(f"Description: {description}")

    email_content = f"To: {email_to}\nSubject: {subject}\n\n" + "\n".join(body_lines)

    logger.info("---- BEGIN EMAIL CONTENT ----")
    logger.info(email_content)
    logger.info("---- END EMAIL CONTENT ----")

    # In a real scenario, you would use smtplib or another email library:
    # import smtplib
    # from email.mime.text import MIMEText
    #
    # msg = MIMEText("\n".join(body_lines))
    # msg['Subject'] = subject
    # msg['From'] = "noreply@spendshare.app" # Or your app's email
    # msg['To'] = email_to
    #
    # try:
    #     with smtplib.SMTP('localhost', 1025) as server: # Or your actual SMTP server
    #         server.sendmail(msg['From'], [msg['To']], msg.as_string())
    #     logger.info(f"Successfully sent beta interest email to {email_to} for {interested_email}")
    # except Exception as e:
    #     logger.error(f"Failed to send beta interest email: {e}")

# Example usage (for testing this file directly, not part of the app flow):
if __name__ == "__main__":
    send_beta_interest_email(
        email_to="support@example.com",
        interested_email="testuser@example.com",
        description="Looking forward to testing!"
    )
    send_beta_interest_email(
        email_to="admin@example.com",
        interested_email="anotheruser@example.com"
    )
