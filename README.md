# Algerian Law RAG Project

A comprehensive bilingual Retrieval-Augmented Generation (RAG) system for Algerian legal documents, supporting both French and Arabic languages with advanced search capabilities, authentication, and real-time chat interface.

## Features

### Core Functionality
- **Bilingual Support**: Native French and Arabic language processing
- **Intelligent Search**: FAISS-powered vector search with semantic understanding
- **Real-time Chat**: Streaming responses with Server-Sent Events (SSE)
- **Authentication**: JWT-based user authentication and session management
- **Conversation Management**: Persistent chat history and conversation threading
- **Auto-Recovery**: Intelligent 404 error handling with seamless conversation recovery

### AI & ML Capabilities
- **Language Detection**: Automatic query language identification
- **Dual Embedding Models**: Specialized French (CamemBERT) and Arabic (Multilingual) embedders
- **Smart Fallback**: Multilingual embedder fallback for robust search
- **Fine-tuned Translation**: Custom translation pipeline for legal terminology
- **Quantized Models**: Optimized model loading for efficient performance

### User Experience
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Dark/Light Theme**: User preference-based theming
- **RTL Support**: Right-to-left layout for Arabic content
- **Toast Notifications**: User-friendly error and status messages
- **Conversation Sidebar**: Easy navigation between chat sessions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│  • Authentication Context  • Language/Theme Context        │
│  • Chat Interface         • Conversation Management        │
│  • Toast Notifications    • Responsive Design              │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/SSE
┌─────────────────┴───────────────────────────────────────────┐
│                 Backend (Flask)                            │
├─────────────────────────────────────────────────────────────┤
│  API Layer:                                                │
│  • Authentication Routes   • Chat Streaming Routes         │
│  • Conversation CRUD      • Test Endpoints                 │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                 │
│  • BilingualSearchService • LanguageService                │
│  • BilingualLLMService    • Authentication Service         │
├─────────────────────────────────────────────────────────────┤
│  Data Layer:                                               │
│  • SQLite Database        • FAISS Indices                  │
│  • Document Collections   • Model Cache                    │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Algerian-Law-RAG-Project/
├── README.md                          # This file
├── backend/                           # Flask API server
│   ├── run.py                        # Application entry point
│   ├── requirements.txt              # Python dependencies
│   ├── app/
│   │   ├── __init__.py              # Flask app factory
│   │   ├── config/
│   │   │   └── settings.py          # Configuration management
│   │   ├── auth/                    # Authentication module
│   │   │   ├── auth_routes.py       # Auth endpoints
│   │   │   ├── auth_middleware.py   # JWT middleware
│   │   │   └── auth_models.py       # User models
│   │   ├── chat/                    # Chat module
│   │   │   ├── chat_routes.py       # Chat endpoints
│   │   │   ├── chat_models.py       # Conversation models
│   │   │   └── utils.py             # Streaming utilities
│   │   ├── services/                # Business logic
│   │   │   ├── language_service/    # Language detection
│   │   │   ├── search_service/      # Vector search
│   │   │   └── llm_service/         # LLM generation
│   │   └── utils/
│   ├── database/
│   │   └── db_setup.py              # Database initialization
│   └── data/                        # Data files and indices
├── frontend/                         # React application
│   ├── package.json                 # Node dependencies
│   ├── vite.config.js              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS config
│   ├── src/
│   │   ├── App.jsx                 # Main application component
│   │   ├── main.jsx                # React entry point
│   │   ├── components/             # Reusable components
│   │   ├── contexts/               # React contexts
│   │   ├── services/               # API clients
│   │   └── screens/                # Page components
│   └── public/
├── evaluation-interface/             # Evaluation dashboard
├── fine-tuning translation model/    # Translation fine-tuning
└── notebooks/                       # Jupyter notebooks
```

## Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** for version control
- **CUDA** (optional, for GPU acceleration)

### Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd Algerian-Law-RAG-Project
   ```

2. **Backend Setup**
   ```bash
   cd backend
   
   # Create virtual environment
   python3 -m venv venv  # Linux/macOS
   python -m venv venv   # Windows
   
   # Activate virtual environment
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate        # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Initialize database
   python database/db_setup.py
   
   # Download and cache models manually (IMPORTANT)
   # This step downloads all required models to local cache before first use
   # Models include: French CamemBERT, Arabic multilingual, and LLM models
   python download_models.py
   
   # Alternative model download scripts (if available):
   # python download_models_2.py
   # bash download_models.sh
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Build for production (optional)
   npm run build
   ```

### Running the Application

1. **Start Backend Server**
   ```bash
   cd backend
   source venv/bin/activate  # Activate virtual environment
   python run.py
   ```
   Server will start at `http://localhost:5000`

2. **Start Frontend Development Server**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will start at `http://localhost:5173`

3. **Access the Application**
   - Open your browser to `http://localhost:5173`
   - Register a new account or login
   - Start chatting with the AI assistant

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Backend Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///algerian_law_rag.db

# Model Configuration
COMPUTE_DEVICE=cuda  # or 'cpu'
FRENCH_EMBEDDING_MODEL=dangvantuan/sentence-camembert-large
ARABIC_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# API Configuration
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=your-jwt-secret-here
JWT_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration

Create a `.env` file in the frontend directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:5000

# Feature Flags
VITE_ENABLE_REGISTRATION=true
VITE_ENABLE_GUEST_MODE=false
```

## Development

### Backend Development

1. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with Debug Mode**
   ```bash
   export FLASK_ENV=development  # Linux/macOS
   set FLASK_ENV=development     # Windows
   python run.py
   ```

3. **Database Operations**
   ```bash
   # Reset database
   python database/db_setup.py --reset
   
   # Add sample data
   python database/db_setup.py --sample-data
   ```

### Frontend Development

1. **Development Commands**
   ```bash
   npm run dev        # Start development server
   npm run build      # Build for production
   npm run preview    # Preview production build
   npm run lint       # Run ESLint
   ```

2. **Available Interfaces**
   
   | Interface | Path | Description |
   | --- | --- | --- |
   | **User RAG** | `/frontend` | Primary user-facing RAG interface |
   | **Evaluation** | `/evaluation-interface` | System evaluation dashboard |

### Testing

1. **Backend Testing**
   ```bash
   # Test search functionality
   python test_search.py
   
   # Test model loading
   python verify_models.py
   
   # Test embeddings
   python verify_embeddings.py
   ```

2. **API Testing**
   ```bash
   # Test registration
   curl -X POST http://localhost:5000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"test","email":"test@example.com","password":"testpass"}'
   
   # Test demo chat (no auth required)
   curl -X POST http://localhost:5000/chat_stream_demo \
     -H "Content-Type: application/json" \
     -d '{"message":"What is the Algerian constitution?"}'
   ```

## API Documentation

### Authentication Endpoints

- **POST** `/auth/register` - Register new user
- **POST** `/auth/login` - User login
- **GET** `/auth/me` - Get user profile

### Chat Endpoints

- **POST** `/chat_stream` - Protected streaming chat
- **POST** `/chat_stream_demo` - Public demo endpoint
- **GET** `/conversations` - Get user conversations
- **POST** `/conversations` - Create new conversation
- **GET** `/conversations/{id}/messages` - Get conversation messages
- **DELETE** `/conversations/{id}` - Delete conversation

### Test Endpoints

- **POST** `/test_search` - Test search functionality
- **GET** `/test_models` - Test model loading

### Request/Response Examples

**Chat Request:**
```json
{
  "message": "What are the fundamental rights in Algeria?",
  "language": "fr",
  "conversation_id": 123
}
```

**Streaming Response:**
```
data: {"chunk": "Les droits fondamentaux en Algérie"}
data: {"chunk": " sont définis dans la Constitution..."}
data: {"chunk": " Article 34 garantit..."}
```

## Features in Detail

### Bilingual Search System

The application uses a sophisticated bilingual search system:

1. **Language Detection**: Automatically identifies query language
2. **Specialized Embeddings**: 
   - French: CamemBERT (1024 dimensions)
   - Arabic: Multilingual MiniLM (384 dimensions)
3. **FAISS Indexing**: High-performance vector search
4. **Smart Fallback**: Multilingual embedder when language-specific unavailable

### Authentication & Security

- **JWT Tokens**: Stateless authentication
- **Password Hashing**: Secure bcrypt hashing
- **CORS Configuration**: Controlled cross-origin access
- **Request Validation**: Input sanitization and validation

### Real-time Chat

- **Server-Sent Events**: Real-time streaming responses
- **Conversation Threading**: Persistent chat history
- **Auto-recovery**: Seamless handling of invalid conversation IDs
- **Toast Notifications**: User feedback for errors and status updates

## Troubleshooting

### Common Issues

1. **Models Not Loading**
   ```bash
   # Re-download models using the download script
   python download_models.py
   
   # This script downloads and caches the following models:
   # - dangvantuan/sentence-camembert-large (French embeddings)
   # - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (Arabic/Multilingual)
   # - LLM models for text generation
   
   # Check model cache location
   ls ~/.cache/huggingface/transformers/  # Linux/macOS
   ls %USERPROFILE%\.cache\huggingface\transformers\  # Windows
   
   # Verify models are properly cached before running the application
   python verify_models.py
   ```

2. **FAISS Index Errors**
   ```bash
   # Verify index files exist
   ls -la data/*.faiss data/*.json
   
   # Check file paths in settings
   python -c "from app.config.settings import settings; print(settings.FRENCH_INDEX_PATH)"
   ```

3. **Database Issues**
   ```bash
   # Reset database
   rm algerian_law_rag.db
   python database/db_setup.py
   ```

4. **Frontend Build Errors**
   ```bash
   # Clear cache and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **Port Already in Use**
   ```bash
   # Kill process using port 5000
   lsof -ti:5000 | xargs kill -9  # Linux/macOS
   netstat -ano | findstr :5000   # Windows
   ```

### Performance Optimization

1. **GPU Acceleration**
   ```bash
   # Set environment variable
   export COMPUTE_DEVICE=cuda
   
   # Verify CUDA availability
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Memory Management**
   ```bash
   # Use quantized models
   export USE_QUANTIZATION=true
   
   # Reduce batch size for embeddings
   export MAX_BATCH_SIZE=8
   ```

### Logging and Debugging

1. **Enable Debug Logging**
   ```bash
   export LOG_LEVEL=DEBUG
   python run.py
   ```

2. **Search Debug Method**
   ```python
   from app.services.search_service.bilingual_search_service import BilingualSearchService
   
   service = BilingualSearchService()
   debug_info = service.test_search_debug("constitution", "fr")
   print(json.dumps(debug_info, indent=2))
   ```

3. **Common Error Solutions**
   
   | Error | Solution |
   | --- | --- |
   | `ModuleNotFoundError` | Check virtual environment activation |
   | `FAISS index not found` | Verify data files exist in correct paths |
   | `CUDA out of memory` | Switch to CPU or reduce batch size |
   | `404 conversation not found` | Auto-recovery should handle this |
   | `JWT token expired` | Re-login to get new token |

## Usage Tips

### For Developers

1. **Hot Reloading**: Both frontend and backend support hot reloading during development
2. **API Testing**: Use the demo endpoints to test functionality without authentication
3. **Debug Mode**: Enable debug logging to troubleshoot issues
4. **Model Cache**: Models are cached locally after first download

### For Users

1. **Language Switching**: The system auto-detects language but you can specify it
2. **Conversation Management**: Use the sidebar to navigate between conversations
3. **Error Recovery**: The app automatically recovers from most errors
4. **Mobile Support**: The interface is fully responsive and mobile-friendly

## Contributing

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Commit Changes**: `git commit -m 'Add amazing feature'`
4. **Push to Branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript
- Add tests for new features
- Update documentation for API changes
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Hugging Face** for transformer models and embeddings
- **FAISS** for efficient vector search
- **Flask** for the robust backend framework
- **React** for the interactive frontend
- **Tailwind CSS** for beautiful styling

## Support

For support and questions:

1. **Documentation**: Check this README and code comments
2. **Issues**: Open a GitHub issue for bugs or feature requests
3. **Discussions**: Use GitHub Discussions for questions
4. **Debug Tools**: Use the built-in test endpoints and debug methods

