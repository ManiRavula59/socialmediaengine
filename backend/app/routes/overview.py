from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from ..database import SessionLocal
from ..models import Tweet, Hashtag

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/api/overview")
async def get_overview(db: Session = Depends(get_db)):
    """Dashboard overview data"""
    
    # Total posts
    total_posts = db.query(func.count(Tweet.id)).scalar() or 0
    
    # Sentiment breakdown
    sentiment_counts = db.query(
        Tweet.sentiment, 
        func.count(Tweet.id)
    ).group_by(Tweet.sentiment).all()
    
    sentiment_data = {
        'positive': 0,
        'negative': 0,
        'neutral': 0
    }
    for s, count in sentiment_counts:
        if s in sentiment_data:
            sentiment_data[s] = count
    
    # Top 10 trending hashtags
    top_hashtags = db.query(
        Hashtag.hashtag,
        func.count(Hashtag.id).label('count')
    ).group_by(
        Hashtag.hashtag
    ).order_by(
        desc('count')
    ).limit(10).all()
    
    # Posts over time (last 24 hours)
    last_24h = datetime.now() - timedelta(hours=24)
    posts_over_time = db.query(
        func.strftime('%Y-%m-%d %H:00:00', Tweet.date).label('hour'),
        func.count(Tweet.id).label('count')
    ).filter(
        Tweet.date >= last_24h
    ).group_by('hour').order_by('hour').all()
    
    return {
        "total_posts": total_posts,
        "sentiment": sentiment_data,
        "top_hashtags": [
            {"tag": tag, "count": count}
            for tag, count in top_hashtags
        ],
        "posts_over_time": [
            {"time": str(row.hour), "count": row.count}
            for row in posts_over_time
        ]
    }
