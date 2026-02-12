from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from .database import Base
from datetime import datetime

class Tweet(Base):
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, unique=True, index=True)
    text = Column(Text)
    sentiment = Column(String)  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1 to 1
    user = Column(String)
    date = Column(DateTime)
    hour_of_day = Column(Integer)
    day_of_week = Column(Integer)

class Hashtag(Base):
    __tablename__ = "hashtags"
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, index=True)
    hashtag = Column(String, index=True)
    date = Column(DateTime)