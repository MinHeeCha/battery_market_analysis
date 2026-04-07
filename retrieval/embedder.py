"""
Embedder - handles embedding generation using BGE-M3 model
"""
from typing import List, Union
import numpy as np
from shared.logger import get_logger

logger = get_logger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
    SentenceTransformer = None


class BGEEmbedder:
    """
    Embedder using BAAI/bge-m3 model (open-source, multilingual).
    
    BGE-M3 Advantages:
    - Open-source and free (Apache 2.0 license)
    - Supports 111+ languages
    - Superior multilingual performance
    - Can run locally without API calls
    - No rate limits or usage costs
    """
    
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        """
        Initialize BGE-M3 embedder.
        
        Args:
            model_name: HuggingFace model name (default: BAAI/bge-m3)
            device: Device to use ('cpu', 'cuda', 'mps')
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.logger = get_logger(__name__)
        
        self._load_model()
    
    def _load_model(self):
        """Load the BGE-M3 model"""
        if SentenceTransformer is None:
            self.logger.error("sentence-transformers not installed")
            return
        
        try:
            self.logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True
            )
            self.logger.info(f"Model loaded successfully on device: {self.device}")
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize_embeddings: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts: Single text or list of texts to encode
            normalize_embeddings: Whether to normalize embeddings to unit length
            batch_size: Batch size for encoding
            
        Returns:
            Embeddings as numpy array (shape: [num_texts, 1024] for BGE-M3)
        """
        if not self.model:
            self.logger.error("Model not loaded")
            raise RuntimeError("Embedder model not initialized")
        
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize_embeddings,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 10
            )
            return embeddings
        except Exception as e:
            self.logger.error(f"Encoding failed: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        if not self.model:
            return 0
        return self.model.get_sentence_embedding_dimension()
    
    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dimension": self.get_embedding_dimension(),
            "model_loaded": self.model is not None
        }
