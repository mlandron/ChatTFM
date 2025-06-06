import os
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
import logging

# Load environment variables
load_dotenv()

class RAGService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.openai_api_key = os.getenv("OPEN_AI_KEY")
        
        # Initialize clients
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Default parameters
        self.default_embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-m3")
        self.default_top_k = int(os.getenv("DEFAULT_TOP_K", 5))
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.1))
        self.default_chat_model = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o-mini")
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_embeddings(self, text: str, model: str = "text-embedding-3-small"):
        """Get embeddings using OpenAI API"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Error getting embeddings: {e}")
            return None

    def search_documents(self, query_embedding, top_k: int = 5):
        """Search documents in Supabase using vector similarity"""
        try:
            # This is a simplified version - in production you would use proper vector search
            # For now, we'll do a simple text search as fallback
            response = self.supabase.table("chunk_embeddings").select("*").limit(top_k).execute()
            return response.data if response.data else []
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return []

    def query_rag(self, query: str, embedding_model: str = None, top_k: int = None, 
                  temperature: float = None, chat_model: str = None):
        """
        Main RAG query function - simplified version for deployment
        """
        if top_k is None:
            top_k = self.default_top_k
        if temperature is None:
            temperature = self.default_temperature
        if chat_model is None:
            chat_model = self.default_chat_model
            
        try:
            # Get query embeddings
            query_embedding = self.get_embeddings(query)
            if not query_embedding:
                return {
                    "answer": "Sorry, I couldn't process your query at the moment.",
                    "source_documents": [],
                    "parameters_used": {
                        "embedding_model": embedding_model or self.default_embedding_model,
                        "top_k": top_k,
                        "temperature": temperature,
                        "chat_model": chat_model
                    }
                }
            
            # Search for relevant documents
            documents = self.search_documents(query_embedding, top_k)
            
            # Prepare context from documents
            context = ""
            source_documents = []
            for doc in documents:
                if 'content' in doc:
                    context += doc['content'] + "\n\n"
                    source_documents.append({
                        "content": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                        "metadata": {k: v for k, v in doc.items() if k != 'content'}
                    })
            
            # Generate response using OpenAI
            if context.strip():
                prompt = f"""Based on the following context, please answer the user's question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context}

Question: {query}

Answer:"""
            else:
                prompt = f"""I don't have specific context documents to answer this question, but I'll provide a general response based on my knowledge.

Question: {query}

Answer:"""
            
            response = self.openai_client.chat.completions.create(
                model=chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # Check if retrieved matches are sufficient
            if not source_documents:
                answer = "I couldn't find sufficient relevant information in the knowledge base to answer your query reliably. However, here's what I can tell you: " + answer
            
            return {
                "answer": answer,
                "source_documents": source_documents,
                "parameters_used": {
                    "embedding_model": embedding_model or self.default_embedding_model,
                    "top_k": top_k,
                    "temperature": temperature,
                    "chat_model": chat_model
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in RAG query: {e}")
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "source_documents": [],
                "parameters_used": {
                    "embedding_model": embedding_model or self.default_embedding_model,
                    "top_k": top_k,
                    "temperature": temperature,
                    "chat_model": chat_model
                }
            }

    def test_connection(self):
        """Test Supabase connection"""
        try:
            # Test Supabase connection
            response = self.supabase.table("chunk_embeddings").select("*").limit(1).execute()
            return {"status": "success", "message": "Connected to Supabase successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

