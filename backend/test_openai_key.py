"""
Quick test script to verify OpenAI Whisper API key works
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

print("=" * 60)
print("OPENAI WHISPER API KEY TEST")
print("=" * 60)

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
print("\nTesting API connection...")

try:
    client = OpenAI(api_key=api_key)
    
    # List models to test authentication
    models = client.models.list()
    
    print("✅ Authentication successful!")
    print(f"✅ API key is valid")
    print("\nAvailable Whisper models:")
    for model in models:
        if 'whisper' in model.id.lower():
            print(f"  - {model.id}")
    
    print("\n" + "=" * 60)
    print("✅ OPENAI_API_KEY is working correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ API Test Failed: {e}")
    print("\nPossible issues:")
    print("1. API key is invalid or expired")
    print("2. No internet connection")
    print("3. OpenAI service is down")
    exit(1)
