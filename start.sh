#!/bin/bash
# 🚀 Quantum MCAGI - Startup Script
# Launches both backend and ensures frontend is available

cd "$(dirname "$0")"

echo "🔮 Starting Quantum MCAGI..."
echo ""

# Activate virtual environment if present
if [ -d "venv" ]; then
    echo "  ↳ Using virtual environment: venv/"
    source venv/bin/activate
else
    echo "  ⚠️  No virtual environment found (venv/). Using system Python."
fi

# Check if frontend is built; if not, build it
if [ ! -d "frontend/dist" ]; then
    echo "⚠️  Frontend not built. Building now..."
    cd frontend
    npm run build
    cd ..
    echo "✅ Frontend built."
else
    echo "✅ Frontend build found."
fi

echo ""
echo "Starting backend server..."
echo "  → API: http://localhost:8000/api/"
echo "  → Frontend: http://localhost:8000/app/"
echo "  → API docs: http://localhost:8000/docs"
echo ""

# Start backend
cd backend
MONGO_URL= python server.py
