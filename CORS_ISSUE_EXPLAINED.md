# Why "Failed to Fetch" Error - CORS Explanation

## The Problem

Frontend on **http://localhost:5174** was trying to call Backend on **http://localhost:5000**.

Even though both were running, the browser was **blocking the request** at the network level due to **CORS (Cross-Origin Resource Sharing)** policy.

The request **never reached the backend** - the browser stopped it before sending it.

That's why:
- ❌ No print statements appeared in backend terminal
- ❌ No error messages appeared in backend logs
- ❌ Frontend showed "Error: Failed to fetch"

---

## Why This Happened

### Before (No CORS)
```
Frontend (localhost:5174)
    ↓ tries to fetch
Backend (localhost:5000)
    ↓
BROWSER BLOCKS IT ✗ (Different origins!)
    ↓
Never reaches backend
```

### After (With CORS)
```
Frontend (localhost:5174)
    ↓ tries to fetch
Backend (localhost:5000)
    ↓
Backend sends CORS headers ✓
    ↓
Browser allows it ✓
    ↓
Request reaches backend, print statement shows up!
```

---

## What Was Fixed

### 1. Added CORS to Backend
**File: `backend/app/__init__.py`**
```python
from flask_cors import CORS

# Enable CORS for frontend connections
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

This tells the browser: **"It's OK to accept requests from these frontend origins"**

### 2. Added Demo Endpoint (No Auth Required)
**File: `backend/app/chat/chat_routes.py`**
```python
@chat_bp.route("/chat_stream_demo", methods=["POST"])
def chat_stream_demo():
    """No JWT required - for testing without login"""
    print("chat_stream_demo called")  # Now this will appear!
```

### 3. Frontend Routes to Demo Endpoint
**File: `frontend/src/services/apiClient.js`**
```javascript
const endpoint = token ? "/chat_stream" : "/chat_stream_demo";
```

If no auth token → use `/chat_stream_demo` (for testing)
If has auth token → use `/chat_stream` (protected endpoint)

---

## How to Test Now

1. **Restart Backend** (to apply CORS changes)
   ```bash
   cd backend
   python run.py
   ```

2. **Backend Terminal Should Show:**
   ```
   * Running on http://127.0.0.1:5000
   * CORS enabled for: ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000']
   ```

3. **Send a message from frontend**

4. **Backend terminal NOW shows:**
   ```
   chat_stream_demo called
   [DEMO] Processing query in language: fr
   ```

---

## Technical Details: CORS Flow

### What is CORS?

CORS is a browser security feature. When JavaScript from one origin (localhost:5174) tries to fetch from another origin (localhost:5000):

1. Browser sends **OPTIONS preflight request** first
2. Backend responds with CORS headers:
   ```
   Access-Control-Allow-Origin: http://localhost:5174
   Access-Control-Allow-Methods: GET, POST, OPTIONS
   Access-Control-Allow-Headers: Content-Type, Authorization
   ```
3. Browser checks the response
4. If allowed → sends actual request ✓
5. If not allowed → shows "Failed to fetch" error ✗

---

## Summary

| Before | After |
|--------|-------|
| ❌ No CORS configured | ✅ CORS enabled |
| ❌ Request blocked by browser | ✅ Request reaches backend |
| ❌ No print/logs in backend | ✅ Print statements appear |
| ❌ Frontend error "Failed to fetch" | ✅ Real responses from backend |

**Now the frontend can properly communicate with the backend!**
