from fastapi import Depends, HTTPException, status, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkErrors, SDKError

from src.db.database import get_session
from src.models.models import User
from src.config import settings

clerk = Clerk(settings.CLERK_SECRET_KEY)


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify the session token
        clerk_session = await clerk.sessions.verify_session(token)
        clerk_user = await clerk.users.get_user(clerk_session.user_id)

        # Check if user exists in our database
        statement = select(User).where(User.clerk_id == clerk_user.id)
        result = await session.exec(statement)
        user = result.first()

        if not user:
            # Create a new user in our database
            user = User(
                clerk_id=clerk_user.id,
                email=clerk_user.email_addresses[0].email_address,
                username=clerk_user.username,
                full_name=clerk_user.first_name + " " + clerk_user.last_name,
                email_verified=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user

    except ClerkErrors.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ClerkErrors.TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except SDKError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Clerk SDK error: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )