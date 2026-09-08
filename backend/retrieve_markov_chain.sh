#!/bin/bash
# Retrieve the recovered Markov chain from Google Drive and decompress it

echo "Retrieving lost_markov_chain_5224669states_apr2026.json.gz from Google Drive..."
rclone copy "gdrive 666:Quantum Cloud/lost_markov_chain_5224669states_apr2026.json.gz" ./ -P

echo "Decompressing markov chain file..."
gunzip -v lost_markov_chain_5224669states_apr2026.json.gz

echo "Done! File decompressed to lost_markov_chain_5224669states_apr2026.json"
echo ""
echo "File details:"
ls -lh lost_markov_chain_5224669states_apr2026.json
