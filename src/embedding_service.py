import torch
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer
from sentence_transformers import SentenceTransformer
from PIL import Image
import whisper
import numpy as np
from typing import Union, List, Optional
from loguru import logger
import io

from src.config import settings


class EmbeddingService:
    """Service for generating embeddings from different media types."""
    
    def __init__(self):
        """Initialize embedding models."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize CLIP for image-text embeddings
        self._init_clip()
        
        # Initialize text embedding model
        self._init_text_model()
        
        # Initialize Whisper for audio transcription
        self._init_whisper()
    
    def _init_clip(self):
        """Initialize CLIP model for multimodal embeddings."""
        try:
            logger.info(f"Loading CLIP model: {settings.clip_model}")
            self.clip_model = CLIPModel.from_pretrained(settings.clip_model).to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained(settings.clip_model)
            self.clip_tokenizer = CLIPTokenizer.from_pretrained(settings.clip_model)
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def _init_text_model(self):
        """Initialize text embedding model."""
        try:
            logger.info("Loading text embedding model")
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Text embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load text embedding model: {e}")
            raise
    
    def _init_whisper(self):
        """Initialize Whisper model for audio transcription."""
        try:
            logger.info(f"Loading Whisper model: {settings.whisper_model}")
            self.whisper_model = whisper.load_model(settings.whisper_model)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using CLIP."""
        try:
            inputs = self.clip_tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            ).to(self.device)
            
            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**inputs)
                # Normalize embeddings
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            embedding = text_features.cpu().numpy()[0].tolist()
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise
    
    def embed_image(self, image: Union[Image.Image, bytes, str]) -> List[float]:
        """Generate embedding for an image using CLIP."""
        try:
            # Handle different input types
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))
            elif isinstance(image, str):
                image = Image.open(image)
            
            # Ensure RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Process image
            inputs = self.clip_processor(
                images=image,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                # Normalize embeddings
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            embedding = image_features.cpu().numpy()[0].tolist()
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed image: {e}")
            raise
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file to text using Whisper."""
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            result = self.whisper_model.transcribe(audio_path)
            transcription = result["text"]
            logger.info(f"Transcription completed: {len(transcription)} characters")
            return transcription
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise
    
    def embed_audio(self, audio_path: str) -> tuple[List[float], str]:
        """
        Generate embedding for audio by first transcribing it,
        then embedding the transcription.
        Returns both the embedding and the transcription.
        """
        try:
            # Transcribe audio
            transcription = self.transcribe_audio(audio_path)
            
            # Embed transcription
            embedding = self.embed_text(transcription)
            
            return embedding, transcription
            
        except Exception as e:
            logger.error(f"Failed to embed audio: {e}")
            raise
    
    def embed_multimodal(
        self,
        text: Optional[str] = None,
        image: Optional[Union[Image.Image, bytes, str]] = None,
        audio_path: Optional[str] = None,
    ) -> tuple[List[float], Optional[str]]:
        """
        Generate a combined embedding from multiple modalities.
        Returns the embedding and any transcription (if audio was provided).
        """
        try:
            embeddings = []
            transcription = None
            
            if text:
                text_emb = self.embed_text(text)
                embeddings.append(text_emb)
            
            if image:
                image_emb = self.embed_image(image)
                embeddings.append(image_emb)
            
            if audio_path:
                audio_emb, transcription = self.embed_audio(audio_path)
                embeddings.append(audio_emb)
            
            if not embeddings:
                raise ValueError("At least one modality must be provided")
            
            # Average embeddings if multiple modalities
            if len(embeddings) > 1:
                combined = np.mean(embeddings, axis=0)
                # Renormalize
                combined = combined / np.linalg.norm(combined)
                return combined.tolist(), transcription
            else:
                return embeddings[0], transcription
                
        except Exception as e:
            logger.error(f"Failed to create multimodal embedding: {e}")
            raise
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            raise


# Global embedding service instance
embedding_service = EmbeddingService()
