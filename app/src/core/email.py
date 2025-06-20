import logging
from pydantic import EmailStr # Good practice to use EmailStr for type hinting if applicable

# Configure basic logging if not already configured elsewhere in the app
# logging.basicConfig(level=logging.INFO) # Commented out, assuming FastAPI handles this

async def send_verification_email(to_email: EmailStr, token: str, subject_prefix: str = "Verify your email"):
    """
    Sends an email with a verification link.
    In a real application, this would integrate with an email service (e.g., SendGrid, Mailgun, or use fastapi-mail).
    """
    # Ensure the base URL for verification links is configurable, e.g., via environment variables
    # For now, using a placeholder. In a real app, this might come from settings.
    base_url = "http://localhost:3000" # This should ideally be configurable
    verification_link = f"{base_url}/verify-email?token={token}"

    logging.info(f"---- EMAIL SIMULATION ----")
    logging.info(f"To: {to_email}")
    logging.info(f"Subject: {subject_prefix} for Your SpendShare Account")
    logging.info(f"Body: Please verify your email address by clicking the link below:")
    logging.info(f"{verification_link}")
    logging.info(f"If you did not request this, please ignore this email.")
    logging.info(f"---- END EMAIL SIMULATION ----")
    # Example of how it might look with a real email library:
    # email = MessageSchema(
    #     subject=f"{subject_prefix} for Your SpendShare Account",
    #     recipients=[to_email],
    #     body=f"Please verify your email by clicking this link: {verification_link}",
    #     subtype="html" # or "plain"
    # )
    # await fm.send_message(email) # fm being an instance of FastMail

async def send_email_change_verification_email(to_email: EmailStr, token: str):
    """
    Sends an email to verify a new email address when a user requests an email change.
    """
    # Ensure the base URL for verification links is configurable
    base_url = "http://localhost:3000" # This should ideally be configurable
    verification_link = f"{base_url}/verify-email-change?token={token}"

    logging.info(f"---- EMAIL SIMULATION ----")
    logging.info(f"To: {to_email}")
    logging.info(f"Subject: Confirm Your New Email Address for SpendShare")
    logging.info(f"Body: Please confirm your new email address by clicking the link below:")
    logging.info(f"{verification_link}")
    logging.info(f"If you did not request this change, please contact support immediately.")
    logging.info(f"---- END EMAIL SIMULATION ----")

async def send_password_reset_email(to_email: EmailStr, token: str):
    """
    Sends an email with a password reset link.
    (Placeholder for now, but good to have a consistent structure)
    """
    base_url = "http://localhost:3000" # This should ideally be configurable
    reset_link = f"{base_url}/reset-password?token={token}" # Example, actual path might differ

    logging.info(f"---- EMAIL SIMULATION ----")
    logging.info(f"To: {to_email}")
    logging.info(f"Subject: Reset Your Password for SpendShare")
    logging.info(f"Body: You requested a password reset. Click the link below to set a new password:")
    logging.info(f"{reset_link}")
    logging.info(f"If you did not request a password reset, please ignore this email or contact support if you have concerns.")
    logging.info(f"---- END EMAIL SIMULATION ----")

# Example Usage (can be removed, just for illustration):
# if __name__ == "__main__":
#     import asyncio
#     async def main():
#         await send_verification_email("test@example.com", "somerandomtoken123")
#         await send_email_change_verification_email("new@example.com", "anotherrandomtoken456")
#         await send_password_reset_email("user@example.com", "resettoken789")
#     asyncio.run(main())
