"""
Tiryaq AI Engine - Najm AI Standard Refactor
Features:
- Multi-tenant RAG with strict grounding.
- Groq/Llama 3.3 70B for fast reasoning.
- ElevenLabs PCM_16000 raw byte streaming.
- Dynamic persona and knowledge base loading.
"""

import asyncio
import json
import os
import time
from typing import AsyncGenerator, Dict, List
from pathlib import Path
import requests
from groq import AsyncGroq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings

class GroqEngine:
    """
    Senior AI Architect Implementation of Tiryaq Voice Engine.
    Strict Adherence to Najm AI Standards: Low Latency, No Hallucinations, Dynamic Context.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.db = self._load_tenant_db(tenant_id)
        self.client = self._init_groq()
        self.elevenlabs_api_key = settings.ELEVENLABS_API_KEY
        
        # Extracted from DB
        persona = self.db.get("persona", {})
        self.voice_id = persona.get("voice_id", "pNInz6obpgnuMvkhbuZ5")
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 150
        self.temperature = 0.5 # Lower temperature for better grounding

    def _load_tenant_db(self, tenant_id: str) -> Dict:
        """Loads the unique JSON database for the tenant."""
        try:
            # Normalization: Map UI/Alias IDs to physical filenames
            id_map = {
                "tiryaq_technology": "tiryaq",
                "tenant1": "tenant1",
                "insurance_client": "insurance_client"
            }
            
            clean_id = id_map.get(tenant_id.lower().strip(), tenant_id)
            
            base_dir = Path(__file__).parent.parent 
            db_path = base_dir / "data" / f"{clean_id}_db.json"
            
            if not db_path.exists():
                logger.warning(f"DB for {tenant_id} not found at {db_path}, using default.")
                db_path = base_dir / "data" / "tiryaq_db.json" 
            
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.success(f"Loaded knowledge base from {db_path} for: {data.get('tenant_name')}")
                return data
        except Exception as e:
            logger.error(f"Critical Error: Failed to load tenant database: {e}")
            return {"knowledge_base": {}, "persona": {}}

    def _init_groq(self) -> AsyncGroq:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing")
        return AsyncGroq(api_key=settings.GROQ_API_KEY)

    def _build_system_prompt(self) -> str:
        """
        Premium Saudi AI Consultant Prompt.
        Focus: Natural White Dialect, Extreme Contextual Awareness, Zero Hallucinations.
        """
        kb_content = json.dumps(self.db.get("knowledge_base", {}), ensure_ascii=False)
        persona_rules = "\n".join(self.db.get("persona", {}).get("rules", []))
        
        prompt = f"""
# IDENTITY:
You are "Tiryaq", an elite medical AI consultant for {self.db.get('tenant_name', 'Tiryaq Technology')}.
Your goal is to provide seamless, human-like, and professional support in Saudi White Dialect (اللهجة البيضاء).

# BEHAVIORAL GUIDELINES:
- Be warm and welcoming. Use "يا هلا"، "سم"، "أبشر" naturally.
- DO NOT sound like a robot. If the user greets you, greet them back warmly.
- If the user is speaking, listen fully. 
- Responses must be SHORT and CONCISE (max 20 words).

# KNOWLEDGE BASE GROUNDING:
- Use the following data as your ONLY source for facts about services, prices, or company info:
{kb_content}

# CRITICAL SAFETY:
- If a question is factual (prices, medical advice, dates) and NOT in the KB, say: "والله حالياً ما عندي معلومة أكيدة عن هالنقطة، ودك أحولك للمختص يخدمك؟"
- DO NOT make up any info.

# PERSONA CUSTOMIZATION:
{persona_rules}

# OUTPUT FORMAT:
Arabic (Saudi White Dialect) ONLY. No English words.
"""
        return prompt.strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def process_request(self, user_text: str, context: Dict) -> AsyncGenerator[Dict, None]:
        start_time = time.time()
        ttfb_recorded = False
        text_buffer = ""
        
        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        if "history" in context:
            messages.extend(context["history"][-4:])
        messages.append({"role": "user", "content": user_text})
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7, # Slightly higher for more natural flow
                stream=True
            )
            
            async for chunk in stream:
                if not ttfb_recorded:
                    ttfb = (time.time() - start_time) * 1000
                    logger.debug(f"TTFT: {ttfb:.2f}ms")
                    ttfb_recorded = True

                content = chunk.choices[0].delta.content
                if content:
                    text_buffer += content
                    yield {"type": "text", "content": content}
                    
                    if any(punct in content for punct in [".", "!", "؟", "\n", "،"]):
                        async for audio in self._tts_stream(text_buffer):
                            yield {"type": "audio", "content": audio}
                        text_buffer = ""
            
            if text_buffer.strip():
                async for audio in self._tts_stream(text_buffer):
                    yield {"type": "audio", "content": audio}

        except Exception as e:
            logger.error(f"Engine Processing Error: {e}")
            yield {"type": "error", "content": "حدث خطأ، لحظة وأكون معك."}

    async def _tts_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """MP3 format for high-stability streaming (Resilient to network jitter)."""
        if not self.elevenlabs_api_key or not text.strip():
            return

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        params = {
            "output_format": "pcm_16000",
            "optimize_streaming_latency": 3 
        }
        
        headers = {
            "Accept": "audio/l16",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, json=data, headers=headers, params=params, stream=True, timeout=8)
            )
            
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=16384): # High-res buffering
                    if chunk:
                        yield chunk
            else:
                logger.error(f"TTS Error: {response.text}")
        except Exception as e:
            logger.error(f"TTS Connection Failed: {e}")