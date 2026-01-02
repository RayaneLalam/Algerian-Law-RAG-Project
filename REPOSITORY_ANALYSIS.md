# Algerian Law RAG Project - Repository Analysis

## Executive Summary

The Algerian Law RAG (Retrieval-Augmented Generation) Project is a production-grade legal information system designed to provide bilingual (French/Arabic) query-response capabilities over Algerian legal documents. The architecture consists of:

- **Backend**: Flask-based REST API with JWT authentication, vector-based semantic search, LLM integration, and persistent conversation management
- **Frontend**: Modern React application with Vite bundler supporting bilingual UI (French/Arabic) and dark/light themes
- **Data Layer**: FAISS vector indices for efficient semantic retrieval, SQLite for user/conversation persistence, JSON-based legal document storage
- **ML Pipeline**: Dual embedding models (French and Arabic), bilingual LLM inference, language detection, and response routing

The notebook (`bilangual-pipeline.ipynb`) implements a complete bilingual RAG pipeline that serves as the reference implementation for integrating into the main application.

---

## Directory Structure & Component Analysis

### Root Level

```
Algerian-Law-RAG-Project/
├── backend/                    # Flask REST API backend
├── frontend/                   # React Vite frontend
├── notebooks/                  # Jupyter notebooks for development
├── data/                       # Data storage and indices
├── fine-tuning translation model/  # Translation model training
├── README.md                   # Project documentation
└── [database files]            # Vector index files
```

---

## Backend (`backend/`)

### Overview
The backend implements a Flask REST API with JWT authentication, vector search, LLM integration, and conversation persistence. It handles:
- User authentication and authorization
- Message processing and routing to search and LLM services
- Vector-based semantic retrieval of legal documents
- Conversation history management
- Streaming responses via Server-Sent Events (SSE)

### Key Files & Structure

#### `run.py`
**Purpose**: Application entry point and server launcher

**Functionality**:
- Initializes Flask application using `create_app()` factory
- Sets up database on startup via `db_setup.init_db(app)`
- Runs Flask server on host `0.0.0.0` port `5000` with debug mode

**Usage**: `python run.py` to start the backend server

---

#### `app/__init__.py`
**Purpose**: Flask application factory and blueprint registration

**Functionality**:
- Creates Flask app instance with configuration
- Loads settings from `app.config.settings` (SECRET_KEY, JWT_SECRET, DATABASE path)
- Registers blueprints:
  - `chat_bp`: Chat and message handling endpoints
  - `auth_bp`: Authentication endpoints (register, login, token refresh)
- Sets up database teardown hooks

**Dependencies**:
- Imports settings module (currently missing, needs creation)
- Depends on `database.db_setup` for initialization

---

#### `database/db_setup.py`
**Purpose**: Database initialization and connection management

**Functionality**:
- **`get_db()`**: Gets or creates SQLite connection stored in Flask `g` object
- **`close_connection(exception)`**: Closes database connection on request cleanup
- **`init_db(app)`**: Creates database schema on application startup

**Database Schema**:

```sql
users
├── id (PRIMARY KEY)
├── username (UNIQUE NOT NULL)
├── email (UNIQUE NOT NULL)
├── password_hash (NOT NULL)
├── role (user|admin, DEFAULT 'user')
└── created_at (TIMESTAMP)

conversations
├── id (PRIMARY KEY)
├── user_id (FOREIGN KEY → users.id)
├── title (TEXT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

messages
├── id (PRIMARY KEY)
├── conversation_id (FOREIGN KEY → conversations.id)
├── role (user|admin|assistant)
├── content (NOT NULL)
└── created_at (TIMESTAMP)
```

**Indices**: Foreign key indices for efficient queries

---

### Authentication Module (`app/auth/`)

#### `auth_routes.py`
**Purpose**: Authentication endpoints and user management

**Endpoints**:
- `POST /auth/register`: Create new user account with role (user or admin)
  - Body: `{username, email, password, role?}`
  - Returns: `{message, user_id, role}`
  - Admin creation rules: First user can be admin OR requires existing admin token

- `POST /auth/login`: Authenticate user and return JWT token
  - Body: `{username, password}`
  - Returns: `{access_token, expires_in, role, user: {id, username, email}}`

- `GET /auth/me`: Get current user profile (requires JWT)
  - Returns: Current user information

**Authorization**: Uses JWT tokens with configurable expiration (default 3600s)

---

#### `auth_models.py`
**Purpose**: User data model operations

**Functions**:
- `create_user(username, email, password, role)`: Create new user with hashed password
- `get_user_by_username(username)`: Retrieve user by username
- `get_user_by_id(user_id)`: Retrieve user by ID
- `verify_password(user, password)`: Verify plaintext password against hash

**Password Security**: Uses bcrypt for password hashing

---

#### `auth_middleware.py`
**Purpose**: JWT token validation middleware

**Decorators**:
- `@jwt_required`: Validates JWT token in Authorization header, populates `g.current_user`
- `@admin_required`: Validates token and checks admin role

**Token Format**: `Authorization: Bearer <jwt_token>`

---

#### `utils.py`
**Purpose**: JWT token generation and decoding

**Functions**:
- `create_access_token(user_id, role, expires_delta)`: Generate signed JWT token
- `decode_token(token)`: Validate and decode JWT token

---

### Chat Module (`app/chat/`)

#### `chat_routes.py`
**Purpose**: Chat and conversation endpoints

**Key Endpoint**: `POST /chat_stream` (protected)
- Accepts: `{message, conversation_id?}`
- Returns: Server-Sent Events (SSE) stream of assistant response chunks
- Creates conversation if none provided
- Saves user message, streams response, persists assistant message

**Workflow**:
1. Extract message and optional conversation_id from request
2. Validate/create conversation for user
3. Insert user message into database
4. Retrieve relevant legal documents via SearchService
5. Stream response via `stream_assistant_reply()` generator
6. Save complete assistant response after streaming completes

---

#### `chat_models.py`
**Purpose**: Conversation and message database operations

**Functions**:
- `create_conversation(user_id, title)`: Create new conversation, return ID
- `get_conversation_for_user(conversation_id, user_id)`: Retrieve conversation with auth check
- `insert_message(conversation_id, role, content)`: Store message in database
- `update_conversation_timestamp(conversation_id)`: Update `updated_at` on new message

---

#### `utils.py`
**Purpose**: Reply generation with streaming

**Functions**:
- `make_reply_stream(received_message, vectors_json_str)`: 
  - Parses retrieved documents JSON
  - Loads prompt template
  - Calls LLM service with formatted prompt
  - Returns streaming generator

- `stream_assistant_reply(message, vectors_json_str, conversation_id)`:
  - Generator that yields SSE-formatted chunks
  - Accumulates full response
  - On completion, saves message to database
  - Handles client disconnections gracefully

---

### Services (`app/services/`)

#### `search_service/search_service.py`
**Purpose**: Vector-based semantic retrieval of legal documents

**Core Functionality**:
- Loads legal documents from JSON file
- Uses sentence-transformers for embedding generation
- Creates and manages FAISS index for fast similarity search
- Handles index persistence and validation

**Key Methods**:
- `__init__(embedding_model)`: Initialize with default multilingual model
- `load_data()`: Load documents and rebuild/validate FAISS index
- `search(query, top_n)`: Encode query and retrieve top-k similar documents
- `_build_vector_db()`: Create FAISS index from all documents
- `_load_vector_db()`: Load existing index and validate integrity

**Data Format**: Expects JSON with documents containing `titre` (title) and `texte` (text) fields

**Embedding Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (multilingual, 384-dim)

---

#### `llm_service/llm_api.py`
**Purpose**: External LLM API integration for response generation

**Configuration**:
- Provider: OpenRouter (https://openrouter.ai/api/v1)
- Model: `google/gemma-3-27b-it:free`
- API Key: Loaded from `app.config.settings.DEEPSEEK_API_KEY`

**Methods**:
- `get_completion(message)`: Send prompt and return full response
- `get_completion_stream(message)`: Stream response tokens as they arrive

**Integration**: Used by chat utils to generate assistant replies

---

### Utilities (`app/utils/`)

#### `prompt_utils.py`
**Purpose**: Prompt template loading and context formatting

**Functions**:
- `_load_prompt_template(path)`: Load prompt template from file
- `_format_context_from_results(results)`: Format retrieved documents for inclusion in prompt

**Template Usage**: Allows customization of system prompts and context presentation

---

### Configuration (Missing)
**Status**: Requires creation

**Expected at**: `app/config/settings.py`

**Required Variables**:
- `SECRET_KEY`: Flask session encryption key
- `JWT_SECRET`: JWT token signing key
- `JWT_ACCESS_TOKEN_EXPIRES`: Token lifetime in seconds
- `DATABASE`: SQLite database file path
- `JSON_AS_ASCII`: JSON encoding flag
- `DEEPSEEK_API_KEY`: OpenRouter API key

---

## Frontend (`frontend/`)

### Overview
Modern React application with Vite bundler, supporting bilingual UI (Arabic/French), dark/light theme switching, and real-time chat with the backend. Built with TailwindCSS for styling and React Icons for UI elements.

### Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable React components
│   │   ├── ChatMessages.jsx
│   │   ├── InputArea.jsx
│   │   └── Sidebar.jsx
│   ├── contexts/           # React Context for state management
│   │   └── LanguageThemeContext.jsx
│   ├── screens/            # Full-page components
│   │   └── WelcomeScreen.jsx
│   ├── App.jsx             # Main application component
│   ├── main.jsx            # React DOM entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML entry point
├── package.json            # Dependencies
├── vite.config.js          # Vite build configuration
├── tailwind.config.js      # TailwindCSS configuration
├── postcss.config.js       # PostCSS configuration
└── eslint.config.js        # Linting configuration
```

---

#### Key Components & Their Roles

##### `App.jsx`
**Purpose**: Root application component managing overall state and layout

**State Management**:
- `messages`: Array of chat messages (user and assistant)
- `isLoading`: Whether LLM is generating response
- `isShowSidebar`: Sidebar visibility toggle
- `isInputCentered`: Centered input on empty chat (moves up when messages appear)
- `conversations`: Array of conversation history
- `currentConversationId`: Currently active conversation

**Key Features**:
- Language and theme context integration
- Conversation persistence via localStorage
- Message management (new chat, send message)
- Layout responsiveness (centered input → expanded chat area transition)

**Sections**:
- Sidebar (conversation history)
- Welcome screen (empty state)
- Chat messages area
- Input area (query submission)

---

##### `components/InputArea.jsx`
**Purpose**: Query input field with send button and formatting

**Features**:
- Textarea with Enter-to-send (Shift+Enter for newline)
- Loading state handling (disabled during response)
- Responsive styling (centered vs. expanded states)
- Dark/light theme support
- Bilingual UI text

**Events**: Calls `onSend()` callback with message text on submit

---

##### `components/ChatMessages.jsx`
**Purpose**: Display conversation history with message formatting

**Features**:
- Renders user and assistant messages
- Markdown support for formatted responses
- Loading indicator during generation
- Auto-scroll to latest message
- Bilingual direction support (RTL for Arabic)

**Styling**: Color-coded messages (user vs. assistant) with theme support

---

##### `components/Sidebar.jsx`
**Purpose**: Navigation and conversation history

**Features**:
- List of previous conversations
- Conversation selection to restore chat
- Delete conversation option
- New chat button
- Theme and language switchers
- Collapsible on mobile

**State**: Receives conversations list and selection callbacks

---

##### `screens/WelcomeScreen.jsx`
**Purpose**: Empty state shown when no messages present

**Content**:
- Application title and description
- Logo/branding
- Quick action suggestions
- Bilingual text

---

##### `contexts/LanguageThemeContext.jsx`
**Purpose**: Global language and theme state management

**Provides**:
- `language`: "ar" (Arabic) or "fr" (French)
- `theme`: "dark" or "light"
- `t(key)`: Translation function for bilingual text
- Setters for language and theme

**Storage**: Persists to localStorage for preference retention

---

### Dependencies

**Key Libraries**:
- `react` / `react-dom`: UI framework
- `react-icons`: Icon library
- `react-markdown`: Markdown rendering for responses
- `remark-gfm`: GitHub-flavored markdown support
- `tailwindcss`: Utility-first CSS framework
- `lucide-react`: Modern icon set

---

## Data Layer (`data/`)

### Structure

```
data/
├── faiss/                          # Vector indices directory
│   ├── algerian_legal...faiss      # FAISS index (binary)
│   ├── algerian_legal...meta       # Index metadata (pickle)
│   ├── algerian_legal..._docs.json # Document collection
│   ├── laws_ar.index               # Arabic index
│   └── laws_ar.index.meta          # Arabic metadata
├── source/                         # Raw source documents
├── structured/                     # Processed/normalized documents
│   └── constitution.json           # Constitutional text
└── [JSON collections]              # Legal document sets
```

### File Formats

**FAISS Indices** (`.faiss`):
- Binary vector index format
- Enables fast similarity search via L2 distance
- Contains millions of document embeddings
- Language-specific: French and Arabic indices separate

**Metadata Files** (`.meta`):
- Pickle-serialized Python objects
- Contain: embedding vectors, document counts, model info
- Used for index validation and state recovery

**Document JSON** (`*_docs.json`):
- UTF-8 JSON format with document collections
- Fields: `titre` (title), `texte` (content), `source_document_type`, `header`, etc.
- One document per JSON array element

---

## Notebooks (`notebooks/`)

### `billangual-pipeline.ipynb` (Reference Implementation)
**Status**: Complete bilingual RAG pipeline reference

**Content**:
1. **Library Setup**: Imports for transformers, torch, FAISS, sentence-transformers
2. **Configuration**: Paths to indices, model names, quantization settings
3. **Language Detection**: 
   - `detect_script()`: Identifies Arabic vs. Latin script
   - `detect_response_language()`: Infers desired output language from query
4. **Embedding Models**:
   - French: `dangvantuan/sentence-camembert-large` (specialized French BERT)
   - Arabic: `paraphrase-multilingual-MiniLM-L12-v2` (multilingual)
5. **LLM Models**:
   - French: `bofenghuang/vigogne-2-7b-chat` (French-tuned 7B)
   - Arabic: `Qwen/Qwen2.5-7B-Instruct` (instruction-tuned 7B)
6. **Key Functions**:
   - `retrieve_documents()`: Bilingual semantic search (retrieves based on response language)
   - `build_context()`: Formats retrieved docs for prompt
   - `generate_french_answer()`: French LLM inference with 4-bit quantization
   - `generate_arabic_answer()`: Arabic LLM inference
   - `bilingual_query()`: Main orchestration function

**Data Flow**:
```
Input Query
    ↓
[Language Detection]
    ↓
[Response Language Inference]
    ↓
[Select Appropriate Embedder + Index]
    ↓
[Semantic Retrieval (Top-K)]
    ↓
[Format Context from Docs]
    ↓
[Route to French or Arabic LLM]
    ↓
[Generate & Stream Response]
    ↓
Output Answer + Sources
```

**Key Innovation**: Routing based on *desired response language*, not query language, allowing cross-lingual QA

---

### Other Notebooks
- `arabic-translation.ipynb`: Arabic-French translation capabilities
- `nlp-project-french-mvp.ipynb`: French MVP implementation

---

## Fine-tuning (`fine-tuning translation model/`)

**Purpose**: Translation model training infrastructure

**Components**:
- `fine-tuning data/`: Training and validation datasets (JSONL format)
- `pipelines/`: Notebooks for LoRA fine-tuning and full training

**Usage**: Not currently integrated into main pipeline; available for future model improvements

---

## Project Dependencies & Configuration

### Backend Requirements (Missing)
**File**: `backend/requirements.txt` (currently empty, needs population)

**Expected Packages**:
```
flask==2.x.x
flask-cors==4.x.x
sentence-transformers==2.x.x
torch==2.x.x
faiss-cpu==1.x.x
transformers==4.x.x
openai==1.x.x
pydantic==2.x.x
python-dotenv==1.x.x
```

### Frontend Dependencies
**File**: `frontend/package.json` (complete)

Key runtime packages:
- react, react-dom (UI)
- react-icons, lucide-react (Icons)
- react-markdown, remark-gfm (Markdown rendering)
- tailwindcss (Styling)

---

## Current Architecture Limitations & Integration Gaps

### Issues to Address

1. **Missing Configuration Module**
   - Backend app imports non-existent `app.config.settings`
   - Need to create settings module with environment variables

2. **No Bilingual Support in Backend**
   - Current search service uses only multilingual model
   - Chat endpoint doesn't detect or route based on language
   - LLM service has no logic to select French vs. Arabic models

3. **Single Search Index**
   - Uses only multilingual embedder, not specialized French/Arabic models
   - Doesn't leverage separate FAISS indices for optimization

4. **No Response Language Routing**
   - Backend LLM service uses single model (Gemma via OpenRouter)
   - Cannot generate French or Arabic responses independently
   - No streaming with bilingual awareness

5. **Frontend-Backend Disconnection**
   - Frontend manages conversations locally (localStorage)
   - Backend has database persistence but frontend doesn't sync
   - No language preference passed to API

6. **Prompt Template Issues**
   - Current template is French-only
   - Needs conditional templates based on response language

7. **Missing LLM Selection Logic**
   - No dual LLM setup (French Vigogne + Arabic Qwen)
   - No local model loading vs. API distinction

---

## Summary

**Current State**: Foundation architecture with Flask backend, React frontend, vector search, and conversation persistence. Single-language, API-based LLM integration.

**Notebook Reference**: Complete bilingual pipeline with language detection, dual embedding models, dual LLMs, and language-aware routing.

**Integration Challenge**: Adapt notebook logic (bilingual detection, dual embeddings, dual LLMs, response routing) into backend services while maintaining API simplicity and frontend bilingual UX.
