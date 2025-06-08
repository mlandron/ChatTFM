import os
import logging
import pickle
from typing import List, Any, Dict, Optional, Iterable

from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.retrievers import BaseRetriever
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from pydantic.v1 import PrivateAttr
from langchain.prompts import ChatPromptTemplate

load_dotenv()

class RAGConfig:
    # --- (No changes to this class) ---
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.openai_api_key = os.getenv("OPEN_AI_KEY")
        if not all([self.supabase_url, self.supabase_key, self.openai_api_key]):
            raise ValueError("Supabase or OpenAI environment variables are missing.")
        self.bm25_retriever_path = os.getenv("BM25_RETRIEVER_PATH", "bm25_retriever.pkl")
        self.default_embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-m3")
        self.default_vector_top_k = int(os.getenv("DEFAULT_VECTOR_TOP_K", 10))
        self.default_bm25_top_k = int(os.getenv("DEFAULT_BM25_TOP_K", 10))
        self.default_rpc_threshold = float(os.getenv("DEFAULT_RPC_THRESHOLD", 0.2))
        self.default_ensemble_weights = [float(w.strip()) for w in os.getenv("DEFAULT_ENSEMBLE_WEIGHTS", "0.6, 0.4").split(',')]
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.1))
        self.default_chat_model = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o-mini")

class SupabaseRPCRetriever(BaseRetriever):
    embeddings: Embeddings
    rpc_name: str = "match_chunks"
    top_k: int = 10
    threshold: float = 0.2
    _client: Any = PrivateAttr()

    def __init__(self, client: Any, embeddings: Embeddings, **kwargs):
        super().__init__(embeddings=embeddings, **kwargs)
        self._client = client

    def _get_relevant_documents(self, query: str) -> List[Document]:
        query_embedding = self.embeddings.embed_query(query)
        try:
            response = self._client.rpc(
                self.rpc_name,
                {"query_embedding": query_embedding, "top_k": self.top_k, "threshold": self.threshold}
            ).execute()
            if not response.data: return []

            return [
                Document(
                    page_content=match.get("text", ""),
                    metadata={
                        # --- CHANGE #1: Aligning with your SQL function ---
                        # We read 'file_name' and 'doc_type' from the top-level response.
                        # We use the key "source" to be consistent with the frontend.
                        "source": match.get("file_name"), 
                        "doc_type": match.get("doc_type"),
                        "score": match.get("score", 0.0)
                    }
                )
                for match in response.data
            ]
        except Exception as e:
            logging.error(f"Error in Supabase RPC call: {e}")
            return []

class RAGService:
    # ... (init, get_embeddings, get_hybrid_retriever, and test_connection are unchanged) ...
    def __init__(self, config: RAGConfig):
        self.config = config
        self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
        self.bm25_retriever: Optional[BM25Retriever] = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._load_bm25_retriever()
    
    def _load_bm25_retriever(self):
        try:
            with open(self.config.bm25_retriever_path, "rb") as f: self.bm25_retriever = pickle.load(f)
            self.logger.info(f"Successfully loaded BM25 retriever from {self.config.bm25_retriever_path}")
        except FileNotFoundError: self.logger.warning(f"BM25 retriever file not found. Hybrid search disabled.")
        except Exception as e: self.logger.error(f"Error loading BM25 retriever: {e}"); self.bm25_retriever = None

    def get_embeddings(self, model_name: Optional[str] = None) -> Embeddings:
        model = model_name or self.config.default_embedding_model
        try:
            if "text-embedding-" in model: return OpenAIEmbeddings(model=model, openai_api_key=self.config.openai_api_key)
            return HuggingFaceEmbeddings(model_name=model)
        except Exception as e: self.logger.error(f"Error creating embeddings for model {model}: {e}"); raise

    def get_hybrid_retriever(self, **kwargs) -> Optional[BaseRetriever]:
        try:
            vector_top_k = kwargs.get("vector_top_k", self.config.default_vector_top_k); bm25_top_k = kwargs.get("bm25_top_k", self.config.default_bm25_top_k)
            embeddings = self.get_embeddings(kwargs.get("embedding_model_name", self.config.default_embedding_model))
            vector_retriever = SupabaseRPCRetriever(client=self.supabase, embeddings=embeddings, top_k=vector_top_k, threshold=kwargs.get("rpc_threshold", self.config.default_rpc_threshold))
            
            if self.bm25_retriever: 
                self.bm25_retriever.k = bm25_top_k
                return EnsembleRetriever(retrievers=[vector_retriever, self.bm25_retriever], weights=kwargs.get("ensemble_weights", self.config.default_ensemble_weights))
            
            return vector_retriever # Fallback to vector-only if BM25 is not loaded
        except Exception as e:
            self.logger.error(f"Error creating retriever: {e}")
            return None # Return None on failure

    def query_rag(self, query: str, **kwargs) -> Dict[str, Any]:
        params = { k: kwargs.get(k, getattr(self.config, f"default_{k}")) for k in ["embedding_model", "vector_top_k", "bm25_top_k", "rpc_threshold", "ensemble_weights", "temperature", "chat_model"] }
        try:
            retriever = self.get_hybrid_retriever(**params)
            
            # This check prevents the ValidationError
            if not retriever:
                raise ValueError("Failed to initialize a valid retriever.")

            llm = ChatOpenAI(model=params["chat_model"], temperature=params["temperature"], openai_api_key=self.config.openai_api_key)
            system_message_content = "Eres un experto en el sistema de pensiones dominicano..."
            human_template = "Por favor, responde la siguiente pregunta... Contexto:\n{context}\n\n---\nPregunta: {question}"
            custom_prompt = ChatPromptTemplate.from_messages([("system", system_message_content), ("human", human_template)])
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm, chain_type="stuff", retriever=retriever,
                return_source_documents=True, chain_type_kwargs={"prompt": custom_prompt}
            )
            result = qa_chain.invoke({"query": query})

            # --- CHANGE #2: Improved URL generation using doc_type ---
            unique_sources = {}
            for doc in result.get("source_documents", []):
                source_name = (doc.metadata.get("source") or "").strip()
                doc_type = (doc.metadata.get("doc_type") or "").strip().lower()
                norm = source_name.lower()

                if source_name and norm != "none" and norm not in unique_sources:
                    # Use the more reliable 'doc_type' for the condition
                    if doc_type == "leyes":
                        link = f"https://www.sipen.gob.do/descarga/{source_name}"
                    else:
                        link = f"https://www.sipen.gob.do/documentos/{source_name}"
                    unique_sources[norm] = {"source_name": source_name, "url": link}

            return { "answer": result["result"], "source_documents": list(unique_sources.values()), "parameters_used": params }
        except Exception as e:
            self.logger.error(f"Error in RAG query: {e}", exc_info=True)
            return { "answer": f"An error occurred: {e}", "source_documents": [], "parameters_used": params }
            
    def test_connection(self) -> Dict[str, str]:
        try:
            self.supabase.table("chunk_embeddings").select("id").limit(1).execute()
            return {"status": "success", "message": "Connected to Supabase successfully."}
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {e}"}

def create_and_save_bm25_retriever(config: RAGConfig):
    logger = logging.getLogger(__name__)
    logger.info("Starting process to create and save BM25 retriever...")
    def document_generator(client: Client) -> Iterable[Document]:
        page_size, start = 500, 0
        while True:
            try:
                # --- CHANGE #3: Select the correct columns for BM25 ---
                response = client.table("chunk_embeddings").select("text, file_name, doc_type").range(start, start + page_size - 1).execute()
                if not response.data: break
                for row in response.data:
                    yield Document(
                        page_content=row.get('text', ''), 
                        metadata={'source': row.get('file_name'), 'doc_type': row.get('doc_type')}
                    )
                if len(response.data) < page_size: break
                start += page_size
            except Exception as e: logger.error(f"Error fetching documents from Supabase: {e}"); break
    
    supabase_client = create_client(config.supabase_url, config.supabase_key)
    docs_iterator = document_generator(supabase_client)
    
    try:
        # --- CHANGE #4: The typo fix ---
        bm25_retriever = BM25Retriever.from_documents(documents=docs_iterator)
        with open(config.bm25_retriever_path, "wb") as f: pickle.dump(bm25_retriever, f)
        logger.info(f"BM25 retriever saved to {config.bm25_retriever_path}")
    except Exception as e:
        logger.error(f"Failed to create or save BM25 retriever: {e}", exc_info=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main_config = RAGConfig()
    create_and_save_bm25_retriever(main_config) # Create the cache file
    
    print("\n--- Testing RAG Service with cached retriever ---")
    rag_service = RAGService(main_config) # Re-initialize to load the new cache
    if rag_service.test_connection()["status"] == "success":
        user_query = "Que dice la ley 87-01 sobre el régimen contributivo de pensiones y jubilaciones?"
        response = rag_service.query_rag(user_query)
        print("\n--- RAG Query Response ---")
        print(f"Answer: {response['answer']}")
        print(f"Source Documents: {response['source_documents']}")