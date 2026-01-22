import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "veriflow_claims"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    
    # Application Settings
    log_level: str = "INFO"
    max_upload_size: str = "50MB"
    
    # Model Configuration
    use_local_models: bool = True
    clip_model: str = "openai/clip-vit-base-patch32"
    whisper_model: str = "base"
    
    # Trust Score Thresholds
    trust_score_high: float = 0.7
    trust_score_medium: float = 0.4
    trust_score_low: float = 0.0
    
    # Vector dimensions
    clip_embedding_dim: int = 512
    text_embedding_dim: int = 384
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
