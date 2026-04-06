#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# 🔮 QUANTUM MCAGI — TERMUX SETUP & TRANSFER SCRIPT
# ============================================================================
# Complete installation of Quantum MCAGI on Termux (Android).
#
# USAGE:
#   Method 1 — Clone from GitHub (review first):
#     curl -sL https://raw.githubusercontent.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-/main/termux_setup.sh -o termux_setup.sh
#     less termux_setup.sh   # Review before running
#     bash termux_setup.sh
#
#   Method 2 — Run locally after cloning:
#     cd ~/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-
#     bash termux_setup.sh
#
#   Method 3 — Transfer from PC via USB/SSH:
#     scp -r ./backend user@phone:~/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-/backend
#     ssh user@phone 'bash ~/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-/termux_setup.sh'
#
# REQUIREMENTS:
#   - Termux 0.119+ (F-Droid version recommended)
#   - Android 10+ (API 29+)
#   - ~500MB free storage
#   - Internet connection (first run only)
#
# What this script does:
#   1. Installs system packages (python, git, clang, etc.)
#   2. Clones or updates the repository
#   3. Installs Python dependencies (21 direct deps)
#   4. Installs PennyLane separately (--no-deps for Termux)
#   5. Downloads NLTK data
#   6. Sets up MongoDB (optional)
#   7. Creates launch script
#   8. Verifies installation
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Banner
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║  🔮 QUANTUM MCAGI — TERMUX SETUP               ║"
echo "  ║  Meta-Cognitive Artificial General Intelligence  ║"
echo "  ║  NO LLM — TRUE AI                               ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Config
REPO_URL="https://github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-.git"
INSTALL_DIR="$HOME/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-"
OLD_INSTALL_DIR="$HOME/Quantum_MCAGI_NO_LLM"
BACKEND_DIR="$INSTALL_DIR/backend"

# ============================================================================
# MIGRATION: Move old install path to new path (preserves brain data)
# ============================================================================
if [ -d "$OLD_INSTALL_DIR" ] && [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[MIGRATE] Found old install at $OLD_INSTALL_DIR${NC}"
    echo -e "${YELLOW}  Moving to $INSTALL_DIR ...${NC}"
    if mv "$OLD_INSTALL_DIR" "$INSTALL_DIR"; then
        # Update alias if it exists
        if [ -f "$HOME/.bashrc" ]; then
            sed -i '/alias mcagi=/s|Quantum_MCAGI_NO_LLM|TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-|g' "$HOME/.bashrc" 2>/dev/null
        fi
        echo -e "${GREEN}  ✓ Migrated to new path. Brain data preserved.${NC}"
    else
        echo -e "${RED}  ✗ Migration failed. Falling back to old path.${NC}"
        INSTALL_DIR="$OLD_INSTALL_DIR"
        BACKEND_DIR="$INSTALL_DIR/backend"
    fi
elif [ -d "$OLD_INSTALL_DIR" ] && [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[MIGRATE] Both old and new paths exist. Using new path: $INSTALL_DIR${NC}"
    echo -e "${YELLOW}  You can remove the old dir: rm -rf $OLD_INSTALL_DIR${NC}"
fi

# ============================================================================
# STEP 1: System packages
# ============================================================================
echo -e "${CYAN}[1/8] Installing system packages...${NC}"

pkg update -y 2>/dev/null || apt update -y
pkg install -y python git clang libffi openssl-tool \
    libjpeg-turbo libpng libxml2 libxslt freetype \
    pkg-config binutils 2>/dev/null || {
    echo -e "${YELLOW}Some packages may already be installed, continuing...${NC}"
}

# Ensure pip is available
python -m ensurepip --upgrade 2>/dev/null || true
pip install --upgrade pip 2>/dev/null || true

echo -e "${GREEN}  ✓ System packages ready${NC}"

# ============================================================================
# STEP 2: Clone or update repository
# ============================================================================
echo -e "${CYAN}[2/8] Setting up repository...${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "  Repository exists, pulling latest..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || {
        echo -e "${YELLOW}  Pull failed (local changes?), continuing with existing code...${NC}"
    }
elif [ -d "$BACKEND_DIR" ]; then
    echo -e "  Backend directory exists (manual transfer), skipping clone..."
else
    echo -e "  Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
echo -e "${GREEN}  ✓ Repository ready at $INSTALL_DIR${NC}"

# ============================================================================
# STEP 3: Python dependencies
# ============================================================================
echo -e "${CYAN}[3/8] Installing Python dependencies (20 packages)...${NC}"

cd "$BACKEND_DIR"

# Install from requirements.txt
pip install -r requirements.txt 2>&1 | tail -5

# duckduckgo_search is optional — primp (Rust binary) has no Termux/aarch64 wheel.
# search_compat.py has a pure-Python fallback using DuckDuckGo Instant Answer API.
pip install duckduckgo_search 2>/dev/null || {
    echo -e "${YELLOW}  duckduckgo_search unavailable (primp needs Rust) — using built-in search fallback${NC}"
}

echo -e "${GREEN}  ✓ Core dependencies installed${NC}"

# ============================================================================
# STEP 4: PennyLane (special handling for Termux)
# ============================================================================
echo -e "${CYAN}[4/8] Installing PennyLane (quantum computing)...${NC}"

# PennyLane has a hard dep on pennylane-lightning which requires
# scipy-openblas32 (no Android wheel). Install with --no-deps.
pip install --no-deps PennyLane 2>&1 | tail -3 || {
    echo -e "${YELLOW}  PennyLane install failed — quantum features will use fallback${NC}"
    echo -e "${YELLOW}  (All PennyLane imports are guarded with try/except)${NC}"
}

# Install autoray (PennyLane needs it at runtime)
pip install autoray 2>/dev/null || true

echo -e "${GREEN}  ✓ PennyLane setup complete${NC}"

# ============================================================================
# STEP 5: NLTK data
# ============================================================================
echo -e "${CYAN}[5/8] Downloading NLTK data...${NC}"

python -c "
import nltk
import os
nltk_dir = os.path.expanduser('~/nltk_data')
os.makedirs(nltk_dir, exist_ok=True)
for pkg in ['punkt', 'punkt_tab', 'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng', 'vader_lexicon', 'wordnet', 'stopwords']:
    try:
        nltk.download(pkg, download_dir=nltk_dir, quiet=True)
    except Exception as e:
        print(f'  Warning: {pkg} download failed: {e}')
print('  NLTK data ready')
" 2>/dev/null

echo -e "${GREEN}  ✓ NLTK data downloaded${NC}"

# ============================================================================
# STEP 6: MongoDB (optional)
# ============================================================================
echo -e "${CYAN}[6/8] Checking MongoDB...${NC}"

if command -v mongod &>/dev/null; then
    echo -e "${GREEN}  ✓ MongoDB already installed${NC}"
elif command -v pkg &>/dev/null; then
    echo -e "  MongoDB is optional. Install with: pkg install mongodb"
    echo -e "  The system works without it using file-based storage."
else
    echo -e "  MongoDB not found. Using file-based storage."
fi

# ============================================================================
# STEP 7: Create launch script
# ============================================================================
echo -e "${CYAN}[7/8] Creating launch script...${NC}"

cat > "$INSTALL_DIR/start.sh" << 'LAUNCH_EOF'
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
LAUNCH_EOF

chmod +x "$INSTALL_DIR/start.sh"

# Also create a convenience alias installer
cat > "$INSTALL_DIR/install_alias.sh" << 'ALIAS_EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Add 'mcagi' alias to .bashrc
ALIAS_LINE='alias mcagi="bash ~/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-/start.sh"'
if ! grep -q "mcagi" "$HOME/.bashrc" 2>/dev/null; then
    echo "$ALIAS_LINE" >> "$HOME/.bashrc"
    echo "✓ Added 'mcagi' alias. Run: source ~/.bashrc"
    echo "  Then just type: mcagi"
else
    echo "✓ 'mcagi' alias already exists"
fi
ALIAS_EOF

chmod +x "$INSTALL_DIR/install_alias.sh"

echo -e "${GREEN}  ✓ Launch scripts created${NC}"

# ============================================================================
# STEP 8: Verify installation
# ============================================================================
echo -e "${CYAN}[8/8] Verifying installation...${NC}"

cd "$BACKEND_DIR"

# Test core imports
python -c "
import sys, os, importlib, importlib.util
ok = 0
fail = 0
modules = [
    ('numpy', 'NumPy'),
    ('scipy', 'SciPy'),
    ('fastapi', 'FastAPI'),
    ('nltk', 'NLTK'),
    ('pydantic', 'Pydantic'),
    ('requests', 'Requests'),
]

for mod, name in modules:
    try:
        __import__(mod)
        ok += 1
    except ImportError:
        print(f'  ✗ {name} — MISSING')
        fail += 1

# Test PennyLane (optional)
try:
    import pennylane
    print(f'  ✓ PennyLane {pennylane.__version__} (quantum mode)')
    ok += 1
except ImportError:
    print(f'  ○ PennyLane — not installed (classical fallback)')

# Test core backend modules using explicit file-based import.
# This avoids issues with PennyLane import hooks or sys.path quirks
# on Termux by loading directly from the known file path.
backend_dir = os.path.abspath(os.getcwd())
core_modules = ['algorithmic_core', 'quantum_markov', 'quantum_memory', 'chat', 'shared_state']
for mod in core_modules:
    mod_path = os.path.join(backend_dir, f'{mod}.py')
    if not os.path.isfile(mod_path):
        print(f'  ✗ {mod} — file not found: {mod_path}')
        fail += 1
        continue
    try:
        spec = importlib.util.spec_from_file_location(mod, mod_path)
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[mod] = loaded  # register before exec (handles circular imports)
        spec.loader.exec_module(loaded)
        ok += 1
    except Exception as e:
        print(f'  ✗ {mod} — {e}')
        fail += 1

print(f'  ─────────────────────────')
print(f'  {ok} OK, {fail} failed')
if fail == 0:
    print(f'  ✅ All core modules verified!')
" 2>&1

echo ""
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║  🔮 INSTALLATION COMPLETE                       ║"
echo "  ║                                                  ║"
echo "  ║  Start:  cd ~/TERMUX-Quantum-MCAGI*              ║"
echo "  ║          bash start.sh          (chat mode)      ║"
echo "  ║          bash start.sh server   (API server)     ║"
echo "  ║                                                  ║"
echo "  ║  Alias:  bash install_alias.sh                   ║"
echo "  ║          Then just: mcagi                        ║"
echo "  ║                                                  ║"
echo "  ║  Transfer brain data:                            ║"
echo "  ║    /cloud-save    (save to Wolfram Cloud)        ║"
echo "  ║    /cloud-load    (restore from Wolfram Cloud)   ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"
