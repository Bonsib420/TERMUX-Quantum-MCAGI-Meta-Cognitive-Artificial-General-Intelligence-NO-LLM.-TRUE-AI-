# Quantum MCAGI - Full Termux Edition

## Quick Start
```bash
# Kill any existing server first
pkill -f "python server.py" 2>/dev/null
pkill -f uvicorn 2>/dev/null

# Install and run
cd backend
pip install -r requirements.txt
python server.py
```

Open: http://localhost:8001

## MongoDB (Optional)
Works without it! To enable:
```bash
pkg install mongodb
mongod --dbpath ~/data/db &
```
