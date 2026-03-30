# Quantum MCAGI - Full Termux Edition

## Quick Start
```bash
# From the project root:
pip install -r requirements.txt
pip install --no-deps PennyLane   # optional: quantum features

# Terminal chat:
cd backend && python chat.py

# Or web server:
bash start.sh
```

Open: http://localhost:8000/app/

## MongoDB (Optional)
Works without it! To enable:
```bash
pkg install mongodb
mongod --dbpath ~/data/db &
```
