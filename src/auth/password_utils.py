"""
Password hashing utilities - Simplified version
"""
import bcrypt
from passlib.context import CryptContext

# Use a simpler context with explicit backend
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Explicitly set rounds
)

def hash_password(password: str) -> str:
    """Hash a password"""
    # Ensure password is within bcrypt limits
    if len(password.encode('utf-8')) > 72:
        password = password[:50]  # Truncate to safe length
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Ensure password is within bcrypt limits
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:50]
    return pwd_context.verify(plain_password, hashed_password)

# Alternative direct bcrypt functions (more reliable)
def hash_password_bcrypt(password: str) -> str:
    """Hash password using direct bcrypt"""
    # Convert to bytes and ensure proper length
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """Verify password using direct bcrypt"""
    try:
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False