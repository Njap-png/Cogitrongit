#!/bin/bash
# Build PHANTOM 3B LLM from Ollama
#
# Usage: bash build_phantom.sh
#
# This creates "phantom" model - your own 3B cybersecurity assistant
# that runs locally without external API calls.

echo "Building PHANTOM 3B LLM..."
echo "First ensuring llama3.1:3b is available..."
ollama pull llama3.1:3b 2>/dev/null || echo "llama3.1:3b already present"

echo "Creating PHANTOM model..."
ollama create phantom -f phantom.Modelfile

echo ""
echo "PHANTOM model created successfully!"
echo ""
echo "To use PHANTOM:"
echo "  1. Start Ollama: ollama serve"
echo "  2. Run: phantom (or python phantom.py)"
echo ""
echo "Run 'ollama list' to verify phantom model exists"