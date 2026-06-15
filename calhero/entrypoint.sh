#!/bin/bash
# Docker entrypoint script
# - No arguments: Start HTTP server (for Cloud Run, Apps Script, or any HTTP client)
# - With arguments: Run CLI mode (for local file processing)

set -e

echo "🚀 Calendar Parser Starting..."
echo "   Parser Type Build: $PARSER_TYPE"
echo "   USE_LLM: $USE_LLM"

# Validate configuration
if [ "$USE_LLM" = "true" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: GEMINI_API_KEY not set but USE_LLM=true"
    exit 1
fi

if [ "$USE_LLM" = "false" ]; then
    if ! command -v tesseract &> /dev/null; then
        echo "❌ ERROR: Tesseract not installed but USE_LLM=false"
        exit 1
    fi
    tesseract --version | head -1
fi

# Choose mode based on arguments (environment-agnostic)
if [ $# -eq 0 ]; then
    # No arguments = HTTP server mode
    echo "   Mode: HTTP Server"
    echo "   Port: ${PORT:-8080}"
    echo "   Starting Flask HTTP server..."
    exec python cloud_run_service.py
else
    # Arguments provided = CLI mode
    echo "   Mode: CLI (processing files)"
    
    if [ "$USE_LLM" = "true" ]; then
        echo "   Using: Gemini LLM Parser"
        exec python calhero.py "$@"
    else
        echo "   Using: ML/OCR Parser (Tesseract)"
        exec python calhero_ml.py "$@"
    fi
fi
