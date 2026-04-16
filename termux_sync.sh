#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# 🔮 QUANTUM MCAGI — TERMUX ↔ GITHUB SYNC
# ============================================================================
# Bidirectional sync between Termux and GitHub using git.
# Replaces rclone/Google Drive — works anywhere git works.
#
# USAGE:
#   bash termux_sync.sh              # Interactive menu
#   bash termux_sync.sh push         # Push local changes to GitHub
#   bash termux_sync.sh pull         # Pull latest from GitHub
#   bash termux_sync.sh status       # Show sync status
#   bash termux_sync.sh backup       # Create local backup before sync
#   bash termux_sync.sh brain-push   # Push brain data (concepts, markov states)
#   bash termux_sync.sh brain-pull   # Pull brain data from GitHub
#
# FIRST-TIME SETUP (run once):
#   1. Install git:  pkg install git
#   2. Set identity: git config --global user.name "YourName"
#                    git config --global user.email "your@email.com"
#   3. Auth via PAT: Create at https://github.com/settings/tokens
#      Then: git remote set-url origin https://<TOKEN>@github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-.git
#
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# Config
INSTALL_DIR="$HOME/Quantum_MCAGI_NO_LLM"
BACKEND_DIR="$INSTALL_DIR/backend"
DATA_DIR="$HOME/.quantum-mcagi"
BRAIN_BRANCH="brain-data"

# ============================================================================
# HELPERS
# ============================================================================

banner() {
    echo -e "${MAGENTA}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║  🔮 QUANTUM MCAGI — TERMUX ↔ GITHUB SYNC       ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_repo() {
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        echo -e "${RED}Error: Not a git repo at $INSTALL_DIR${NC}"
        echo -e "Run termux_setup.sh first to clone the repository."
        exit 1
    fi
    cd "$INSTALL_DIR"
}

# Files that should NOT be synced (backups, caches, debug files)
ensure_gitignore() {
    local gitignore="$INSTALL_DIR/.gitignore"
    local needs_update=false

    # Patterns that must be in .gitignore
    local patterns=(
        "**/__pycache__/"
        "*.pyc"
        "*.bak"
        "*.backup"
        "*.debug"
        "*.trace"
        "*.orchorfix.backup"
        "backend/chat_backup.py"
        "backend/chat_broken.py"
        "backend/chat.py.WORKING_STAGE3"
        "backend/backups/"
        "backend/test_render.png"
        "backend/quantum_language_engine.py.backup"
        "backend/quantum_language_engine.py.bak"
        "backend/quantum_language_engine.py.orchorfix.backup"
    )

    for pattern in "${patterns[@]}"; do
        if ! grep -qF "$pattern" "$gitignore" 2>/dev/null; then
            needs_update=true
            break
        fi
    done

    if [ "$needs_update" = true ]; then
        echo -e "${YELLOW}  Updating .gitignore with backup/cache exclusions...${NC}"
        for pattern in "${patterns[@]}"; do
            if ! grep -qF "$pattern" "$gitignore" 2>/dev/null; then
                echo "$pattern" >> "$gitignore"
            fi
        done
        echo -e "${GREEN}  ✓ .gitignore updated${NC}"
    fi
}

# Count of files that differ from remote
sync_status() {
    check_repo

    echo -e "${CYAN}Fetching latest from GitHub...${NC}"
    git fetch origin 2>/dev/null || {
        echo -e "${RED}  Cannot reach GitHub. Check internet connection.${NC}"
        return 1
    }

    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)
    local remote_ref="origin/$branch"

    # Check if remote branch exists
    if ! git rev-parse --verify "$remote_ref" &>/dev/null; then
        echo -e "${YELLOW}  Remote branch '$branch' doesn't exist yet.${NC}"
        echo -e "  Local commits will be pushed as a new branch."
        return 0
    fi

    local ahead behind
    ahead=$(git rev-list --count "$remote_ref..HEAD" 2>/dev/null || echo "?")
    behind=$(git rev-list --count "HEAD..$remote_ref" 2>/dev/null || echo "?")

    echo ""
    echo -e "${BOLD}  Branch: ${CYAN}$branch${NC}"
    echo -e "  ────────────────────────────────"

    if [ "$ahead" = "0" ] && [ "$behind" = "0" ]; then
        echo -e "  ${GREEN}✓ In sync with GitHub${NC}"
    else
        [ "$ahead" != "0" ] && echo -e "  ${YELLOW}↑ $ahead commit(s) ahead${NC} (local changes not pushed)"
        [ "$behind" != "0" ] && echo -e "  ${YELLOW}↓ $behind commit(s) behind${NC} (new changes on GitHub)"
    fi

    # Show uncommitted changes
    local modified untracked
    modified=$(git diff --name-only 2>/dev/null | wc -l)
    untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)

    if [ "$modified" -gt 0 ] || [ "$untracked" -gt 0 ]; then
        echo ""
        echo -e "  ${BOLD}Uncommitted:${NC}"
        [ "$modified" -gt 0 ] && echo -e "    ${YELLOW}$modified modified file(s)${NC}"
        [ "$untracked" -gt 0 ] && echo -e "    ${YELLOW}$untracked new file(s)${NC}"
    fi

    # Show data directory stats
    if [ -d "$DATA_DIR" ]; then
        echo ""
        echo -e "  ${BOLD}Brain data:${NC}"
        local concepts markov
        concepts=$(find "$DATA_DIR" -name "concepts.json" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
        markov=$(find "$DATA_DIR" -name "markov_*.json" -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
        echo -e "    Concepts file: ~${concepts} lines"
        echo -e "    Markov data: ${markov}"
    fi

    echo ""
}

# ============================================================================
# PUSH — Commit and push local changes to GitHub
# ============================================================================
do_push() {
    check_repo
    ensure_gitignore

    echo -e "${CYAN}Preparing to push local changes to GitHub...${NC}"

    # Stage all changes (respects .gitignore)
    git add -A

    # Check if there's anything to commit
    if git diff --cached --quiet; then
        echo -e "${GREEN}  ✓ Nothing new to commit.${NC}"

        # But there might be unpushed commits
        git fetch origin 2>/dev/null
        local branch
        branch=$(git rev-parse --abbrev-ref HEAD)
        local ahead
        ahead=$(git rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo "0")

        if [ "$ahead" -gt 0 ]; then
            echo -e "${YELLOW}  $ahead unpushed commit(s) found. Pushing...${NC}"
            git push origin "$branch" && \
                echo -e "${GREEN}  ✓ Pushed $ahead commit(s) to GitHub${NC}" || \
                echo -e "${RED}  ✗ Push failed. Check auth (see --help for PAT setup)${NC}"
        else
            echo -e "${GREEN}  ✓ Already in sync with GitHub${NC}"
        fi
        return 0
    fi

    # Show what's being committed
    echo -e "${BOLD}  Changes to commit:${NC}"
    git diff --cached --stat | head -20

    # Auto-generate commit message
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M')
    local added modified deleted
    added=$(git diff --cached --diff-filter=A --name-only | wc -l)
    modified=$(git diff --cached --diff-filter=M --name-only | wc -l)
    deleted=$(git diff --cached --diff-filter=D --name-only | wc -l)

    local msg="Termux sync $timestamp"
    local details=""
    [ "$added" -gt 0 ] && details="${details}+${added} "
    [ "$modified" -gt 0 ] && details="${details}~${modified} "
    [ "$deleted" -gt 0 ] && details="${details}-${deleted} "
    [ -n "$details" ] && msg="$msg ($details)"

    echo ""
    echo -e "  Commit message: ${CYAN}$msg${NC}"

    # Allow custom message
    read -p "  Custom message? (Enter to accept, or type new): " custom_msg
    [ -n "$custom_msg" ] && msg="$custom_msg"

    git commit -m "$msg"

    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)
    echo -e "${CYAN}  Pushing to origin/$branch...${NC}"

    git push origin "$branch" && \
        echo -e "${GREEN}  ✓ Pushed to GitHub successfully!${NC}" || {
        echo -e "${RED}  ✗ Push failed.${NC}"
        echo ""
        echo -e "  ${BOLD}Troubleshooting:${NC}"
        echo -e "  1. Set up a Personal Access Token (PAT):"
        echo -e "     https://github.com/settings/tokens"
        echo -e "  2. Update remote URL:"
        echo -e "     git remote set-url origin https://TOKEN@github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-.git"
        return 1
    }
}

# ============================================================================
# PULL — Pull latest from GitHub
# ============================================================================
do_pull() {
    check_repo

    echo -e "${CYAN}Pulling latest from GitHub...${NC}"

    # Stash local changes if any
    local has_changes=false
    if ! git diff --quiet || ! git diff --cached --quiet; then
        has_changes=true
        echo -e "${YELLOW}  Stashing local changes...${NC}"
        git stash push -m "termux-sync-$(date +%s)"
    fi

    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)

    git pull origin "$branch" --ff-only 2>/dev/null && \
        echo -e "${GREEN}  ✓ Pulled latest from GitHub${NC}" || {
        echo -e "${YELLOW}  Fast-forward failed, trying merge...${NC}"
        git pull origin "$branch" --no-rebase && \
            echo -e "${GREEN}  ✓ Merged from GitHub${NC}" || {
            echo -e "${RED}  ✗ Pull failed — conflicts detected${NC}"
            echo -e "  Run: git status   to see conflicts"
            echo -e "  Fix conflicts, then: git add . && git commit"
            # Restore stash even on failure
            if [ "$has_changes" = true ]; then
                echo -e "${YELLOW}  Your local changes are in git stash.${NC}"
                echo -e "  Restore with: git stash pop"
            fi
            return 1
        }
    }

    # Restore stashed changes
    if [ "$has_changes" = true ]; then
        echo -e "${CYAN}  Restoring local changes...${NC}"
        git stash pop 2>/dev/null && \
            echo -e "${GREEN}  ✓ Local changes restored${NC}" || {
            echo -e "${YELLOW}  Stash pop had conflicts. Check: git stash show${NC}"
        }
    fi
}

# ============================================================================
# BACKUP — Create timestamped local backup before sync
# ============================================================================
do_backup() {
    check_repo

    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_dir="$HOME/mcagi_backups/$timestamp"

    echo -e "${CYAN}Creating backup at $backup_dir...${NC}"
    mkdir -p "$backup_dir"

    # Copy backend code (not __pycache__)
    rsync -a --exclude='__pycache__' --exclude='*.pyc' \
        "$BACKEND_DIR/" "$backup_dir/backend/" 2>/dev/null || \
        cp -r "$BACKEND_DIR" "$backup_dir/backend"

    # Copy brain data
    if [ -d "$DATA_DIR" ]; then
        cp -r "$DATA_DIR" "$backup_dir/brain_data"
    fi

    local size
    size=$(du -sh "$backup_dir" 2>/dev/null | awk '{print $1}')
    echo -e "${GREEN}  ✓ Backup created: $backup_dir ($size)${NC}"

    # Cleanup old backups (keep last 5)
    local backup_count
    backup_count=$(ls -d "$HOME/mcagi_backups"/*/ 2>/dev/null | wc -l)
    if [ "$backup_count" -gt 5 ]; then
        echo -e "  Cleaning old backups (keeping last 5)..."
        ls -dt "$HOME/mcagi_backups"/*/ | tail -n +6 | xargs rm -rf
        echo -e "${GREEN}  ✓ Old backups cleaned${NC}"
    fi
}

# ============================================================================
# BRAIN-PUSH — Push brain state (concepts, markov, growth) to a data branch
# ============================================================================
do_brain_push() {
    check_repo

    if [ ! -d "$DATA_DIR" ]; then
        echo -e "${YELLOW}  No brain data found at $DATA_DIR${NC}"
        echo -e "  Run the chat first to generate brain data."
        return 1
    fi

    echo -e "${CYAN}Pushing brain data to GitHub...${NC}"

    # Create brain-data directory in repo
    local brain_export="$INSTALL_DIR/brain-data"
    mkdir -p "$brain_export"

    # Copy brain state files
    local file_count=0
    for f in "$DATA_DIR"/*.json "$DATA_DIR"/*.txt "$DATA_DIR"/markov_*.json; do
        if [ -f "$f" ]; then
            cp "$f" "$brain_export/"
            file_count=$((file_count + 1))
        fi
    done

    if [ "$file_count" -eq 0 ]; then
        echo -e "${YELLOW}  No brain data files found to push${NC}"
        return 0
    fi

    # Add to .gitignore note
    cat > "$brain_export/README.md" << 'EOF'
# 🧠 Brain Data Export

Exported from Termux Quantum MCAGI. Contains:
- `concepts.json` — Concept graph (nodes + edges)
- `markov_*.json` — Markov chain transition states
- `growth.json` — Growth stage metrics
- `conversations.json` — Conversation memory

**Import on another device:**
```bash
bash termux_sync.sh brain-pull
```
EOF

    git add brain-data/
    git commit -m "Brain data export $(date '+%Y-%m-%d %H:%M')" || {
        echo -e "${GREEN}  ✓ No changes in brain data${NC}"
        return 0
    }

    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)
    git push origin "$branch" && \
        echo -e "${GREEN}  ✓ Brain data pushed ($file_count files)${NC}" || \
        echo -e "${RED}  ✗ Push failed — check auth${NC}"
}

# ============================================================================
# BRAIN-PULL — Pull brain state from GitHub
# ============================================================================
do_brain_pull() {
    check_repo

    local brain_export="$INSTALL_DIR/brain-data"

    if [ ! -d "$brain_export" ]; then
        echo -e "${YELLOW}  No brain-data/ in repo. Push brain data first.${NC}"
        return 1
    fi

    echo -e "${CYAN}Pulling brain data from GitHub...${NC}"

    # Pull latest
    git pull origin "$(git rev-parse --abbrev-ref HEAD)" 2>/dev/null

    # Copy to data dir
    mkdir -p "$DATA_DIR"

    local file_count=0
    for f in "$brain_export"/*.json "$brain_export"/*.txt; do
        if [ -f "$f" ]; then
            local basename
            basename=$(basename "$f")
            if [ -f "$DATA_DIR/$basename" ]; then
                echo -e "  ${YELLOW}⚠ $basename exists locally. Overwrite? (y/N)${NC}"
                read -r answer
                [ "$answer" != "y" ] && [ "$answer" != "Y" ] && continue
            fi
            cp "$f" "$DATA_DIR/"
            file_count=$((file_count + 1))
        fi
    done

    echo -e "${GREEN}  ✓ Brain data imported ($file_count files → $DATA_DIR)${NC}"
}

# ============================================================================
# INTERACTIVE MENU
# ============================================================================
interactive_menu() {
    banner

    echo -e "  ${BOLD}Commands:${NC}"
    echo -e "    ${CYAN}1${NC}) ${BOLD}status${NC}      — Show sync status"
    echo -e "    ${CYAN}2${NC}) ${BOLD}push${NC}        — Push local changes → GitHub"
    echo -e "    ${CYAN}3${NC}) ${BOLD}pull${NC}        — Pull from GitHub → local"
    echo -e "    ${CYAN}4${NC}) ${BOLD}backup${NC}      — Create local backup"
    echo -e "    ${CYAN}5${NC}) ${BOLD}brain-push${NC}  — Push brain data → GitHub"
    echo -e "    ${CYAN}6${NC}) ${BOLD}brain-pull${NC}  — Pull brain data ← GitHub"
    echo -e "    ${CYAN}q${NC}) ${BOLD}quit${NC}"
    echo ""

    while true; do
        read -p "  Choose [1-6, q]: " choice
        case "$choice" in
            1|status)     sync_status ;;
            2|push)       do_push ;;
            3|pull)       do_pull ;;
            4|backup)     do_backup ;;
            5|brain-push) do_brain_push ;;
            6|brain-pull) do_brain_pull ;;
            q|quit|exit)  echo -e "${GREEN}  Done.${NC}"; exit 0 ;;
            *)            echo -e "${YELLOW}  Unknown option: $choice${NC}" ;;
        esac
        echo ""
    done
}

# ============================================================================
# MAIN
# ============================================================================
case "${1:-}" in
    push)       banner; do_push ;;
    pull)       banner; do_pull ;;
    status)     banner; sync_status ;;
    backup)     banner; do_backup ;;
    brain-push) banner; do_brain_push ;;
    brain-pull) banner; do_brain_pull ;;
    help|--help|-h)
        banner
        echo -e "  ${BOLD}Usage:${NC} bash termux_sync.sh [command]"
        echo ""
        echo -e "  ${BOLD}Commands:${NC}"
        echo -e "    push        Push local changes to GitHub"
        echo -e "    pull        Pull latest from GitHub"
        echo -e "    status      Show sync status"
        echo -e "    backup      Create timestamped local backup"
        echo -e "    brain-push  Export + push brain data to GitHub"
        echo -e "    brain-pull  Pull + import brain data from GitHub"
        echo ""
        echo -e "  ${BOLD}First-time setup:${NC}"
        echo -e "    1. Create a GitHub Personal Access Token:"
        echo -e "       https://github.com/settings/tokens"
        echo -e "       (select 'repo' scope)"
        echo ""
        echo -e "    2. Configure git authentication:"
        echo -e "       git remote set-url origin https://YOUR_TOKEN@github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-.git"
        echo ""
        echo -e "    3. Set git identity:"
        echo -e "       git config --global user.name \"YourName\""
        echo -e "       git config --global user.email \"your@email.com\""
        echo ""
        ;;
    "")         interactive_menu ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run: bash termux_sync.sh --help"
        exit 1
        ;;
esac
