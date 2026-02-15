
import asyncio
import sys
from typing import AsyncGenerator

# Mocking the Gemini class as per 'backend/services/agent_engine.py' logic
# with enhanced simulation capabilities for this dry run.

class GeminiMock:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        # VERIFICATION POINT 1: Check if System Prompt enforces Identity & Dialect
        print("\n[VERIFICATION] Loaded System Prompt Rules:")
        for line in system_prompt.split('\n'):
            if "ROLE" in line or "DIALECT" in line or "LATENCY" in line:
                print(f"  {line.strip()}")
    
    async def generate_content_stream(self, prompt):
        print(f"\n[VERIFICATION] Input received by LLM Brain: '{prompt}'")
        
        # VERIFICATION POINT 2: Simulate Smart Response based on "Saudi Dialect" rule
        # Since this is a Mock, we return hardcoded strings for this specific query
        if "تعبان" in prompt or "موعد" in prompt:
            response_parts = ["سلامتك ", "يا غالي ", "ما تشوف شر. ", "تبي ", "أحجز لك ", "عند طبيب عام؟"]
        else:
            response_parts = ["أبشر، ", "طلبك ", "جاهز ", "طال عمرك."]
            
        print("[VERIFICATION] Streaming response (Latency Killer simulation)...")
        for part in response_parts:
            yield part
            await asyncio.sleep(0.1) # Simulate network packet delay

class TiryaqEngine:
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
        self.llm = GeminiMock(self.system_prompt)

    def _load_system_prompt(self) -> str:
        return """
        # ROLE
        You are "Tiryaq", an elite AI Voice Assistant representing Tiryaq Company in Saudi Arabia.
        
        # DIALECT
        Speak strictly in "Saudi White Dialect".
        
        # LATENCY KILLER
        Keep responses under 20 words.
        """

    async def process_audio_stream(self, audio_chunks: AsyncGenerator[bytes, None], context: dict):
        full_audio = b""
        async for chunk in audio_chunks:
            if self.detect_silence(chunk):
                break
            full_audio += chunk
        
        # SIMULATION STUB: Injecting the specific user request for verification
        user_text = await self._stt_stub(full_audio) 
        
        async for response_chunk in self.llm.generate_content_stream(user_text):
            yield response_chunk

    def detect_silence(self, chunk: bytes) -> bool:
        # Mock VAD Logic
        return len(chunk) < 10

    async def _stt_stub(self, audio_data: bytes) -> str:
        # Override to simulate specific input request
        return "هلا، أنا تعبان وأبغى موعد"

async def mock_audio_generator():
    # Simulate receiving Audio Bytes from WebSocket
    yield b"CHUNK_1_AUDIO_DATA"
    yield b"CHUNK_2_AUDIO_DATA"
    yield b"SILENCE" # Trigger silence detection (less than 10 bytes)

async def main():
    print("--- STARTING TIRYAQ ENGINE SIMULATION ---")
    engine = TiryaqEngine()
    
    context = {"name": "User"}
    response_buffer = []
    
    print("\n--- PROCESSING AUDIO STREAM ---")
    async for text_chunk in engine.process_audio_stream(mock_audio_generator(), context):
        print(f"Server > Client (Chunk): {text_chunk}")
        response_buffer.append(text_chunk)
        
    full_response = "".join(response_buffer)
    print(f"\n--- FINAL OUTPUT ---")
    print(f"Full Response: {full_response}")
    
    # LATENCY CHECK
    word_count = len(full_response.split())
    print(f"\n[VERIFICATION] Word Count: {word_count} (Pass if <= 20)")
    if word_count <= 20:
        print("[SUCCESS] Latency Killer Constraint Met.")
    else:
        print("[FAILURE] Response too long!")

if __name__ == "__main__":
    asyncio.run(main())
