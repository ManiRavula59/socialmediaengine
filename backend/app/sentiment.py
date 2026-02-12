import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
from typing import Tuple

# Download NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> Tuple[str, float]:
        """Fast sentiment analysis for 500K+ tweets"""
        # Clean text
        text = text.lower()
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'[^\w\s#]', '', text)
        
        # Get sentiment scores
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']
        
        # Classify
        if compound >= 0.05:
            return 'positive', compound
        elif compound <= -0.05:
            return 'negative', compound
        else:
            return 'neutral', compound
    
    def extract_hashtags(self, text: str) -> list:
        """Extract hashtags from tweet text"""
        return re.findall(r'#(\w+)', text.lower())

# Global instance
sentiment_analyzer = SentimentAnalyzer()