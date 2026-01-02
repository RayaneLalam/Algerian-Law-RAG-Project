# Environment Setup Guide

This guide explains how to configure environment variables for the Algerian Law RAG application.

## Backend Configuration

### File: `backend/.env`

Copy `backend/.env.example` to `backend/.env` and update the values:

```bash
cp backend/.env.example backend/.env
```

### Required Variables

#### Authentication & Security
```
SECRET_KEY=<generate-a-secure-random-string>
JWT_SECRET=<generate-a-secure-jwt-secret>
JWT_ACCESS_TOKEN_EXPIRES=3600  # Token validity in seconds
```

#### Database
```
DATABASE=./database.db  # SQLite database file path
JSON_AS_ASCII=false     # Support Arabic/French characters
```

#### Vector Databases & Embeddings

**French Models**:
```
FRENCH_INDEX_PATH=./data/faiss/algerian_legal...large.faiss
FRENCH_DOCS_PATH=./data/faiss/algerian_legal..._docs.json
```

**Arabic Models**:
```
ARABIC_INDEX_PATH=./data/faiss/laws_ar.index
ARABIC_META_PATH=./data/faiss/laws_ar.index.meta
```

Ensure these files are available in the `data/faiss/` directory before starting the application.

#### LLM Configuration

**Option 1: Use API-Based LLM (Recommended for Initial Setup)**
```
USE_LOCAL_LLMS=false
OPENROUTER_API_KEY=<your-openrouter-api-key>
DEFAULT_LLM_MODEL=google/gemma-3-27b-it:free
```

Get an OpenRouter API key at: https://openrouter.ai/

**Option 2: Use Local Models (Requires GPU)**
```
USE_LOCAL_LLMS=true
FRENCH_LLM_MODEL=bofenghuang/vigogne-2-7b-chat
ARABIC_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
USE_4BIT_QUANTIZATION=true
DEVICE=auto  # or 'cuda' for GPU
```

Requirements for local models:
- CUDA-capable GPU with at least 16GB VRAM (with 4-bit quantization)
- PyTorch with CUDA support
- bitsandbytes library

#### LLM Parameters
```
TOP_K_RETRIEVAL=3           # Number of documents to retrieve per query
MAX_NEW_TOKENS_FR=512       # Max tokens for French responses
MAX_NEW_TOKENS_AR=1024      # Max tokens for Arabic responses
LLM_TEMPERATURE=0.7         # Creativity level (0.0-1.0)
```

## Frontend Configuration

### File: `frontend/.env.local`

Copy `frontend/.env.example` to `frontend/.env.local`:

```bash
cp frontend/.env.example frontend/.env.local
```

### Required Variables

```
VITE_API_URL=http://localhost:5000  # Backend API URL
```

For production:
```
VITE_API_URL=https://api.yourdomain.com
```

## Installation & Startup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run server
python run.py
```

Server will be available at: `http://localhost:5000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local if needed

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Troubleshooting

### 1. Missing FAISS Indices

**Error**: "French index not found" or "Arabic index not available"

**Solution**: 
- Ensure FAISS index files exist in `data/faiss/` directory
- Update paths in `.env` to match your data location
- Verify file permissions

### 2. LLM API Errors

**Error**: "API client not configured" or OpenRouter errors

**Solution**:
- Verify `OPENROUTER_API_KEY` is set correctly
- Check API key has sufficient credits
- Ensure backend can reach API: `curl https://openrouter.ai/api/v1/models`

### 3. Local Model Loading Failures

**Error**: "Failed to load French LLM" or CUDA out of memory

**Solution**:
- Ensure 4-bit quantization is enabled: `USE_4BIT_QUANTIZATION=true`
- Verify CUDA/GPU availability: `python -c "import torch; print(torch.cuda.is_available())"`
- Fall back to API-based LLM: set `USE_LOCAL_LLMS=false`

### 4. Database Issues

**Error**: "Database locked" or connection errors

**Solution**:
- Delete stale `database.db` file
- Ensure `DATABASE` path is writable
- Check no other process is using the database

### 5. Frontend API Connection Issues

**Error**: CORS errors or "Failed to fetch"

**Solution**:
- Verify `VITE_API_URL` points to running backend
- Check backend is running: `curl http://localhost:5000`
- Verify network connectivity between frontend and backend

## Production Deployment

For production deployment, update:

1. **Backend `.env`**:
   - Set `SECRET_KEY` and `JWT_SECRET` to secure random values
   - Use production OPENROUTER_API_KEY
   - Set `FLASK_ENV=production`

2. **Frontend `.env.local`**:
   - Set `VITE_API_URL` to production API domain
   - Build: `npm run build`

3. **Security**:
   - Use HTTPS/SSL certificates
   - Configure CORS properly
   - Set appropriate database permissions
   - Use environment secrets manager (AWS Secrets, etc.)

## Security Notes

- Never commit `.env` files to version control
- Rotate API keys regularly
- Use strong SECRET_KEY and JWT_SECRET values
- Restrict database file permissions (chmod 600)
- Use HTTPS in production
- Implement rate limiting
- Regular security audits

