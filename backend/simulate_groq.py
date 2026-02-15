
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(dotenv_path="backend/.env")

# Mock Settings 
class MockSettings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    DEFAULT_PERSONA_PATH = "personas/tiryaq.json"
    LOG_LEVEL = "DEBUG"

import builtins
import types
config_mock = types.ModuleType("config")
config_mock.settings = MockSettings()
sys.modules["config"] = config_mock

# Mock Requests for ElevnLabs
from unittest.mock import MagicMock
sys.modules["requests"] = MagicMock()

sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from services.agent_engine import GroqEngine
    print("[SIMULATION] Imported GroqEngine")
except ImportError as e:
    print(f"[FAIL] Import Error: {e}")
    sys.exit(1)

async def main():
    print("--- STARTING GROQ PLAN B VERIFICATION ---")
    
    if not MockSettings.GROQ_API_KEY:
        print("[FAIL] GROQ_API_KEY missing in .env")
        return

    try:
        engine = GroqEngine()
        print(f"[SUCCESS] Engine Init. Persona: {engine.persona.get('role')}")
    except Exception as e:
        print(f"[FAIL] Init Error: {e}")
        return

    print("\n--- Sending Test Query ---")
    print("User: أشعر بألم في الصدر")
    
    async for event in engine.process_request("أشعر بألم في الصدر", {"user_id": 123}):
        if event['type'] == 'text':
            print(f"Groq: {event['content']}", end="", flush=True)
        elif event['type'] == 'error':
            print(f"\n[ERROR] {event['content']}")

    print("\n\n[SUCCESS] Stream Completed.")

if __name__ == "__main__":
    asyncio.run(main())
