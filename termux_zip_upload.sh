#!/data/data/com.termux/files/usr/bin/bash
# Upload quantum_mcagi_full.zip to GitHub Releases
REPO="Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-"
ZIP="/storage/emulated/0/Download/quantum_mcagi_full.zip"
TAG="v1.0.0"

if [ ! -f "$ZIP" ]; then
    echo "File not found: $ZIP"
    exit 1
fi

if gh release view "$TAG" --repo "$REPO" > /dev/null 2>&1; then
    echo "Release exists, uploading zip..."
    gh release upload "$TAG" "$ZIP" --repo "$REPO" --clobber
else
    echo "Creating release and uploading zip..."
    gh release create "$TAG" "$ZIP" --repo "$REPO" \
        --title "Quantum MCAGI Full Release" \
        --notes "By Cory N.B. Blackburn"
fi
