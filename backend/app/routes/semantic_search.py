from fastapi import APIRouter, Query
from app.vector_store import vector_store
from app.llm_orchestrator import orchestrator
from app.question_classifier import classifier
from app.analytics_engine import analytics
import asyncio

router = APIRouter()

@router.get("/api/ask")
async def ask_question(q: str = Query(..., min_length=1)):
    """
    🤖 Ask ANY question about the 500K tweets!
    Automatically detects if you're asking about content OR dataset analytics.
    """
    
    # 1. CLASSIFY THE QUESTION TYPE
    question_type = classifier.classify(q)
    
    # 2. HANDLE ANALYTICS QUESTIONS (hashtags, trends, counts)
    if question_type['is_analytics']:
        return await handle_analytics_question(q, question_type)
    
    # 3. HANDLE CONTENT QUESTIONS (sentiment, opinions) - YOUR EXISTING RAG
    else:
        return await handle_content_question(q)

async def handle_analytics_question(q: str, question_type: dict):
    """
    Handle questions about hashtags, trends, and dataset statistics
    """
    limit = question_type['limit']
    categories = question_type['categories']
    
    # CASE 1: Top hashtags request
    if 'hashtag' in categories or 'trending' in categories or 'rank' in categories:
        time_filter = 'today' if 'time' in categories else None
        top_hashtags = analytics.get_top_hashtags(limit=limit, time_filter=time_filter)
        
        # Create a prompt for ONE model to summarize
        hashtag_list = "\n".join([f"{i+1}. {h['hashtag']} - {h['count']} mentions, {h['sentiment']['positive_pct']}% positive" 
                                 for i, h in enumerate(top_hashtags[:limit])])
        
        prompt = f"""Based on 500,000 tweets, here are the top {limit} trending hashtags:

{hashtag_list}

Please provide a brief summary of what these hashtags tell us about what people are discussing right now."""
        
        insight = await orchestrator.get_best_insight(prompt, {})
        
        return {
            "question": q,
            "answer": insight['selected_insight'],
            "type": "analytics",
            "subtype": "top_hashtags",
            "data": top_hashtags[:limit],
            "model_used": insight['selected_model'],
            "confidence": insight['confidence'],
            "llm_summary": insight
        }
    
    # CASE 2: Dataset statistics
    elif 'count' in categories and 'hashtag' not in categories:
        stats = analytics.get_dataset_stats()
        
        prompt = f"""Based on our Twitter dataset:
- Total tweets: {stats['total_tweets']:,}
- Total hashtags: {stats['total_hashtags']:,}
- Unique hashtags: {stats['unique_hashtags']:,}
- Unique users: {stats['unique_users']:,}

Summarize these statistics in a simple, engaging way."""
        
        insight = await orchestrator.get_best_insight(prompt, {})
        
        return {
            "question": q,
            "answer": insight['selected_insight'],
            "type": "analytics",
            "subtype": "dataset_stats",
            "data": stats,
            "model_used": insight['selected_model'],
            "confidence": insight['confidence']
        }
    
    # CASE 3: Comparison between hashtags
    elif 'compare' in categories:
        # Extract hashtags from question
        import re
        hashtags = re.findall(r'#?(\w+)', q)[:2]
        if len(hashtags) >= 2:
            comparison = analytics.get_trending_comparison(hashtags[0], hashtags[1])
            
            prompt = f"""Compare #{hashtags[0]} and #{hashtags[1]}:
            
#{hashtags[0]}: {comparison['hashtag1']['count'] if comparison['hashtag1'] else 0} mentions, {comparison['hashtag1']['sentiment']['positive_pct'] if comparison['hashtag1'] else 0}% positive
#{hashtags[1]}: {comparison['hashtag2']['count'] if comparison['hashtag2'] else 0} mentions, {comparison['hashtag2']['sentiment']['positive_pct'] if comparison['hashtag2'] else 0}% positive

Winner: {comparison['comparison']['winner']}

Summarize this comparison."""
            
            insight = await orchestrator.get_best_insight(prompt, {})
            
            return {
                "question": q,
                "answer": insight['selected_insight'],
                "type": "analytics",
                "subtype": "comparison",
                "data": comparison,
                "model_used": insight['selected_model'],
                "confidence": insight['confidence']
            }
    
    # Default analytics response
    return {
        "question": q,
        "answer": "I found analytics data for your question. Try asking 'top hashtags' or 'dataset statistics' for specific insights.",
        "type": "analytics",
        "subtype": "general"
    }

async def handle_content_question(q: str):
    """
    Handle content/sentiment questions - YOUR EXISTING WORKING RAG SYSTEM
    """
    # Get relevant tweets
    topic_data = vector_store.analyze_topic(q)
    
    if not topic_data['found']:
        return {
            "question": q,
            "answer": f"I couldn't find any tweets about '{q}'. Try asking about: iPhone, Google, movies, music, etc.",
            "type": "content",
            "total_tweets_found": 0
        }
    
    # Create prompt
    prompt = f"""
    Based on {topic_data['total_relevant']} tweets about '{q}':
    - Sentiment: {topic_data['sentiment']['positive_pct']}% positive, {topic_data['sentiment']['negative_pct']}% negative
    - {topic_data['unique_users']} unique users discussing this
    
    Sample tweets:
    {chr(10).join(['- ' + t for t in topic_data['sample_tweets'][:5]])}
    
    Summarize what people are saying about {q} in 2-3 sentences.
    """
    
    # Get insight from 4 models
    insight = await orchestrator.get_best_insight(prompt, {
        "total_posts": topic_data['total_relevant'],
        "positive_pct": str(topic_data['sentiment']['positive_pct']),
        "negative_pct": str(topic_data['sentiment']['negative_pct'])
    })
    
    return {
        "question": q,
        "answer": insight['selected_insight'],
        "type": "content",
        "model_used": insight['selected_model'],
        "confidence": insight['confidence'],
        "latency": insight['latency'],
        "statistics": {
            "total_relevant_tweets": topic_data['total_relevant'],
            "sentiment": topic_data['sentiment'],
            "unique_users": topic_data['unique_users']
        },
        "sample_tweets": topic_data['sample_tweets'][:5],
        "llm_summary": insight
    }

@router.get("/api/explore")
async def explore_topic(topic: str = Query(..., min_length=1)):
    """Deep dive into ANY topic from the 500K tweets"""
    results = vector_store.search(topic, n_results=50)
    
    if not results['tweets']:
        return {
            "topic": topic,
            "message": f"No tweets found about '{topic}'",
            "total": 0
        }
    
    return {
        "topic": topic,
        "total_related_tweets": len(results['tweets']),
        "tweets": [
            {
                "text": results['tweets'][i],
                "sentiment": results['metadatas'][i]['sentiment'],
                "relevance": round(1 - results['distances'][i], 3)
            }
            for i in range(min(20, len(results['tweets'])))
        ]
    }