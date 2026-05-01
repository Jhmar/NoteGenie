"""
JWT token handling
"""
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # Token expires in 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Refresh token expires in 7 days

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def create_refresh_token(data: Dict) -> str:
    """Create a refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Verify a token and return its payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        return payload
    except JWTError:
        return None

def get_current_user(token: str) -> Optional[Dict]:
    """Get current user from token"""
    payload = verify_token(token)
    if payload:
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role")
        }
    return None