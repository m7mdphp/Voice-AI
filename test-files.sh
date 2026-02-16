#!/bin/bash
echo "=== Checking file locations ==="
echo "Current directory: $(pwd)"
echo "Files in /app:"
ls -la /app/ 2>/dev/null || echo "Directory /app not found"
echo ""
echo "Files in /app/frontend:"
ls -la /app/frontend/ 2>/dev/null || echo "Directory /app/frontend not found"
echo ""
echo "Looking for voice_assistant_v3.html:"
find /app -name "voice_assistant_v3.html" 2>/dev/null
echo ""
echo "Looking for voice_assistant_v4.html:"
find /app -name "voice_assistant_v4.html" 2>/dev/null
