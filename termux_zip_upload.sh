#!/data/data/com.termux/files/usr/bin/bash
# Upload quantum_mcagi_full.zip to GitHub Releases
# Retries automatically on TLS/network errors
REPO="Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-"
ZIP="/storage/emulated/0/Download/quantum_mcagi_full.zip"
TAG="v1.0.0"
MAX_RETRIES=5
RETRY_DELAY=10

if [ ! -f "$ZIP" ]; then
    echo "Error: File not found: $ZIP"
    exit 1
fi

attempt=1
while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "=== Attempt $attempt of $MAX_RETRIES ==="

    if gh release view "$TAG" --repo "$REPO" > /dev/null 2>&1; then
        echo "Release exists, uploading zip..."
        if gh release upload "$TAG" "$ZIP" --repo "$REPO" --clobber; then
            echo "Upload successful!"
            exit 0
        fi
    else
        echo "Creating release and uploading zip..."
        if gh release create "$TAG" "$ZIP" --repo "$REPO" \
            --title "Quantum MCAGI Full Release" \
            --notes "By Cory N.B. Blackburn"; then
            echo "Release created and upload successful!"
            exit 0
        fi
    fi

    echo "Failed (likely TLS/network error). Waiting ${RETRY_DELAY}s before retry..."
    sleep "$RETRY_DELAY"
    attempt=$((attempt + 1))
done

echo "All $MAX_RETRIES attempts failed. Tips:"
echo "  1. Connect to stable WiFi (not mobile data)"
echo "  2. Run: pkg upgrade -y (updates TLS libraries)"
echo "  3. Try again: bash termux_zip_upload.sh"
exit 1
