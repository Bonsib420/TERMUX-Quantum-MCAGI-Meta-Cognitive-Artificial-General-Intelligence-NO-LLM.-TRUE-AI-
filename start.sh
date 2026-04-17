#!/data/data/com.termux/files/usr/bin/bash
# 🔮 Launch Quantum MCAGI
cd "$(dirname "$0")/backend"

echo "🔮 Starting Quantum MCAGI..."
echo "   Backend: http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "   Chat mode: python chat.py"
echo "   Server mode: python -m uvicorn server:app --host 0.0.0.0 --port 8000"
echo ""

# Default: interactive chat
if [ "$1" = "server" ] || [ "$1" = "--server" ]; then
    python -m uvicorn server:app --host 0.0.0.0 --port 8000
elif [ "$1" = "chat" ] || [ "$1" = "--chat" ] || [ -z "$1" ]; then
    python chat.py
else
    echo "Usage: ./start.sh [chat|server]"
fi
