#!/data/data/com.termux/files/usr/bin/bash
# Upload quantum_mcagi_full.zip to GitHub Releases
REPO="Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-"
ZIP="/storage/emulated/0/Download/quantum_mcagi_full.zip"

if gh release view v1.0.0 --repo "$REPO" > /dev/null 2>&1; then
    gh release upload v1.0.0 "$ZIP" --repo "$REPO" --clobber
else
    gh release create v1.0.0 "$ZIP" --repo "$REPO" --title "Quantum MCAGI Full Release" --notes "By Cory N.B. Blackburn"
fi
