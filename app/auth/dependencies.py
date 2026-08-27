"""Auth utilities for routes - DEMO MODE: Authentication disabled for public access"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.auth.security import TokenData, SECRET_KEY, ALGORITHM
import os
from dotenv import load_dotenv

load_dotenv()

# DEMO MODE: Set to True for public demo (no login required)
DEMO_MODE = True

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=not DEMO_MODE)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate JWT token and return current user.
    In DEMO_MODE, returns a dummy user without requiring authentication.
    """
    # DEMO MODE: Return a dummy user for public access
    if DEMO_MODE:

        class DemoUser:
            id = 1
            username = "demo_user"
            email = "demo@example.com"

        return DemoUser()

    from app.models.database import SessionLocal
    from app.models.schemas import User

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise credential_exception
        return user
    finally:
        db.close()
