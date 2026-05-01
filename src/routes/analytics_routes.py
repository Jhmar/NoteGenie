"""
Analytics Routes for NoteGenie
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from src.models.user import get_db, UserDocument, UserActivity
from src.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview")
async def get_analytics_overview(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics overview for user"""
    
    # Total counts by type
    total_docs = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id
    ).count()
    
    # Count by file type
    type_counts = {}
    file_types = ['ocr', 'stt', 'tts', 'summary', 'questions', 'pdf']
    for doc_type in file_types:
        count = db.query(UserDocument).filter(
            UserDocument.user_id == current_user.id,
            UserDocument.file_type == doc_type
        ).count()
        type_counts[doc_type] = count
    
    # Activity over time (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_activity = db.query(
        func.date(UserActivity.created_at).label('date'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.user_id == current_user.id,
        UserActivity.created_at >= seven_days_ago
    ).group_by(func.date(UserActivity.created_at)).order_by(func.date(UserActivity.created_at)).all()
    
    # Format daily activity
    activity_data = []
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        found = False
        for act in daily_activity:
            if act.date == date:
                activity_data.insert(0, {"date": str(date), "count": act.count})
                found = True
                break
        if not found:
            activity_data.insert(0, {"date": str(date), "count": 0})
    
    # Storage usage
    total_storage = db.query(func.sum(UserDocument.file_size)).filter(
        UserDocument.user_id == current_user.id
    ).scalar() or 0
    
    # Most used features
    feature_usage = db.query(
        UserActivity.action,
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.user_id == current_user.id
    ).group_by(UserActivity.action).order_by(func.count(UserActivity.id).desc()).limit(5).all()
    
    # Recent activity (last 10)
    recent_activity = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).order_by(UserActivity.created_at.desc()).limit(10).all()
    
    # Recent files (last 6)
    recent_files = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id
    ).order_by(UserDocument.created_at.desc()).limit(6).all()
    
    return {
        "total_documents": total_docs,
        "by_type": type_counts,
        "daily_activity": activity_data,
        "total_storage_mb": round(total_storage / (1024 * 1024), 2),
        "feature_usage": [
            {"feature": feat.action, "count": feat.count}
            for feat in feature_usage
        ],
        "recent_activity": [
            {
                "action": act.action,
                "time": act.created_at,
                "details": act.details
            } for act in recent_activity
        ],
        "recent_files": [
            {
                "id": file.id,
                "filename": file.filename,
                "type": file.file_type,
                "created_at": file.created_at,
                "size": file.file_size
            } for file in recent_files
        ],
        "member_since": current_user.created_at
    }

@router.get("/study-patterns")
async def get_study_patterns(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze study patterns"""
    
    # Peak study hours
    hour_activity = db.query(
        extract('hour', UserActivity.created_at).label('hour'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.user_id == current_user.id
    ).group_by('hour').order_by('hour').all()
    
    # Weekday distribution
    weekday_activity = db.query(
        extract('dow', UserActivity.created_at).label('weekday'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.user_id == current_user.id
    ).group_by('weekday').order_by('weekday').all()
    
    # Weekday names
    weekday_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    
    return {
        "hourly_activity": [
            {"hour": int(h.hour), "count": h.count}
            for h in hour_activity
        ],
        "weekly_activity": [
            {"weekday": weekday_names[int(w.weekday)], "count": w.count}
            for w in weekday_activity
        ]
    }