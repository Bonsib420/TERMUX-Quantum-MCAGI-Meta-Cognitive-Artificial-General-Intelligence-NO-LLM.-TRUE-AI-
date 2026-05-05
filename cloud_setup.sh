#!/usr/bin/env bash
# ============================================================================
# 🔮 QUANTUM MCAGI — CLOUD SYNC SETUP
# ============================================================================
# Configures rclone for Google Drive, downloads the latest code + brain data,
# and writes backend/.env so all in-chat cloud commands (/cloud-save,
# /cloud-load, /rclone-setup, etc.) use the correct remote automatically.
#
# USAGE — three ways to supply the Google Drive OAuth token:
#
#   1. Environment variable (non-interactive, CI-friendly):
#        GDRIVE_TOKEN='{"access_token":"...","refresh_token":"..."}' bash cloud_setup.sh
#
#   2. Token file (saves you copy-pasting large JSON):
#        echo '{"access_token":"...","refresh_token":"..."}' > /tmp/gdrive_token.json
#        GDRIVE_TOKEN_FILE=/tmp/gdrive_token.json bash cloud_setup.sh
#
#   3. Interactive prompt (default when neither of the above is set):
#        bash cloud_setup.sh
#        # You will be asked to paste the token JSON.
#
# WHAT THIS SCRIPT DOES:
#   1. Installs rclone (Linux: curl installer; Termux: pkg install rclone)
#   2. Writes ~/.config/rclone/rclone.conf with a remote named "gdrive 666"
#   3. Downloads code  → ~/Quantum_MCAGI_NO_LLM_V⁰²/
#      Downloads brain → ~/.quantum-mcagi/
#   4. Writes backend/.env so RCLONE_REMOTE is set for the chat application
#   5. Installs PennyLane Lightning 0.44.1
#
# SECURITY NOTE:
#   The token is written ONLY to ~/.config/rclone/rclone.conf (local machine).
#   It is never committed to the repository.  backend/.env is git-ignored.
# ============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Google Drive path constants (must match your Drive layout)
GDRIVE_REMOTE="gdrive 666"
GDRIVE_CODE_PATH="Quantum Cloud/Quantum_MCAGI_NO_LLM_V⁰²_LIGHTNING"
GDRIVE_BRAIN_PATH="Quantum Cloud/MCAGI_BRAIN"

# Local destination paths
CODE_DEST="$HOME/Quantum_MCAGI_NO_LLM_V⁰²"
BRAIN_DEST="$HOME/.quantum-mcagi"

echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║  🔮 QUANTUM MCAGI — CLOUD SYNC SETUP            ║"
echo "  ║  rclone · Google Drive · PennyLane Lightning    ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# STEP 1 — Install rclone
# ============================================================================
echo -e "${CYAN}[1/5] Installing rclone...${NC}"

if command -v rclone &>/dev/null; then
    echo -e "${GREEN}  ✓ rclone already installed: $(rclone --version | head -1)${NC}"
else
    # Termux
    if command -v pkg &>/dev/null; then
        pkg install -y rclone 2>/dev/null || true
    fi

    # Generic Linux (also works on Replit, GitHub Codespaces, etc.)
    if ! command -v rclone &>/dev/null; then
        echo "  Installing rclone via official installer..."
        if command -v curl &>/dev/null; then
            curl -fsSL https://rclone.org/install.sh | sudo bash 2>/dev/null || \
            curl -fsSL https://rclone.org/install.sh | bash 2>/dev/null || true
        fi
    fi

    if command -v rclone &>/dev/null; then
        echo -e "${GREEN}  ✓ rclone installed: $(rclone --version | head -1)${NC}"
    else
        echo -e "${RED}  ✗ rclone installation failed.${NC}"
        echo -e "${YELLOW}  Manual install: https://rclone.org/install/${NC}"
        echo -e "${YELLOW}  Termux: pkg install rclone${NC}"
        exit 1
    fi
fi

# ============================================================================
# STEP 2 — Obtain the Google Drive OAuth token
# ============================================================================
echo -e "${CYAN}[2/5] Configuring rclone remote \"${GDRIVE_REMOTE}\"...${NC}"

TOKEN_JSON=""

# Source 1: environment variable
if [[ -n "${GDRIVE_TOKEN:-}" ]]; then
    TOKEN_JSON="$GDRIVE_TOKEN"
    echo "  Using token from GDRIVE_TOKEN environment variable."

# Source 2: token file
elif [[ -n "${GDRIVE_TOKEN_FILE:-}" && -f "${GDRIVE_TOKEN_FILE}" ]]; then
    TOKEN_JSON="$(cat "$GDRIVE_TOKEN_FILE")"
    echo "  Using token from file: $GDRIVE_TOKEN_FILE"

# Source 3: existing rclone.conf that already has the remote
elif rclone listremotes 2>/dev/null | grep -qF "${GDRIVE_REMOTE}:"; then
    echo -e "${GREEN}  ✓ Remote \"${GDRIVE_REMOTE}\" already present in rclone.conf — skipping token entry.${NC}"
    TOKEN_JSON="__already_configured__"

# Source 4: interactive prompt
else
    echo ""
    echo -e "${YELLOW}  No GDRIVE_TOKEN env var or token file found.${NC}"
    echo "  Please paste your Google Drive OAuth token JSON below."
    echo "  (The JSON object starting with {\"access_token\":... ending with })"
    echo "  Press Enter twice when done:"
    echo ""
    TOKEN_JSON=""
    while IFS= read -r line; do
        [[ -z "$line" ]] && break
        TOKEN_JSON+="$line"
    done
fi

# Write rclone config (only when we have a new token)
if [[ "$TOKEN_JSON" != "__already_configured__" ]]; then
    if [[ -z "$TOKEN_JSON" ]]; then
        echo -e "${RED}  ✗ No token provided. Cannot configure rclone.${NC}"
        exit 1
    fi

    mkdir -p "$HOME/.config/rclone"
    RCLONE_CONF="$HOME/.config/rclone/rclone.conf"

    # Remove existing gdrive 666 section if present, then append fresh one
    if [[ -f "$RCLONE_CONF" ]]; then
        # Strip old [gdrive 666] block (from section header to next blank line + header)
        python3 - "$RCLONE_CONF" <<'PYEOF'
import sys, re
text = open(sys.argv[1]).read()
# Remove [gdrive 666] section
text = re.sub(r'\[gdrive 666\][^\[]*', '', text, flags=re.DOTALL)
open(sys.argv[1], 'w').write(text.rstrip('\n') + '\n')
PYEOF
    fi

    cat >> "$HOME/.config/rclone/rclone.conf" << CONF
[gdrive 666]
type = drive
scope = drive
token = ${TOKEN_JSON}
CONF

    echo -e "${GREEN}  ✓ rclone.conf written: $HOME/.config/rclone/rclone.conf${NC}"
fi

# Verify connectivity
echo "  Testing connection to Google Drive..."
if rclone lsd "gdrive 666:Quantum Cloud" --max-depth 1 &>/dev/null; then
    echo -e "${GREEN}  ✓ Google Drive connection OK${NC}"
else
    echo -e "${YELLOW}  ⚠ Connection test failed — token may be expired; rclone will try to refresh automatically.${NC}"
    echo -e "${YELLOW}    If downloads fail, re-run with a fresh GDRIVE_TOKEN.${NC}"
fi

# ============================================================================
# STEP 3 — Download code + brain from Google Drive
# ============================================================================
echo -e "${CYAN}[3/5] Downloading from Google Drive...${NC}"

mkdir -p "$CODE_DEST" "$BRAIN_DEST"

echo "  Downloading code: \"${GDRIVE_REMOTE}:${GDRIVE_CODE_PATH}\" → ${CODE_DEST}"
rclone copy "gdrive 666:${GDRIVE_CODE_PATH}/" "${CODE_DEST}/" -P \
    --transfers=4 \
    --retries=3 \
    --low-level-retries=10 \
    2>&1 | grep -E "Transferred|Errors|Elapsed|ETA|%" || true

echo "  Downloading brain: \"${GDRIVE_REMOTE}:${GDRIVE_BRAIN_PATH}\" → ${BRAIN_DEST}"
rclone copy "gdrive 666:${GDRIVE_BRAIN_PATH}/" "${BRAIN_DEST}/" -P \
    --transfers=4 \
    --retries=3 \
    --low-level-retries=10 \
    2>&1 | grep -E "Transferred|Errors|Elapsed|ETA|%" || true

echo -e "${GREEN}  ✓ Downloads complete${NC}"

# ============================================================================
# STEP 4 — Write backend/.env so chat app knows which remote to use
# ============================================================================
echo -e "${CYAN}[4/5] Writing backend/.env for cloud sync...${NC}"

mkdir -p "$BACKEND_DIR"
ENV_FILE="$BACKEND_DIR/.env"

# Preserve any existing non-rclone settings
if [[ -f "$ENV_FILE" ]]; then
    # Remove old RCLONE_REMOTE and RCLONE_BASE_PATH lines
    python3 - "$ENV_FILE" <<'PYEOF'
import sys
lines = open(sys.argv[1]).readlines()
lines = [l for l in lines if not l.startswith('RCLONE_REMOTE=') and not l.startswith('RCLONE_BASE_PATH=')]
open(sys.argv[1], 'w').writelines(lines)
PYEOF
fi

cat >> "$ENV_FILE" << 'ENVEOF'
# Google Drive cloud sync — set by cloud_setup.sh
RCLONE_REMOTE=gdrive 666
RCLONE_BASE_PATH=Quantum Cloud/MCAGI_BRAIN
ENVEOF

echo -e "${GREEN}  ✓ backend/.env updated${NC}"
echo "     RCLONE_REMOTE=gdrive 666"
echo "     RCLONE_BASE_PATH=Quantum Cloud/MCAGI_BRAIN"

# ============================================================================
# STEP 5 — Install PennyLane Lightning 0.44.1
# ============================================================================
echo -e "${CYAN}[5/5] Installing PennyLane Lightning 0.44.1...${NC}"

BREAK_FLAG=""
# Termux / system-managed Python needs --break-system-packages
python3 -m pip install --quiet pennylane-lightning==0.44.1 2>/dev/null || \
    python3 -m pip install --quiet --break-system-packages pennylane-lightning==0.44.1 2>/dev/null || {
    echo -e "${YELLOW}  ⚠ pennylane-lightning==0.44.1 wheel not available for this platform.${NC}"
    echo -e "${YELLOW}    Trying latest compatible release...${NC}"
    python3 -m pip install --quiet pennylane-lightning 2>/dev/null || \
        python3 -m pip install --quiet --break-system-packages pennylane-lightning 2>/dev/null || \
        echo -e "${YELLOW}    pennylane-lightning unavailable — quantum will use default.lightning.qubit${NC}"
}

# Verify PennyLane import
python3 -c "
import importlib, sys
for pkg in ('pennylane', 'pennylane_lightning'):
    spec = importlib.util.find_spec(pkg)
    if spec:
        mod = importlib.import_module(pkg)
        ver = getattr(mod, '__version__', 'unknown')
        print(f'  ✓ {pkg} {ver}')
    else:
        print(f'  ○ {pkg} not installed (classical fallback active)')
" 2>/dev/null || true

echo -e "${GREEN}  ✓ PennyLane setup complete${NC}"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║  🔮 CLOUD SYNC SETUP COMPLETE                   ║"
echo "  ║                                                  ║"
echo "  ║  rclone remote : gdrive 666                     ║"
echo "  ║  Code downloaded to : ~/Quantum_MCAGI_NO_LLM_V⁰²║"
echo "  ║  Brain downloaded to: ~/.quantum-mcagi/          ║"
echo "  ║                                                  ║"
echo "  ║  In-chat cloud commands (all use gdrive 666):   ║"
echo "  ║    /rclone-setup   — verify connection          ║"
echo "  ║    /rclone-status  — list Drive contents        ║"
echo "  ║    /cloud-save     — save brain to Drive        ║"
echo "  ║    /cloud-load     — restore brain from Drive   ║"
echo "  ║    /cloud-pull     — pull all providers         ║"
echo "  ║                                                  ║"
echo "  ║  To run the app:                                ║"
echo "  ║    cd ~/Quantum_MCAGI_NO_LLM_V⁰²/backend        ║"
echo "  ║    python3 chat.py                              ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${NC}"
