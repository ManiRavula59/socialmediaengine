"""
Analytics Engine - Handles hashtag trends, counts, and dataset statistics
"""
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from .database import SessionLocal
from .models import Tweet, Hashtag

class AnalyticsEngine:
    def __init__(self):
        self.db = SessionLocal()
    
    def get_top_hashtags(self, limit: int = 10, time_filter: str = None):
        """
        Get top hashtags with counts and sentiment
        """
        query = self.db.query(
            Hashtag.hashtag,
            func.count(Hashtag.id).label('count'),
            func.count(func.distinct(Hashtag.tweet_id)).label('unique_tweets')
        ).group_by(Hashtag.hashtag)
        
        # Apply time filter if specified
        if time_filter == 'today':
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Hashtag.date >= today)
        elif time_filter == 'week':
            week_ago = datetime.now() - timedelta(days=7)
            query = query.filter(Hashtag.date >= week_ago)
        elif time_filter == 'month':
            month_ago = datetime.now() - timedelta(days=30)
            query = query.filter(Hashtag.date >= month_ago)
        
        # Get top hashtags
        top_tags = query.order_by(desc('count')).limit(limit).all()
        
        result = []
        for tag, count, unique_tweets in top_tags:
            # Get sentiment for this hashtag
            sentiment_data = self.db.query(
                Tweet.sentiment,
                func.count(Tweet.id)
            ).join(
                Hashtag, Tweet.tweet_id == Hashtag.tweet_id
            ).filter(
                Hashtag.hashtag == tag
            ).group_by(
                Tweet.sentiment
            ).all()
            
            sentiment_dict = {'positive': 0, 'negative': 0, 'neutral': 0}
            for s, c in sentiment_data:
                if s in sentiment_dict:
                    sentiment_dict[s] = c
            
            total = sum(sentiment_dict.values()) or 1
            result.append({
                'hashtag': f"#{tag}",
                'count': count,
                'unique_tweets': unique_tweets,
                'sentiment': {
                    'positive': sentiment_dict['positive'],
                    'positive_pct': round((sentiment_dict['positive']/total)*100, 1),
                    'negative': sentiment_dict['negative'],
                    'negative_pct': round((sentiment_dict['negative']/total)*100, 1),
                    'neutral': sentiment_dict['neutral'],
                    'neutral_pct': round((sentiment_dict['neutral']/total)*100, 1)
                }
            })
        
        return result
    
    def get_trending_comparison(self, hashtag1: str, hashtag2: str):
        """
        Compare two hashtags
        """
        h1_data = self.get_top_hashtags(limit=50)
        h1 = next((h for h in h1_data if h['hashtag'] == f"#{hashtag1}"), None)
        h2 = next((h for h in h1_data if h['hashtag'] == f"#{hashtag2}"), None)
        
        return {
            'hashtag1': h1,
            'hashtag2': h2,
            'comparison': {
                'difference': abs((h1['count'] if h1 else 0) - (h2['count'] if h2 else 0)),
                'winner': hashtag1 if (h1['count'] if h1 else 0) > (h2['count'] if h2 else 0) else hashtag2
            }
        }
    
    def get_dataset_stats(self):
        """
        Get overall dataset statistics
        """
        total_tweets = self.db.query(func.count(Tweet.id)).scalar() or 0
        total_hashtags = self.db.query(func.count(Hashtag.id)).scalar() or 0
        unique_hashtags = self.db.query(func.count(func.distinct(Hashtag.hashtag))).scalar() or 0
        unique_users = self.db.query(func.count(func.distinct(Tweet.user))).scalar() or 0
        
        # Date range
        oldest = self.db.query(func.min(Tweet.date)).scalar()
        newest = self.db.query(func.max(Tweet.date)).scalar()
        
        return {
            'total_tweets': total_tweets,
            'total_hashtags': total_hashtags,
            'unique_hashtags': unique_hashtags,
            'unique_users': unique_users,
            'date_range': {
                'oldest': oldest.isoformat() if oldest else None,
                'newest': newest.isoformat() if newest else None
            }
        }

# Global instance
analytics = AnalyticsEngine()
