from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MediaType(str, Enum):
    """Supported media types for claims."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class Platform(str, Enum):
    """Social media platforms where claims can originate."""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    NEWS_WEBSITE = "news_website"
    PODCAST = "podcast"
    OTHER = "other"


class TrustLevel(str, Enum):
    """Trust level classification for claims."""
    VERIFIED = "verified"
    LIKELY_TRUE = "likely_true"
    UNCERTAIN = "uncertain"
    LIKELY_FALSE = "likely_false"
    DEBUNKED = "debunked"


class ClaimMetadata(BaseModel):
    """Metadata associated with a claim in Qdrant."""
    claim_id: str
    media_type: MediaType
    platform: Platform
    source_url: Optional[str] = None
    timestamp: datetime
    trust_score: float = Field(ge=0.0, le=1.0, default=0.5)
    trust_level: TrustLevel = TrustLevel.UNCERTAIN
    verification_count: int = 0
    supporting_evidence_count: int = 0
    refuting_evidence_count: int = 0
    last_updated: datetime
    original_text: Optional[str] = None
    transcription: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class EvidenceEntry(BaseModel):
    """A piece of evidence supporting or refuting a claim."""
    evidence_id: str
    claim_id: str
    media_type: MediaType
    content: str
    source_url: Optional[str] = None
    timestamp: datetime
    is_supporting: bool
    credibility_score: float = Field(ge=0.0, le=1.0)


class ClaimInput(BaseModel):
    """Input model for submitting a new claim."""
    content: Optional[str] = None
    media_type: MediaType
    platform: Platform
    source_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SearchQuery(BaseModel):
    """Input model for searching claims."""
    query: Optional[str] = None
    media_type: Optional[MediaType] = None
    platform: Optional[Platform] = None
    trust_level: Optional[TrustLevel] = None
    min_trust_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_trust_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=10, ge=1, le=100)


class ClaimEvolution(BaseModel):
    """Represents the evolution of a claim over time."""
    claim_id: str
    original_claim: ClaimMetadata
    related_claims: List[ClaimMetadata]
    evidence_trail: List[EvidenceEntry]
    trust_score_history: List[Dict[str, Any]]


class ProvenanceReport(BaseModel):
    """Comprehensive provenance report for a claim."""
    claim_id: str
    current_status: ClaimMetadata
    trust_assessment: str
    evidence_summary: str
    timeline: List[Dict[str, Any]]
    related_claims: List[ClaimMetadata]
    recommendation: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    qdrant_connected: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
