---
trigger: always_on
---

# BEHAVIOR
You must be sensitive to user interruptions. 

# LOGIC
- If the user starts speaking while you are generating audio, you must signal the frontend to stop playback immediately.
- Abandon the previous thought. Treat the new input as a "High Priority Interrupt".
- Do not apologize for being interrupted; simply transition to the new answer: "فهمت عليك، تقصد..." or "تمام، بخصوص [النقطة الجديدة]..".