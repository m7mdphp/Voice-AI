# 🐛 Bug Report & Quick Fixes

## Critical Issues Identified

### 1. **Backend Uses Mock STT (Line 113 in main.py)**
```python
# CURRENT (BROKEN):
user_text = "أعاني من صداع وحرارة" # Simulation override
```

**Problem:** The backend receives real audio from frontend but **ignores it** and always processes the same hardcoded text.

**Impact:** No matter what you say, the AI responds to "أعاني من صداع وحرارة"

---

### 2. **Missing API Keys**
The system needs 3 API keys that are probably missing:
- `GROQ_API_KEY` - For Llama 3 (LLM)
- `ELEVENLABS_API_KEY` - For voice synthesis
- `OPENAI_API_KEY` - For Whisper (speech-to-text)

---

### 3. **Whisper STT Not Implemented**
The audio data is buffered but never sent to Whisper for transcription.

---

## Quick Fix Options

### Option A: Test with Mock (Quick Demo)
Keep mock but make it respond properly to connection:

```python
# In main.py line 113, change to:
user_text = "تحية، كيف حالك؟"  # Will trigger greeting response
```

Then add `GROQ_API_KEY` to `.env` to at least test the Groq→Text pipeline.

---

### Option B: Implement Real Whisper STT (Production Ready)

Add this function to `main.py`:

```python
import openai
from config import settings

async def transcribe_audio(audio_data: bytearray) -> str:
    """Convert audio to text using OpenAI Whisper"""
    try:
        # Save temporary audio file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Write WAV header + PCM data
            import wave
            with wave.open(f.name, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(16000)
                wav.writeframes(audio_data)
            
            # Transcribe
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            with open(f.name, 'rb') as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ar"
                )
            
            os.unlink(f.name)  # Delete temp file
            return transcription.text
    except Exception as e:
        logger.error(f"Whisper Error: {e}")
        return ""
```

Then replace line 113:
```python
user_text = await transcribe_audio(buffer)
if not user_text.strip():
    return  # Ignore empty/failed transcription
```

---

## Testing Checklist

### Backend Health Check
```powershell
# 1. Check if server is running
# You should see: "Uvicorn running on http://0.0.0.0:8000"

# 2. Check for API keys in .env
cat backend/.env
# Should have:
# GROQ_API_KEY=gsk_...
# ELEVENLABS_API_KEY=sk_...
# OPENAI_API_KEY=sk-...
```

### Frontend Health Check
1. Open `frontend/index.html` in Chrome
2. Press F12 → Console tab
3. Click "ابدأ المحادثة"
4. **Expected logs:**
   - ✅ "Connected to Tiryaq backend"
   - ✅ State changes: idle → listening
5. **Error indicators:**
   - ❌ "WebSocket error"
   - ❌ "فشل الوصول للمايك"

---

## Current System Status

### ✅ Working:
- Backend server (Uvicorn)
- WebSocket connection
- Frontend UI
- Audio capture from microphone
- Groq LLM integration (if API key present)
- ElevenLabs TTS (if API key present)

### ❌ Not Working:
- Speech-to-Text (using mock text)
- End-to-end voice conversation

---

## Recommended Next Steps

1. **Add GROQ_API_KEY** to test text→text pipeline
2. **Implement Whisper** using code above
3. **Add OPENAI_API_KEY** 
4. **(Optional) Add ELEVENLABS_API_KEY** for voice output

---

## Expected Behavior After Fix

1. User speaks Arabic
2. Frontend captures audio → sends to backend
3. Backend buffers until silence detected
4. **Whisper transcribes** audio to Arabic text
5. Groq processes text → generates response
6. **(If ElevenLabs key)** Response converted to audio
7. Frontend plays audio
8. Cycle repeats

Currently stuck at step 4 (using mock text instead).
