"""
VeriFlow: A Multimodal Digital Trust & Forensic Memory Agent

This package provides tools for tracking and verifying claims across different media types
(text, images, audio) using Qdrant vector database and multimodal embeddings.
"""

__version__ = "1.0.0"
__author__ = "VeriFlow Team"

from src.config import settings
from src.models import (
    ClaimMetadata,
    MediaType,
    Platform,
    TrustLevel,
    ClaimInput,
    SearchQuery,
    ProvenanceReport,
)

__all__ = [
    "settings",
    "ClaimMetadata",
    "MediaType",
    "Platform",
    "TrustLevel",
    "ClaimInput",
    "SearchQuery",
    "ProvenanceReport",
]
