import os
import logging
from typing import List, Any, Dict, Optional

from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from pydantic.v1 import PrivateAttr
from langchain.prompts import ChatPromptTemplate

load_dotenv()

class RAGConfig:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.openai_api_key = os.getenv("OPEN_AI_KEY")
        if not all([self.supabase_url, self.supabase_key, self.openai_api_key]):
            raise ValueError("Supabase or OpenAI environment variables are missing.")
        self.default_embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-m3")
        self.default_vector_top_k = int(os.getenv("DEFAULT_VECTOR_TOP_K", 10))
        self.default_bm25_top_k = int(os.getenv("DEFAULT_BM25_TOP_K", 10))
        # Updated to higher threshold for better quality matches
        self.default_rpc_threshold = float(os.getenv("DEFAULT_RPC_THRESHOLD", 0.75))
        self.default_ensemble_weights = [float(w.strip()) for w in os.getenv("DEFAULT_ENSEMBLE_WEIGHTS", "0.6, 0.4").split(',')]
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.1))
        self.default_chat_model = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o-mini")
        # New configuration options for threshold management
        self.min_document_count = int(os.getenv("MIN_DOCUMENT_COUNT", 1))
        self.adaptive_threshold_enabled = os.getenv("ADAPTIVE_THRESHOLD_ENABLED", "true").lower() == "true"
        self.adaptive_threshold_steps = [0.75, 0.6, 0.5]  # More restrictive - minimum 0.5
        self.bm25_score_threshold = float(os.getenv("BM25_SCORE_THRESHOLD", 0.3))  # Minimum BM25 score

class SupabaseRPCRetriever(BaseRetriever):
    embeddings: Embeddings
    rpc_name: str = "match_chunks"
    top_k: int = 10
    threshold: float = 0.75  # Updated default threshold
    _client: Any = PrivateAttr()

    def __init__(self, client: Any, embeddings: Embeddings, **kwargs):
        super().__init__(embeddings=embeddings, **kwargs)
        self._client = client
        # Override threshold if provided
        if 'threshold' in kwargs:
            self.threshold = kwargs['threshold']

    def _get_relevant_documents(self, query: str) -> List[Document]:
        query_embedding = self.embeddings.embed_query(query)
        try:
            response = self._client.rpc(
                self.rpc_name,
                {"query_embedding": query_embedding, "top_k": self.top_k, "threshold": self.threshold}
            ).execute()
            
            if not response.data:
                logging.warning(f"No documents found with threshold {self.threshold}")
                return []

            # Post-filtering: Remove documents that don't meet the threshold
            filtered_documents = []
            for match in response.data:
                score = match.get("score", 0.0)
                if score >= self.threshold:
                    filtered_documents.append(
                        Document(
                            page_content=match.get("text", ""),
                            metadata={
                                "source": match.get("file_name"), 
                                "doc_type": match.get("doc_type"),
                                "score": score,
                                "retriever_type": "vector"
                            }
                        )
                    )
                else:
                    logging.debug(f"Filtered out document with score {score} (threshold: {self.threshold})")

            logging.info(f"Retrieved {len(filtered_documents)} documents after filtering (original: {len(response.data)})")
            return filtered_documents
            
        except Exception as e:
            logging.error(f"Error in Supabase RPC call: {e}")
            return []

    def _get_relevant_documents_with_adaptive_threshold(self, query: str, threshold_steps: List[float]) -> List[Document]:
        """Try multiple thresholds to find relevant documents"""
        for threshold in threshold_steps:
            self.threshold = threshold
            documents = self._get_relevant_documents(query)
            if documents:
                logging.info(f"Found {len(documents)} documents with threshold {threshold}")
                return documents
        
        logging.warning(f"No documents found with any threshold in {threshold_steps}")
        return []

class DatabaseBM25Retriever(BaseRetriever):
    """Database-backed BM25 retriever using PostgreSQL full-text search"""
    top_k: int = 10
    score_threshold: float = 0.3
    _client: Any = PrivateAttr()
    
    def __init__(self, supabase_client: Client, k: int = 10, score_threshold: float = 0.3):
        # Initialize with proper Pydantic model structure
        super().__init__(top_k=k, score_threshold=score_threshold)
        self._client = supabase_client
        self.top_k = k  # Ensure instance attribute is set
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        try:
            response = self._client.rpc(
                'bm25_search',
                {
                    'query_text': query,
                    'limit_count': self.top_k
                }
            ).execute()
            
            if not response.data:
                logging.warning("No BM25 search results found")
                return []
            
            # Filter and normalize scores
            filtered_documents = []
            max_score = max((row.get('score', 0) for row in response.data), default=1.0)
            
            for row in response.data:
                score = row.get('score', 0)
                # Normalize score to 0-1 range
                normalized_score = score / max_score if max_score > 0 else 0
                
                if normalized_score >= self.score_threshold:
                    filtered_documents.append(
                        Document(
                            page_content=row['text'],
                            metadata={
                                'source': row['file_name'],
                                'doc_type': row['doc_type'],
                                'score': normalized_score,
                                'raw_score': score,
                                'retriever_type': 'bm25'
                            }
                        )
                    )
                else:
                    logging.debug(f"Filtered out BM25 document with normalized score {normalized_score} (threshold: {self.score_threshold})")
            
            logging.info(f"BM25 retrieved {len(filtered_documents)} documents after filtering (original: {len(response.data)})")
            return filtered_documents
            
        except Exception as e:
            logging.error(f"Database BM25 search error: {e}")
            return []

class RAGService:
    def __init__(self, config: RAGConfig):
        self.config = config
        self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
        self.database_bm25_retriever: Optional[DatabaseBM25Retriever] = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._initialize_database_bm25_retriever()
    
    def _initialize_database_bm25_retriever(self):
        try:
            self.database_bm25_retriever = DatabaseBM25Retriever(
                supabase_client=self.supabase, 
                k=self.config.default_bm25_top_k,
                score_threshold=self.config.bm25_score_threshold
            )
            self.logger.info("Successfully initialized Database BM25 retriever")
        except Exception as e:
            self.logger.error(f"Error initializing Database BM25 retriever: {e}")
            self.database_bm25_retriever = None

    def get_embeddings(self, model_name: Optional[str] = None) -> Embeddings:
        model = model_name or self.config.default_embedding_model
        try:
            if "text-embedding-" in model: return OpenAIEmbeddings(model=model, openai_api_key=self.config.openai_api_key)
            return HuggingFaceEmbeddings(model_name=model)
        except Exception as e: self.logger.error(f"Error creating embeddings for model {model}: {e}"); raise

    def get_hybrid_retriever(self, **kwargs) -> Optional[BaseRetriever]:
        try:
            vector_top_k = kwargs.get("vector_top_k", self.config.default_vector_top_k)
            bm25_top_k = kwargs.get("bm25_top_k", self.config.default_bm25_top_k)
            rpc_threshold = kwargs.get("rpc_threshold", self.config.default_rpc_threshold)
            
            embeddings = self.get_embeddings(kwargs.get("embedding_model_name", self.config.default_embedding_model))
            vector_retriever = SupabaseRPCRetriever(
                client=self.supabase, 
                embeddings=embeddings, 
                top_k=vector_top_k, 
                threshold=rpc_threshold
            )
            
            if self.database_bm25_retriever:
                # Update the k parameter for the database BM25 retriever
                self.database_bm25_retriever.top_k = bm25_top_k
                return EnsembleRetriever(
                    retrievers=[vector_retriever, self.database_bm25_retriever], 
                    weights=kwargs.get("ensemble_weights", self.config.default_ensemble_weights)
                )
            
            return vector_retriever  # Fallback to vector-only if BM25 is not available
        except Exception as e:
            self.logger.error(f"Error creating retriever: {e}")
            return None  # Return None on failure

    def get_adaptive_retriever(self, query: str, **kwargs) -> Optional[BaseRetriever]:
        """Create a retriever with adaptive threshold handling"""
        if not self.config.adaptive_threshold_enabled:
            return self.get_hybrid_retriever(**kwargs)
        
        # Try with the highest threshold first
        for threshold in self.config.adaptive_threshold_steps:
            try:
                kwargs['rpc_threshold'] = threshold
                retriever = self.get_hybrid_retriever(**kwargs)
                if retriever:
                    # Test if the retriever returns any documents using the new invoke method
                    test_docs = retriever.invoke(query)
                    if len(test_docs) >= self.config.min_document_count:
                        self.logger.info(f"Adaptive threshold successful with {threshold}: {len(test_docs)} documents")
                        return retriever
                    else:
                        self.logger.info(f"Threshold {threshold} returned only {len(test_docs)} documents, trying next")
            except Exception as e:
                self.logger.warning(f"Error with threshold {threshold}: {e}")
                continue
        
        self.logger.warning("No adaptive threshold found sufficient documents")
        return None

    def _check_document_relevance(self, documents: List[Document]) -> bool:
        """Check if documents are relevant to Dominican social security system"""
        if not documents:
            return False
        
        # Keywords that indicate relevance to Dominican social security
        relevant_keywords = [
            'pensiones', 'jubilación', 'seguridad social', 'sipen', 'dominicano', 'dominicana',
            'ley 87-01', 'régimen contributivo', 'régimen subsidiado', 'afp', 'sistema de pensiones',
            'contribuciones', 'cotizaciones', 'beneficiarios', 'pensionado', 'jubilado',
            'república dominicana', 'rd', 'santo domingo', 'santiago', 'puerto plata',
            'afiliación', 'registro', 'certificación', 'documentos', 'requisitos'
        ]
        
        # Check if any document contains relevant keywords
        for doc in documents:
            content_lower = doc.page_content.lower()
            if any(keyword in content_lower for keyword in relevant_keywords):
                return True
        
        # If no relevant keywords found, check metadata
        for doc in documents:
            source_lower = (doc.metadata.get('source', '') or '').lower()
            doc_type_lower = (doc.metadata.get('doc_type', '') or '').lower()
            
            if any(keyword in source_lower for keyword in relevant_keywords) or \
               any(keyword in doc_type_lower for keyword in relevant_keywords):
                return True
        
        return False

    def query_rag(self, query: str, **kwargs) -> Dict[str, Any]:
        params = { k: kwargs.get(k, getattr(self.config, f"default_{k}")) for k in ["embedding_model", "vector_top_k", "bm25_top_k", "rpc_threshold", "ensemble_weights", "temperature", "chat_model"] }
        try:
            # Use adaptive retriever if enabled, otherwise use regular hybrid retriever
            if self.config.adaptive_threshold_enabled:
                retriever = self.get_adaptive_retriever(query, **params)
            else:
                retriever = self.get_hybrid_retriever(**params)
            
            # This check prevents the ValidationError
            if not retriever:
                self.logger.warning("No retriever could be initialized - no relevant documents found")
                return {
                    "answer": "Favor revisar la pregunta para que tenga relacion con el sistema dominicano de seguridad social",
                    "source_documents": [],
                    "parameters_used": params,
                    "warning": "No se encontraron documentos relevantes"
                }

            # Get documents to check if we have sufficient context
            source_documents = retriever.invoke(query)
            
            # Check if we have sufficient documents AND they are relevant
            if len(source_documents) < self.config.min_document_count or not self._check_document_relevance(source_documents):
                self.logger.warning(f"Insufficient or irrelevant documents found: {len(source_documents)} documents")
                return {
                    "answer": "Favor revisar la pregunta para que tenga relacion con el sistema dominicano de seguridad social",
                    "source_documents": [],
                    "parameters_used": params,
                    "warning": f"Solo se encontraron {len(source_documents)} documentos relevantes"
                }

            llm = ChatOpenAI(model=params["chat_model"], temperature=params["temperature"], openai_api_key=self.config.openai_api_key)
            system_message_content = "Eres un experto en el sistema de pensiones dominicano..."
            human_template = "Por favor, responde la siguiente pregunta... Contexto:\n{context}\n\n---\nPregunta: {question}"
            custom_prompt = ChatPromptTemplate.from_messages([("system", system_message_content), ("human", human_template)])
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm, chain_type="stuff", retriever=retriever,
                return_source_documents=True, chain_type_kwargs={"prompt": custom_prompt}
            )
            result = qa_chain.invoke({"query": query})

            # Enhanced source document processing with score information
            unique_sources = {}
            total_score = 0
            for doc in result.get("source_documents", []):
                source_name = (doc.metadata.get("source") or "").strip()
                doc_type = (doc.metadata.get("doc_type") or "").strip().lower()
                score = doc.metadata.get("score", 0.0)
                retriever_type = doc.metadata.get("retriever_type", "unknown")
                norm = source_name.lower()

                if source_name and norm != "none":
                    if norm not in unique_sources:
                        # Use the more reliable 'doc_type' for the condition
                        if doc_type == "leyes":
                            link = f"https://www.sipen.gob.do/descarga/{source_name}"
                        else:
                            link = f"https://www.sipen.gob.do/documentos/{source_name}"
                        
                        unique_sources[norm] = {
                            "source_name": source_name, 
                            "url": link,
                            "doc_type": doc_type,
                            "avg_score": score,
                            "retriever_type": retriever_type
                        }
                    else:
                        # Update average score if document appears multiple times
                        current_avg = unique_sources[norm]["avg_score"]
                        unique_sources[norm]["avg_score"] = (current_avg + score) / 2
                    
                    total_score += score

            # Calculate average confidence score
            avg_confidence = total_score / len(result.get("source_documents", [])) if result.get("source_documents") else 0

            return { 
                "answer": result["result"], 
                "source_documents": list(unique_sources.values()), 
                "parameters_used": params,
                "confidence_score": avg_confidence,
                "document_count": len(result.get("source_documents", [])),
                "unique_sources_count": len(unique_sources)
            }
        except Exception as e:
            self.logger.error(f"Error in RAG query: {e}", exc_info=True)
            return { 
                "answer": f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}", 
                "source_documents": [], 
                "parameters_used": params,
                "error": str(e)
            }
            
    def test_connection(self) -> Dict[str, str]:
        try:
            self.supabase.table("chunk_embeddings").select("id").limit(1).execute()
            return {"status": "success", "message": "Connected to Supabase successfully."}
        except Exception as e:
            return {"status": "error", "message": f"Connection failed: {e}"}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main_config = RAGConfig()
    
    print("\n--- Testing RAG Service with Database BM25 ---")
    rag_service = RAGService(main_config)
    if rag_service.test_connection()["status"] == "success":
        user_query = "Que dice la ley 87-01 sobre el régimen contributivo de pensiones y jubilaciones?"
        print(f"Testing query: {user_query}")
        
        result = rag_service.query_rag(user_query)
        print(f"Answer: {result.get('answer', '')[:200]}...")
        print(f"Sources: {len(result.get('source_documents', []))} documents")
    else:
        print("Failed to connect to Supabase")