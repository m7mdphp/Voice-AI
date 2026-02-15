---
trigger: always_on
---

# CONTEXTUAL MEMORY
Access the 'user_history' object from Firestore at the start of every session.

# PERSONALIZATION LOGIC
- If 'first_name' exists, greet them: "هلا [Name]..".
- If 'last_intent' exists, reference it: "بخصوص موضوعك الأخير عن [Intent]، وش صار معك؟".
- After every interaction, generate a 1-sentence summary of the user's need and update the 'long_term_memory' field.
- Ensure Multi-tenancy: Strictly isolate data. Only access records matching the current 'tenant_id'.