from flask import Blueprint, request, jsonify
from rag_service import RAGService, RAGConfig 
from chat_history import save_message_to_supabase, generate_conversation_id
import logging
import sys

# --- Blueprint Setup ---
# This line creates the Blueprint that main.py needs to import.
chat_bp = Blueprint('chat', __name__)

# --- Initialize Service (Singleton Pattern) ---
# This single instance is shared across all requests, saving memory.
# The embedding model and BM25 retriever are loaded only ONCE.
try:
    config = RAGConfig()
    rag_service = RAGService(config)
    logger = logging.getLogger(__name__)
except ValueError as e:
    logging.critical(f"FATAL: Could not start RAG service due to config error: {e}")
    # The application is not usable without the service.
    # It's better to log the error and stop.
    sys.exit(f"Application shutdown: {e}")


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handles chat requests by querying the RAG service and saving to chat history."""
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        # Extract and validate parameters
        query = data['query']
        user_id = data.get('user_id', 'anonymous')  # Default to anonymous if not provided
        conversation_id = data.get('conversation_id')
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = generate_conversation_id()
        
        params = {
            "embedding_model": data.get('embedding_model'),
            "vector_top_k": data.get('top_k'),
            "bm25_top_k": data.get('top_k'),
            "temperature": data.get('temperature'),
            "chat_model": data.get('chat_model'),
            "rpc_threshold": data.get('rpc_threshold'),
            "ensemble_weights": data.get('ensemble_weights'),
        }
        
        # Filter out None values so service uses defaults
        final_params = {k: v for k, v in params.items() if v is not None}

        # Save user message to chat history
        user_message_result = save_message_to_supabase(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content=query,
            sender='user'
        )
        
        if user_message_result['status'] != 'success':
            logger.warning(f"Failed to save user message: {user_message_result['message']}")

        # Perform RAG query
        result = rag_service.query_rag(query, **final_params)
        
        # Save bot response to chat history
        bot_message_result = save_message_to_supabase(
            user_id=user_id,
            conversation_id=conversation_id,
            message_content=result.get('answer', ''),
            sender='bot',
            ragas_metrics=result.get('ragas_metrics')
        )
        
        if bot_message_result['status'] != 'success':
            logger.warning(f"Failed to save bot message: {bot_message_result['message']}")
        
        # Add conversation_id to the result
        result['conversation_id'] = conversation_id
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@chat_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """Tests the connection to the Supabase backend."""
    try:
        status = rag_service.test_connection()
        if status["status"] == "success":
            return jsonify(status), 200
        else:
            return jsonify(status), 500
    except Exception as e:
        logger.error(f"Error testing connection: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Connection test failed: {e}"}), 500

@chat_bp.route('/parameters', methods=['GET'])
def get_parameters():
    """Provides available models and parameter ranges for the frontend."""
    return jsonify({
        "embedding_models": [
            {"value": "BAAI/bge-m3", "label": "BAAI/bge-m3 (Default)"},
            {"value": "text-embedding-3-small", "label": "OpenAI text-embedding-3-small"},
            {"value": "text-embedding-3-large", "label": "OpenAI text-embedding-3-large"}
        ],
        "chat_models": [
            {"value": "gpt-4o-mini", "label": "GPT-4o Mini (Default)"},
            {"value": "gpt-4o", "label": "GPT-4o"},
            {"value": "gpt-4", "label": "GPT-4"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"}
        ]
    })