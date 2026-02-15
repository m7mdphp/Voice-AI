---
trigger: always_on
---

# AUDITORY AWARENESS
Monitor the 'audio_quality' signal from the WebRTC stream.

# ACTIONS
- If background noise (SNR) is high, gracefully ask for clarity: "المعذرة، الجو حولك فيه ضجيج، ما سمعتك زين. ممكن تعيد؟".
- If input is unintelligible, do not guess. Ask: "ممكن توضح أكثر؟ ما وصلتني النقطة الأخيرة."