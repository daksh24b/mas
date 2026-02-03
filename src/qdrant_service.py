from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    DatetimeRange,
)
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import uuid

from src.config import settings
from src.models import ClaimMetadata, MediaType, Platform, TrustLevel


class QdrantService:
    """Service for managing Qdrant vector database operations."""
    
    def __init__(self):
        """Initialize Qdrant client and create collection if needed."""
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Qdrant client connection."""
        try:
            if settings.qdrant_api_key:
                self.client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    api_key=settings.qdrant_api_key,
                )
            else:
                self.client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                )
            logger.info(f"Connected to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(self, embedding_dim: int = 512):
        """Create the Qdrant collection with appropriate schema."""
        try:
            # Check if collection already exists
            collections = self.client.get_collections().collections
            if any(col.name == self.collection_name for col in collections):
                logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            # Create collection with vector configuration
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            
            # Create payload indexes for efficient filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="media_type",
                field_schema="keyword",
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="platform",
                field_schema="keyword",
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="trust_level",
                field_schema="keyword",
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="trust_score",
                field_schema="float",
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="timestamp",
                field_schema="datetime",
            )
            
            logger.info(f"Successfully created collection '{self.collection_name}'")
            
        except Exception as e:
            # Handle 409 Conflict (collection already exists) gracefully
            if "already exists" in str(e):
                logger.info(f"Collection '{self.collection_name}' already exists (concurrent creation)")
            else:
                logger.error(f"Failed to create collection: {e}")
                raise
    
    def insert_claim(
        self,
        embedding: List[float],
        metadata: ClaimMetadata,
    ) -> str:
        """Insert a new claim into Qdrant."""
        try:
            point_id = str(uuid.uuid4())
            
            # Convert metadata to dictionary
            payload = metadata.model_dump()
            payload["timestamp"] = payload["timestamp"].isoformat()
            payload["last_updated"] = payload["last_updated"].isoformat()
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
            
            logger.info(f"Inserted claim with ID: {point_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"Failed to insert claim: {e}")
            raise
    
    def search_claims(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar claims using vector similarity and optional filters."""
        try:
            # Build filter conditions
            filter_conditions = None
            if filters:
                conditions = []
                
                if "media_type" in filters:
                    conditions.append(
                        FieldCondition(
                            key="media_type",
                            match=MatchValue(value=filters["media_type"]),
                        )
                    )
                
                if "platform" in filters:
                    conditions.append(
                        FieldCondition(
                            key="platform",
                            match=MatchValue(value=filters["platform"]),
                        )
                    )
                
                if "trust_level" in filters:
                    conditions.append(
                        FieldCondition(
                            key="trust_level",
                            match=MatchValue(value=filters["trust_level"]),
                        )
                    )
                
                if "min_trust_score" in filters or "max_trust_score" in filters:
                    conditions.append(
                        FieldCondition(
                            key="trust_score",
                            range=Range(
                                gte=filters.get("min_trust_score"),
                                lte=filters.get("max_trust_score"),
                            ),
                        )
                    )
                
                if conditions:
                    filter_conditions = Filter(must=conditions)
            
            # Perform search
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=filter_conditions,
            ).points
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search claims: {e}")
            raise
    
    def update_trust_score(
        self,
        claim_id: str,
        new_trust_score: float,
        new_trust_level: TrustLevel,
        verification_count: Optional[int] = None,
    ):
        """Update the trust score and related metadata for a claim."""
        try:
            updates = {
                "trust_score": new_trust_score,
                "trust_level": new_trust_level.value,
                "last_updated": datetime.utcnow().isoformat(),
            }
            
            if verification_count is not None:
                updates["verification_count"] = verification_count
            
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=updates,
                points=[claim_id],
            )
            
            logger.info(f"Updated trust score for claim {claim_id}: {new_trust_score}")
            
        except Exception as e:
            logger.error(f"Failed to update trust score: {e}")
            raise
    
    def get_claim_by_id(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific claim by its ID."""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[claim_id],
            )
            
            if result:
                return {
                    "id": result[0].id,
                    "payload": result[0].payload,
                    "vector": result[0].vector,
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve claim: {e}")
            raise
    
    def get_related_claims(
        self,
        claim_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get claims related to a specific claim based on vector similarity."""
        try:
            # First get the target claim
            claim = self.get_claim_by_id(claim_id)
            if not claim or not claim.get("vector"):
                return []
            
            # Search for similar claims
            results = self.search_claims(
                query_vector=claim["vector"],
                limit=limit + 1,  # +1 to exclude the original claim
            )
            
            # Filter out the original claim
            related = [r for r in results if r["id"] != claim_id][:limit]
            return related
            
        except Exception as e:
            logger.error(f"Failed to get related claims: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Qdrant connection is healthy."""
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant service instance
qdrant_service = QdrantService()
