# Docker Parameterization Guide

Complete guide to building and running parameterized Docker images.

## 🎯 Overview

The Docker image supports **three build modes** and **runtime switching** between parsers:

### Build-Time Parameters (Build Args)

Choose what to include in the image:

| Build Arg | Includes | Image Size | Use Case |
|-----------|----------|------------|----------|
| `both` (default) | LLM + ML/OCR | ~800MB | Maximum flexibility |
| `ml` | ML/OCR only | ~750MB | Free, no API costs |
| `llm` | LLM only | ~600MB | Smallest, needs API key |

### Runtime Parameters (Environment Variables)

Choose which parser to use when running:

| Env Var | Value | Uses | Requirements |
|---------|-------|------|--------------|
| `USE_LLM` | `false` | ML/OCR (Tesseract) | Tesseract in image |
| `USE_LLM` | `true` | Gemini LLM | GEMINI_API_KEY set |

---

## 🔨 Building Images

### Option 1: Both Parsers (Most Flexible)

**Build:**
```bash
docker build -t calhero .
# OR explicitly:
docker build --build-arg PARSER_TYPE=both -t calhero .
```

**Run with ML:**
```bash
docker run -e USE_LLM=false calhero
```

**Run with LLM:**
```bash
docker run -e USE_LLM=true -e GEMINI_API_KEY=your_key calhero
```

**Image size:** ~800MB  
**Best for:** Cloud Run (switch parsers without rebuilding)

### Option 2: ML Only (Free Forever)

**Build:**
```bash
docker build --build-arg PARSER_TYPE=ml -t calhero-ml .
```

**Run:**
```bash
docker run calhero-ml
# USE_LLM defaults to false
```

**Image size:** ~750MB  
**Best for:** Production with consistent OCR needs

### Option 3: LLM Only (Smallest)

**Build:**
```bash
docker build --build-arg PARSER_TYPE=llm -t calhero-llm .
```

**Run:**
```bash
docker run -e USE_LLM=true -e GEMINI_API_KEY=your_key calhero-llm
```

**Image size:** ~600MB  
**Best for:** Serverless with fast cold starts

---

## ☁️ Cloud Run Deployment

### Deploy with Both Parsers (Switch at Runtime)

```bash
# Deploy once
gcloud run deploy calhero \
  --source . \
  --allow-unauthenticated \
  --set-env-vars USE_LLM=false \
  --memory 1Gi

# Switch to LLM later (no rebuild!)
gcloud run services update calhero \
  --set-env-vars USE_LLM=true,GEMINI_API_KEY=your_key
```

### Deploy ML Only (Optimized)

```bash
# Build specific image
docker build --build-arg PARSER_TYPE=ml -t gcr.io/PROJECT/calhero .
docker push gcr.io/PROJECT/calhero

# Deploy
gcloud run deploy calhero \
  --image gcr.io/PROJECT/calhero \
  --set-env-vars USE_LLM=false
```

### Deploy LLM Only (Smallest)

```bash
# Build specific image
docker build --build-arg PARSER_TYPE=llm -t gcr.io/PROJECT/calhero-llm .
docker push gcr.io/PROJECT/calhero-llm

# Deploy
gcloud run deploy calhero \
  --image gcr.io/PROJECT/calhero-llm \
  --set-env-vars USE_LLM=true,GEMINI_API_KEY=your_key
```

---

## 🚀 Quick Deployment Script

Use the included deployment script:

```bash
# Deploy to Cloud Run with ML parser
./deploy.sh --type cloudrun --parser ml --project-id my-project

# Deploy with both parsers
./deploy.sh --type cloudrun --parser both --project-id my-project

# Build Docker locally
./deploy.sh --type docker --parser ml
```

---

## 🧪 Testing Different Configurations

### Test ML Parser Locally

```bash
docker build -t calhero .
docker run -it \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -e USE_LLM=false \
  calhero
```

### Test LLM Parser Locally

```bash
docker build -t calhero .
docker run -it \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -e USE_LLM=true \
  -e GEMINI_API_KEY=your_key \
  calhero
```

### Test Cloud Run Service

```bash
# Get service URL
URL=$(gcloud run services describe calhero --format='value(status.url)')

# Test health endpoint
curl $URL/health

# Test ML parser
curl -X POST $URL -F "image=@screenshots/test.png"

# Switch to LLM
gcloud run services update calhero --set-env-vars USE_LLM=true

# Test LLM parser
curl -X POST $URL -F "image=@screenshots/test.png"
```

---

## 🔄 Switching Parsers in Production

### Cloud Run (Zero Downtime)

```bash
# Switch from ML to LLM
gcloud run services update calhero \
  --set-env-vars USE_LLM=true,GEMINI_API_KEY=your_key

# Switch back to ML
gcloud run services update calhero \
  --set-env-vars USE_LLM=false

# Takes ~10 seconds, no downtime
```

### Docker Container (Restart Required)

```bash
# Stop current container
docker stop calhero

# Start with different parser
docker run -d --name calhero \
  -e USE_LLM=true \
  -e GEMINI_API_KEY=your_key \
  calhero
```

---

## 📊 Image Size Comparison

```bash
# Build all three variants
docker build --build-arg PARSER_TYPE=both -t calhero-both .
docker build --build-arg PARSER_TYPE=ml -t calhero-ml .
docker build --build-arg PARSER_TYPE=llm -t calhero-llm .

# Check sizes
docker images | grep calhero

# Typical output:
# calhero-llm    ~600MB
# calhero-ml     ~750MB
# calhero-both   ~800MB
```

---

## 🔧 Advanced Configuration

### Multi-Stage Build (Even Smaller)

For production, use multi-stage builds:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
RUN pip install --user ...

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LLM` | `false` | Which parser to use |
| `GEMINI_API_KEY` | none | Required if USE_LLM=true |
| `PORT` | `8080` | HTTP server port |
| `PARSER_TYPE` | build arg | What's included in image |

### Health Checks

The Docker image includes health checks:

```bash
# Check container health
docker ps --filter "name=calhero" --format "{{.Status}}"

# Manual health check
docker exec calhero curl localhost:8080/health
```

---

## 💡 Best Practices

### For Development

```bash
# Use 'both' build for flexibility
docker build -t calhero .

# Test both parsers easily
docker run -e USE_LLM=false calhero  # Test ML
docker run -e USE_LLM=true calhero   # Test LLM
```

### For Production

**If using Cloud Run:**
```bash
# Deploy 'both', switch at runtime
gcloud run deploy --source . --set-env-vars USE_LLM=false
```

**If using Docker (VPS/home):**
```bash
# Build specific type to save space
docker build --build-arg PARSER_TYPE=ml -t calhero .
```

### For Cost Optimization

1. **Start with ML** (free):
   ```bash
   --set-env-vars USE_LLM=false
   ```

2. **Test with your images** using comparison tool:
   ```bash
   python test_comparison.py
   ```

3. **If ML accuracy >90%**, keep using ML
4. **If ML accuracy <85%**, switch to LLM:
   ```bash
   gcloud run services update calhero --set-env-vars USE_LLM=true
   ```

---

## 🐛 Troubleshooting

### "Tesseract not found"

**Cause:** Built with `PARSER_TYPE=llm` but running with `USE_LLM=false`

**Solution:**
```bash
# Rebuild with ML support
docker build --build-arg PARSER_TYPE=both -t calhero .
```

### "GEMINI_API_KEY not set"

**Cause:** Running with `USE_LLM=true` but no API key

**Solution:**
```bash
docker run -e USE_LLM=true -e GEMINI_API_KEY=your_key calhero
```

### "Module not found: pytesseract"

**Cause:** Built with `PARSER_TYPE=llm`, missing ML dependencies

**Solution:**
```bash
# Rebuild with appropriate parser type
docker build --build-arg PARSER_TYPE=both -t calhero .
```

---

## 📚 Summary

**Build once with `PARSER_TYPE=both`:**
- Most flexible
- Switch parsers at runtime
- Only ~200MB larger than single parser

**Switch parsers with `USE_LLM` environment variable:**
- No rebuild needed
- No downtime on Cloud Run
- Test both approaches easily

**Use deployment script for convenience:**
```bash
./deploy.sh --type cloudrun --parser both --project-id my-project
```

That's it! Maximum flexibility with minimal effort. 🚀
