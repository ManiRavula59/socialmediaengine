import aiohttp
import asyncio
import json

API_KEY = "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"
URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "Social Media Insight Engine"
}

MODELS = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "arcee-ai/trinity-mini:free"
]

async def test_model(model):
    print(f"\n🔸 Testing {model}...")
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Say hello in one sentence"}
        ],
        "max_tokens": 50
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(URL, headers=HEADERS, json=data, timeout=30) as resp:
                result = await resp.json()
                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                    print(f"   ✅ Response: {content[:100]}...")
                    return True
                else:
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                    return False
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False

async def main():
    print("🚀 TESTING ALL MODELS WITH SIMPLE PROMPT...")
    print("=" * 60)
    
    for model in MODELS:
        await test_model(model)

asyncio.run(main())
