import os
from typing import Dict, Any
from loguru import logger

class MemoryManager:
    _local_storage = {}
    
    def __init__(self):
        self.db = None
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            from datetime import datetime
            
            # Check if app is already initialized to avoid "app already exists" error
            if not firebase_admin._apps:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # Go up one level to find serviceAccountKey.json in backend root or /app
                # Adjust path logic to look in likely places: current dir, parent dir, or /app
                potential_paths = [
                    os.path.join(current_dir, "serviceAccountKey.json"),
                    os.path.join(os.path.dirname(current_dir), "serviceAccountKey.json"),
                    "/app/serviceAccountKey.json"
                ]
                
                cred_path = None
                for p in potential_paths:
                    if os.path.exists(p):
                        cred_path = p
                        break
                
                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    logger.info(f"Firestore initialized successfully using {cred_path}")
                else:
                    logger.warning("serviceAccountKey.json not found in common locations. Using local memory.")
            else:
                self.db = firestore.client()
                logger.info("Using existing Firestore instance")
        except ImportError:
            logger.warning("Firestore/gRPC libraries not installed. Falling back to local memory.")
            self.db = None
        except Exception as e:
            logger.warning(f"Firestore initialization failed. Falling back to local memory. Error: {e}")
            self.db = None

    async def get_user_context(self, tenant_id: str, user_id: str) -> dict:
        storage_key = f"{tenant_id}_{user_id}"
        
        if not self.db:
            if storage_key not in self._local_storage:
                self._local_storage[storage_key] = {
                    "first_name": "ضيف",
                    "long_term_memory": "",
                    "history": []
                }
            return self._local_storage[storage_key]

        try:
            user_ref = self.db.collection("tenants").document(tenant_id).collection("users").document(user_id)
            doc = user_ref.get()
    
            if doc.exists:
                return doc.to_dict()
            else:
                return {}
        except Exception as e:
            logger.error(f"Firestore read error: {e}. Returning empty context.")
            return {}

    async def save_summary(self, tenant_id: str, user_id: str, summary: str):
        if not self.db:
            # Update local storage if needed, though usually used for ephemeral sessions
            storage_key = f"{tenant_id}_{user_id}"
            if storage_key in self._local_storage:
                self._local_storage[storage_key]["long_term_memory"] = summary
            return

        try:
            from datetime import datetime
            user_ref = self.db.collection("tenants").document(tenant_id).collection("users").document(user_id)
            
            user_ref.set({
                "long_term_memory": summary,
                "last_interaction": datetime.utcnow()
            }, merge=True)
        except Exception as e:
            logger.error(f"Firestore save error: {e}")

    async def log_session(self, session_id: str, data: dict):
        if not self.db:
            return
            
        try:
            self.db.collection("sessions").document(session_id).set(data)
        except Exception as e:
            logger.error(f"Firestore session log error: {e}")
