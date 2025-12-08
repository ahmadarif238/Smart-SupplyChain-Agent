from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()
import logging
logger = logging.getLogger("auth")

# Settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing - direct bcrypt to avoid passlib issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


# Generate proper bcrypt hash directly to avoid validation errors
def hash_password(password: str) -> str:
    """Hash password using bcrypt directly"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


# Load admin credentials from env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret").strip()

# Users database removed - using DB instead


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash using bcrypt directly"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate hash for a password using bcrypt directly"""
    return hash_password(password)


def authenticate_user(db, username: str, password: str):
    """Authenticate user with username and password against DB"""
    from app.models.schemas import User
    
    # DEBUG LOGGING
    logger.info(f"Attempting login for user: '{username}'")
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        logger.warning(f"User '{username}' not found in db.")
        return False
    
    # User found, verifying password calls...
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Password verification failed for user '{username}'")
        return False
    
    logger.info(f"Login successful for user '{username}'")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
