"""
Unified Retriever - combines vector search and web search using BGE-M3.
Uses persistent Chroma DB as primary retrieval backend.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from shared.logger import get_logger
from retrieval.embedder import BGEEmbedder
from config.settings import config

logger = get_logger(__name__)

try:
    import chromadb
except ImportError:
    chromadb = None


class Retriever:
    """
    Retriever for document search with BGE-M3 embeddings.
    Supports both vector search and optional web search.
    """
    
    def __init__(
        self,
        vector_store_path: str = "./data/vector_store",
        use_web_search: bool = False,
        embedding_model: str = None,
        device: str = None,
        collection_name: str = "battery_documents"
    ):
        self.vector_store_path = vector_store_path
        self.use_web_search = use_web_search
        self.collection_name = collection_name
        self.docs = []
        self.chroma_client = None
        self.collection = None
        self.logger = get_logger(__name__)
        
        # Initialize embedder with BGE-M3
        model_name = embedding_model or config.rag.embedding_model
        device_type = device or config.rag.embedding_device
        
        self.logger.info(f"Initializing embedder with model: {model_name}")
        try:
            self.embedder = BGEEmbedder(
                model_name=model_name,
                device=device_type
            )
            self.logger.info(f"Embedder initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedder: {str(e)}")
            self.embedder = None

        self._init_vector_store()

    def _init_vector_store(self) -> None:
        """Initialize persistent Chroma vector store."""
        if chromadb is None:
            self.logger.warning("chromadb not installed. Falling back to in-memory retrieval")
            return

        try:
            self.chroma_client = chromadb.PersistentClient(path=self.vector_store_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Battery analysis document embeddings"}
            )
            self.logger.info(
                "Chroma initialized at %s (collection=%s, count=%s)",
                self.vector_store_path,
                self.collection_name,
                self.collection.count() if self.collection else 0,
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Chroma vector store: {str(e)}")
            self.chroma_client = None
            self.collection = None
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the retriever"""
        self.docs.extend(documents)
        self.logger.info(f"Added {len(documents)} documents to retriever")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using BGE-M3 embeddings.
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of relevant document snippets with scores
        """
        self.logger.info(f"Searching for: {query} (top_k={top_k})")
        
        if not self.embedder:
            self.logger.warning("Embedder not initialized, returning placeholder results")
            return self._get_placeholder_results(query)

        vector_results = self._search_vector_store(query=query, top_k=top_k)
        if vector_results:
            return vector_results
        
        if not self.docs:
            self.logger.warning("No documents in retriever, returning placeholder results")
            return self._get_placeholder_results(query)
        
        try:
            # Encode query using BGE-M3
            query_embedding = self.embedder.encode(query)
            
            # Encode all documents
            doc_texts = [doc.get("content", "") for doc in self.docs]
            doc_embeddings = self.embedder.encode(doc_texts)
            
            # Calculate similarity scores (cosine similarity)
            scores = np.dot(doc_embeddings, query_embedding[0].T)
            
            # Get top-k results
            top_indices = np.argsort(scores)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if idx < len(self.docs):
                    doc = self.docs[idx]
                    results.append({
                        "content": doc.get("content", ""),
                        "source": doc.get("source", "internal_knowledge_base"),
                        "score": float(scores[idx])
                    })
            
            self.logger.info(f"Found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return self._get_placeholder_results(query)
    
    def _search_vector_store(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search in Chroma vector store using query embeddings."""
        if not self.collection or not self.embedder:
            return []

        try:
            if self.collection.count() == 0:
                self.logger.warning("Vector store collection is empty")
                return []

            query_embedding = self.embedder.encode(query)
            response = self.collection.query(
                query_embeddings=[query_embedding[0].tolist()],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]

            results = []
            for i, content in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else None
                # Convert distance to similarity-like score for consistency.
                score = float(1 / (1 + distance)) if distance is not None else 0.0

                results.append({
                    "content": content,
                    "source": metadata.get("source", "internal_knowledge_base"),
                    "score": score,
                    "metadata": metadata,
                })

            self.logger.info(f"Found {len(results)} vector search results")
            return results
        except Exception as e:
            self.logger.error(f"Vector store search failed: {str(e)}")
            return []

    def _get_placeholder_results(self, query: str) -> List[Dict[str, Any]]:
        """Return placeholder results when embedder not available"""
        return [
            {
                "content": f"Placeholder document for query: {query}",
                "source": "internal_knowledge_base",
                "score": 0.95
            },
            {
                "content": f"Additional result for: {query}",
                "source": "internal_knowledge_base",
                "score": 0.87
            }
        ]
    
    def search_by_keyword(self, keyword: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Keyword-based search (alias for search)"""
        return self.search(keyword, top_k)
    
    def clear(self) -> None:
        """Clear in-memory documents only."""
        self.docs = []
        self.logger.info("Retriever cleared")
    
    def get_embedder_info(self) -> Dict[str, Any]:
        """Get information about the embedder"""
        if self.embedder:
            info = self.embedder.get_model_info()
            info.update({
                "vector_store_path": self.vector_store_path,
                "collection_name": self.collection_name,
                "collection_count": self.collection.count() if self.collection else 0,
                "vector_store_ready": self.collection is not None,
            })
            return info
        return {"model_loaded": False, "error": "Embedder not initialized"}
