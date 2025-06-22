import logging
from typing import Optional
from pydantic import EmailStr

import requests

from app.src.config import get_settings

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def send_email_mailgun(
    email_to: EmailStr,
    subject: str,
    html_content: str
) -> bool:
    """
    Sends an email using the Mailgun API.
    Returns True if the email was sent successfully (or at least accepted by Mailgun), False otherwise.
    """
    settings = get_settings()
    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN_NAME:
        logger.error("Mailgun API key or domain name not configured. Cannot send email.")
        return False

    mailgun_url = f"{settings.MAILGUN_API_BASE_URL.rstrip('/')}/{settings.MAILGUN_DOMAIN_NAME}/messages"

    from_email = settings.MAIL_FROM_EMAIL
    if not from_email:
        logger.error("MAIL_FROM_EMAIL not configured. Cannot send email.")
        return False

    try:
        response = requests.post(
            mailgun_url,
            auth=("api", settings.MAILGUN_API_KEY),
            data={"from": f"SpendShare <{from_email}>",
                  "to": [email_to],
                  "subject": subject,
                  "html": html_content})

        if response.status_code == 200:
            logger.info(f"Email sent to {email_to} via Mailgun. Subject: {subject}")
            return True
        else:
            logger.error(f"Failed to send email via Mailgun. Status: {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email via Mailgun: {e}")
        return False


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

    html_body_lines = [
        f"<p>A new user has registered their interest in the beta program.</p>",
        f"<p><strong>Email:</strong> {interested_email}</p>",
    ]
    if description:
        html_body_lines.append(f"<p><strong>Description:</strong> {description}</p>")

    html_content = "<html><body>" + "".join(html_body_lines) + "</body></html>"

    # The `email_to` for this function is the notification recipient (e.g., admin)
    # The `interested_email` is the user who signed up.
    # We are sending an email TO the admin ABOUT the interested user.
    send_email_mailgun(email_to=email_to, subject=subject, html_content=html_content)

async def send_verification_email(to_email: EmailStr, token: str, subject_prefix: str = "Verify your email"):
    """
    Sends an email with a verification link.
    In a real application, this would integrate with an email service (e.g., SendGrid, Mailgun, or use fastapi-mail).
    """
    settings = get_settings()
    base_url = settings.FRONTEND_URL
    verification_link = f"{base_url}/verify-email?token={token}"

    subject = f"{subject_prefix} for Your SpendShare Account"
    html_content = f"""
    <html>
    <body>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        <p>If you did not request this, please ignore this email.</p>
    </body>
    </html>
    """
    send_email_mailgun(email_to=to_email, subject=subject, html_content=html_content)

async def send_email_change_verification_email(to_email: EmailStr, token: str):
    """
    Sends an email to verify a new email address when a user requests an email change.
    """
    settings = get_settings()
    base_url = settings.FRONTEND_URL
    verification_link = f"{base_url}/verify-email-change?token={token}"

    subject = "Confirm Your New Email Address for SpendShare"
    html_content = f"""
    <html>
    <body>
        <p>Please confirm your new email address by clicking the link below:</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        <p>If you did not request this change, please contact support immediately.</p>
    </body>
    </html>
    """
    send_email_mailgun(email_to=to_email, subject=subject, html_content=html_content)

async def send_password_reset_email(to_email: EmailStr, token: str):
    """
    Sends an email with a password reset link.
    (Placeholder for now, but good to have a consistent structure)
    """
    settings = get_settings()
    base_url = settings.FRONTEND_URL
    reset_link = f"{base_url}/reset-password?token={token}" # Example, actual path might differ

    subject = "Reset Your Password for SpendShare"
    html_content = f"""
    <html>
    <body>
        <p>You requested a password reset. Click the link below to set a new password:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
    </body>
    </html>
    """
    send_email_mailgun(email_to=to_email, subject=subject, html_content=html_content)
