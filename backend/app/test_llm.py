import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.llm_orchestrator import orchestrator

async def test_models():
    print("\n" + "="*70)
    print("🚀 TESTING 4 VERIFIED WORKING MODELS")
    print("="*70)
    
    context = {
        "total_posts": 500000,
        "positive_pct": "65",
        "neutral_pct": "20",
        "negative_pct": "15",
        "top_hashtags": ["#AI", "#Tech", "#Innovation", "#Future"],
        "time_range": "24"
    }
    
    print("\n📊 Context:", context)
    print("\n⏳ Querying all models in parallel...\n")
    
    result = await orchestrator.get_best_insight(
        prompt="What are the key trends and sentiment about AI technology?",
        context=context
    )
    
    if result["success"]:
        print(f"\n✅ BEST MODEL: {result['selected_model']}")
        print(f"🎯 CONFIDENCE: {result['confidence']}%")
        print(f"⚡ LATENCY: {result['latency']}s")
        print(f"\n💡 INSIGHT:\n{result['selected_insight']}")
        
        print("\n" + "="*70)
        print("📊 ALL MODEL RESPONSES:")
        print("="*70)
        
        for r in result['all_responses']:
            print(f"\n🔸 {r['model']}")
            print(f"   Confidence: {r['confidence']}%")
            print(f"   Latency: {r['latency']}s")
            if r['success']:
                print(f"   Response: {r['content']}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_models())