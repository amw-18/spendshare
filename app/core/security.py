from passlib.context import CryptContext

# Initialize a password context (using bcrypt as the scheme)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Potentially add JWT token functions here later if needed for authentication
# from datetime import datetime, timedelta
# from typing import Optional
# from jose import JWTError, jwt
# SECRET_KEY = "YOUR_SECRET_KEY" # Should be loaded from env variables
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None): ...
# def verify_token(token: str, credentials_exception): ...
