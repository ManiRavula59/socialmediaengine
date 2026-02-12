from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
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

@router.get("/api/search")
async def search_posts(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Full-text search with multi-model LLM summary"""
    
    # Search tweets containing the query
    results = db.query(Tweet).filter(
        Tweet.text.ilike(f'%{q}%')
    ).limit(50).all()
    
    if not results:
        return {
            "query": q,
            "total_results": 0,
            "sentiment_breakdown": {"positive": 0, "negative": 0, "neutral": 0},
            "top_hashtags": [],
            "posts": []
        }
    
    # Calculate sentiment of results
    sentiments = [r.sentiment for r in results if r.sentiment]
    pos = sentiments.count('positive')
    neg = sentiments.count('negative')
    neu = sentiments.count('neutral')
    total = len(sentiments) or 1
    
    # Get hashtags in results
    result_ids = [r.tweet_id for r in results]
    hashtags = db.query(Hashtag.hashtag).filter(
        Hashtag.tweet_id.in_(result_ids)
    ).distinct().limit(10).all()
    
    context = {
        "total_posts": len(results),
        "positive_pct": f"{(pos/total*100):.0f}",
        "negative_pct": f"{(neg/total*100):.0f}",
        "neutral_pct": f"{(neu/total*100):.0f}",
        "top_hashtags": [h[0] for h in hashtags[:5]]
    }
    
    # Get summary from best model
    summary = await orchestrator.get_best_insight(
        prompt=f"What are people saying about '{q}'? Summarize the sentiment and key topics in 2-3 sentences.",
        context=context
    )
    
    return {
        "query": q,
        "total_results": len(results),
        "sentiment_breakdown": {
            "positive": pos,
            "negative": neg,
            "neutral": neu
        },
        "top_hashtags": [h[0] for h in hashtags[:10]],
        "llm_summary": summary,
        "posts": [
            {
                "text": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                "sentiment": r.sentiment,
                "date": r.date.isoformat() if r.date else None,
                "user": r.user
            }
            for r in results[:20]
        ]
    }
