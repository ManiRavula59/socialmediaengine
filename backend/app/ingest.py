import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from .database import SessionLocal
from .models import Tweet, Hashtag
from .sentiment import sentiment_analyzer
import os

def ingest_tweets(csv_path: str, sample_size: int = None):
    """Load Sentiment140 dataset into database"""
    
    print(f"📥 Loading dataset from: {csv_path}")
    
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return
    
    db = SessionLocal()
    
    try:
        # Read CSV in chunks (no headers in Sentiment140)
        chunk_size = 10000
        total_processed = 0
        
        for chunk in pd.read_csv(
            csv_path,
            encoding='latin-1',
            header=None,
            names=['target', 'ids', 'date', 'flag', 'user', 'text'],
            chunksize=chunk_size,
            nrows=sample_size
        ):
            tweets_batch = []
            hashtags_batch = []
            
            for _, row in chunk.iterrows():
                # Skip if no text
                if pd.isna(row['text']) or not str(row['text']).strip():
                    continue
                
                # Analyze sentiment
                sentiment, score = sentiment_analyzer.analyze(row['text'])
                
                # Parse date
                try:
                    date = datetime.strptime(row['date'], '%a %b %d %H:%M:%S %Z %Y')
                except:
                    date = datetime.now()
                
                # Create tweet record
                tweets_batch.append(Tweet(
                    tweet_id=str(row['ids']),
                    text=str(row['text'])[:500],
                    sentiment=sentiment,
                    sentiment_score=score,
                    user=str(row['user']),
                    date=date,
                    hour_of_day=date.hour,
                    day_of_week=date.weekday()
                ))
                
                # Extract hashtags
                hashtags = sentiment_analyzer.extract_hashtags(str(row['text']))
                for tag in hashtags[:5]:  # Limit per tweet
                    hashtags_batch.append(Hashtag(
                        tweet_id=str(row['ids']),
                        hashtag=tag.lower(),
                        date=date
                    ))
            
            # Bulk insert
            db.bulk_save_objects(tweets_batch)
            db.bulk_save_objects(hashtags_batch)
            db.commit()
            
            total_processed += len(tweets_batch)
            print(f"✅ Processed {total_processed} tweets...")
        
        print(f"\n🎉 Successfully ingested {total_processed} tweets!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Change this path to where your dataset is
    DATASET_PATH = "data/training.1600000.processed.noemoticon.csv"
    
    # For testing with 5000 tweets (remove sample_size for full dataset)
    ingest_tweets(DATASET_PATH, sample_size=5000)
