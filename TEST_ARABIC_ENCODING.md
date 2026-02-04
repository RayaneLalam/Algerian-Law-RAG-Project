# Arabic Text Encoding Fix - Test Guide

## Problem Fixed
Arabic responses were appearing corrupted with garbled text and spacing issues:
```
❌ BEFORE: "الل غات الرسم ية" (garbled with spaces between letters)
✅ AFTER: "اللغات الرسمية" (proper Arabic text)
```

## Root Causes Identified & Fixed

### 1. **Backend SSE Encoding Issue** ✅ FIXED
**File:** `backend/app/chat/utils.py`

**Problem:**
```python
# ❌ BEFORE: Sending raw text without JSON encoding
yield f"data: {chunk}\n\n"  # Arabic characters corrupted in transit
```

**Solution:**
```python
# ✅ AFTER: Proper JSON encoding with ensure_ascii=False
encoded_chunk = json.dumps({'chunk': chunk}, ensure_ascii=False)
yield f"data: {encoded_chunk}\n\n"  # Arabic properly preserved
```

### 2. **Frontend SSE Parsing Issue** ✅ FIXED
**File:** `frontend/src/App.jsx`

**Problem:**
```javascript
// ❌ BEFORE: Treating JSON lines as raw text
for (const line of lines) {
  if (line === "[DONE]") break;
  displayedText += line + " ";  // Concatenating without parsing JSON
}
```

**Solution:**
```javascript
// ✅ AFTER: Properly parsing JSON with error handling
for (const line of lines) {
  try {
    const parsed = JSON.parse(line);
    const text = parsed.chunk || parsed.error || "";
    displayedText += text;  // Uses actual content from JSON
  } catch (e) {
    // Fallback for backward compatibility
    displayedText += line + " ";
  }
}
```

### 3. **UTF-8 Encoding in Backend Response Headers**
**File:** `backend/app/chat/chat_routes.py`

Confirmed proper headers are already set:
```python
headers={
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "X-Language": language
}
# Note: Content-Type is implicitly text/event-stream with UTF-8
```

## Files Modified

1. ✅ `backend/app/chat/utils.py`
   - Fixed `stream_assistant_reply()` - proper JSON encoding
   - Fixed `stream_assistant_reply_demo()` - proper JSON encoding

2. ✅ `frontend/src/App.jsx`
   - Fixed SSE parsing logic to decode JSON properly
   - Added fallback for backward compatibility

## How to Test

### Test 1: Direct Arabic Search (Backend)
```bash
cd backend
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from app.services.search_service.bilingual_search_service import BilingualSearchService

search = BilingualSearchService()
results = search.search("اللغات الرسمية", language='ar', top_k=2)
print(f"Found {len(results)} results")
for r in results:
    print(f"Content: {r.get('content', '')[:100]}")
EOF
```

### Test 2: API Test (With curl)
```bash
curl -X POST http://localhost:5000/chat_stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "اللغات الرسمية", "language": "ar"}'
```

Expected output (properly formatted Arabic):
```
data: {"chunk":"اللغات الرسمية في الجزائر هي العربية..."}
data: {"chunk":"المزيد من المعلومات..."}
data: {"status": "[DONE]"}
```

### Test 3: Frontend Chat (Manual)
1. Start backend: `cd backend && python3 run.py`
2. Start frontend: `cd frontend && npm run dev`
3. Send Arabic query: "ما هي اللغات الرسمية؟"
4. Verify response displays cleanly without garbled text

## Expected Behavior After Fix

### Arabic Query
```
User: "ما هي اللغات الرسمية في الدستور الجزائري؟"

Bot Response:
"اللغات الرسمية في الدستور الجزائري هي العربية والفرنسية.
[المصادر]
Article 3 - Constitution algérienne"
```

### French Query (Ensures we didn't break it)
```
User: "Quelles sont les langues officielles?"

Bot Response:
"Les langues officielles en Algérie sont l'arabe et le français 
selon l'article 3 de la Constitution algérienne.
[SOURCES]
Article 3 - Constitution"
```

## Technical Details

### Why `ensure_ascii=False` is Critical
- Without it: `{"chunk": "اللغات"}` → `{"chunk": "\u0627\u0644\u0644\u063a\u0627\u062a"}`
- With it: `{"chunk": "اللغات"}` → stays as Arabic characters
- Frontend can parse directly without Unicode escape sequences

### SSE Format Requirements
- Each line must start with `data: `
- Followed by JSON string
- Ends with `\n\n`
- Frontend parses by splitting on `\n`, filtering for `data:` prefix

### Character Encoding Path
```
Backend (Arabic text) 
  → JSON stringify with ensure_ascii=False
  → UTF-8 bytes in HTTP response
  → Frontend TextDecoder("utf-8")
  → JSON parse
  → Display as proper Arabic
```

## Rollback Instructions
If issues occur, revert these files:
```bash
git checkout backend/app/chat/utils.py
git checkout frontend/src/App.jsx
```

## Verification Checklist
- [ ] Backend starts without errors
- [ ] Arabic search returns documents
- [ ] Frontend connects to backend
- [ ] Arabic text displays without garbling
- [ ] Sources are properly cited
- [ ] French queries still work
- [ ] Streaming appears smooth
