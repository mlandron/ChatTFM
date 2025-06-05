import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# Ensure you have sentence_transformers for HuggingFaceEmbeddings
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings 
from langchain.chains import RetrievalQA
from langchain.retrievers import EnsembleRetriever # EnsembleRetriever might also move soon, but this is the BM25 fix
from langchain_community.retrievers import BM25Retriever
from langchain_core.retrievers import BaseRetriever
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from pydantic.v1 import PrivateAttr # Langchain often uses Pydantic v1 features internally
from typing import List, Any, Dict, Optional

import logging
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

# Load environment variables
load_dotenv()

# Define SupabaseRPCRetriever (as provided in "corrected" code)
# This can be in the same file or imported if it's in a utils.py
class SupabaseRPCRetriever(BaseRetriever):
    """
    Retriever that calls the RPC `match_chunks` function in Supabase.
    """
    embeddings: Embeddings
    rpc_name: str = "match_chunks"
    top_k: int = 10
    threshold: float = 0.2  # Similarity threshold

    _client: Any = PrivateAttr()
    model_config = {"arbitrary_types_allowed": True} # Pydantic v2, or remove for v1

    def __init__(self, client: Any, embeddings: Embeddings, **kwargs):
        super().__init__(embeddings=embeddings, **kwargs) # Pass embeddings to parent
        self._client = client

    def _get_relevant_documents(self, query: str) -> List[Document]:
        q_vec = self.embeddings.embed_query(query)
        
        # Ensure query_embedding is a list of floats
        if hasattr(q_vec, 'tolist'): # For numpy arrays
            q_vec_list = q_vec.tolist()
        else:
            q_vec_list = list(q_vec)


        matches = (
            self._client.rpc(
                self.rpc_name,
                {
                    #"query_embedding": q_vec_list,
                    "query_embedding": q_vec,
                    "top_k": self.top_k, # Changed from "top_k" to "match_count" if your RPC expects that
                    "threshold": self.threshold, # Changed from "threshold" if your RPC expects that
                },
            )
            .execute()
            .data
        )
        
        # Handle cases where matches might be None or not as expected
        if not matches:
            return []

        return [
            Document(
                page_content=m.get("text", m.get("content", "")), # Check for "text" or "content"
                metadata={
                    "file_name": m.get("file_name", m.get("metadata", {}).get("file_name")), # Adapt based on actual RPC return
                    "score": m.get("similarity", m.get("score", 0.0)), # Adapt based on actual RPC return
                    # Add any other metadata fields returned by your RPC
                    **m.get("metadata", {}) # Include other metadata if present
                },
            )
            for m in matches
        ]

class RAGService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY") # Corrected uses SERVICE_KEY
        self.openai_api_key = os.getenv("OPEN_AI_KEY") # Your original key name
        
        if not all([self.supabase_url, self.supabase_key, self.openai_api_key]):
            raise ValueError("Supabase URL, Key, or OpenAI API Key not found in environment variables.")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        self.default_embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-m3")
        self.default_vector_top_k = int(os.getenv("DEFAULT_VECTOR_TOP_K", 10)) # For vector retriever
        self.default_bm25_top_k = int(os.getenv("DEFAULT_BM25_TOP_K", 10))   # For BM25 retriever
        self.default_rpc_threshold = float(os.getenv("DEFAULT_RPC_THRESHOLD", 0.2))
        self.default_ensemble_weights = [float(w.strip()) for w in os.getenv("DEFAULT_ENSEMBLE_WEIGHTS", "0.6, 0.4").split(',')]
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.1))
        self.default_chat_model = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o-mini") # Your original, corrected uses gpt-4o
        
        self.all_docs: Optional[List[Document]] = None # Cache for BM25 documents

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_embeddings(self, embedding_model_name: Optional[str] = None) -> Embeddings:
        """Get embeddings model instance."""
        model_name = embedding_model_name or self.default_embedding_model
        self.logger.info(f"Initializing embeddings model: {model_name}")
        try:
            if model_name == "BAAI/bge-m3":
                # Ensure sentence-transformers is installed: pip install sentence-transformers
                return HuggingFaceEmbeddings(model_name=model_name)
            elif "text-embedding-" in model_name: # OpenAI embedding models
                 return OpenAIEmbeddings(
                    model=model_name,
                    openai_api_key=self.openai_api_key
                )
            else: # Default to OpenAI's small embedding model as a fallback
                self.logger.warning(f"Unsupported embedding model '{model_name}'. Falling back to text-embedding-3-small.")
                return OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=self.openai_api_key
                )
        except Exception as e:
            self.logger.error(f"Error creating embeddings for model {model_name}: {e}")
            raise

    def _fetch_all_docs(self, table="chunk_embeddings", content_col="text", metadata_col="metadata", page_size=1000) -> List[Document]:
        """Fetches all documents from a Supabase table for BM25."""
        self.logger.info(f"Fetching all documents from table '{table}' for BM25...")
        docs: List[Document] = []
        start = 0
        while True:
            end = start + page_size - 1
            try:
                rows_query = self.supabase.table(table).select(f"{content_col}, {metadata_col}").range(start, end)
                response = rows_query.execute()
                rows = response.data
            except Exception as e:
                self.logger.error(f"Error fetching documents from Supabase: {e}")
                raise
                
            if not rows:
                break
            
            docs.extend(
                Document(
                    page_content=r.get(content_col, ""), # Ensure page_content is string
                    metadata=r.get(metadata_col) or {},
                )
                for r in rows
            )
            if len(rows) < page_size:
                break
            start += page_size
        self.logger.info(f"Fetched {len(docs)} documents for BM25.")
        return docs

    def _load_all_docs_for_bm25_if_needed(self):
        """Loads documents for BM25 if not already loaded."""
        if self.all_docs is None:
            try:
                # Assuming your Supabase table for chunks is 'chunk_embeddings'
                # and it has 'text' (or 'content') and 'metadata' columns.
                # Adjust table_name, content_col, metadata_col if different.
                self.all_docs = self._fetch_all_docs(
                    table="chunk_embeddings", 
                    content_col="text", # or "content" if that's your column name
                    metadata_col="metadata"
                )
            except Exception as e:
                self.logger.error(f"Failed to load documents for BM25: {e}")
                self.all_docs = [] # Set to empty list on failure to avoid retrying constantly

    def get_vector_retriever(self, embeddings: Embeddings, top_k: Optional[int] = None, threshold: Optional[float] = None) -> SupabaseRPCRetriever:
        """Get Supabase RPC retriever."""
        current_top_k = top_k if top_k is not None else self.default_vector_top_k
        current_threshold = threshold if threshold is not None else self.default_rpc_threshold
        
        self.logger.info(f"Initializing SupabaseRPCRetriever with top_k={current_top_k}, threshold={current_threshold}")
        try:
            return SupabaseRPCRetriever(
                client=self.supabase,
                embeddings=embeddings,
                top_k=current_top_k,
                threshold=current_threshold,
                rpc_name="match_chunks" # Ensure this matches your Supabase RPC function name
            )
        except Exception as e:
            self.logger.error(f"Error creating SupabaseRPCRetriever: {e}")
            raise

    def get_bm25_retriever(self, top_k: Optional[int] = None) -> BM25Retriever:
        """Get BM25 retriever."""
        self._load_all_docs_for_bm25_if_needed()
        current_top_k = top_k if top_k is not None else self.default_bm25_top_k
        
        self.logger.info(f"Initializing BM25Retriever with top_k={current_top_k}")
        if not self.all_docs:
            self.logger.warning("No documents available for BM25Retriever. It might not return any results.")
            # Return a retriever that will yield no results, or handle as an error
            # For now, let it initialize with an empty list, Langchain handles this.
        
        try:
            bm25_retriever = BM25Retriever.from_documents(self.all_docs if self.all_docs else [])
            bm25_retriever.k = current_top_k
            return bm25_retriever
        except Exception as e:
            self.logger.error(f"Error creating BM25Retriever: {e}")
            raise

    def get_hybrid_retriever(
        self, 
        embedding_model_name: Optional[str] = None, 
        vector_top_k: Optional[int] = None, 
        bm25_top_k: Optional[int] = None,
        rpc_threshold: Optional[float] = None,
        ensemble_weights: Optional[List[float]] = None
    ) -> EnsembleRetriever:
        """Create hybrid retriever combining vector search and BM25."""
        current_embedding_model = embedding_model_name or self.default_embedding_model
        current_vector_top_k = vector_top_k if vector_top_k is not None else self.default_vector_top_k
        current_bm25_top_k = bm25_top_k if bm25_top_k is not None else self.default_bm25_top_k
        current_rpc_threshold = rpc_threshold if rpc_threshold is not None else self.default_rpc_threshold
        current_weights = ensemble_weights if ensemble_weights is not None else self.default_ensemble_weights

        self.logger.info("Initializing Hybrid (Ensemble) Retriever.")
        try:
            embeddings = self.get_embeddings(current_embedding_model)
            vector_retriever = self.get_vector_retriever(embeddings, current_vector_top_k, current_rpc_threshold)
            bm25_retriever = self.get_bm25_retriever(current_bm25_top_k)
            
            return EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=current_weights
            )
        except Exception as e:
            self.logger.error(f"Error creating hybrid retriever: {e}")
            raise

    def query_rag(self, query: str, 
                  embedding_model: Optional[str] = None, 
                  vector_top_k: Optional[int] = None, # top_k for vector retriever
                  bm25_top_k: Optional[int] = None,   # top_k for bm25 retriever
                  rpc_threshold: Optional[float] = None,
                  ensemble_weights: Optional[List[float]] = None,
                  temperature: Optional[float] = None, 
                  chat_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Main RAG query function using the ensemble retriever.
        Preserves the user's specific LangChain code structure for RetrievalQA.
        """
        current_embedding_model = embedding_model or self.default_embedding_model
        current_vector_top_k = vector_top_k if vector_top_k is not None else self.default_vector_top_k
        current_bm25_top_k = bm25_top_k if bm25_top_k is not None else self.default_bm25_top_k
        current_rpc_threshold = rpc_threshold if rpc_threshold is not None else self.default_rpc_threshold
        current_ensemble_weights = ensemble_weights if ensemble_weights is not None else self.default_ensemble_weights
        current_temperature = temperature if temperature is not None else self.default_temperature
        current_chat_model = chat_model or self.default_chat_model
            
        parameters_used = {
            "embedding_model": current_embedding_model,
            "vector_top_k": current_vector_top_k,
            "bm25_top_k": current_bm25_top_k,
            "rpc_threshold": current_rpc_threshold,
            "ensemble_weights": current_ensemble_weights,
            "temperature": current_temperature,
            "chat_model": current_chat_model
        }
        self.logger.info(f"Executing RAG query with parameters: {parameters_used}")

        try:
            llm = ChatOpenAI(
                model=current_chat_model,
                temperature=current_temperature,
                openai_api_key=self.openai_api_key
            )

            system_template = """
            Eres un experto en el sistema de pensiones dominicano y en normativas de la SIPEN. Sigue estas reglas:
            1. Responde siempre basado en el contexto proporcionado.
            2. Usa un lenguaje claro, empático y amigable, con un tono cercano al dominicano común, evitando tecnicismos innecesarios.
            3. Sé breve pero explica bien lo necesario.
            4. Si no tienes información suficiente para responder, di simplemente "Discúlpame, no tengo esa información ahora mismo".

            Contexto:
            {context}
            """
            messages = [
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
            custom_prompt = ChatPromptTemplate.from_messages(messages)
            
            hybrid_retriever = self.get_hybrid_retriever(
                embedding_model_name=current_embedding_model,
                vector_top_k=current_vector_top_k,
                bm25_top_k=current_bm25_top_k,
                rpc_threshold=current_rpc_threshold,
                ensemble_weights=current_ensemble_weights
            )
            
            # THIS PART IS VERY IMPORTANT - DO NOT CHANGE (as requested by user)
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=hybrid_retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": custom_prompt} 
            )
            result = qa_chain.invoke({"query": query})
            
            answer = result["result"]
            source_documents = result.get("source_documents", [])
            
            if not source_documents and "Discúlpame, no tengo esa información ahora mismo" not in answer :
                 # Check if the LLM already indicated it doesn't know.
                 # If it found sources but still couldn't answer, or if it hallucinated without sources,
                 # this default message might be better.
                answer = "I couldn't find sufficient relevant information in the knowledge base to answer your query reliably. Please try rephrasing your question or provide more specific details."
            
            return {
                "answer": answer,
                "source_documents": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    } for doc in source_documents
                ],
                "parameters_used": parameters_used
            }
            
        except Exception as e:
            self.logger.error(f"Error in RAG query: {e}", exc_info=True)
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "source_documents": [],
                "parameters_used": parameters_used
            }

    def test_connection(self) -> Dict[str, str]:
        """Test Supabase connection by trying to fetch a single row."""
        try:
            # Test Supabase connection by trying to select from the table used for BM25
            # If this table name is configurable, ensure it's reflected here.
            response = self.supabase.table("chunk_embeddings").select("id").limit(1).execute() # Check for existence of 'id' or any column
            if response.data or response.data == []: # Empty table is still a successful connection
                 self.logger.info("Supabase connection test successful.")
                 return {"status": "success", "message": "Connected to Supabase successfully"}
            else: # Should not happen if execute() doesn't raise error
                 self.logger.error(f"Supabase connection test failed: No data or error in response structure {response}")
                 return {"status": "error", "message": f"Connection to Supabase failed, response: {response}"}
        except Exception as e:
            self.logger.error(f"Supabase connection test failed: {str(e)}", exc_info=True)
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

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
        """Test Supabase connection"""
        try:
            # Test Supabase connection
            response = self.supabase.table("chunk_embeddings").select("*").limit(1).execute()
            return {"status": "success", "message": "Connected to Supabase successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

