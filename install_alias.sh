#!/data/data/com.termux/files/usr/bin/bash
# Add 'mcagi' alias to .bashrc
ALIAS_LINE='alias mcagi="bash ~/Quantum_MCAGI_NO_LLM/start.sh"'
if ! grep -q "mcagi" "$HOME/.bashrc" 2>/dev/null; then
    echo "$ALIAS_LINE" >> "$HOME/.bashrc"
    echo "✓ Added 'mcagi' alias. Run: source ~/.bashrc"
    echo "  Then just type: mcagi"
else
    echo "✓ 'mcagi' alias already exists"
fi
