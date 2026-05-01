"""
Authentication Routes for NoteGenie
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
import uuid

from src.models.user import get_db, User, UserSettings, UserActivity
from src.auth.password_utils import hash_password_bcrypt, verify_password_bcrypt
from src.auth.jwt_handler import create_access_token, create_refresh_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = ""

@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(400, "Username taken")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(400, "Email registered")
    
    # Create user
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password_bcrypt(user_data.password),
        full_name=user_data.full_name,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    
    # Create token
    token_data = {"sub": new_user.id, "username": new_user.username}
    access_token = create_access_token(token_data)
    
    return JSONResponse({
        "success": True,
        "access_token": access_token,
        "user_id": new_user.id,
        "username": new_user.username
    })

@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user or not verify_password_bcrypt(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    token_data = {"sub": user.id, "username": user.username}
    access_token = create_access_token(token_data)
    
    return JSONResponse({
        "success": True,
        "access_token": access_token,
        "user_id": user.id,
        "username": user.username
    })