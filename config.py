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