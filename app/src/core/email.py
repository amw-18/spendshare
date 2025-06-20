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

async def send_verification_email(to_email: EmailStr, token: str, subject_prefix: str = "Verify your email"):
    """
    Sends an email with a verification link.
    In a real application, this would integrate with an email service (e.g., SendGrid, Mailgun, or use fastapi-mail).
    """
    base_url = "http://localhost:3000" # This should ideally be configurable
    verification_link = f"{base_url}/verify-email?token={token}"

    logger.info(f"---- EMAIL SIMULATION ----")
    logger.info(f"To: {to_email}")
    logger.info(f"Subject: {subject_prefix} for Your SpendShare Account")
    logger.info(f"Body: Please verify your email address by clicking the link below:")
    logger.info(f"{verification_link}")
    logger.info(f"If you did not request this, please ignore this email.")
    logger.info(f"---- END EMAIL SIMULATION ----")

async def send_email_change_verification_email(to_email: EmailStr, token: str):
    """
    Sends an email to verify a new email address when a user requests an email change.
    """
    base_url = "http://localhost:3000" # This should ideally be configurable
    verification_link = f"{base_url}/verify-email-change?token={token}"

    logger.info(f"---- EMAIL SIMULATION ----")
    logger.info(f"To: {to_email}")
    logger.info(f"Subject: Confirm Your New Email Address for SpendShare")
    logger.info(f"Body: Please confirm your new email address by clicking the link below:")
    logger.info(f"{verification_link}")
    logger.info(f"If you did not request this change, please contact support immediately.")
    logger.info(f"---- END EMAIL SIMULATION ----")

async def send_password_reset_email(to_email: EmailStr, token: str):
    """
    Sends an email with a password reset link.
    (Placeholder for now, but good to have a consistent structure)
    """
    base_url = "http://localhost:3000" # This should ideally be configurable
    reset_link = f"{base_url}/reset-password?token={token}" # Example, actual path might differ

    logger.info(f"---- EMAIL SIMULATION ----")
    logger.info(f"To: {to_email}")
    logger.info(f"Subject: Reset Your Password for SpendShare")
    logger.info(f"Body: You requested a password reset. Click the link below to set a new password:")
    logger.info(f"{reset_link}")
    logger.info(f"If you did not request a password reset, please ignore this email or contact support if you have concerns.")
    logger.info(f"---- END EMAIL SIMULATION ----")
