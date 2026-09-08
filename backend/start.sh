#!/bin/bash

# Kill any existing processes
pkill -f "engine_api.py" 2>/dev/null
pkill -f "http.server" 2>/dev/null

# Start backend
echo "🚀 Starting Quantum MCAGI Engine..."
python engine_api.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend server
echo "🌐 Starting web server on port 8080..."
python -m http.server 8080 &
FRONTEND_PID=$!

echo ""
echo "✅ ALL SYSTEMS ONLINE"
echo "======================"
echo "📍 Backend: http://127.0.0.1:5000"
echo "📍 Frontend: http://localhost:8080"
echo "📍 Open in browser: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop everything"

# Wait for Ctrl+C
wait $FRONTEND_PID

# Cleanup on exit
trap "pkill -f 'engine_api.py'; pkill -f 'http.server'; exit" INT
