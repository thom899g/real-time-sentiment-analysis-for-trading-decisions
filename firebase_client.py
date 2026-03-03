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