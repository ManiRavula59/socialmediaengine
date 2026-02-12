import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from .database import SessionLocal
from .models import Tweet
import pandas as pd
from tqdm import tqdm

class TweetVectorStore:
    def __init__(self):
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db_500k")
        
        # Use sentence-transformers for embeddings (lightweight)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="tweets_500k",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name='all-MiniLM-L6-v2'
            )
        )
    
    def index_tweets(self, limit=500000):
        """Index exactly 500K tweets into vector database"""
        db = SessionLocal()
        try:
            # Get only 500K tweets
            tweets = db.query(Tweet).limit(limit).all()
            print(f"📚 Indexing {len(tweets)} tweets (500K requirement)...")
            
            # Process in batches of 1000
            batch_size = 1000
            for i in tqdm(range(0, len(tweets), batch_size)):
                batch = tweets[i:i+batch_size]
                
                ids = [str(t.id) for t in batch]
                documents = [t.text for t in batch]
                metadatas = [{
                    "sentiment": t.sentiment,
                    "date": t.date.isoformat() if t.date else "",
                    "user": t.user
                } for t in batch]
                
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                
            print(f"✅ Successfully indexed {len(tweets)} tweets!")
            return len(tweets)
            
        finally:
            db.close()
    
    def search(self, query: str, n_results: int = 100):
        """Search for relevant tweets (semantic understanding)"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return {
            'tweets': results['documents'][0],
            'metadatas': results['metadatas'][0],
            'distances': results['distances'][0]
        }
    
    def analyze_topic(self, query: str):
        """Understand and analyze ANY topic from the tweets"""
        
        # Get relevant tweets
        results = self.search(query, n_results=100)
        
        if not results['tweets']:
            return {
                "found": False,
                "message": f"No tweets found about '{query}'"
            }
        
        # Analyze sentiment
        sentiments = [m['sentiment'] for m in results['metadatas']]
        pos = sentiments.count('positive')
        neg = sentiments.count('negative')
        neu = sentiments.count('neutral')
        total = len(sentiments)
        
        # Get unique users
        users = list(set([m['user'] for m in results['metadatas'] if m['user']]))
        
        return {
            "found": True,
            "total_relevant": total,
            "sentiment": {
                "positive": pos,
                "positive_pct": round((pos/total)*100, 1),
                "negative": neg,
                "negative_pct": round((neg/total)*100, 1),
                "neutral": neu,
                "neutral_pct": round((neu/total)*100, 1)
            },
            "unique_users": len(users),
            "sample_tweets": results['tweets'][:10],
            "all_tweets_for_context": results['tweets'][:50]
        }

# Global instance
vector_store = TweetVectorStore()
