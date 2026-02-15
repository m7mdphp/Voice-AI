---
description: Automated session post-processing to consolidate conversational intelligence and ensure secure, isolated data persistence.
---

# STEP 1: INTELLIGENT SUMMARIZATION
- Action: Use LLM to extract {Key Topic, User Sentiment, Resolved/Unresolved Status}.
- Output: Store as a compact 'session_snapshot' string.

# STEP 2: SECURE PERSISTENCE
- Target: Update Firestore [tenants/{id}/users/{id}/history].
- Compliance: Ensure no PII (Personal Identifiable Information) is logged in plain text.
- Metadata: Log {latency_metrics, duration, handoff_count}.

# STEP 3: GRACEFUL TERMINATION
- Action: Send 'EOS' (End of Stream) signal to frontend.
- Farewell: Use 'tiryaq-saudi-vibe' for a warm closing: "في أمان الله، ترياق دايم بخدمتك."