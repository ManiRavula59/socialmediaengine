"""
Question Classifier - Detects if a question is about content or dataset analytics
"""
import re
from typing import Dict, Tuple

class QuestionClassifier:
    def __init__(self):
        # Keywords that indicate analytics/dataset questions
        self.analytics_patterns = {
            'hashtag': [
                r'hashtag', r'#\w+', r'tag', r'mention'
            ],
            'trending': [
                r'trend', r'trending', r'viral', r'popular', r'top', r'hot'
            ],
            'count': [
                r'how many', r'count', r'total', r'number of', r'frequency'
            ],
            'compare': [
                r'vs?\.?\s', r'versus', r'compared? to', r'more than', r'less than'
            ],
            'time': [
                r'today', r'this week', r'this month', r'last \d+', r'past \d+',
                r'24 hours', r'7 days', r'30 days'
            ],
            'rank': [
                r'top \d+', r'highest', r'most', r'best', r'worst', r'leaderboard'
            ],
            'list': [
                r'list', r'show me', r'give me', r'what are the'
            ]
        }
        
        # Keywords that indicate content/sentiment questions
        self.content_patterns = [
            r'think', r'feel', r'say', r'opinion', r'sentiment',
            r'like|dislike', r'good|bad', r'happy|sad', r'love|hate'
        ]
    
    def classify(self, question: str) -> Dict[str, any]:
        """
        Classify question type and return structured info
        """
        question_lower = question.lower()
        
        # Check for analytics patterns
        analytics_score = 0
        detected_categories = []
        
        for category, patterns in self.analytics_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    analytics_score += 1
                    detected_categories.append(category)
                    break
        
        # Check for content patterns
        content_score = 0
        for pattern in self.content_patterns:
            if re.search(pattern, question_lower):
                content_score += 1
        
        # Extract number if present (e.g., "top 10" -> 10)
        number_match = re.search(r'top (\d+)', question_lower)
        limit = int(number_match.group(1)) if number_match else 10
        
        # Determine question type
        is_analytics = analytics_score > content_score or any(c in detected_categories for c in ['hashtag', 'trending', 'rank', 'list'])
        
        return {
            'is_analytics': is_analytics,
            'is_content': not is_analytics,
            'categories': list(set(detected_categories)),
            'limit': limit,
            'has_time_filter': 'time' in detected_categories,
            'has_comparison': 'compare' in detected_categories,
            'confidence': max(analytics_score, content_score) / (analytics_score + content_score + 0.1)
        }

# Global instance
classifier = QuestionClassifier()
