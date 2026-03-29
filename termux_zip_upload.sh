#!/data/data/com.termux/files/usr/bin/bash
# ================================================
#  Upload quantum_mcagi_full.zip to GitHub Releases
#  Run this in Termux on your phone.
# ================================================

set -e

ZIP_FILE="/storage/emulated/0/Download/quantum_mcagi_full.zip"
REPO="Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-"

echo "================================="
echo " Quantum MCAGI — Upload Zip"
echo "================================="
echo ""

# Install gh CLI
echo "[1/3] Installing GitHub CLI..."
pkg update -y
pkg install -y gh

# Grant storage access if needed
if [ ! -d "/storage/emulated/0" ]; then
    termux-setup-storage
    echo "Grant storage permission, then re-run this script."
    exit 1
fi

# Check the zip exists
echo "[2/3] Checking zip file..."
if [ ! -f "$ZIP_FILE" ]; then
    echo "ERROR: File not found: $ZIP_FILE"
    exit 1
fi
ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "  Found: $ZIP_FILE ($ZIP_SIZE)"

# Upload to GitHub Release
echo "[3/3] Uploading to GitHub Release..."
echo ""
gh auth login
TAG="v1.0.0"
if gh release view "$TAG" --repo "$REPO" > /dev/null 2>&1; then
    TAG="v1.0.0-$(date +%Y%m%d-%H%M%S)"
    echo "  v1.0.0 already exists, using $TAG"
fi

gh release create "$TAG" "$ZIP_FILE" \
    --repo "$REPO" \
    --title "Quantum MCAGI Full Release" \
    --notes "Full Quantum MCAGI release by Cory N.B. Blackburn - Architecture: RQR³ · Orch-OR · Self-Evolving · No-LLM"

echo ""
echo "================================="
echo " DONE! Your zip is now at:"
echo " https://github.com/$REPO/releases"
echo "================================="
