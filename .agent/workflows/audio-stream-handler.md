---
description: Dynamic orchestration of live audio streams, featuring proactive noise management, low-latency synthesis, and intelligent barge-in handling.
---

# STEP 1: SIGNAL PROCESSING
- Constant Monitor: Evaluate input stream via 'noise-cancellation-logic'.
- Action: If Signal-to-Noise Ratio (SNR) is low, trigger comfort noise or a polite request for clarity.

# STEP 2: COGNITIVE PROCESSING (Gemini 3 Pro)
- Thinking: Analyze user intent while ignoring background speech.
- Constraint: Apply 'voice-latency-killer'—short sentences, high-frequency words.

# STEP 3: BARGE-IN & INTERRUPTION
- Event: IF 'Voice Activity Detected' (VAD) while AI is speaking:
  - Immediately KILL the current audio buffer.
  - Reset generation state.
  - Process new user tokens as "Top Priority".
  - Acknowledge the interruption naturally: "تمام، فهمت قصدك.." or "وصلت النقطة، كمل..".

# STEP 4: FAILURE RECOVERY
- If STT confidence < 60%, trigger short recovery phrase: "المعذرة، ما سمعتك زين، ممكن تعيد؟".