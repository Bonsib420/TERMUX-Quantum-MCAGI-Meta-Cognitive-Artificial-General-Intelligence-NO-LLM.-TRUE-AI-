#!/bin/bash
FILES=$(ls *.py | tr '\n' ', ')
echo "Project Context: Quantum MCAGI Backend. Files available: $FILES"
tgpt -i
