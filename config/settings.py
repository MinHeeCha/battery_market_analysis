"""
Global configuration for Battery Analysis System
"""
import os
from dataclasses import dataclass, field
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM configuration"""
    model: str = os.getenv("LLM_MODEL", "gpt-4")
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


@dataclass
class RAGConfig:
    """RAG configuration"""
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")  # 'cpu', 'cuda', 'mps'
    vector_store_type: Literal["chroma", "pinecone"] = "chroma"
    chunk_size: int = 500
    chunk_overlap: int = 100
    vector_store_path: str = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")


@dataclass
class ProjectConfig:
    """Main project configuration"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    
    # Paths
    data_dir: str = os.getenv("DATA_DIR", "./data")
    output_dir: str = os.getenv("OUTPUT_DIR", "./outputs")
    
    # Runtime settings
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("RETRY_DELAY", "2"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Search settings
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    use_web_search: bool = os.getenv("USE_WEB_SEARCH", "false").lower() == "true"
    
    def __post_init__(self):
        """Validate and create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/reports_md", exist_ok=True)
        os.makedirs(f"{self.output_dir}/reports_pdf", exist_ok=True)
        os.makedirs(f"{self.output_dir}/logs", exist_ok=True)


# Global config instance
config = ProjectConfig()
