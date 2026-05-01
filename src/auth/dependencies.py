"""
Authentication dependencies for FastAPI routes
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from src.auth.jwt_handler import verify_token
from src.models.user import get_db, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user - checks multiple places"""
    
    # Try header first
    if not token:
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
    
    # Try cookie second
    if not token:
        token = request.cookies.get("access_token")
    
    # Try query parameter last (for testing)
    if not token:
        token = request.query_params.get("token")
    
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user

async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user