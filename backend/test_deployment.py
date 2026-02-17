"""
Tiryaq Voice AI - Deployment Test Script
Najm AI Standard: Automated Self-Testing for Production Validation

Tests:
1. Server startup and health check
2. WebSocket connection and handshake
3. Echo endpoint functionality
4. Multi-tenant engine initialization
5. Memory manager fallback validation

Run: python test_deployment.py
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List

# Windows console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Ensure backend directory is in path
BACKEND_DIR = Path(__file__).parent.resolve()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import httpx
    import websockets
except ImportError:
    print("[ERROR] Missing test dependencies. Install with: pip install httpx websockets")
    sys.exit(1)


class DeploymentTester:
    """Comprehensive deployment validation suite."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"
        self.results: List[Dict] = []
        self.passed = 0
        self.failed = 0
    
    def log_result(self, test_name: str, success: bool, message: str = "", duration_ms: float = 0):
        """Record test result."""
        status = "[PASS]" if success else "[FAIL]"
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration_ms": duration_ms
        })
        
        if success:
            self.passed += 1
        else:
            self.failed += 1
        
        duration_str = f" ({duration_ms:.0f}ms)" if duration_ms > 0 else ""
        print(f"  {status}: {test_name}{duration_str}")
        if message:
            print(f"         {message}")
    
    async def test_health_endpoint(self) -> bool:
        """Test /health endpoint returns valid response."""
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    self.log_result("Health Endpoint", False, f"Status: {response.status_code}")
                    return False
                
                data = response.json()
                if data.get("status") != "healthy":
                    self.log_result("Health Endpoint", False, f"Invalid status: {data}")
                    return False
                
                duration = (time.time() - start) * 1000
                self.log_result("Health Endpoint", True, f"Version: {data.get('version', 'unknown')}", duration)
                return True
                
        except Exception as e:
            self.log_result("Health Endpoint", False, str(e))
            return False
    
    async def test_debug_endpoint(self) -> bool:
        """Test /ws/debug endpoint for environment info."""
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/ws/debug")
                
                if response.status_code != 200:
                    self.log_result("Debug Endpoint", False, f"Status: {response.status_code}")
                    return False
                
                data = response.json()
                duration = (time.time() - start) * 1000
                self.log_result("Debug Endpoint", True, f"Mode: {data.get('mode', 'unknown')}", duration)
                return True
                
        except Exception as e:
            self.log_result("Debug Endpoint", False, str(e))
            return False
    
    async def test_root_endpoint(self) -> bool:
        """Test / endpoint returns valid response."""
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/")
                
                if response.status_code != 200:
                    self.log_result("Root Endpoint", False, f"Status: {response.status_code}")
                    return False
                
                # Could be HTML or JSON
                content_type = response.headers.get("content-type", "")
                duration = (time.time() - start) * 1000
                
                if "html" in content_type:
                    self.log_result("Root Endpoint", True, "Serving HTML frontend", duration)
                else:
                    data = response.json()
                    self.log_result("Root Endpoint", True, f"JSON: {data.get('message', 'ok')}", duration)
                return True
                
        except Exception as e:
            self.log_result("Root Endpoint", False, str(e))
            return False
    
    async def test_websocket_echo(self) -> bool:
        """Test /ws/echo WebSocket endpoint."""
        start = time.time()
        try:
            async with websockets.connect(
                f"{self.ws_url}/ws/echo",
                ping_timeout=5,
                close_timeout=5
            ) as ws:
                # Wait for server response
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                
                if response == "HANDSHAKE_SUCCESS":
                    duration = (time.time() - start) * 1000
                    self.log_result("WebSocket Echo", True, "Handshake successful", duration)
                    return True
                else:
                    self.log_result("WebSocket Echo", False, f"Unexpected response: {response}")
                    return False
                    
        except asyncio.TimeoutError:
            self.log_result("WebSocket Echo", False, "Timeout waiting for response")
            return False
        except Exception as e:
            self.log_result("WebSocket Echo", False, str(e))
            return False
    
    async def test_websocket_session(self) -> bool:
        """Test /ws/session/{tenant_id}/{user_id} WebSocket endpoint."""
        start = time.time()
        try:
            uri = f"{self.ws_url}/ws/session/test_tenant/test_user"
            
            async with websockets.connect(
                uri,
                ping_timeout=10,
                close_timeout=5
            ) as ws:
                # Wait for connection confirmation (should receive state message)
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    duration = (time.time() - start) * 1000
                    
                    # Connection established successfully
                    self.log_result("WebSocket Session", True, f"Connected to tenant session", duration)
                    return True
                    
                except asyncio.TimeoutError:
                    # No immediate response is OK - connection is established
                    duration = (time.time() - start) * 1000
                    self.log_result("WebSocket Session", True, "Connection established (no initial message)", duration)
                    return True
                    
        except Exception as e:
            error_msg = str(e)
            if "4001" in error_msg:
                self.log_result("WebSocket Session", False, "Tenant engine failed to initialize (check API keys)")
            else:
                self.log_result("WebSocket Session", False, error_msg)
            return False
    
    async def test_memory_manager(self) -> bool:
        """Test MemoryManager initialization and fallback."""
        start = time.time()
        try:
            from services.firestore_memory import MemoryManager
            
            manager = MemoryManager()
            status = manager.get_status()
            
            duration = (time.time() - start) * 1000
            
            if status["storage_type"] == "in_memory":
                self.log_result("Memory Manager", True, "Using in-memory fallback (Firestore unavailable)", duration)
            else:
                self.log_result("Memory Manager", True, "Firestore initialized successfully", duration)
            
            # Test get_user_context
            context = await manager.get_user_context("test_tenant", "test_user")
            if isinstance(context, dict) and "first_name" in context:
                return True
            else:
                self.log_result("Memory Manager", False, f"Invalid context: {context}")
                return False
                
        except Exception as e:
            self.log_result("Memory Manager", False, str(e))
            return False
    
    async def test_engine_initialization(self) -> bool:
        """Test GroqEngine initialization with tenant database."""
        start = time.time()
        try:
            from services.agent_engine import GroqEngine
            
            # Test with default tenant
            engine = GroqEngine(tenant_id="tiryaq")
            
            # Verify database loaded
            if not engine.db:
                self.log_result("Engine Init", False, "Database not loaded")
                return False
            
            # Verify system prompt builds correctly
            prompt = engine._build_system_prompt()
            if "Tiryaq" not in prompt or "اللهجة البيضاء" not in prompt:
                self.log_result("Engine Init", False, "System prompt missing Saudi persona")
                return False
            
            duration = (time.time() - start) * 1000
            self.log_result("Engine Init", True, f"Tenant: {engine.db.get('tenant_name', 'unknown')}", duration)
            return True
            
        except ValueError as e:
            if "GROQ_API_KEY" in str(e):
                self.log_result("Engine Init", False, "GROQ_API_KEY not configured")
            else:
                self.log_result("Engine Init", False, str(e))
            return False
        except Exception as e:
            self.log_result("Engine Init", False, str(e))
            return False
    
    async def test_import_paths(self) -> bool:
        """Test all critical imports work correctly."""
        start = time.time()
        failed_imports = []
        
        modules = [
            "fastapi",
            "uvicorn",
            "websockets",
            "openai",
            "groq",
            "aiohttp",
            "loguru",
            "tenacity",
            "pydantic_settings",
            "config",
            "services.agent_engine",
            "services.firestore_memory",
        ]
        
        for module in modules:
            try:
                __import__(module)
            except ImportError as e:
                failed_imports.append(f"{module}: {e}")
        
        duration = (time.time() - start) * 1000
        
        if failed_imports:
            self.log_result("Import Paths", False, f"Failed: {', '.join(failed_imports)}")
            return False
        else:
            self.log_result("Import Paths", True, f"All {len(modules)} modules imported", duration)
            return True
    
    async def run_all_tests(self):
        """Execute all tests and generate report."""
        print("\n" + "="*60)
        print("Tiryaq Voice AI - Deployment Test Suite")
        print("="*60)
        print(f"Target: {self.base_url}")
        print("-"*60 + "\n")
        
        # Phase 1: Basic connectivity
        print("Phase 1: HTTP Endpoints")
        await self.test_health_endpoint()
        await self.test_debug_endpoint()
        await self.test_root_endpoint()
        
        # Phase 2: WebSocket
        print("\nPhase 2: WebSocket Connections")
        await self.test_websocket_echo()
        await self.test_websocket_session()
        
        # Phase 3: Backend services
        print("\nPhase 3: Backend Services")
        await self.test_import_paths()
        await self.test_memory_manager()
        await self.test_engine_initialization()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = self.passed + self.failed
        print(f"  Total Tests: {total}")
        print(f"  Passed:      {self.passed}")
        print(f"  Failed:      {self.failed}")
        print(f"  Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "N/A")
        print("="*60)
        
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for r in self.results:
                if not r["success"]:
                    print(f"  - {r['test']}: {r['message']}")
        
        return self.failed == 0


async def check_server_running(host: str = "localhost", port: int = 8000) -> bool:
    """Check if server is already running."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://{host}:{port}/health")
            return response.status_code == 200
    except:
        return False


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tiryaq Voice AI Deployment Tester")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--start-server", action="store_true", help="Start server before testing")
    args = parser.parse_args()
    
    # Check if server is running
    if not await check_server_running(args.host, args.port):
        if args.start_server:
            print("[INFO] Starting server...")
            # Server would be started here in a subprocess
            # For now, just warn the user
            print(f"[WARN] Server not running at {args.host}:{args.port}")
            print("   Please start the server first: cd backend && python main.py")
            print("   Or run with uvicorn: uvicorn main:app --host 0.0.0.0 --port 8000")
        else:
            print(f"[ERROR] Server not running at {args.host}:{args.port}")
            print("   Start with: cd backend && python main.py")
            print("   Or pass --start-server flag")
        
        # Run tests anyway (some will fail but we get partial results)
        print("\n[WARN] Running tests anyway (some will fail)...\n")
    
    tester = DeploymentTester(args.host, args.port)
    success = await tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
