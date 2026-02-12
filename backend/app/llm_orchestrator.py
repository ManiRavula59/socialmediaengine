import asyncio
import aiohttp
from typing import List, Dict, Any
import time

class MultiModelOrchestrator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Social Media Insight Engine"
        }
        
        # ✅ YOUR VERIFIED WORKING MODELS - 100% TESTED
        self.planner_models = [
            "nvidia/nemotron-3-nano-30b-a3b:free",  # Planning & reasoning
            "stepfun/step-3.5-flash:free"           # Fast reasoning
        ]
        
        self.chat_models = [
            "arcee-ai/trinity-large-preview:free",  # Creative insights
            "arcee-ai/trinity-mini:free"            # Efficient & fast
        ]
        
        self.fallback_model = "openrouter/free"      # Auto-router
        
        # Combine all models for parallel querying
        self.all_models = self.planner_models + self.chat_models
        
        # Track model performance
        self.model_scores = {model: 1.0 for model in self.all_models}
        self.latency_history = {model: [] for model in self.all_models}
    
    async def query_model(self, session: aiohttp.ClientSession, model: str, 
                         prompt: str, context: Dict[str, Any]) -> Dict:
        """Query single model asynchronously"""
        
        system_prompt = """You are a social media analytics expert. 
        Analyze the Twitter data and provide accurate, data-driven insights.
        Be concise and specific. Use exact numbers when available."""
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
Context:
- Total posts analyzed: {context.get('total_posts', 'N/A')}
- Sentiment: {context.get('positive_pct', '0')}% positive, 
             {context.get('negative_pct', '0')}% negative, 
             {context.get('neutral_pct', '0')}% neutral
- Top hashtags: {', '.join(context.get('top_hashtags', ['none']))[:100]}
- Time period: Last {context.get('time_range', '24')} hours

Question: {prompt}

Provide a brief, data-backed insight (2-3 sentences)."""}
            ],
            "temperature": 0.1,
            "max_tokens": 300
        }
        
        start_time = time.time()
        try:
            async with session.post(self.url, headers=self.headers, 
                                  json=data, timeout=30) as response:
                result = await response.json()
                latency = time.time() - start_time
                
                if "error" in result:
                    return {
                        "model": model,
                        "success": False,
                        "error": result["error"]["message"],
                        "latency": latency
                    }
                
                return {
                    "model": model,
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "latency": latency,
                    "tokens": result["usage"]["total_tokens"]
                }
        except Exception as e:
            return {
                "model": model,
                "success": False,
                "error": str(e),
                "latency": time.time() - start_time
            }
    
    async def query_all_models(self, prompt: str, context: Dict[str, Any]) -> List[Dict]:
        """Query ALL 4 models in PARALLEL ⚡"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.query_model(session, model, prompt, context)
                for model in self.all_models
            ]
            responses = await asyncio.gather(*tasks)
            
            # Update latency history
            for response in responses:
                if response["success"]:
                    model = response["model"]
                    self.latency_history[model].append(response["latency"])
                    self.latency_history[model] = self.latency_history[model][-10:]
            
            return responses
    
    def calculate_confidence(self, response: Dict) -> float:
        """Score model response confidence 0-1"""
        if not response["success"]:
            return 0.0
        
        score = 0.7  # Base score
        
        # Length appropriateness (20%)
        content = response["content"]
        if 50 < len(content) < 400:
            score += 0.2
        elif len(content) < 30:
            score += 0.1
        else:
            score += 0.15
        
        # Speed bonus (10%)
        if response["latency"] < 3.0:
            score += 0.1
        elif response["latency"] < 5.0:
            score += 0.05
            
        return min(1.0, score)
    
    async def get_best_insight(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get insights from ALL models in parallel"""
        
        # Query all 4 models simultaneously
        responses = await self.query_all_models(prompt, context)
        
        # Score successful responses
        successful = []
        for response in responses:
            if response["success"]:
                response["confidence"] = self.calculate_confidence(response)
                successful.append(response)
        
        # If all models failed, try fallback
        if not successful:
            print("⚠️ All primary models failed, trying fallback...")
            async with aiohttp.ClientSession() as session:
                fallback_response = await self.query_model(
                    session, self.fallback_model, prompt, context
                )
                if fallback_response["success"]:
                    fallback_response["confidence"] = self.calculate_confidence(fallback_response)
                    successful = [fallback_response]
        
        # If still no success, return error
        if not successful:
            return {
                "success": False,
                "error": "All models failed to respond",
                "selected_insight": "Unable to generate insight at this time. Please try again.",
                "selected_model": "none",
                "confidence": 0,
                "latency": 0,
                "all_responses": [
                    {
                        "model": r["model"],
                        "error": r.get("error", "Failed"),
                        "success": False
                    }
                    for r in responses
                ]
            }
        
        # Select best response
        best_response = max(successful, key=lambda x: x["confidence"])
        
        return {
            "success": True,
            "selected_insight": best_response["content"],
            "selected_model": best_response["model"],
            "confidence": int(best_response["confidence"] * 100),
            "latency": round(best_response["latency"], 1),
            "all_responses": [
                {
                    "model": r["model"],
                    "content": r.get("content", "")[:150] + "..." if len(r.get("content", "")) > 150 else r.get("content", ""),
                    "confidence": int(r.get("confidence", 0) * 100),
                    "latency": round(r.get("latency", 0), 1),
                    "success": r["success"]
                }
                for r in successful[:4]  # Show all successful responses
            ]
        }

# Create global instance with YOUR key
orchestrator = MultiModelOrchestrator(
    api_key="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"
)