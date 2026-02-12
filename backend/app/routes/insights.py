from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import asyncio
import re
from collections import Counter
from ..database import SessionLocal
from ..models import Tweet, Hashtag
from ..llm_orchestrator import orchestrator

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def extract_keywords(texts, n=5):
    """Simple keyword extraction"""
    words = []
    for text in texts:
        if text:
            words.extend(re.findall(r'\b\w{4,}\b', text.lower()))
    
    stopwords = {'this', 'that', 'with', 'from', 'have', 'they', 'will', 
                 'what', 'when', 'where', 'which', 'there', 'their', 'about'}
    filtered = [w for w in words if w not in stopwords and len(w) > 3]
    
    return [word for word, _ in Counter(filtered).most_common(n)]

@router.get("/api/insights/crisis-detection")
async def detect_crisis(db: Session = Depends(get_db)):
    """Detect customer service crises using multi-model validation"""
    
    # Time ranges
    last_6h = datetime.now() - timedelta(hours=6)
    prev_6h = datetime.now() - timedelta(hours=12)
    
    # Current negative count
    current_neg = db.query(func.count(Tweet.id)).filter(
        Tweet.sentiment == 'negative',
        Tweet.date >= last_6h
    ).scalar() or 0
    
    # Previous negative count
    prev_neg = db.query(func.count(Tweet.id)).filter(
        Tweet.sentiment == 'negative',
        Tweet.date.between(prev_6h, last_6h)
    ).scalar() or 0
    
    # Calculate spike
    spike_pct = 0
    if prev_neg > 0:
        spike_pct = ((current_neg - prev_neg) / prev_neg) * 100
    
    # Get crisis tweets
    crisis_tweets = db.query(Tweet.text).filter(
        Tweet.sentiment == 'negative',
        Tweet.date >= last_6h
    ).limit(50).all()
    
    tweet_texts = [t.text for t in crisis_tweets if t.text]
    
    # Context for LLM
    total_posts = db.query(func.count(Tweet.id)).scalar() or 0
    context = {
        "total_posts": total_posts,
        "time_range": "6 hours",
        "negative_count": current_neg,
        "spike_percentage": f"{spike_pct:.0f}%",
        "positive_pct": "0",
        "neutral_pct": "0",
        "top_hashtags": [],
        "keywords": extract_keywords(tweet_texts, 5)
    }
    
    # Get insights from all 4 models in parallel
    insight = await orchestrator.get_best_insight(
        prompt=f"Analyze this customer service crisis: {spike_pct:.0f}% spike in negative mentions, {current_neg} negative tweets in last 6 hours. Keywords: {', '.join(context['keywords'])}. What's happening and what should brands do?",
        context=context
    )
    
    return {
        "insight_type": "crisis_detection",
        "metrics": {
            "negative_tweets": current_neg,
            "spike_percentage": f"{spike_pct:.0f}%",
            "keywords": context['keywords']
        },
        "llm_insight": insight,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/insights/trending")
async def get_trending_insight(db: Session = Depends(get_db)):
    """Get insights about trending topics"""
    
    last_24h = datetime.now() - timedelta(hours=24)
    
    # Get top hashtag
    top_tag = db.query(
        Hashtag.hashtag,
        func.count(Hashtag.id).label('count')
    ).filter(
        Hashtag.date >= last_24h
    ).group_by(
        Hashtag.hashtag
    ).order_by(
        func.count(Hashtag.id).desc()
    ).first()
    
    if not top_tag:
        return {"insight_type": "trending", "message": "No trending topics"}
    
    tag_name = top_tag[0]
    tag_count = top_tag[1]
    
    # Get sentiment for this hashtag
    sentiment_data = db.query(
        Tweet.sentiment,
        func.count(Tweet.id)
    ).join(
        Hashtag, Tweet.tweet_id == Hashtag.tweet_id
    ).filter(
        Hashtag.hashtag == tag_name,
        Tweet.date >= last_24h
    ).group_by(
        Tweet.sentiment
    ).all()
    
    sentiment_dict = {'positive': 0, 'negative': 0, 'neutral': 0}
    for s, count in sentiment_data:
        if s in sentiment_dict:
            sentiment_dict[s] = count
    
    total = sum(sentiment_dict.values()) or 1
    positive_pct = (sentiment_dict['positive'] / total) * 100
    
    context = {
        "total_posts": tag_count,
        "positive_pct": f"{positive_pct:.0f}",
        "neutral_pct": f"{(sentiment_dict['neutral']/total*100):.0f}",
        "negative_pct": f"{(sentiment_dict['negative']/total*100):.0f}",
        "top_hashtags": [tag_name]
    }
    
    # Get insights from all 4 models
    insight = await orchestrator.get_best_insight(
        prompt=f"#{tag_name} is trending with {tag_count} mentions in 24h. Sentiment is {positive_pct:.0f}% positive. Why is this trending?",
        context=context
    )
    
    return {
        "insight_type": "trending",
        "hashtag": tag_name,
        "mentions": tag_count,
        "sentiment": {
            "positive": sentiment_dict['positive'],
            "positive_pct": f"{positive_pct:.0f}%"
        },
        "llm_insight": insight
    }
