# chat.py

from flask import Blueprint, request, jsonify
#from rag_service_deploy import RAGService
from rag_service import RAGService # Make sure you're using the updated RAGService
import logging
import os

chat_bp = Blueprint('chat', __name__)
rag_service = RAGService()

logger = logging.getLogger(__name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for RAG queries
    Expected JSON payload:
    {
        "query": "Your question here",
        "embedding_model": "BAAI/bge-m3" (optional),
        "top_k": 5 (optional, will be used for both vector and BM25 retrieval),
        "temperature": 0.1 (optional),
        "chat_model": "gpt-4o-mini" (optional),
        "rpc_threshold": 0.2 (optional),
        "ensemble_weights": [0.6, 0.4] (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing 'query' in request body"
            }), 400
        
        query = data['query']
        embedding_model = data.get('embedding_model')
        # This top_k will be used for both vector and bm25 retrievers
        top_k_from_request = data.get('top_k') 
        temperature = data.get('temperature')
        chat_model = data.get('chat_model')
        
        # New parameters you might want to control
        rpc_threshold = data.get('rpc_threshold')
        ensemble_weights = data.get('ensemble_weights')

        # Prepare parameters for query_rag
        query_params = {
            "query": query,
            "embedding_model": embedding_model,
            "temperature": temperature,
            "chat_model": chat_model,
            "rpc_threshold": 0.2, # Initialize to None
            "ensemble_weights":[0.6, 0.4] # Initialize to None
        }

        # Validate and set top_k for both vector and bm25
        parsed_vector_top_k = 10
        parsed_bm25_top_k = 10

        if top_k_from_request is not None:
            try:
                validated_top_k = int(top_k_from_request)
                if not (0 <= validated_top_k <= 20): # Allow 0 if it makes sense for your use case
                    return jsonify({
                        "error": "top_k must be between 0 and 20"
                    }), 400
                parsed_vector_top_k = validated_top_k
                parsed_bm25_top_k = validated_top_k
            except ValueError:
                return jsonify({
                    "error": "top_k must be an integer"
                }), 400
        
        query_params["vector_top_k"] = parsed_vector_top_k
        query_params["bm25_top_k"] = parsed_bm25_top_k

        if temperature is not None:
            try:
                query_params["temperature"] = float(temperature)
                if not (0.01 <= query_params["temperature"] <= 1.0):
                    return jsonify({
                        "error": "temperature must be between 0.01 and 1.0"
                    }), 400
            except ValueError:
                return jsonify({
                    "error": "temperature must be a number"
                }), 400
        
        if rpc_threshold is not None:
            try:
                query_params["rpc_threshold"] = float(rpc_threshold)
                # Add validation for rpc_threshold if needed (e.g., 0.0 to 1.0)
            except ValueError:
                return jsonify({
                    "error": "rpc_threshold must be a number"
                }), 400

        if ensemble_weights is not None:
            if not (isinstance(ensemble_weights, list) and \
                    len(ensemble_weights) == 2 and \
                    all(isinstance(w, (int, float)) for w in ensemble_weights) and \
                    sum(ensemble_weights) <= 1.01 and sum(ensemble_weights) >= 0.99): # check sum is close to 1
                return jsonify({
                    "error": "ensemble_weights must be a list of two numbers (e.g., [0.6, 0.4]) that sum to ~1.0"
                }), 400
            query_params["ensemble_weights"] = [float(w) for w in ensemble_weights]


        # Remove None values so defaults in RAGService are used
        final_query_params = {k: v for k, v in query_params.items() if v is not None}
        
        # Process the query using RAG
        #result = rag_service.query_rag(**final_query_params) # Use dictionary unpacking
        
        result = rag_service.query_rag(
                query,
                 embedding_model="BAAI/bge-m3",
                 vector_top_k=10,
                 bm25_top_k=10,
                 rpc_threshold=0.2,
                 ensemble_weights=[0.5, 0.5],
                 temperature=0.2,
                 chat_model="gpt-4o" # More powerful model
            )


        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True) # Log traceback
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500



@chat_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """Test Supabase connection"""
    try:
        result = rag_service.test_connection()
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({
            "status": "error",
            "message": f"Connection test failed: {str(e)}"
        }), 500

@chat_bp.route('/parameters', methods=['GET'])
def get_parameters():
    """Get available parameter options"""
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
        ],
        "defaults": {
            "embedding_model": "BAAI/bge-m3",
            "top_k": 5,
            "temperature": 0.1,
            "chat_model": "gpt-4o-mini"
        },
        "ranges": {
            "top_k": {"min": 0, "max": 20},
            "temperature": {"min": 0.01, "max": 1.0}
        }
    })

"""
# Example Usage (assuming .env is set up correctly):
if __name__ == '__main__':
    # ---- Sanity checks for .env variables ----
    print("--- Environment Variables ---")
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL') is not None}")
    print(f"SUPABASE_SERVICE_KEY: {os.getenv('SUPABASE_SERVICE_KEY') is not None}")
    print(f"OPEN_AI_KEY: {os.getenv('OPEN_AI_KEY') is not None}")
    print(f"DEFAULT_EMBEDDING_MODEL: {os.getenv('DEFAULT_EMBEDDING_MODEL', 'BAAI/bge-m3')}")
    print("-----------------------------")
    
    try:
        rag_service = RAGService()
        
        # Test connection
        connection_status = rag_service.test_connection()
        print(f"Connection Test: {connection_status}")

        if connection_status["status"] == "success":
            # Test fetching embeddings (will print log messages)
            try:
                print("\n--- Testing Embeddings ---")
                bge_embeddings = rag_service.get_embeddings("BAAI/bge-m3")
                print(f"BGE Embeddings type: {type(bge_embeddings)}")
                openai_embeddings = rag_service.get_embeddings("text-embedding-3-small")
                print(f"OpenAI Embeddings type: {type(openai_embeddings)}")
            except Exception as e:
                print(f"Error testing embeddings: {e}")

            # Test fetching all docs for BM25 (will print log messages)
            # This might take time if you have many documents
            # try:
            #     print("\n--- Testing BM25 Doc Loading ---")
            #     rag_service._load_all_docs_for_bm25_if_needed()
            #     if rag_service.all_docs is not None:
            #         print(f"Loaded {len(rag_service.all_docs)} documents for BM25.")
            #     else:
            #         print("Failed to load documents for BM25 or no documents found.")
            # except Exception as e:
            #     print(f"Error testing BM25 doc loading: {e}")

            print("\n--- Performing RAG Query ---")
            # Example query
            user_query = "¿Cuáles son los requisitos para una pensión por vejez?"
            
            # You can override defaults here:
            response = rag_service.query_rag(
                user_query,
                # embedding_model="BAAI/bge-m3",
                # vector_top_k=7,
                # bm25_top_k=7,
                # rpc_threshold=0.25,
                # ensemble_weights=[0.5, 0.5],
                # temperature=0.0,
                # chat_model="gpt-4o" # More powerful model
            )
            
            print("\n--- RAG Query Response ---")
            print(f"Answer: {response['answer']}")
            print(f"Parameters Used: {response['parameters_used']}")
            print(f"Source Documents ({len(response['source_documents'])}):")
            for i, doc in enumerate(response['source_documents']):
                print(f"  Source {i+1}:")
                print(f"    Content: {doc['content'][:200]}...") # Print snippet
                print(f"    Metadata: {doc['metadata']}")
        else:
            print("Cannot proceed with further tests due to connection failure.")

    except ValueError as ve:
        print(f"Initialization Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during example usage: {e}")
        import traceback
        traceback.print_exc()


    def test_connection(self):
        try:
            # Test Supabase connection
            response = self.supabase.table("chunk_embeddings").select("*").limit(1).execute()
            return {"status": "success", "message": "Connected to Supabase successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {str(e)}"}
"""



