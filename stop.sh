#!/bin/bash

echo "=== K&H2 종료 ==="
pkill -f "uvicorn backend.app" 2>/dev/null && echo "백엔드 종료" || echo "백엔드 미실행"
pkill -f "vite" 2>/dev/null && echo "프론트엔드 종료" || echo "프론트엔드 미실행"
pkill -f "ollama serve" 2>/dev/null && echo "Ollama 종료" || echo "Ollama 미실행"
pkill -f "ollama runner" 2>/dev/null
echo "=== 완료 ==="
