# Integration Plan: Bilingual RAG Pipeline

## Overview

This document specifies how to integrate the notebook's complete bilingual (Arabic/French) RAG pipeline into the Algerian Law RAG application. The integration will enable:

1. Automatic language detection from user queries
2. Inference request language routing
3. Language-specific document retrieval
4. Dual LLM support (French Vigogne + Arabic Qwen2.5)
5. Cross-lingual question answering

---

## Integration Strategy

### Design Principles

1. **Backward Compatibility**: All changes use optional parameters; existing single-language flows still work
2. **Separation of Concerns**: Language handling isolated in dedicated services
3. **Extensibility**: Easy to add more languages or swap models
4. **Performance**: Lazy-load language-specific models only when needed
5. **Type Safety**: Clear data structures for language metadata throughout pipeline

---

## Detailed Integration Plan

### Phase 1: Infrastructure & Configuration

#### 1.1 Create Configuration Module

**File**: `backend/app/config/settings.py` (NEW)

**Purpose**: Centralize environment and model configuration

**Content**:
- Model paths and API keys
- Vector database paths
- Language-specific model selections
- Quantization parameters
- LLM provider settings

**Key Variables**:
```python
# Authentication
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key')
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))

# Database
DATABASE = os.getenv('DATABASE', './database.db')
JSON_AS_ASCII = False  # Support Arabic/French text

# Vector Database & Embeddings
FRENCH_INDEX_PATH = os.getenv('FRENCH_INDEX_PATH', './data/faiss/algerian_legal...large.faiss')
FRENCH_DOCS_PATH = os.getenv('FRENCH_DOCS_PATH', './data/faiss/algerian_legal..._docs.json')
ARABIC_INDEX_PATH = os.getenv('ARABIC_INDEX_PATH', './data/faiss/laws_ar.index')
ARABIC_META_PATH = os.getenv('ARABIC_META_PATH', './data/faiss/laws_ar.index.meta')

# Embeddings
FRENCH_EMBEDDING_MODEL = 'dangvantuan/sentence-camembert-large'
ARABIC_EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

# LLM Configuration (local or API)
USE_LOCAL_LLMS = os.getenv('USE_LOCAL_LLMS', 'false').lower() == 'true'
FRENCH_LLM_MODEL = os.getenv('FRENCH_LLM_MODEL', 'bofenghuang/vigogne-2-7b-chat')
ARABIC_LLM_MODEL = os.getenv('ARABIC_LLM_MODEL', 'Qwen/Qwen2.5-7B-Instruct')

# API-based LLM fallback
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', DEEPSEEK_API_KEY)

# LLM Parameters
USE_4BIT_QUANTIZATION = os.getenv('USE_4BIT_QUANTIZATION', 'true').lower() == 'true'
TOP_K_RETRIEVAL = int(os.getenv('TOP_K_RETRIEVAL', 3))
MAX_NEW_TOKENS = int(os.getenv('MAX_NEW_TOKENS', 512))

# Device
DEVICE = os.getenv('DEVICE', 'auto')  # 'auto', 'cpu', 'cuda'
```

**Create**: `backend/app/config/__init__.py` (empty init file)

---

#### 1.2 Update Backend Requirements

**File**: `backend/requirements.txt` (MODIFY)

**Content**:
```
flask==2.3.0
flask-cors==4.0.0
sentence-transformers==2.2.2
torch==2.0.1
faiss-cpu==1.7.4
transformers==4.32.0
accelerate==0.21.0
bitsandbytes==0.41.0
pydantic==2.0.0
python-dotenv==1.0.0
openai==1.0.0
pyyaml==6.0
```

**Rationale**: 
- Adds torch for local LLM inference
- Adds bitsandbytes for 4-bit quantization
- Adds accelerate for distributed inference
- Pins versions for reproducibility

---

### Phase 2: Language Detection & Routing

#### 2.1 Create Language Service

**File**: `backend/app/services/language_service/language_service.py` (NEW)

**Purpose**: Centralized language detection and routing logic

**Key Components**:

```python
class LanguageService:
    def detect_script(text: str) -> str:
        """Returns 'arabic' or 'french' based on character prevalence"""
        # Count Unicode ranges:
        # Arabic: U+0600 to U+06FF
        # Latin: standard ASCII ranges
        
    def detect_response_language(query: str) -> str:
        """Infer desired response language from query"""
        # Check for explicit requests: "en arabe", "in arabic", "بالعربية", etc.
        # Fall back to script detection if ambiguous
        
    def get_language_config(language: str) -> LanguageConfig:
        """Return language-specific model and index paths"""
        # Returns: LanguageConfig(embedder_model, index_path, llm_model, prompt_template)
        
    def normalize_language(language: str) -> str:
        """Ensure language code is valid ('ar' or 'fr')"""
```

**Data Structure**:

```python
from typing import TypedDict

class LanguageConfig(TypedDict):
    language: str  # 'ar' or 'fr'
    embedder_model: str
    index_path: str
    docs_path: str
    llm_model: str
    prompt_template_path: str
    max_tokens: int
```

**Integration Points**:
- Chat routes use `detect_response_language()` before search
- Search service uses `get_language_config()` to select embedder
- LLM service uses `get_language_config()` to select model

---

#### 2.2 Create `__init__.py` for Services

**File**: `backend/app/services/__init__.py` (NEW)

Export service classes for easy access from routes

---

### Phase 3: Enhanced Search Service

#### 3.1 Modify Search Service for Bilingual Support

**File**: `backend/app/services/search_service/search_service.py` (MODIFY)

**Changes**:

1. **Dual Index Support**:
   - Load both French and Arabic FAISS indices
   - Select based on language parameter

2. **Language-Aware Search**:
   ```python
   def search(query: str, language: str = 'auto', top_n: int = 3):
       """
       Args:
           query: User query
           language: 'fr', 'ar', or 'auto' (detect)
           top_n: Number of results
       Returns: List[Dict] with documents + language metadata
       """
   ```

3. **Document Metadata**:
   - Add `language` field to retrieved documents
   - Track embedding model used for transparency

4. **Graceful Fallback**:
   - If language index missing, use multilingual model
   - Log warnings for missing indices

---

#### 3.2 New Class: Bilingual Search Service

**File**: `backend/app/services/search_service/bilingual_search_service.py` (NEW)

**Purpose**: Wraps language selection logic around base SearchService

```python
class BilingualSearchService:
    def __init__(self):
        self.french_service = SearchService(FRENCH_EMBEDDING_MODEL, FRENCH_INDEX_PATH)
        self.arabic_service = SearchService(ARABIC_EMBEDDING_MODEL, ARABIC_INDEX_PATH)
        self.language_service = LanguageService()
    
    def search(self, query: str, language: str, top_n: int = 3):
        """Select appropriate service and perform search"""
        service = self.french_service if language == 'fr' else self.arabic_service
        results = service.search(query, top_n)
        # Add language metadata
        return [{'language': language, **doc} for doc in results]
```

---

### Phase 4: Dual LLM Integration

#### 4.1 Create Language-Aware LLM Service

**File**: `backend/app/services/llm_service/bilingual_llm_service.py` (NEW)

**Purpose**: Route inference requests to appropriate LLM (local or API-based)

```python
class BilingualLLMService:
    def __init__(self):
        self.language_service = LanguageService()
        self.use_local_llms = settings.USE_LOCAL_LLMS
        
        if self.use_local_llms:
            self.french_llm = self._load_french_llm()
            self.arabic_llm = self._load_arabic_llm()
        else:
            self.api_client = OpenAI(...)  # OpenRouter API
    
    def generate_completion(self, prompt: str, language: str, stream: bool = False):
        """Route to appropriate LLM based on language"""
        if self.use_local_llms:
            if language == 'fr':
                return self._generate_french_local(prompt, stream)
            else:
                return self._generate_arabic_local(prompt, stream)
        else:
            return self._generate_api(prompt, language, stream)
    
    def _load_french_llm(self):
        """Load Vigogne-2-7B with 4-bit quantization"""
        # Lazy load on first call
        
    def _load_arabic_llm(self):
        """Load Qwen2.5-7B with 4-bit quantization"""
        # Lazy load on first call
    
    def _generate_french_local(self, prompt: str, stream: bool):
        """Generate using local French model"""
        
    def _generate_arabic_local(self, prompt: str, stream: bool):
        """Generate using local Arabic model"""
    
    def _generate_api(self, prompt: str, language: str, stream: bool):
        """Fall back to OpenRouter API with language awareness"""
```

**Key Features**:
- Lazy loading of models (loaded only when needed)
- Streaming support for both local and API models
- Graceful fallback to API if local models unavailable
- Error handling and logging

---

#### 4.2 Update Existing LLM Service

**File**: `backend/app/services/llm_service/llm_api.py` (KEEP BUT EXTEND)

**Changes**:
- Rename to `api_llm_service.py` for clarity
- Keep existing OpenRouter integration
- Add language-aware model selection if API supports multiple models
- Add temperature/parameter adjustments per language

---

### Phase 5: Prompt Templates

#### 5.1 Create Language-Specific Prompts

**File**: `backend/app/prompt_templates/qa_with_context_fr.txt` (NEW)

```
INSTRUCTIONS SYSTEME:
Vous etes un assistant juridique specialise. Repondez en utilisant uniquement le contexte fourni.
Si vous citez le contexte, referencez l'element correspondant (ex: [1], [2]).

QUESTION:
{query}

CONTEXTE LEGAL (top resultats):
{context}

FORMAT DE REPONSE:
- Commencez par une reponse courte (1-3 phrases) en francais
- Citez les elements du contexte avec leurs numeros entre crochets
- Si le contexte ne contient pas la reponse: "Je ne trouve pas l'information demandee dans le contexte."
- Limitez a 200 mots maximum
```

**File**: `backend/app/prompt_templates/qa_with_context_ar.txt` (NEW)

```
تعليمات النظام:
انت مساعد قانوني متخصص. اجب باستخدام السياق المقدم فقط.
إذا قمت بالإشارة إلى السياق، أرجع الى العنصر المقابل (مثال: [1], [2]).

السؤال:
{query}

السياق القانوني (أفضل النتائج):
{context}

صيغة الإجابة:
- ابدأ بإجابة قصيرة (1-3 جمل) باللغة العربية
- استشهد بعناصر السياق برقمها بين قوسين
- إذا لم يكن السياق يحتوي على الإجابة: "لا أجد المعلومات المطلوبة في السياق المقدم"
- حدد الإجابة بـ 200 كلمة كحد أقصى
```

#### 5.2 Create Prompt Utils Enhancement

**File**: `backend/app/utils/prompt_utils.py` (MODIFY)

**New Functions**:
```python
def load_language_prompt_template(language: str, template_path: str):
    """Load language-specific template"""
    
def format_context_from_results(results: List[Dict], language: str):
    """Format context aware of document fields by language"""
    # For French docs: use 'header' and 'content' fields
    # For Arabic docs: use 'titre' and 'texte' fields
```

---

### Phase 6: Chat Route Modifications

#### 6.1 Update Chat Routes for Bilingual Support

**File**: `backend/app/chat/chat_routes.py` (MODIFY)

**Changes to `/chat_stream` endpoint**:

1. **Accept Language Parameter**:
   ```python
   # Request body: {message, conversation_id?, language?}
   language = data.get('language', 'auto')
   if language == 'auto':
       language = language_service.detect_response_language(message)
   ```

2. **Pass Language to Search**:
   ```python
   docs = search_service.search(message, language=language, top_n=top_k)
   ```

3. **Pass Language to LLM**:
   ```python
   for chunk in llm_service.generate_completion(prompt, language=language, stream=True):
       yield chunk
   ```

4. **Store Language in Conversation Metadata**:
   - Add `language` field to messages or conversation
   - Track which language was used for each interaction

**Updated Endpoint Flow**:
```
1. Extract message, conversation_id, optional language from request
2. Detect/normalize response language
3. Retrieve conversation (validate ownership)
4. Insert user message with language metadata
5. Search documents in chosen language
6. Build context from language-specific document fields
7. Load language-specific prompt template
8. Stream response from appropriate LLM model
9. Save assistant message with language metadata
10. Return as SSE stream
```

---

### Phase 7: Frontend Modifications

#### 7.1 Update Language Context

**File**: `frontend/src/contexts/LanguageThemeContext.jsx` (MODIFY)

**Changes**:
1. Track UI language (already done: 'ar', 'fr')
2. Add `queryLanguage` state for explicit query language override
3. Add functions to suggest query language based on input

---

#### 7.2 Enhance Input Area Component

**File**: `frontend/src/components/InputArea.jsx` (MODIFY)

**New Features**:
1. Optional language selector (dropdown or toggle)
2. Display detected language (informational badge)
3. Allow override of auto-detected language
4. Pass language preference to backend

**Updated Message Submission**:
```javascript
const handleSubmit = () => {
    const payload = {
        message: text,
        conversation_id: currentConversationId,
        language: selectedLanguage || 'auto'  // NEW
    };
    // Send to /chat_stream
};
```

---

#### 7.3 Update Chat Messages Component

**File**: `frontend/src/components/ChatMessages.jsx` (MODIFY)

**Changes**:
1. Display language metadata for each message
2. Show which language was used for each assistant response
3. Add visual indicator (AR/FR badge)

---

#### 7.4 Backend Integration Setup

**Create**: `frontend/src/services/apiClient.js` (NEW if not exists)

**Purpose**: Centralize API communication

```javascript
export const chatStream = async (message, conversationId, language = 'auto') => {
    const response = await fetch('/chat_stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            message,
            conversation_id: conversationId,
            language
        })
    });
    return response;
};
```

---

### Phase 8: Database Extensions

#### 8.1 Update Database Schema

**File**: `backend/database/db_setup.py` (MODIFY)

**Schema Changes**:

```sql
-- Add language tracking to messages
ALTER TABLE messages ADD COLUMN language TEXT DEFAULT 'fr' CHECK(language IN ('ar', 'fr'));

-- Add language preference to users
ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'fr' CHECK(preferred_language IN ('ar', 'fr'));

-- Add language tracking to conversations (for analytics)
ALTER TABLE conversations ADD COLUMN primary_language TEXT DEFAULT 'fr';
```

**Backward Compatibility**: Use defaults to avoid breaking existing data

---

## Implementation Order

### Sprint 1: Infrastructure & Configuration
1. Create settings module (`app/config/settings.py`)
2. Create language service
3. Update requirements.txt with new dependencies
4. Update database schema

### Sprint 2: Search & Retrieval
5. Modify search service for dual indices
6. Create bilingual search service wrapper
7. Add integration tests for language routing

### Sprint 3: LLM Integration
8. Create bilingual LLM service (API-based initially)
9. Add local model loading capability (optional)
10. Update chat routes to use new services
11. Create language-specific prompt templates

### Sprint 4: Frontend Integration
12. Update language context
13. Modify input and chat components
14. Create API client service
15. Add language selector UI

### Sprint 5: Testing & Polish
16. End-to-end tests (Arabic and French flows)
17. Performance optimization
18. Error handling and logging
19. Documentation updates

---

## File Changes Summary

### New Files to Create (14)
- `backend/app/config/__init__.py`
- `backend/app/config/settings.py`
- `backend/app/services/__init__.py`
- `backend/app/services/language_service/__init__.py`
- `backend/app/services/language_service/language_service.py`
- `backend/app/services/search_service/bilingual_search_service.py`
- `backend/app/services/llm_service/bilingual_llm_service.py`
- `backend/app/prompt_templates/qa_with_context_ar.txt`
- `backend/app/prompt_templates/qa_with_context_fr.txt`
- `frontend/src/services/apiClient.js` (if not exists)
- Test files for new services

### Files to Modify (8)
- `backend/app/__init__.py` - Import config module
- `backend/requirements.txt` - Add dependencies
- `backend/app/chat/chat_routes.py` - Language routing
- `backend/app/utils/prompt_utils.py` - Language-aware formatting
- `backend/app/services/search_service/search_service.py` - Dual index support
- `backend/app/services/llm_service/llm_api.py` - Keep and extend
- `backend/database/db_setup.py` - Schema additions
- `frontend/src/components/InputArea.jsx` - Language selector
- `frontend/src/components/ChatMessages.jsx` - Language display
- `frontend/src/contexts/LanguageThemeContext.jsx` - Language tracking

### Configuration Files
- `.env` - Environment variables (for local development)
- `.env.production` - Production configuration

---

## Data Flow Diagram

### Current (Single-Language) Flow:
```
Query (FR or AR) → Auto-detected as FR → 
French FAISS Index (multilingual embedder) → 
Retrieved docs → API LLM (Gemma) → 
Response (may not match query language) → User
```

### Target (Bilingual) Flow:
```
Query (FR or AR)
    ↓
[Language Detection Service]
    ↓ (auto or explicit)
Response Language (AR or FR)
    ↓
[Select Language Config]
    ├─ Embedder: French CamemBERT OR Multilingual MiniLM
    ├─ Index: French FAISS OR Arabic FAISS
    ├─ LLM: Vigogne OR Qwen2.5
    └─ Prompt Template: French OR Arabic
    ↓
[Bilingual Search Service]
    ↓
Retrieved Documents (language-marked)
    ↓
[Format Context (language-aware)]
    ↓
[Load Appropriate Prompt Template]
    ↓
[Bilingual LLM Service]
    ├─ If local: Use local model + 4-bit quantization
    └─ If API: Route to appropriate model
    ↓
Response Stream (correct language guaranteed)
    ↓
[Store Language Metadata]
    ↓
User (with language metadata)
```

---

## Backward Compatibility

All changes maintain backward compatibility:

1. **API Contracts**: Existing endpoints accept optional language parameter (defaults to auto-detection)
2. **Database**: Existing records unaffected; new schema fields have defaults
3. **Frontend**: Works with or without language selector
4. **Fallbacks**: If language services unavailable, system reverts to single-language behavior

---

## Performance Considerations

1. **Model Loading**:
   - Lazy load large LLM models (only on first inference)
   - Cache loaded models in memory for subsequent requests
   - Use 4-bit quantization to reduce memory footprint (7B → ~2GB)

2. **Vector Search**:
   - Keep separate indices (no cross-lingual contamination)
   - Use efficient FAISS indexing (already in place)

3. **Streaming**:
   - Stream responses to user immediately (reduce perceived latency)
   - Background process: save to database after streaming

4. **Multi-Threading**:
   - Each language service can run independently
   - Use ThreadPoolExecutor for parallel model operations if needed

---

## Testing Strategy

### Unit Tests
- Language detection (Arabic vs. French)
- Response language inference (explicit vs. implicit)
- Service initialization and routing

### Integration Tests
- Full flow: French query → French response
- Full flow: Arabic query → Arabic response
- Cross-lingual: French query → Arabic response (explicit)
- Fallback: Missing index → multilingual model

### Performance Tests
- Model loading time
- Search latency by language
- LLM inference latency by model
- End-to-end response time

### User Acceptance Tests
- Bilingual UI functionality
- Conversation history with mixed languages
- Language preference persistence

---

## Deployment Considerations

1. **Model Files**: Download and cache large models before deployment
2. **FAISS Indices**: Ensure both French and Arabic indices available
3. **Environment Variables**: Set all language-specific paths
4. **GPU Resources**: Plan memory allocation if using local models
5. **Monitoring**: Track language distribution and model performance per language

---

## Future Enhancements

1. **More Languages**: Add support for other languages (Tamazight, English)
2. **Fine-tuned Models**: Fine-tune LLMs on Algerian legal domain
3. **Multi-turn Context**: Maintain language consistency across conversation turns
4. **User Preferences**: Save language preferences per user
5. **Analytics**: Track language usage patterns
6. **A/B Testing**: Compare response quality between models and languages

