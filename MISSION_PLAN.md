# Real-Time Sentiment Analysis for Trading Decisions

## Objective
A sentiment analysis tool that processes news, social media, and other textual data to provide actionable insights for trading decisions in real-time.

## Strategy
Use transformer-based models like BERT for sentiment analysis, integrate with real-time news

## Execution Output
SUMMARY: I have architected a comprehensive Real-Time Sentiment Analysis System for Trading Decisions. The system features a modular pipeline for data collection, preprocessing, sentiment analysis, and actionable insights generation. The architecture includes robust error handling, Firebase Firestore integration for state management, and proper logging throughout.

OUTPUT:

### FILE: requirements.txt
```
# Core dependencies
firebase-admin>=6.4.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
nltk>=3.8.0
textblob>=0.17.1
requests>=2.31.0
tweepy>=4.14.0
python-dotenv>=1.0.0

# Optional for advanced models
transformers>=4.30.0
torch>=2.0.0

# For news APIs (when needed)
newspaper3k>=0.2.8
feedparser>=6.0.10

# Async processing
aiohttp>=3.8.0
asyncio>=3.4.3

# Monitoring
schedule>=1.2.0
```

### FILE: config.py
```python
"""
Configuration manager for the Sentiment Analysis System.
Centralizes all configuration parameters with environment variable fallbacks.
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "sentiment-trading-dev")
    credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    collection_name: str = os.getenv("FIREBASE_COLLECTION", "sentiment_analysis")
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not self.project_id:
            raise ValueError("Firebase Project ID must be set")
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Firebase credentials not found at {self.credentials_path}")
        return True

@dataclass
class APIConfig:
    """API configuration for data sources"""
    newsapi_key: Optional[str] = os.getenv("NEWSAPI_KEY")
    twitter_bearer_token: Optional[str] = os.getenv("TWITTER_BEARER_TOKEN")
    twitter_consumer_key: Optional[str] = os.getenv("TWITTER_CONSUMER_KEY")
    twitter_consumer_secret: Optional[str] = os.getenv("TWITTER_CONSUMER_SECRET")
    
    @property
    def twitter_enabled(self) -> bool:
        """Check if Twitter API is properly configured"""
        return all([self.twitter_bearer_token, self.twitter_consumer_key, self.twitter_consumer_secret])

@dataclass
class AnalysisConfig:
    """Analysis algorithm configuration"""
    sentiment_threshold_positive: float = 0.2
    sentiment_threshold_negative: float = -0.2
    confidence_threshold: float = 0.7
    batch_size: int = 100
    max_text_length: int = 1000
    
class Config:
    """Main configuration singleton"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.firebase = FirebaseConfig()
            cls._instance.api = APIConfig()
            cls._instance.analysis = AnalysisConfig()
            cls._instance.validate()
        return cls._instance
    
    def validate(self):
        """Validate all configurations"""
        self.firebase.validate()
        if not self.api.twitter_enabled:
            print("WARNING: Twitter API not fully configured - Twitter collection disabled")
            
    def to_dict(self) -> dict:
        """Return configuration as dictionary (excluding sensitive data)"""
        return {
            "firebase": {
                "project_id": self.firebase.project_id,
                "collection_name": self.firebase.collection_name
            },
            "analysis": {
                "sentiment_threshold_positive": self.analysis.sentiment_threshold_positive,
                "sentiment_threshold_negative": self.analysis.sentiment_threshold_negative,
                "batch_size": self.analysis.batch_size
            }
        }

# Global configuration instance
config = Config()
```

### FILE: firebase_client.py
```python
"""
Firebase Firestore client for real-time data storage and retrieval.
Implements robust error handling and connection management.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseClient:
    """Firebase Firestore client with connection pooling and error recovery"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                # Initialize Firebase app if not already initialized
                if not firebase_admin._apps:
                    cred = credentials.Certificate(config.firebase.credentials_path)
                    firebase_admin.initialize_app(cred, {
                        'projectId': config.firebase.project_id
                    })
                    logger.info(f"Firebase initialized for project: {config.firebase.project_id}")
                
                self.db = firestore.client