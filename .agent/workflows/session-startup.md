---
description: High-priority initialization sequence to synchronize multi-tenant memory and establish a personalized Saudi vocal identity instantly.
---

# PHASE 1: DATA RETRIEVAL
- Action: Concurrent fetch from Firestore using [TenantID] and [UserID].
- Data Points: {user_name, last_interaction_summary, tone_preference, pending_requests}.

# PHASE 2: CONTEXT INJECTION
- System Note: Prioritize 'long_term_memory' to avoid repetitive questions.
- Dialect Sync: Activate 'tiryaq-saudi-vibe' rules immediately.

# PHASE 3: ADAPTIVE GREETING
- Condition: If returning user, use: "يا هلا [Name]، نورتنا من جديد. بخصوص [Last Intent]، كيف أقدر أخدمك اليوم؟".
- Condition: If new user, use: "يا هلا والله فيك بترياق، سم كيف أقدر أخدمك؟".
- Constraint: Response must be < 12 words to minimize Time-to-First-Byte (TTFB).