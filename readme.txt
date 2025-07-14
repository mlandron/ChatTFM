# RAG Chatbot for Dominican Social Security System

## Overview

This is a Retrieval-Augmented Generation (RAG) chatbot specifically designed for the Dominican Social Security System (SIPEN). The system provides accurate, context-aware responses to questions about Dominican pension laws, regulations, and procedures using a hybrid vector and BM25 search approach.

## Key Features

### 🎯 **Enhanced Threshold Management**
- **High-quality filtering**: Default similarity threshold of 0.75 for better relevance
- **Adaptive thresholding**: Automatically adjusts from 0.75 → 0.6 → 0.5 if no documents found
- **Domain-specific filtering**: Only returns documents related to Dominican social security
- **Graceful fallback**: Returns helpful message for irrelevant queries

### 💬 **Chat History Management**
- **Persistent conversations**: Save and retrieve chat history in Supabase
- **User-specific storage**: Separate conversation tracking per user
- **Conversation management**: Load, delete, and organize chat sessions
- **Message metadata**: Track sender, timestamps, and conversation IDs

### 🔍 **Hybrid Search System**
- **Vector similarity search**: Using BAAI/bge-m3 embeddings via Supabase RPC
- **BM25 full-text search**: PostgreSQL-based keyword matching
- **Ensemble retrieval**: Combines both approaches for optimal results
- **Score normalization**: Consistent scoring across different retrieval methods

### 🛡️ **Quality Assurance**
- **Relevance checking**: Filters out non-Dominican social security content
- **Confidence scoring**: Provides quality metrics for responses
- **Source attribution**: Links to original SIPEN documents
- **Error handling**: Graceful degradation and informative error messages

## Project Structure

```
chatbotTFM/
├── FrontEnd/                 # React frontend application
│   ├── src/
│   │   ├── components/       # UI components including chat history
│   │   ├── App.jsx          # Main application component
│   │   └── main.jsx         # Application entry point
│   ├── package.json         # Frontend dependencies
│   └── vite.config.js       # Vite configuration
├── Documentation/            # Project documentation and SQL files
│   ├── THRESHOLD_IMPROVEMENTS.md
│   ├── SUPABASE_SETUP.md
│   ├── supabase_functions.sql
│   └── recreate_table.sql
├── Testing/                  # Test scripts and utilities
│   ├── test_threshold_improvements.py
│   ├── test_chat_history.py
│   └── test_optimized_service.py
├── rag_service.py           # Core RAG service with threshold improvements
├── chat.py                  # Chat API endpoints
├── chat_history.py          # Chat history management
├── main.py                  # Flask application entry point
└── requirements.txt         # Python dependencies
```

## Technology Stack

### Backend
- **Python 3.9+** with Flask framework
- **LangChain** for RAG pipeline orchestration
- **Supabase** for vector database and chat history
- **OpenAI GPT-4o-mini** for text generation
- **BAAI/bge-m3** for embeddings

### Frontend
- **React 18** with Vite build system
- **Tailwind CSS** for styling
- **Shadcn/ui** components
- **Axios** for API communication

### Database
- **Supabase PostgreSQL** with vector extensions
- **pgvector** for similarity search
- **Full-text search** with Spanish language support

## Configuration

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# OpenAI Configuration
OPEN_AI_KEY=your_openai_api_key

# RAG Service Configuration
DEFAULT_EMBEDDING_MODEL=BAAI/bge-m3
DEFAULT_VECTOR_TOP_K=10
DEFAULT_BM25_TOP_K=10
DEFAULT_RPC_THRESHOLD=0.7
DEFAULT_ENSEMBLE_WEIGHTS=0.5,0.5
DEFAULT_TEMPERATURE=0.1
DEFAULT_CHAT_MODEL=gpt-4o-mini

# Threshold Management
BM25_SCORE_THRESHOLD=0.3
MIN_DOCUMENT_COUNT=1
ADAPTIVE_THRESHOLD_ENABLED=true
```

## Installation & Setup

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd chatbotTFM
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### 3. Setup Supabase Database

Run the SQL scripts in `Documentation/`:
- `recreate_table.sql` - Creates the chunk_embeddings table
- `supabase_functions.sql` - Creates RPC functions for search

### 4. Start the Backend

```bash
python main.py
```

### 5. Start the Frontend

```bash
cd FrontEnd
npm install
npm run dev
```

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send a message and get RAG response
- `GET /api/test-connection` - Test backend connectivity
- `GET /api/parameters` - Get available models and parameters

### Chat History Endpoints
- `POST /api/chat-history/save-message` - Save a chat message
- `GET /api/chat-history/conversations/<user_id>` - Get user conversations
- `GET /api/chat-history/conversation/<conversation_id>/messages` - Get conversation messages
- `DELETE /api/chat-history/conversation/<conversation_id>` - Delete conversation

## Usage Examples

### Basic Chat Query
```python
from rag_service import RAGConfig, RAGService

config = RAGConfig()
service = RAGService(config)

result = service.query_rag("¿Qué dice la ley 87-01 sobre pensiones?")
print(result["answer"])
```

### Testing Threshold Improvements
```bash
cd Testing
python test_threshold_improvements.py
```

## Key Improvements

### Threshold Management
- **Before**: Default threshold 0.2, allowing low-quality matches
- **After**: Default threshold 0.75, with adaptive fallback to 0.6 → 0.5
- **Result**: Higher quality responses, fewer irrelevant results

### Domain Filtering
- **Before**: Could return answers for non-Dominican social security queries
- **After**: Strict relevance checking with fallback message
- **Result**: Only domain-relevant responses, clear guidance for off-topic queries

### Error Handling
- **Before**: Could crash or return confusing errors
- **After**: Graceful handling with informative messages
- **Result**: Better user experience, no system crashes

## Testing

### Run All Tests
```bash
cd Testing
python test_threshold_improvements.py
python test_chat_history.py
python test_optimized_service.py
```

### Test Specific Scenarios
- **Relevant queries**: Should return detailed answers with sources
- **Irrelevant queries**: Should return fallback message
- **Edge cases**: Should handle gracefully without crashes

## Deployment

### Backend Deployment
- Compatible with Vercel, Railway, or any Python hosting
- Uses Gunicorn for production serving
- Environment variables must be configured

### Frontend Deployment
- Built with Vite for optimized production builds
- Deploy to Vercel, Netlify, or similar platforms
- Configure API endpoint URLs for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is developed for the Dominican Social Security System (SIPEN) and follows their specific requirements and guidelines.

## Support

For issues related to:
- **RAG functionality**: Check `Documentation/THRESHOLD_IMPROVEMENTS.md`
- **Database setup**: Check `Documentation/SUPABASE_SETUP.md`
- **API issues**: Check the test files in `Testing/`

## Recent Updates

### v2.0 - Threshold Improvements
- Enhanced similarity threshold management
- Adaptive threshold system
- Domain-specific relevance filtering
- Improved error handling and fallback responses

### v1.5 - Chat History
- Persistent conversation storage
- User-specific chat management
- Conversation CRUD operations
- Enhanced UI for chat history

### v1.0 - Initial Release
- Basic RAG functionality
- Vector and BM25 search
- React frontend
- Supabase integration
