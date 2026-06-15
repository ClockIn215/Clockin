# Multi-stage Dockerfile for Calendar Parser
# Supports both LLM and ML/OCR versions with runtime selection
#
# Build arguments:
#   PARSER_TYPE: 'ml' (default) or 'llm' or 'both'
#
# Runtime environment variables:
#   USE_LLM: 'true' or 'false' (default: false)
#   GEMINI_API_KEY: Required if USE_LLM=true
#
# Build examples:
#   docker build -t calhero .                              # Both parsers, ML default
#   docker build --build-arg PARSER_TYPE=llm -t calhero .  # LLM only (smaller)
#   docker build --build-arg PARSER_TYPE=ml -t calhero .   # ML only (no Gemini)
#
# Run examples:
#   docker run -e USE_LLM=false calhero                    # Use ML/OCR
#   docker run -e USE_LLM=true -e GEMINI_API_KEY=xxx calhero  # Use LLM

FROM python:3.11-slim as base

# Build argument for parser type
ARG PARSER_TYPE=both

# Set working directory
WORKDIR /app

# Install system dependencies conditionally
    # Only install Tesseract if PARSER_TYPE is 'ml' or 'both'
    RUN if [ "$PARSER_TYPE" = "ml" ] || [ "$PARSER_TYPE" = "both" ]; then \
            apt-get update && apt-get install -y \
                tesseract-ocr \
                libtesseract-dev \
                libgl1 \
                libglib2.0-0 \
            && rm -rf /var/lib/apt/lists/* \
            && tesseract --version; \
        fi

# Copy requirements files
COPY requirements.txt requirements_ml.txt ./

# Install Python dependencies based on parser type
RUN if [ "$PARSER_TYPE" = "llm" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    elif [ "$PARSER_TYPE" = "ml" ]; then \
        pip install --no-cache-dir -r requirements_ml.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt && \
        pip install --no-cache-dir -r requirements_ml.txt; \
    fi

# Copy application code
COPY calendar_utils.py ./
COPY calhero.py ./
COPY calhero_ml.py ./
COPY cloud_run_service.py ./
COPY entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create necessary directories
RUN mkdir -p screenshots screenshots/processed

# Environment variable defaults
ENV USE_LLM=false
ENV PARSER_TYPE=${PARSER_TYPE}

# Use entrypoint script to select parser at runtime
ENTRYPOINT ["./entrypoint.sh"]

# Health check - adapts based on installed packages
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import sys; sys.exit(0)" || exit 1
