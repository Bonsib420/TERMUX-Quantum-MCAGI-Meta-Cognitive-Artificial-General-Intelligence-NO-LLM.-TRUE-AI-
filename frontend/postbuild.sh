#!/bin/bash
# Remove crossorigin attributes from generated index.html
sed -i 's/ crossorigin//g' dist/index.html
echo "✓ Stripped crossorigin from index.html"
