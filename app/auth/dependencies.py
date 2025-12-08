"""Auth utilities for routes"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.auth.security import TokenData, SECRET_KEY, ALGORITHM
import os
from dotenv import load_dotenv

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return current user from DB"""
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
