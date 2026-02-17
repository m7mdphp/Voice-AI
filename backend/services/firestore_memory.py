"""
Tiryaq Voice AI - Memory Manager
Najm AI Standard: Robust Firebase/Firestore with In-Memory Fallback
Handles gRPC/libstdc++ failures gracefully in restricted environments.
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add parent directory to path for config import
PARENT_DIR = Path(__file__).parent.parent.resolve()
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))


class MemoryManager:
    """
    Production-grade Memory Manager with automatic fallback.
    
    Priority:
    1. Firebase Firestore (if credentials available)
    2. In-Memory Dictionary (always available as fallback)
    """
    
    # Class-level in-memory storage for fallback across instances
    _memory_cache: Dict[str, Dict] = {}
    
    def __init__(self):
        self.db: Optional[Any] = None
        self._firebase_available = False
        self._init_firestore()
    
    def _init_firestore(self):
        """Initialize Firebase with comprehensive error handling."""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Check if already initialized
            if firebase_admin._apps:
                self.db = firestore.client()
                self._firebase_available = True
                logger.info("Using existing Firebase app instance")
                return
            
            # Search for credentials file
            cred_path = self._find_credentials()
            
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self._firebase_available = True
                logger.success(f"Firebase initialized from: {cred_path}")
            else:
                logger.warning("No Firebase credentials found - using in-memory fallback")
                
        except ImportError as e:
            logger.warning(f"Firebase packages not installed: {e}")
            logger.info("Using in-memory storage fallback")
            
        except Exception as e:
            # Catch gRPC/libstdc++ errors and other system-level issues
            error_msg = str(e).lower()
            if any(x in error_msg for x in ['grpc', 'libstdc++', 'libgcc', 'protoc', 'dll', 'shared object']):
                logger.warning(f"Firebase system dependency error: {e}")
                logger.info("Switching to in-memory fallback for deployment compatibility")
            else:
                logger.warning(f"Firebase initialization failed: {e}")
            
            self.db = None
            self._firebase_available = False
    
    def _find_credentials(self) -> Optional[str]:
        """Search for Firebase credentials in common locations."""
        search_paths = [
            # Deployment paths
            "/app/serviceAccountKey.json",
            "/app/backend/serviceAccountKey.json",
            # Local development paths
            str(PARENT_DIR / "serviceAccountKey.json"),
            str(PARENT_DIR.parent / "serviceAccountKey.json"),
            # Environment variable path
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        ]
        
        for path in search_paths:
            if path and Path(path).exists():
                return path
        
        return None
    
    def _get_cache_key(self, tenant_id: str, user_id: str) -> str:
        """Generate consistent cache key."""
        return f"{tenant_id}_{user_id}"
    
    async def get_user_context(self, tenant_id: str, user_id: str) -> Dict:
        """
        Retrieve user context with automatic fallback.
        Always returns a valid dict - never raises.
        """
        cache_key = self._get_cache_key(tenant_id, user_id)
        
        # Return from in-memory cache if Firebase unavailable
        if not self._firebase_available or not self.db:
            return self._memory_cache.get(cache_key, self._create_default_context())
        
        try:
            user_ref = self.db.collection("tenants").document(tenant_id).collection("users").document(user_id)
            doc = user_ref.get()
            
            if doc.exists:
                data = doc.to_dict() or {}
                # Cache for fallback
                self._memory_cache[cache_key] = data
                return data
            else:
                return self._create_default_context()
                
        except Exception as e:
            logger.error(f"Firestore read error: {e}")
            # Return cached data or default
            return self._memory_cache.get(cache_key, self._create_default_context())
    
    def _create_default_context(self) -> Dict:
        """Create default user context."""
        return {
            "first_name": "ضيف",
            "long_term_memory": "",
            "history": [],
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def save_summary(self, tenant_id: str, user_id: str, summary: str):
        """Save conversation summary to persistent storage."""
        cache_key = self._get_cache_key(tenant_id, user_id)
        
        # Always update in-memory cache
        if cache_key in self._memory_cache:
            self._memory_cache[cache_key]["long_term_memory"] = summary
        else:
            self._memory_cache[cache_key] = self._create_default_context()
            self._memory_cache[cache_key]["long_term_memory"] = summary
        
        # Skip Firestore if unavailable
        if not self._firebase_available or not self.db:
            return
        
        try:
            user_ref = self.db.collection("tenants").document(tenant_id).collection("users").document(user_id)
            user_ref.set({
                "long_term_memory": summary,
                "last_interaction": datetime.utcnow()
            }, merge=True)
        except Exception as e:
            logger.error(f"Firestore save error: {e}")
    
    async def log_session(self, session_id: str, data: dict):
        """Log session data for analytics."""
        if not self._firebase_available or not self.db:
            logger.debug(f"Session log (memory-only): {session_id}")
            return
            
        try:
            self.db.collection("sessions").document(session_id).set(data)
        except Exception as e:
            logger.error(f"Firestore session log error: {e}")
    
    def get_status(self) -> Dict:
        """Return current status for health checks."""
        return {
            "firebase_available": self._firebase_available,
            "storage_type": "firestore" if self._firebase_available else "in_memory",
            "cached_users": len(self._memory_cache)
        }
