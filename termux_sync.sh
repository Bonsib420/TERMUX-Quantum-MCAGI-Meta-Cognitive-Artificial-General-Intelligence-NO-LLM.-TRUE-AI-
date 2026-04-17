#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# 🔮 QUANTUM MCAGI -- TERMUX -> GITHUB SYNC
# ============================================================================
# Push ALL local state (code + brain data) to GitHub in one command.
# Brain data from ~/.quantum-mcagi/ is bundled into brain-data/ automatically.
#
# USAGE:
#   bash termux_sync.sh              # Interactive menu
#   bash termux_sync.sh push         # Push EVERYTHING (code + brain) to GitHub
#   bash termux_sync.sh pull         # Pull latest from GitHub
#   bash termux_sync.sh status       # Show sync status
#   bash termux_sync.sh backup       # Create local backup before sync
#   bash termux_sync.sh brain-push   # Push ONLY brain data to GitHub
#   bash termux_sync.sh brain-pull   # Pull brain data from GitHub -> ~/.quantum-mcagi/
#   MCAGI_INSTALL_DIR=/path/to/repo bash termux_sync.sh push  # Override repo path
#
# WHAT GETS PUSHED (on `push`):
#   Code:  All .py files, scripts, configs in the repo
#   Brain: concepts.json, growth.json, conversations.json, session_state.json,
#          orch_or_state.json, engine_state/markov_chain.json,
#          engine_state/corpus_stats.json, engine_state/engine_state.json,
#          + any other JSON/txt in ~/.quantum-mcagi/ and subdirectories
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_INSTALL_DIR="$HOME/Quantum_MCAGI_NO_LLM"
if [ -n "${MCAGI_INSTALL_DIR:-}" ]; then
    INSTALL_DIR="$MCAGI_INSTALL_DIR"
elif [ -d "$SCRIPT_DIR/.git" ] && [ -d "$SCRIPT_DIR/backend" ]; then
    INSTALL_DIR="$SCRIPT_DIR"
else
    INSTALL_DIR="$DEFAULT_INSTALL_DIR"
fi
BACKEND_DIR="$INSTALL_DIR/backend"
DATA_DIR="$HOME/.quantum-mcagi"
BRAIN_BRANCH="brain-data"

# ============================================================================
# HELPERS
# ============================================================================

banner() {
    echo -e "${MAGENTA}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║  🔮 QUANTUM MCAGI -- TERMUX <-> GITHUB SYNC       ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_repo() {
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        echo -e "${RED}Error: Not a git repo at $INSTALL_DIR${NC}"
        echo -e "Run termux_setup.sh first to clone the repository."
        echo -e "Or set MCAGI_INSTALL_DIR to your existing project path."
        exit 1
    fi
    cd "$INSTALL_DIR"
}

# Detect and recover from in-progress rebase/merge/cherry-pick/detached HEAD
recover_git_state() {
    local git_dir="$INSTALL_DIR/.git"

    # Check for in-progress rebase
    if [ -d "$git_dir/rebase-merge" ] || [ -d "$git_dir/rebase-apply" ]; then
        echo -e "${YELLOW}  Detected in-progress rebase. Aborting to clean state...${NC}"
        git rebase --abort 2>/dev/null
        echo -e "${GREEN}  ✓ Rebase aborted${NC}"
        return 0
    fi

    # Check for in-progress merge
    if [ -f "$git_dir/MERGE_HEAD" ]; then
        echo -e "${YELLOW}  Detected in-progress merge. Aborting to clean state...${NC}"
        git merge --abort 2>/dev/null
        echo -e "${GREEN}  ✓ Merge aborted${NC}"
        return 0
    fi

    # Check for in-progress cherry-pick
    if [ -f "$git_dir/CHERRY_PICK_HEAD" ]; then
        echo -e "${YELLOW}  Detected in-progress cherry-pick. Aborting to clean state...${NC}"
        git cherry-pick --abort 2>/dev/null
        echo -e "${GREEN}  ✓ Cherry-pick aborted${NC}"
        return 0
    fi

    # Check for detached HEAD (common after failed rebase or git pull --rebase)
    if [ "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" = "HEAD" ]; then
        echo -e "${YELLOW}  Detected detached HEAD. Reattaching to branch...${NC}"
        local current_sha target_branch
        current_sha=$(git rev-parse HEAD)
        target_branch=""

        # Strategy 1: Find a local branch pointing at exactly this commit
        target_branch=$(git for-each-ref --points-at="$current_sha" \
            --format='%(refname:short)' refs/heads/ 2>/dev/null | head -1)

        # Strategy 2: Check reflog for the last branch we were on
        if [ -z "$target_branch" ]; then
            while IFS= read -r reflog_line; do
                local candidate
                candidate=$(echo "$reflog_line" | sed -n 's/checkout: moving from \([^ ]*\) to .*/\1/p')
                if [ -n "$candidate" ] && git rev-parse --verify "refs/heads/$candidate" &>/dev/null; then
                    target_branch="$candidate"
                    break
                fi
            done < <(git log -g --format='%gs' HEAD 2>/dev/null)
        fi

        # Strategy 3: Find any branch containing this commit
        if [ -z "$target_branch" ]; then
            target_branch=$(git branch --contains "$current_sha" 2>/dev/null | \
                grep -v 'HEAD detached' | head -1 | sed 's/^[* ]*//')
        fi

        if [ -n "$target_branch" ]; then
            # Reattach HEAD; -B moves the branch pointer to current commit
            git checkout -B "$target_branch" "$current_sha" 2>/dev/null
            echo -e "${GREEN}  ✓ Reattached to branch: $target_branch${NC}"
        else
            # Last resort: create a timestamped recovery branch
            target_branch="termux-recovery-$(date +%Y%m%d-%H%M%S)"
            git checkout -b "$target_branch" 2>/dev/null
            echo -e "${GREEN}  ✓ Created recovery branch: $target_branch${NC}"
            echo -e "${YELLOW}  (Could not determine original branch. You may want to merge into your main branch later.)${NC}"
        fi
        return 0
    fi

    # Check for unmerged files (leftover conflict markers without active operation)
    if git ls-files -u --error-unmatch . >/dev/null 2>&1; then
        echo -e "${YELLOW}  Detected unmerged files. Resetting to clean state...${NC}"
        git reset HEAD . 2>/dev/null
        git checkout -- . 2>/dev/null
        echo -e "${GREEN}  ✓ Reset to clean state${NC}"
        return 0
    fi

    return 1  # No recovery needed
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

# Push current branch with automatic rebase + force-with-lease fallback
push_with_fallback() {
    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)

    if git push origin "$branch" 2>&1; then
        echo -e "${GREEN}  ✓ Pushed to GitHub successfully!${NC}"
        return 0
    fi

    # Push rejected -- try rebase then re-push
    echo -e "${YELLOW}  Push rejected -- remote has newer commits.${NC}"
    echo -e "${CYAN}  Pulling with rebase to integrate remote changes...${NC}"

    if git pull --rebase origin "$branch"; then
        echo -e "${GREEN}  ✓ Rebased on top of remote changes${NC}"
        echo -e "${CYAN}  Retrying push...${NC}"
        if git push origin "$branch"; then
            echo -e "${GREEN}  ✓ Pushed to GitHub successfully!${NC}"
            return 0
        fi
        echo -e "${RED}  ✗ Push still failed after rebase.${NC}"
        echo ""
        echo -e "  ${BOLD}Troubleshooting:${NC}"
        echo -e "  1. Set up a Personal Access Token (PAT):"
        echo -e "     https://github.com/settings/tokens"
        echo -e "  2. Update remote URL:"
        echo -e "     git remote set-url origin https://TOKEN@github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-.git"
        return 1
    fi

    # Rebase hit conflicts -- auto-resolve with local (Termux) as source of truth
    echo -e "${YELLOW}  Rebase hit conflicts -- auto-resolving (Termux = source of truth)...${NC}"
    # During rebase, --theirs = our local commits (counterintuitive Git naming)
    local conflict_count=0
    while IFS= read -r cfile; do
        [ -z "$cfile" ] && continue
        git checkout --theirs "$cfile" 2>/dev/null && git add "$cfile"
        conflict_count=$((conflict_count + 1))
    done < <(git diff --name-only --diff-filter=U 2>/dev/null)

    if [ "$conflict_count" -gt 0 ]; then
        echo -e "  ${GREEN}✓ Auto-resolved $conflict_count conflict(s) using local version${NC}"
        if GIT_EDITOR=true git rebase --continue 2>/dev/null; then
            echo -e "${CYAN}  Retrying push...${NC}"
            if git push origin "$branch"; then
                echo -e "${GREEN}  ✓ Pushed to GitHub successfully!${NC}"
                return 0
            fi
        fi
    fi

    # Rebase continue failed or no conflicts detected -- abort and force push
    echo -e "${YELLOW}  Aborting rebase and retrying with force-with-lease...${NC}"
    git rebase --abort 2>/dev/null
    if git push --force-with-lease origin "$branch"; then
        echo -e "${GREEN}  ✓ Pushed to GitHub (force-with-lease)${NC}"
        return 0
    fi

    echo -e "${RED}  ✗ Push failed.${NC}"
    echo -e "  ${BOLD}Manual fix:${NC}"
    echo -e "    git push --force origin $branch"
    return 1
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
# PUSH -- Commit and push local changes to GitHub
# ============================================================================
do_push() {
    check_repo
    recover_git_state && echo ""  # recover if needed, blank line separator
    ensure_gitignore

    echo -e "${CYAN}Preparing to push ALL local state to GitHub...${NC}"

    # ── Step 1: Bundle brain data into repo so it gets pushed too ─────────
    if [ -d "$DATA_DIR" ]; then
        echo -e "  ${BOLD}Bundling brain data from $DATA_DIR ...${NC}"
        local brain_export="$INSTALL_DIR/brain-data"
        mkdir -p "$brain_export"

        local brain_count=0
        # Top-level JSON + txt
        for f in "$DATA_DIR"/*.json "$DATA_DIR"/*.txt; do
            [ -f "$f" ] && cp "$f" "$brain_export/" && brain_count=$((brain_count + 1))
        done
        # engine_state/ (Markov chain, corpus stats)
        if [ -d "$DATA_DIR/engine_state" ]; then
            mkdir -p "$brain_export/engine_state"
            for f in "$DATA_DIR/engine_state"/*.json; do
                [ -f "$f" ] && cp "$f" "$brain_export/engine_state/" && brain_count=$((brain_count + 1))
            done
        fi
        # Any subdirectories with JSON (hilbert, qram, etc.)
        while IFS= read -r f; do
            local rel_dir
            rel_dir=$(dirname "${f#$DATA_DIR/}")
            mkdir -p "$brain_export/$rel_dir"
            cp "$f" "$brain_export/$rel_dir/"
            brain_count=$((brain_count + 1))
        done < <(find "$DATA_DIR" -mindepth 2 -name "*.json" -not -path "*/engine_state/*" 2>/dev/null)

        if [ "$brain_count" -gt 0 ]; then
            echo -e "  ${GREEN}✓ Bundled $brain_count brain data files${NC}"
            # Show key stats
            if [ -f "$brain_export/concepts.json" ]; then
                local cc
                cc=$(python -c "import json; print(len(json.load(open('$brain_export/concepts.json'))))" 2>/dev/null || echo "?")
                echo -e "    Concepts: $cc"
            fi
            if [ -f "$brain_export/engine_state/markov_chain.json" ]; then
                local cs
                cs=$(du -sh "$brain_export/engine_state/markov_chain.json" 2>/dev/null | awk '{print $1}')
                echo -e "    Markov chain: $cs"
            fi
            if [ -f "$brain_export/growth.json" ]; then
                local stage
                stage=$(python -c "import json; g=json.load(open('$brain_export/growth.json')); print(f\"Stage {g.get('stage',0)} ({g.get('name','?')})\")" 2>/dev/null || echo "?")
                echo -e "    Growth: $stage"
            fi
        fi
    fi

    # ── Step 2: Stage all changes (code + brain data; respects .gitignore) ─
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
            push_with_fallback || true
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

    push_with_fallback || return 1
}

# ============================================================================
# PULL -- Pull latest from GitHub
# ============================================================================
do_pull() {
    check_repo
    recover_git_state && echo ""  # recover if needed

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
            echo -e "${RED}  ✗ Pull failed -- conflicts detected${NC}"
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
# BACKUP -- Create timestamped local backup before sync
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
# BRAIN-PUSH -- Push brain state (concepts, markov, growth) to a data branch
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

    # Copy ALL brain state files (top-level JSON + txt)
    local file_count=0
    for f in "$DATA_DIR"/*.json "$DATA_DIR"/*.txt; do
        if [ -f "$f" ]; then
            cp "$f" "$brain_export/"
            file_count=$((file_count + 1))
        fi
    done

    # Copy engine_state/ subdirectory (Markov chain, corpus stats, engine metadata)
    if [ -d "$DATA_DIR/engine_state" ]; then
        mkdir -p "$brain_export/engine_state"
        for f in "$DATA_DIR/engine_state"/*.json; do
            if [ -f "$f" ]; then
                cp "$f" "$brain_export/engine_state/"
                file_count=$((file_count + 1))
            fi
        done
        echo -e "  Copied engine_state/ (Markov chain + corpus stats)"
    fi

    # Copy orch_or state if present
    if [ -f "$DATA_DIR/orch_or_state.json" ]; then
        cp "$DATA_DIR/orch_or_state.json" "$brain_export/"
    fi

    if [ "$file_count" -eq 0 ]; then
        echo -e "${YELLOW}  No brain data files found to push${NC}"
        return 0
    fi

    # Summary of what's included
    echo -e "  Files collected: $file_count"
    if [ -f "$brain_export/concepts.json" ]; then
        local concept_count
        concept_count=$(python -c "import json; print(len(json.load(open('$brain_export/concepts.json'))))" 2>/dev/null || echo "?")
        echo -e "  Concepts: $concept_count"
    fi
    if [ -f "$brain_export/engine_state/markov_chain.json" ]; then
        local chain_size
        chain_size=$(du -sh "$brain_export/engine_state/markov_chain.json" 2>/dev/null | awk '{print $1}')
        echo -e "  Markov chain: $chain_size"
    fi

    cat > "$brain_export/README.md" << 'EOF'
# 🧠 Brain Data Export

Exported from Termux Quantum MCAGI. Contains:
- `concepts.json` -- Concept graph (nodes + edges)
- `growth.json` -- Growth stage metrics
- `conversations.json` -- Conversation memory (last 500)
- `session_state.json` -- Session tracking
- `orch_or_state.json` -- Orch-OR conscious moments
- `engine_state/markov_chain.json` -- Full Markov chain (states + transitions)
- `engine_state/corpus_stats.json` -- TF-IDF corpus statistics
- `engine_state/engine_state.json` -- Engine metadata

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
        echo -e "${RED}  ✗ Push failed -- check auth${NC}"
}

# ============================================================================
# BRAIN-PULL -- Pull brain state from GitHub
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

    # Copy top-level files
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

    # Copy engine_state/ subdirectory (Markov chain, corpus stats)
    if [ -d "$brain_export/engine_state" ]; then
        mkdir -p "$DATA_DIR/engine_state"
        for f in "$brain_export/engine_state"/*.json; do
            if [ -f "$f" ]; then
                local basename
                basename=$(basename "$f")
                if [ -f "$DATA_DIR/engine_state/$basename" ]; then
                    echo -e "  ${YELLOW}⚠ engine_state/$basename exists locally. Overwrite? (y/N)${NC}"
                    read -r answer
                    [ "$answer" != "y" ] && [ "$answer" != "Y" ] && continue
                fi
                cp "$f" "$DATA_DIR/engine_state/"
                file_count=$((file_count + 1))
            fi
        done
    fi

    # Copy any other subdirectories (hilbert, qram, etc.)
    while IFS= read -r f; do
        local rel_path="${f#$brain_export/}"
        local target_dir="$DATA_DIR/$(dirname "$rel_path")"
        mkdir -p "$target_dir"
        cp "$f" "$target_dir/"
        file_count=$((file_count + 1))
    done < <(find "$brain_export" -mindepth 2 -name "*.json" -not -path "*/engine_state/*" 2>/dev/null)

    echo -e "${GREEN}  ✓ Brain data imported ($file_count files -> $DATA_DIR)${NC}"
    echo -e "  Restart chat to load the new brain state."
}

# ============================================================================
# INTERACTIVE MENU
# ============================================================================
interactive_menu() {
    banner

    echo -e "  ${BOLD}Commands:${NC}"
    echo -e "    ${CYAN}1${NC}) ${BOLD}status${NC}      -- Show sync status"
    echo -e "    ${CYAN}2${NC}) ${BOLD}push${NC}        -- Push local changes -> GitHub"
    echo -e "    ${CYAN}3${NC}) ${BOLD}pull${NC}        -- Pull from GitHub -> local"
    echo -e "    ${CYAN}4${NC}) ${BOLD}backup${NC}      -- Create local backup"
    echo -e "    ${CYAN}5${NC}) ${BOLD}brain-push${NC}  -- Push brain data -> GitHub"
    echo -e "    ${CYAN}6${NC}) ${BOLD}brain-pull${NC}  -- Pull brain data <- GitHub"
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
        echo -e "  ${BOLD}Repo path:${NC} $INSTALL_DIR"
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
