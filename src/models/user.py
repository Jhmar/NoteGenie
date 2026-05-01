"""
Database Models for NoteGenie
"""
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    profile_pic = Column(String(255))
    
    # Relationships
    documents = relationship("UserDocument", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", uselist=False, back_populates="user", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")

class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default='#f59e0b')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="folders")
    documents = relationship("UserDocument", back_populates="folder")

class UserDocument(Base):
    __tablename__ = 'user_documents'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    folder_id = Column(String(36), ForeignKey('folders.id'), nullable=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(255))  # Display title
    file_type = Column(String(50))  # 'ocr', 'stt', 'tts', 'summary', 'questions', 'pdf', 'audio', 'text'
    original_filename = Column(String(255))
    file_size = Column(Integer)
    content = Column(Text)  # extracted text
    summary = Column(Text)  # for summaries
    questions = Column(JSON)  # for generated questions
    audio_url = Column(String(255))  # for TTS/STT
    created_at = Column(DateTime, default=datetime.utcnow)
    last_opened = Column(DateTime, default=datetime.utcnow)
    is_favorite = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    folder = relationship("Folder", back_populates="documents")

class UserActivity(Base):
    __tablename__ = 'user_activities'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    action = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activities")

class UserSettings(Base):
    __tablename__ = 'user_settings'
    
    user_id = Column(String(36), ForeignKey('users.id'), primary_key=True)
    theme = Column(String(20), default='light')
    default_language = Column(String(10), default='en')
    email_notifications = Column(Boolean, default=True)
    auto_save = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="settings")

# Database setup
DATABASE_URL = "sqlite:///./notegenie.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")

def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()