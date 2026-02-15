import firebase_admin
import os
from datetime import datetime
from loguru import logger

try:
    from firebase_admin import credentials, firestore
    HAS_FIRESTORE = True
except ImportError:
    logger.warning("Firestore/gRPC libraries not found or system libraries (libstdc++) missing. Falling back to local memory.")
    HAS_FIRESTORE = False

# تهيئة الاتصال بقاعدة البيانات (Placeholder for actual creds path)
# يجب التأكد من وجود ملف الاعتماد في البيئة الإنتاجية
# تهيئة الاتصال بقاعدة البيانات
if HAS_FIRESTORE and not firebase_admin._apps:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(current_dir, "serviceAccountKey.json")
    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            HAS_FIRESTORE = False
    else:
        logger.warning("serviceAccountKey.json not found. Firestore features will be mocked.")
        HAS_FIRESTORE = False

class MemoryManager:
    """
    مدير الذاكرة (Memory Manager) المحدث ليدعم التخزين المحلي في حال غياب Firestore.
    """
    _local_storage = {} # ذاكرة ثابتة على مستوى الكلاس لمنع فقدان البيانات عند إعادة الاتصال
    
    def __init__(self):
        self.db = firestore.client() if (HAS_FIRESTORE and firebase_admin._apps) else None

    async def get_user_context(self, tenant_id: str, user_id: str) -> dict:
        storage_key = f"{tenant_id}_{user_id}"
        
        if not self.db:
            # استخدام الذاكرة المحلية إذا لم يتوفر Firestore
            if storage_key not in self._local_storage:
                self._local_storage[storage_key] = {
                    "first_name": "ضيف",
                    "long_term_memory": "",
                    "history": []
                }
            return self._local_storage[storage_key]

        # مسار الوثيقة: tenants/{tenant_id}/users/{user_id}
        # هذا المسار يضمن العزل التام للبيانات بين المستأجرين
        user_ref = self.db.collection("tenants").document(tenant_id).collection("users").document(user_id)
        doc = user_ref.get()

        if doc.exists:
            return doc.to_dict()
        else:
            return {}

    async def save_summary(self, tenant_id: str, user_id: str, summary: str):
        """
        حفظ ملخص المحادثة (Save Summary)
        
        يتم استدعاء هذه الدالة بعد انتهاء الجلسة لتحديث الذاكرة طويلة المدى.
        """
        if not self.db:
            return

        user_ref = self.db.collection("tenants").document(tenant_id).collection("users").document(user_id)
        
        # تحديث حقل الذاكرة طويلة المدى وتاريخ آخر تفاعل
        user_ref.set({
            "long_term_memory": summary,
            "last_interaction": datetime.utcnow()
        }, merge=True)

    async def log_session(self, session_id: str, data: dict):
        """
        تسجيل تفاصيل الجلسة (Session Logging)
        يتم حفظ سجلات المحادثة للأغراض التحليلية والتحسين.
        """
        if not self.db:
            return

        self.db.collection("sessions").document(session_id).set(data)
