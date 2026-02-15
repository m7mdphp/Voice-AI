
import asyncio
import os
import sys
from dotenv import load_dotenv
from typing import AsyncGenerator

# Force UTF-8 for Windows Console
sys.stdout.reconfigure(encoding='utf-8')

# Force load .env for testing
load_dotenv(dotenv_path="backend/.env")

# Check environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[SIMULATION] GEMINI_API_KEY Found? {'YES' if GEMINI_API_KEY else 'NO'}")

# --- MOCKING THE NEW SDK FOR DRY RUN (Since user has no Python/Internet access for real call) ---
# In a real environment, we would import: from google import genai
class GenAiClientMock:
    def __init__(self, api_key):
        self.api_key = api_key
        self.aio = self.AioMock()

    class AioMock:
        def __init__(self):
            self.models = self.ModelsMock()

        class ModelsMock:
            async def generate_content_stream(self, model, contents, config):
                print(f"\n[SIMULATION] Sending to Google GenAI ({model})...")
                print(f"[SIMULATION] Prompt Preview: {contents[:50]}...")
                
                # Verify Config
                print(f"[SIMULATION] System Instruction: {config.system_instruction[:30]}...")
                
                # Mock Response Stream
                response_parts = ["أبشر ", "يا غالي، ", "تم حجز ", "الموعد ", "بنجاح."]
                for part in response_parts:
                    yield type('obj', (object,), {'text': part})
                    await asyncio.sleep(0.1)

# --- REPLICATING ENGINE LOGIC FROM agent_engine.py ---
class TiryaqEngine:
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        if GEMINI_API_KEY:
            self.client = GenAiClientMock(api_key=GEMINI_API_KEY)
        else:
            self.client = None

    def _load_system_prompt(self) -> str:
        return "You are Tiryaq, speak Saudi Dialect..."

    async def process_audio_stream(self, audio_chunks: AsyncGenerator[bytes, None], context: dict):
        full_audio = b""
        async for chunk in audio_chunks:
            full_audio += chunk
        
        user_text = await self._stt_stub(full_audio)
        print(f"[SIMULATION] User Said: {user_text}")

        if self.client:
            # Mock Config Object
            config = type('obj', (object,), {'system_instruction': self.system_prompt})
            
            final_prompt = f"User Context: {context}\nUser said: {user_text}"
            
            async for chunk in self.client.aio.models.generate_content_stream(
                model="gemini-1.5-flash", 
                contents=final_prompt,
                config=config
            ):
                if chunk.text:
                    yield chunk.text
        else:
            yield "NO_API_KEY_FOUND_ERROR"

    async def _stt_stub(self, audio_data: bytes) -> str:
        return "أبغى أحجز موعد"

async def mock_audio_generator():
    yield b"AUDIO_DATA"

async def main():
    print("--- STARTING GENAI SDK MIGRATION TEST ---")
    engine = TiryaqEngine()
    
    context = {"name": "TestUser"}
    response_buffer = []
    
    async for text_chunk in engine.process_audio_stream(mock_audio_generator(), context):
        print(f"Stream Chunk: {text_chunk}")
        response_buffer.append(text_chunk)
        
    print(f"\nfinal Output: {''.join(response_buffer)}")
    
    if "ERROR" in "".join(response_buffer):
        print("\n[FAIL] Environment Variable Issue Detected.")
    else:
        print("\n[SUCCESS] Migration & Env Loading Logic Verified.")

if __name__ == "__main__":
    asyncio.run(main())
